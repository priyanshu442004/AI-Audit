import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
# Let's find any pkl files from S3 uploads.
# The `get_cache_path` hash files. Let's find the pkl files in `CACHE_DIR`.
for fn in os.listdir(cache_dir):
    if len(fn) == 36 and fn.endswith(".pkl"): # MD5 is 32 chars + .pkl is 4 chars = 36 chars
        p = os.path.join(cache_dir, fn)
        try:
            with open(p, "rb") as f:
                df = pickle.load(f)
            # Check what kind of DataFrame this is by checking columns
            print(f"\nCache file: {fn}")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)[:10]}")
        except Exception as e:
            pass
