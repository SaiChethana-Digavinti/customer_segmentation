import pandas as pd

file_path = "data/raw/UCI online retail dataset/Online Retail.xlsx"

df = pd.read_excel(file_path)

print("\nDataset loaded successfully!")
print("\nShape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())