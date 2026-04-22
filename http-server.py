from http.server import HTTPServer, SimpleHTTPRequestHandler

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

# Serves on port 1000
HTTPServer(('0.0.0.0', 1000), CORSRequestHandler).serve_forever()
