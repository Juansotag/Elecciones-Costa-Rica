import pandas as pd
xl = pd.ExcelFile('Scrapping data v2.xlsx')
df = pd.read_excel(xl, sheet_name='Facebook', nrows=1)
print("FB_FIRST_ROW")
print(df.iloc[0].to_dict())
print("FB_COLS_LIST")
print(df.columns.tolist())
