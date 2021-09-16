import http.server
import socketserver

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/v1/api/center818/box/version/file/':
            self.path = '/v1/api/center818/box/version/file/test_file.txt'
        elif self.path == '/v1/api/center818/box/version/check/':
            self.path = '/v1/api/center818/box/version/check/check'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Create an object of the above class
handler_object = MyHttpRequestHandler

PORT = 8088
my_server = socketserver.TCPServer(("172.0.0.1", PORT), handler_object)

# Star the server
my_server.serve_forever()