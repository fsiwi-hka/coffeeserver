import math
from sqlalchemy import *#Column, Integer, String, ForeignKey
#from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *#backref, mapper, relation, sessionmaker
 
Base = declarative_base()
 
class Wallet(Base):
    __tablename__ = "wallets"
 
    id = Column(Integer, primary_key=True)
    mifareid = Column(Integer)
    cardid = Column(Integer)
    balance = Column(Float)
 
    def __init__(self, mifareid, cardid):
        self.mifareid = mifareid
        self.cardid = cardid
        self.balance = 0.0
 
    def __repr__(self):
        return "<Wallet('%s','%s', '%s', '%s')>" % (self.id, self.mifareid, self.carid, self.balance)
 
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    walletid = Column(Integer, ForeignKey('wallets.id'))
    time = Column(Integer)
    wallet = relation(Wallet, backref=backref('transactions', order_by=id))
    change = Column(Float)
    description = Column(String)
 
    def __init__(self, time, change, description = ""):
        self.time = time
        self.change = change
        self.description = description
 
    def __repr__(self):
        return "<Transaction('%s', '%s', '%s', '%s', '%s')>" % (self.id, self.time, self.walletid, self.wallet, self.change)
 
class Payment(object):
    def __init__(self, dbfile = "payment.db", debug=False):
        self.engine = create_engine("sqlite:///" + str(dbfile), echo=debug) 
        self.metadata = Base.metadata
        self.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def getWalletByCard(self, mifareid, cardid):
        return self.session.query(Wallet).filter_by(mifareid=mifareid, cardid=cardid).first()

    def getWalletById(self, id):
        return self.session.query(Wallet).filter_by(id=id).first()

    def addWallet(self, mifareid, cardid):
        wallet = Wallet(mifareid, cardid)
        self.session.add(wallet)
        self.session.commit()
        return wallet

    def addBalance(self, wallet, balance):
        if wallet == None:
            return
        
        wallet.balance = wallet.balance + balance
        wallet.transactions.append(Transaction(0, balance, "Added moneh"))
        self.session.commit()
        return

    def buyItem(self, wallet, price, description = ""):
        if wallet == None:
            return False

        if wallet.balance < math.fabs(price):
            return False

        wallet.balance = wallet.balance - 1
        wallet.transactions.append(Transaction(0, price, description))
        self.session.commit()
        return True

mifareid = 3
cardid = 6

p = Payment(debug=True)

wallet = p.getWalletByCard(mifareid, cardid)

if wallet == None:
    wallet = p.addWallet(mifareid, cardid)

p.addBalance(wallet, 1)
p.buyItem(wallet, -1.0, "Club-Mate")
p.buyItem(wallet, -1.0, "Club-Mate")
