import webview
import os
import threading
import http.server
import socketserver

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 18432

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)
    def log_message(self, format, *args):
        pass  # kein Output im Terminal

def start_server():
    with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as httpd:
        httpd.serve_forever()

thread = threading.Thread(target=start_server, daemon=True)
thread.start()

class Api:
    def open_image(self, path):
        webview.create_window(
            'Bild',
            html=f'''<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin:0; padding:0; }}
  body {{ background:#000; display:flex; align-items:center;
          justify-content:center; height:100vh; overflow:hidden; }}
  img {{ max-width:100%; max-height:100vh; object-fit:contain; }}
</style>
</head>
<body>
  <img src="{path}">
</body>
</html>''',
            width=1400,
            height=900,
            resizable=True
        )

api = Api()

webview.create_window(
    'PVOC – Projektübersicht',
    f'http://127.0.0.1:{PORT}/projekte.html',
    width=1200,
    height=800,
    resizable=True,
    js_api=api
)

webview.start()
