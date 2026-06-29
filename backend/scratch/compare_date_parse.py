import time
import pandas as pd
from datetime import datetime

date_str = "28/01/26"

print("Timing pd.to_datetime for 10,000 iterations...")
t0 = time.time()
for _ in range(10000):
    try:
        dt = pd.to_datetime(date_str, format="%d/%m/%y")
    except:
        pass
t1 = time.time()
print(f"pd.to_datetime: {t1 - t0:.4f} seconds")

print("\nTiming datetime.strptime for 10,000 iterations...")
t0 = time.time()
for _ in range(10000):
    try:
        dt = datetime.strptime(date_str, "%d/%m/%y")
    except:
        pass
t1 = time.time()
print(f"datetime.strptime: {t1 - t0:.4f} seconds")
