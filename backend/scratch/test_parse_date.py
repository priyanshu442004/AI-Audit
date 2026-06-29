import pandas as pd
from app.analysis.payment_aging_domestic import parse_date

print("Testing parse_date for '28/01/26':")
res = parse_date("28/01/26")
print(f"Result: {res} (type: {type(res)})")

print("\nTesting pd.to_datetime directly:")
try:
    dt = pd.to_datetime("28/01/26", format="%d/%m/%y")
    print(f"Direct: {dt} (isnat: {pd.isnat(dt)})")
except Exception as e:
    print(f"Direct error: {e}")
