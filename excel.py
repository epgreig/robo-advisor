import openpyxl as xl

wb = xl.Workbook()
wb.remove(wb.active)

composition = wb.create_sheet("Composition", 0)
composition.sheet_properties.tabColor = "DC143C"

analytics = wb.create_sheet("Performance", 2)
analytics.sheet_properties.tabColor = "228B22"

analytics = wb.create_sheet("Risk Analytics", 1)
analytics.sheet_properties.tabColor = "FFD700"

wb.save("Report.xlsx")

# Three worksheets for each type of analytic:
#
# Composition
# Backward Peformance Analytics
# Forward Risk Analytics

