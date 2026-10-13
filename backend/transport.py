"""TLS is always verified. macOS curl fallback uses the system certificate store."""
import subprocess
import httpx

def get_bytes(url,timeout=20,limit=30_000_000):
    try:
        with httpx.Client(timeout=timeout,follow_redirects=False) as client:
            with client.stream('GET',url) as response:
                response.raise_for_status();chunks=[];size=0
                for chunk in response.iter_bytes():
                    size+=len(chunk)
                    if size>limit:raise ValueError('Resposta excede limite')
                    chunks.append(chunk)
                return b''.join(chunks)
    except httpx.ConnectError as e:
        if 'CERTIFICATE_VERIFY_FAILED' not in str(e):raise
        # No -k / --insecure: curl must verify TLS with its configured trust store.
        result=subprocess.run(['curl','--fail','--silent','--show-error','--max-time',str(timeout),'--max-filesize',str(limit),url],capture_output=True,timeout=timeout+3,check=True)
        if len(result.stdout)>limit:raise ValueError('Resposta excede limite')
        return result.stdout
