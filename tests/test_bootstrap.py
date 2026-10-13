from backend.bootstrap import excerpt

def test_quote_stops_at_first_terminator():
    assert excerpt('Uma promessa; 8 Outra seção.','Uma promessa')=='Uma promessa;'
