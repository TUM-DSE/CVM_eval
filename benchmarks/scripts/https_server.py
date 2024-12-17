from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
from ctypes import *

my_outb_so = CDLL("/root/libmy_outb.so")


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    global my_outb_so

    def do_GET(self):
        my_outb_so.my_outb(247)
        print("Got a request")
        self.send_response(200)
        self.end_headers()
        # self.wfile.write(b'Hello, world!')

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        print(f"Content len {content_length}")
        body = self.rfile.read(content_length)
        # print(f'Body {body}')
        my_outb_so.my_outb(247)
        self.send_response(200)
        self.end_headers()
        # self.wfile.write(b'Hello, world!')

    def log_message(self, format, *args):
        return


httpd = HTTPServer(("172.45.0.2", 4443), SimpleHTTPRequestHandler)

httpd.socket = ssl.wrap_socket(
    httpd.socket, certfile="/root/server.pem", server_side=True
)

httpd.serve_forever()
