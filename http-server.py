from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

dataset_dir = Path(__file__).parent / "dataset"
os.chdir(dataset_dir)

HTTPServer(('0.0.0.0', 1000), CORSRequestHandler).serve_forever()
