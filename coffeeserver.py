import math, hashlib, time, random, socket, os, sys, json, cgi, ast

from payment import *

sys.path.insert(0, "thirdparty/")
sys.path.insert(0, "coffeeprotocol/")
import config

# Coffeeprotcol
from coffeeprotocol import *

# HTTPS Server
from httpsserver import *


def start():
    server_address = ('', 1443)

    print "Parsing config file ..."
    cfg = config.Config(file("coffeeserver.config"))

    payment = Payment(cfg.server.constring, debug=cfg.server.debug)
    server_cert = cfg.server.server_cert
    client_pub = cfg.server.client_pub

    #wallet = payment.getWalletByCard(3, 6)
    #if wallet == None:
    #    wallet = payment.addWallet(3, 6)
    #    payment.addBalance(wallet, 100)

    items = payment.getItems()
    if len(items) == 0:
        payment.addItem(Item("Kaffee", 5, "coffee.png", True))
        payment.addItem(Item("Club-Mate", 10, "mate.png", True))
       
    httpd = SecureHTTPServer(server_address, SecureHTTPRequestHandler, payment, server_cert, client_pub, cfg.server.debug)
    sa = httpd.socket.getsockname()
    print "Serving HTTPS on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()

if __name__ == '__main__':
    start()

