
import http.server
import socketserver
import os

PORT = 8000

# This will change the current working directory to the directory where this script is located.
# So the server will serve files from this directory.
web_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(web_dir)

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at: http://localhost:{PORT}")
    httpd.serve_forever()
