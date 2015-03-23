import math, hashlib, time, random, socket, os, sys, json, cgi, ast
from SocketServer import BaseServer
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from OpenSSL import SSL
import ssl

# Coffeeprotocol
from coffeeprotocol import *


def toInt(s):
    i = 0
    try:
        i = int(s)
    except:
        pass
    return i

class SecureHTTPServer(HTTPServer):
    def __init__(self, server_address, HandlerClass, payment, server_cert, client_pub, debug = False):
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        self.payment = payment
        self.debug = debug
        #server.pem's location (containing the server private key and
        #the server certificate).
        fpem = server_cert
        self.client_pub = client_pub
        ctx.use_privatekey_file(fpem)
        ctx.use_certificate_file(fpem)
        
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family, self.socket_type))
        self.protocol = CoffeeProtocol()
        
        self.server_bind()
        self.server_activate()

    def shutdown_request(self, request):
        request.shutdown()

class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

    def do_GET(self):
        item = None
        cmd = self.path[1:].split("/")
        if self.path.startswith("/resource/item/"):
            command = cmd[-2]
            id = toInt(cmd[-1])
            item = self.server.payment.getItemById(id)
    
            if item is None:
                return

            if command == "lastModified":
                self.send_response(200)
                self.send_header('Content-type','text/plain')
                self.end_headers()
                ctime = 0
                try:
                    ctime = os.path.getmtime("resource/items/" + item.image)
                except:
                    pass
                self.wfile.write(ctime)

            if command == "image":
                self.send_response(200)
                self.send_header('Content-type','image/png')
                self.end_headers()
                file = open("resource/items/" + item.image, "r")
                self.wfile.write(file.read())
            return

        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("Sorry.")
        
    def do_POST(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type'], })
        request = None
        if form['request']:
            request = form['request'].value
            if self.server.debug:
                print request
            request = ast.literal_eval(request)
        
        if self.path=='/payment/':
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
    
            req = self.server.protocol.parseRequest(request, self.server.client_pub)
            if self.server.debug:
                print "Request:"
                print req
            resp = self.server.payment.parseRequest(req, self.server.protocol.buildResponse())
            resp_comp = resp.compile()
            if self.server.debug:
                print "Response:"
                print resp_comp
            self.wfile.write(resp_comp)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("")
