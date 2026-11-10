# Export the deck to PDF: each slide captured at 2x via the Chrome DevTools protocol, videos replaced by
# their poster frame, then assembled into one PDF.
# Usage (with `python3 -m http.server 8765` serving the folder): pdf.py OUT.pdf N_SLIDES
import os
import base64, io, json, subprocess, sys, time, urllib.request
import websocket
from PIL import Image

out, n_slides = sys.argv[1], int(sys.argv[2])
chrome = subprocess.Popen(["google-chrome", "--headless=new", "--no-first-run", "--disable-gpu", "--hide-scrollbars",
    "--mute-audio", "--remote-debugging-port=9335", "--remote-allow-origins=http://localhost:9335",
    "--user-data-dir=/tmp/claude-1001/pdf-cdp", "--window-size=1280,960", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen("http://localhost:9335/json")); break
        except Exception:
            time.sleep(0.2)
    ws = websocket.create_connection([t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"])
    n = 0
    def call(method, **params):
        global n; n += 1
        ws.send(json.dumps({"id": n, "method": method, "params": params}))
        while True:
            m = json.loads(ws.recv())
            if m.get("id") == n:
                return m.get("result", {})
    call("Emulation.setDeviceMetricsOverride", width=1280, height=960, deviceScaleFactor=2, mobile=False)
    call("Page.navigate", url="http://localhost:8765/#1"); time.sleep(6)
    pages = []
    for s in range(1, n_slides + 1):
        call("Runtime.evaluate", expression='location.hash = "#%d"' % s); time.sleep(1.0)
        js = """(() => {
          const sl = document.querySelector('.remark-visible .remark-slide-content');
          sl.querySelectorAll('video').forEach(v => {
            v.pause(); v.removeAttribute('src');
            v.querySelectorAll('source').forEach(x => x.remove());
            v.load();
          });
          const r = sl.getBoundingClientRect();
          return JSON.stringify([r.x, r.y, r.width, r.height]);
        })()"""
        x, y, w, h = json.loads(call("Runtime.evaluate", expression=js)["result"]["value"])
        time.sleep(1.2)  # let posters load
        png = call("Page.captureScreenshot", format="png",
                   clip={"x": x, "y": y, "width": w, "height": h, "scale": 1})["data"]
        pages.append(Image.open(io.BytesIO(base64.b64decode(png))).convert("RGB"))
        print("slide", s, pages[-1].size, flush=True)
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=200, quality=88)
finally:
    chrome.terminate()
