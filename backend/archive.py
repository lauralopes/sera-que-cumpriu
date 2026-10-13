import ipaddress
import json
import socket
from urllib.parse import urlparse,urlencode
from .transport import get_bytes
from .ingest import now

def validate_public_url(url, resolve=False):
    parsed=urlparse(url)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:raise ValueError('URL pública inválida')
    host=parsed.hostname.lower()
    if host=='localhost' or host.endswith(('.localhost','.local','.internal')) or parsed.port not in (None,80,443):raise ValueError('Endereço local não permitido')
    try:
        if not ipaddress.ip_address(host).is_global:raise ValueError('Endereço privado não permitido')
    except ValueError as e:
        if 'permitido' in str(e):raise
    if resolve:
        for x in socket.getaddrinfo(host,parsed.port or 443,type=socket.SOCK_STREAM):
            if not ipaddress.ip_address(x[4][0]).is_global:raise ValueError('Resolução privada não permitida')
    return url

def parse_snapshot(data, requested_timestamp):
    closest=data.get('archived_snapshots',{}).get('closest',{})
    stamp=closest.get('timestamp')
    link=closest.get('url')
    if link and urlparse(link).hostname!='web.archive.org':raise ValueError('Captura fora do Internet Archive')
    return dict(available=bool(closest.get('available')),timestamp=stamp,url=link,
                status=closest.get('status'),requested_timestamp=requested_timestamp,
                exact_date=bool(stamp and requested_timestamp and stamp[:8]==requested_timestamp[:8]),raw=data)

def wayback(db, url, timestamp='', force=False):
    validate_public_url(url)
    if timestamp and (not timestamp.isdigit() or len(timestamp)>14):raise ValueError('Timestamp inválido')
    cached=db.execute('SELECT * FROM archive_cache WHERE url=? AND requested_timestamp=?',(url,timestamp)).fetchone()
    if cached and not force:
        result=json.loads(cached['response']);result['cached']=True;return result
    data=json.loads(get_bytes('https://archive.org/wayback/available?'+urlencode({'url':url,'timestamp':timestamp}),limit=1_000_000))
    result=parse_snapshot(data,timestamp);result['consulted_at']=now();result['original_url']=url
    with db:db.execute('INSERT INTO archive_cache VALUES(?,?,?,?) ON CONFLICT(url,requested_timestamp) DO UPDATE SET response=excluded.response,consulted_at=excluded.consulted_at',(url,timestamp,json.dumps(result),result['consulted_at']))
    return result
