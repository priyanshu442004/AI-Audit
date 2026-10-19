import requests
import openpyxl
import pandas as pd

# Direct download link for OneDrive link
onedrive_url = "https://1drv.ms/x/c/4221214d1cf08ade/IQBu8oeg5J3UQLDTpuKzE-FWAUhCOiEMWwSHcOchzxPcDYU?e=RPrbYD"
# Convert OneDrive view link to direct download link
# 1drv.ms links can be downloaded by appending &download=1 or converting
download_url = onedrive_url.replace("1drv.ms/x/c/", "api.onedrive.com/v1.0/shares/c!").split('?')[0] + "/root/content"

print("Downloading from OneDrive direct link...")
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(onedrive_url, headers=headers, allow_redirects=True)
print("Initial status:", res.status_code, "Final URL:", res.url)

# Try fetching content if redirected or direct
if "1drv.ms" in onedrive_url:
    # Use alternative download format
    dl_url = "https://onedrive.live.com/download?resid=4221214D1CF08ADE!108&authkey=!AHzyh6DkndRAsNM"
    res2 = requests.get(dl_url, headers=headers)
    print("Download status:", res2.status_code)
    if res2.status_code == 200:
        with open("scratch/onedrive_report.xlsx", "wb") as f:
            f.write(res2.content)
        print("Saved to scratch/onedrive_report.xlsx!")
        
        xl = pd.ExcelFile("scratch/onedrive_report.xlsx")
        print("\nONEDRIVE EXCEL SHEETS:", xl.sheet_names)
        for s in xl.sheet_names:
            print(f"\n--- SHEET: {s} ---")
            df = pd.read_excel("scratch/onedrive_report.xlsx", sheet_name=s)
            print("Shape:", df.shape)
            print("Columns:", list(df.columns[:15]))
            print("Head:")
            print(df.head(3))
