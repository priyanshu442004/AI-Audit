import urllib.request

url = "http://127.0.0.1:8000/api/analyze/combined?entity=ITL&process=P2P"
req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
try:
    with urllib.request.urlopen(req) as response:
        for _ in range(10):
            line = response.readline().decode('utf-8')
            if "result" in line:
                print("SUCCESS: Received SSE result payload!")
                print("Line preview:", line[:200])
                break
            else:
                print("Line:", line.strip())
except Exception as e:
    print("SSE Request error:", e)
