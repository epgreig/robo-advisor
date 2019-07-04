import openpyxl as xl
from openpyxl.styles import Color, PatternFill, Font, Border
from openpyxl.chart import (
    PieChart,
    ProjectedPieChart,
    Reference
)
from openpyxl.chart.series import DataPoint
from openpyxl.styles import colors
from openpyxl.cell import Cell

wb = xl.Workbook()
wb.remove(wb.active)

ws_comp = wb.create_sheet("Composition", 0)
ws_comp.sheet_properties.tabColor = "DC143C"

ws_perf = wb.create_sheet("Performance", 2)
ws_perf.sheet_properties.tabColor = "228B22"

ws_risk = wb.create_sheet("Risk Analytics", 1)
ws_risk.sheet_properties.tabColor = "FFD700"

sheets = [ws_comp, ws_perf, ws_risk]

# Three worksheets for each type of analytic:
#
# Composition
# Backward Peformance Analytics
# Forward Risk Analytics

etfs = ['SPY', 'EFA', 'XLF', 'XLK', 'XLV', 'XLP', 'XLE', 'EWJ', 'EWZ', 'XLU', 'XLI', 'EZU', 'IYR', 'XLB',
        'RWR', 'IXN', 'ISMUF', 'ICF', 'IYZ', 'ILF', 'IEV', 'TIP', 'AGG', 'IEF', 'TLT', 'SHY', 'LQD']

types = ['EQ', 'FI', 'EM', 'RE']

darkBlue  = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
lightBlue = PatternFill(start_color='B8CCE4', end_color='B8CCE4', fill_type='solid')

for ws in sheets:
    for array in [ws['A1':'B1'],
                 ws['A2':'A5'],
                 ws['K1':'L1'],
                 ws['K2':'K28']]:
        for range in array:
            for cell in range:
                cell.fill = darkBlue

    for array in [ws['B2':'B5'],
                  ws['L2':'L28']]:
        for range in array:
            for cell in range:
                cell.fill = lightBlue

    for row, aClass in zip(ws.iter_rows(min_row=2, min_col=1, max_col=1, max_row=5), types):
        for cell in row:
            cell.value = aClass

    for row, etf in zip(ws.iter_rows(min_row=2, min_col=11, max_col=11, max_row=28), etfs):
        for cell in row:
            cell.value = etf

ws_comp['B1'].value = 'Weight by Asset Class'
ws_comp['L1'].value = 'Weight by ETF'

######################
# PLACEHOLDER VALUES #
##################################
ws_comp['B2'].value = 0.2
ws_comp['B3'].value = 0.3
ws_comp['B4'].value = 0.4
ws_comp['B5'].value = 0.1
##################################

pie = PieChart()
labels = Reference(ws_comp, min_col=1, max_col=1, min_row=2, max_row=5)
data = Reference(ws_comp, min_col=2, max_col=2, min_row=1, max_row=5)
pie.add_data(data, titles_from_data=True)
pie.set_categories(labels)
pie.title = "Weight by Asset Class"
pie.height = 7.5
pie.width = 8.5
ws_comp.add_chart(pie, 'A7')

labels = Reference(ws_comp, min_col=1, max_col=1, min_row=2, max_row=5)
data = Reference(ws_comp, min_col=2, max_col=2, min_row=1, max_row=5)

for ws in sheets:
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.coordinate in ws.merged_cells:
                continue
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width

wb.save("Report.xlsx")
