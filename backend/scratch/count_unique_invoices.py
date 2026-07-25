import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def count_unique_docs(fname):
    path = os.path.join(cache_dir, fname)
    if not os.path.exists(path):
        return 0, 0
    with open(path, "rb") as f:
        data = pickle.load(f)
    rows = data.get("rows", [])
    docs = {r.get("invoice_doc_number") for r in rows if r.get("invoice_doc_number") and r.get("invoice_doc_number") != "—"}
    open_docs = {r.get("invoice_doc_number") for r in rows if r.get("invoice_doc_number") and r.get("invoice_doc_number") != "—" and r.get("status") in ('Open', 'Partially paid')}
    return len(docs), len(open_docs)

dom_all, dom_open = count_unique_docs("aging_domestic.pkl")
for_all, for_open = count_unique_docs("aging_foreign.pkl")

print(f"Domestic: All unique docs = {dom_all}, Open unique docs = {dom_open}")
print(f"Foreign: All unique docs = {for_all}, Open unique docs = {for_open}")
print(f"Total Unique Docs: {dom_all + for_all}")
print(f"Total Open Unique Docs: {dom_open + for_open}")
