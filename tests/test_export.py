from io import BytesIO
from openpyxl import load_workbook
from backend.export import export_bytes

def test_formula_text_is_inert_in_both_exports():
    rows=[dict(id='1',description='=HYPERLINK("evil")',refs=[],evidence=[],history=[])]
    csv=export_bytes(rows,'csv').decode('utf-8-sig');assert "'=HYPERLINK" in csv
    wb=load_workbook(BytesIO(export_bytes(rows,'xlsx')))
    cells=[c for row in wb['Compromissos'] for c in row if c.value=='=HYPERLINK("evil")']
    assert cells and cells[0].data_type=='s'
