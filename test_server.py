import urllib.request
import json
import time

endpoints = ['/', '/style.css', '/app.js', '/api/data', '/api/status']
for ep in endpoints:
    t0 = time.time()
    url = f'http://127.0.0.1:8088{ep}'
    req = urllib.request.Request(url, headers={'Connection': 'close'})
    with urllib.request.urlopen(req, timeout=5) as response:
        content = response.read()
        dur = (time.time() - t0) * 1000
        print(f'{ep:15} -> Status: {response.status}, Size: {len(content):6} bytes, Time: {dur:.1f}ms')

# Verify API data
req = urllib.request.Request('http://127.0.0.1:8088/api/data', headers={'Connection': 'close'})
with urllib.request.urlopen(req, timeout=5) as response:
    d = json.loads(response.read().decode('utf-8'))
    print("=" * 50)
    print(f"Categories ({len(d['major_categories'])}):")
    for cat in d['major_categories'][:5]:
        print(f" - #{cat['id']}: {cat['name']:30} Net Flow: ${cat['net_flow_1w']/1e9:6.2f}B (Rate: {cat['inflow_rate_1w']}%)")
    print("=" * 50)
    print("ALL TESTS PASSED SUCCESSFULLY!")
