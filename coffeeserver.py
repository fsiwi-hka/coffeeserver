import math, hashlib, time, random, socket, os, sys, json, cgi, ast
from SocketServer import BaseServer
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from OpenSSL import SSL

from payment import *

sys.path.insert(0, "thirdparty/")
sys.path.insert(0, "coffeeprotocol/")
import config
from coffeeprotocol import *

class SecureHTTPServer(HTTPServer):
    def __init__(self, server_address, HandlerClass, payment):
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        self.payment = payment
        #server.pem's location (containing the server private key and
        #the server certificate).
        fpem = 'server.pem'
        ctx.use_privatekey_file(fpem)
        ctx.use_certificate_file(fpem)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family, self.socket_type))

        self.protocol = CoffeeProtocol()

        self.server_bind()
        self.server_activate()


class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

    def do_GET(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("")
        
    def do_POST(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type'], })
        request = None
        if form['request']:
            request = form['request'].value
            print request
            request = ast.literal_eval(request)
        
        if self.path=='/payment/':
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
    
            req = self.server.protocol.parseRequest(request, "public.pem")
            print req
            resp = self.server.payment.parseRequest(req, self.server.protocol.buildResponse())
            self.wfile.write(resp.compile())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("")

def start():
    server_address = ('', 1443)

    cfg = config.Config(file("coffeeserver.config"))

    payment = Payment(cfg.server.constring, debug=True)

    wallet = payment.getWalletByCard(3, 6)

    if wallet == None:
        wallet = payment.addWallet(3, 6)
        payment.addBalance(wallet, 10)


    httpd = SecureHTTPServer(server_address, SecureHTTPRequestHandler, payment)
    sa = httpd.socket.getsockname()
    print "Serving HTTPS on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()

if __name__ == '__main__':
    start()

