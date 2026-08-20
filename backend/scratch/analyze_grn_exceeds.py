import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.loaders import load_file
from app.cleaning import detect_columns

data_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P New Q2 Data"
ge_path = os.path.join(data_dir, "Gate Entry Report ITL.xls")
grpo_path = os.path.join(data_dir, "new GRPO Report-ITL1.xls")

print("Loading Gate Entry...")
ge_df = load_file(ge_path, "Gate Entry Report ITL.xls")
print(f"Gate Entry shape: {ge_df.shape}")

print("Loading GRPO...")
grpo_df = load_file(grpo_path, "new GRPO Report-ITL1.xls")
print(f"GRPO shape: {grpo_df.shape}")

print("\n--- Gate Entry Columns ---")
print(ge_df.columns.tolist())

print("\n--- GRPO Columns ---")
print(grpo_df.columns.tolist())

print("\n--- Gate Entry Head ---")
print(ge_df.head(2))

print("\n--- GRPO Head ---")
print(grpo_df.head(2))
