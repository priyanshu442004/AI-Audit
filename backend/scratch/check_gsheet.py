import urllib.request
import re
import os
import pandas as pd
import json

url = 'https://docs.google.com/spreadsheets/d/1Ypehh57_0Xawp60QngnWbmql8prtQ1V-2gGqd0eKgCU/edit?usp=sharing'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# Find sheet tab info
gids = re.findall(r'gid=(\d+)', html)
sheet_matches = re.findall(r'\[\d+,\s*\"([^\"]+)\"', html)
print("GIDs found:", set(gids))

# Download first sheet
csv_url = 'https://docs.google.com/spreadsheets/d/1Ypehh57_0Xawp60QngnWbmql8prtQ1V-2gGqd0eKgCU/gviz/tq?tqx=out:csv'
req2 = urllib.request.Request(csv_url, headers={'User-Agent': 'Mozilla/5.0'})
csv_data = urllib.request.urlopen(req2).read().decode('utf-8')

os.makedirs('scratch', exist_ok=True)
with open('scratch/gsheet_raw.csv', 'w', encoding='utf-8') as f:
    f.write(csv_data)

print("Saved raw CSV to scratch/gsheet_raw.csv. Rows count:", len(csv_data.splitlines()))
