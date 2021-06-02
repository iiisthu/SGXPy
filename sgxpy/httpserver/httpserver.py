import SimpleHTTPServer
import SocketServer
import sys

PORT = 8000

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
server_address = ('0.0.0.0', PORT)
httpd = SocketServer.TCPServer(server_address, Handler)
sa = httpd.socket.getsockname()

print "Serving HTTP on", sa[0], "port", sa[1], "..."
sys.stdout.flush()
httpd.serve_forever()
