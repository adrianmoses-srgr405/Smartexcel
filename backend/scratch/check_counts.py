import sys
sys.path.insert(0, '.')
import pandas as pd
from app.core.database import SessionLocal
from app.models.dataset import Dataset

db = SessionLocal()
d = db.query(Dataset).filter_by(id='81189e58-e059-4aba-bde9-2ac5c10e74cd').first()
df = pd.read_excel(d.file_path, sheet_name="Data_Penjualan")

print("Total rows:", len(df))
feb_toyota = df[(df['Merek'] == 'Toyota') & (pd.to_datetime(df['Tanggal']).dt.month == 2)]
print("Toyota Feb 2024 rows:", len(feb_toyota))
print("Branches in Feb Toyota:", feb_toyota['Cabang'].value_counts().to_dict())
print("Kecamatans in Feb Toyota:", feb_toyota['Kecamatan'].value_counts().to_dict())

pekanbaru_cabang = feb_toyota[feb_toyota['Cabang'].str.contains('Pekanbaru', case=False, na=False)]
print("Toyota Feb 2024 in Pekanbaru Cabang:", len(pekanbaru_cabang))

pekanbaru_both = feb_toyota[feb_toyota['Cabang'].str.contains('Pekanbaru', case=False, na=False) & feb_toyota['Kecamatan'].str.contains('Pekanbaru', case=False, na=False)]
print("Toyota Feb 2024 with BOTH Cabang & Kecamatan:", len(pekanbaru_both))
