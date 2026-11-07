# Measure displayed width of the main image/video of given slides (CSS px), via Chrome DevTools.
import json, subprocess, sys, time, urllib.request
import websocket
slides = sys.argv[1:]
chrome = subprocess.Popen(["google-chrome", "--headless=new", "--no-first-run", "--disable-gpu", "--hide-scrollbars",
    "--remote-debugging-port=9334", "--remote-allow-origins=http://localhost:9334",
    "--user-data-dir=/tmp/claude-1001/measure-cdp", "--window-size=1280,960", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen("http://localhost:9334/json")); break
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
    call("Page.navigate", url="http://localhost:8765/#" + slides[0]); time.sleep(5)
    for s in slides:
        call("Runtime.evaluate", expression='location.hash = "#%s"' % s); time.sleep(1.2)
        js = """(() => { const sl = document.querySelector('.remark-visible .remark-slide-content');
          const r0 = sl.getBoundingClientRect();
          return JSON.stringify({slide: r0.width, els: [...sl.querySelectorAll('img, video')].map(e => [ (e.currentSrc||e.src).split('/').pop(), Math.round(e.getBoundingClientRect().width) ])}); })()"""
        print(s, call("Runtime.evaluate", expression=js)["result"]["value"])
finally:
    chrome.terminate()
