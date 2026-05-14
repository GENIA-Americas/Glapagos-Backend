
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime, timezone

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/health/', '/health', '/']:
            body = json.dumps({
                "status": "healthy",
                "platform": "Glapagos - AI Corridor of the Americas",
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "version": "1.0.0",
                "repo": "https://github.com/GENIA-Americas/Glapagos-Backend"
            }).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass

port = int(os.environ.get('PORT', 8000))
print(f'Starting on port {port}')
HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()
