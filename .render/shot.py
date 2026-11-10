# Screenshot remark slides via the Chrome DevTools protocol.
# Usage: shot.py OUTDIR SLIDE [SLIDE ...]
import os
import base64, json, subprocess, sys, time, urllib.request
import websocket

out, slides = sys.argv[1], sys.argv[2:]
chrome = subprocess.Popen(["google-chrome", "--headless=new", "--no-first-run", "--disable-gpu",
    "--hide-scrollbars", "--mute-audio", "--remote-debugging-port=9333",
    "--remote-allow-origins=http://localhost:9333",
    "--user-data-dir=" + out + "/chrome-cdp", "--window-size=1280,960", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen("http://localhost:9333/json")); break
        except Exception:
            time.sleep(0.2)
    ws = websocket.create_connection([t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"])
    n = 0
    def call(method, **params):
        global n; n += 1
        ws.send(json.dumps({"id": n, "method": method, "params": params}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == n:
                return msg.get("result", {})
    call("Page.navigate", url="http://localhost:" + os.environ.get("DECK_PORT", "8765") + "/#" + slides[0])
    time.sleep(5)
    for s in slides:
        call("Runtime.evaluate", expression="location.hash = \"#%s\"" % s)
        time.sleep(1.5)
        png = call("Page.captureScreenshot", format="png")["data"]
        open("%s/slide%s.png" % (out, s), "wb").write(base64.b64decode(png))
        print("slide", s)
finally:
    chrome.terminate()
