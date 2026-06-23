import webview
import os

html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'projekte.html')

webview.create_window(
    'PVOC – Projektübersicht',
    f'file://{html_file}',
    width=1200,
    height=800,
    resizable=True
)

webview.start()
