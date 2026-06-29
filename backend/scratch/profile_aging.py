import pandas as pd
import time
import cProfile
import pstats
import io
from app.analysis.payment_aging_domestic import run_payment_aging_domestic

gl_path = r"C:\Users\hp\Desktop\excel files\General Ledger ITL.csv"
bp_path = r"C:\Users\hp\Desktop\excel files\BP Master-ITL.csv"
po_path = r"C:\Users\hp\Desktop\excel files\Purchase Order Report-ITL.csv"

print("Loading CSV files...")
df_gl = pd.read_csv(gl_path)
df_po = pd.read_csv(po_path)
df_bp = pd.read_csv(bp_path)

dfs = {
    "general_ledger": df_gl,
    "purchase_order": df_po,
    "vendor_master": df_bp
}

print("Running cProfile on run_payment_aging_domestic...")
pr = cProfile.Profile()
pr.enable()

start_time = time.time()
result = run_payment_aging_domestic(dfs)
end_time = time.time()

pr.disable()
print(f"Calculation took {end_time - start_time:.2f} seconds.")

s = io.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats(30)
print(s.getvalue())
