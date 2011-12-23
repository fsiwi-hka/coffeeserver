import json, math

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
 
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    salt = Column(String)
    wallet = relationship("Wallet", uselist=False, backref="users")

    def __init__(self, username, password):
        self.username = username
        self.password = self.hash(password)

        random.seed(time.time()*4.2)
        self.salt = str(time.time()) + ":" + str(random.randint(100000, 999999)) + ":" + str(username)

    def hash(self, password):
        saltedHash = hashlib.sha512(password + str(self.salt)).hexdigest()
        return saltedHash

    def __repr__(self):
        return "<User('%s', '%s', '%s', '%s')>" % (self.id, self.username, self.password, self.wallet)

class Wallet(Base):
    __tablename__ = "wallets"
 
    id = Column(Integer, primary_key=True)
    mifareid = Column(Integer)
    cardid = Column(Integer)
    balance = Column(Integer)
    userid = Column(Integer, ForeignKey('users.id'))
 
    def __init__(self, mifareid, cardid):
        self.mifareid = mifareid
        self.cardid = cardid
        self.balance = 0.0
 
    def __repr__(self):
        return "<Wallet('%s', '%s', '%s', '%s')>" % (self.id, self.mifareid, self.carid, self.balance)
 
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    walletid = Column(Integer, ForeignKey('wallets.id'))
    time = Column(Integer)
    wallet = relationship(Wallet, backref=backref('transactions', order_by=id))
    change = Column(Integer)
    description = Column(String)
 
    def __init__(self, time, change, description = ""):
        self.time = time
        self.change = change
        self.description = description
 
    def __repr__(self):
        return "<Transaction('%s', '%s', '%s', '%s', '%s')>" % (self.id, self.time, self.walletid, self.wallet, self.change)

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    token = Column(Integer)
    value = Column(Integer)
    valid = Column(Boolean)
    used_by = Column(Integer, ForeignKey('wallets.id'))
    used_time = Column(Integer)

    def __init__(self, token, value):
        self.token = token
        self.value = value
        self.valid = True

    def __repr__(self):
        return "<Token('%s', '%s', '%s', '%s')>" % (self.id, self.token, self.value, self.valid)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    price = Column(Integer)
    desc = Column(String)
    image = Column(String)

    def __init__(self, desc, price, image):
        self.desc = desc
        self.price = price
        self.image = image

    def __repr__(self):
        return "<Item('%s', '%s', '%s')>" % (self.price, self.desc, self.image)

class Payment(object):
    def __init__(self, constring= "sqlite:///payment.db", debug=False):
        self.engine = create_engine(constring, echo=debug) 
        self.metadata = Base.metadata
        self.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def addItem(self, item):
        self.session.add(item)
        self.session.commit()
        
    def getItems(self):
        return self.session.query(Item).all()
 
    def getWalletByCard(self, mifareid, cardid):
        return self.session.query(Wallet).filter_by(mifareid=mifareid, cardid=cardid).first()

    def getWalletById(self, id):
        return self.session.query(Wallet).filter_by(id=id).first()

    def addWallet(self, mifareid, cardid):
        wallet = Wallet(mifareid, cardid)
        self.session.add(wallet)
        self.session.commit()
        return wallet

    def addUser(self, username, password, wallet):
        if wallet == None or username == "" or password == "":
            return False

        user = User(username, password)
        user.wallet = wallet
        self.session.add(user)
        self.session.commit()
        return True

    def addBalance(self, wallet, balance):
        if wallet == None:
            return False
        
        wallet.balance = wallet.balance + balance
        wallet.transactions.append(Transaction(0, balance, "Added moneh"))
        self.session.commit()
        return True
    
    def redeemToken(self, wallet, tokenCode):
        if wallet == None or tokenCode == None:
            return False

        token = self.session.query(Token).filter_by(token=tokenCode, valid=True).first()
        if token is not None:
            wallet.balance += token.value
            token.valid = True
            wallet.transactions.append(Transaction(0, token.value, "Redeemed " + str(token.token)))
            self.session.commit()    
            return True

        # Umh... 
        if tokenCode == 1337:
            wallet.balance = wallet.balance + 1000
            wallet.transactions.append(Transaction(0, 100, "Used 1337 cheat code"))
            self.session.commit()
            return True
        
        return False

    def buyItem(self, wallet, price, description = ""):
        if wallet == None:
            return False

        if wallet.balance < math.fabs(price) or math.fabs(price) == 0:
            return False

        wallet.balance = wallet.balance - math.fabs(price)
        wallet.transactions.append(Transaction(0, (price*-1), "Bought " + str(description)))
        self.session.commit()
        return True
    
    def parseRequest(self, request, response):
        response.success = False
        
        if request == None:
            return response

        if request.action == "" or request.mifareid == 0 or request.cardid == 0:
            return response

        wallet = self.getWalletByCard(request.mifareid, request.cardid)
        
        # This is the only command that does not need a valid wallet, it will create one on success 
        if request.action == "redeemToken":
            try:
                code = int(request.data['token'])
            except:
                return response

            if not wallet:
                wallet = self.addWallet(request.mifareid, request.cardid)
            if not wallet:
                return response
            
            if not self.redeemToken(wallet, code):
                return response

            response.success = True
            return response

        # Get balance by cardid, return 0 when card is not known
        if request.action == "getBalance":
            response.data['balance'] = 0
            if wallet:
                response.data['balance'] = wallet.balance
            response.success = True
            return response
  
        # After this, a valid wallet is needed
        if not wallet:
            return response
        
        if request.action == "buyItem":
            try:
                item = int(request.data['item'])
            except:
                return response
            
            price = 0
            desc = ""
            
            if item == 1:
                price = 5
                desc = "Kaffee"

            if item == 2:
                price = 15
                desc = "Club-Mate"

            if self.buyItem(wallet, price, desc):
                response.success = True
                response.data['balance'] = wallet.balance
                return response

            return response
        return response

