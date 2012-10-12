import json, math, time

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
    admin = Column(Boolean)
    wallet = Column(Integer, ForeignKey('wallets.id'))

    def __init__(self, username, password):
        self.username = username
        
        random.seed(time.time()*4.2)
        self.salt = str(time.time()) + ":" + str(random.randint(100000, 999999)) + ":" + str(username)
        self.password = self.hash(password)

    def hash(self, password):
        saltedHash = hashlib.sha512(password + str(self.salt)).hexdigest()
        return saltedHash

    def pack(self):
        packed = {}
        packed['id'] = self.id
        packed['username'] = self.username
        packed['admin'] = self.admin
        return packed

    def __repr__(self):
        return "<User('%s', '%s', '%s', '%s')>" % (self.id, self.username, self.password, self.wallet)

class Wallet(Base):
    __tablename__ = "wallets"
 
    id = Column(Integer, primary_key=True)
    mifareid = Column(BigInteger)
    cardid = Column(BigInteger)
    balance = Column(Integer)
    user = relationship("User", uselist=False, backref="wallets")

    def __init__(self, mifareid, cardid):
        self.mifareid = mifareid
        self.cardid = cardid
        self.balance = 0
 
    def pack(self):
        packed = {}
        packed['id'] = self.id
        packed['mifareid'] = self.mifareid
        packed['cardid'] = self.cardid
        packed['balance'] = self.balance
        return packed

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
 
    def pack(self):
        packed = {}
        packed['id'] = self.id
        packed['walletid'] = self.walletid
        packed['time'] = self.time
        packed['change'] = self.change
        packed['description'] = self.description
        return packed
    
    def __repr__(self):
        return "<Transaction('%s', '%s', '%s', '%s', '%s')>" % (self.id, self.time, self.walletid, self.wallet, self.change)

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String)
    pageHash = Column(String)
    value = Column(Integer)
    valid = Column(Boolean)
    used_by = Column(Integer, ForeignKey('wallets.id'))
    used_time = Column(Integer)

    def __init__(self, token, value):
        self.token = token
        self.value = value
        self.valid = True

    def pack(self):
        packed = {}
        packed['id'] = self.id
        packed['token'] = self.token
        packed['pageHash'] = self.pageHash
        packed['value'] = self.value
        packed['valid'] = self.valid
        packed['used_by'] = self.used_by
        packed['used_time'] = self.used_time
        return packed
    
    def __repr__(self):
        return "<Token('%s', '%s', '%s', '%s')>" % (self.id, self.token, self.value, self.valid)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    price = Column(Integer)
    desc = Column(String)
    image = Column(String)
    enabled = Column(Boolean)

    def __init__(self, desc, price, image, enabled):
        self.desc = desc
        self.price = price
        self.image = image
        self.enabled = enabled

    def pack(self):
        packed = {}
        packed['id'] = self.id
        packed['price'] = self.price
        packed['desc'] = self.desc
        packed['image'] = self.image
        packed['enabled'] = self.enabled
        return packed
 
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

    def getItemById(self, id):
        return self.session.query(Item).filter_by(id=id).first()

    def getWalletByCard(self, mifareid, cardid):
        if mifareid == 0 or cardid == 0:
            return None

        return self.session.query(Wallet).filter_by(mifareid=mifareid, cardid=cardid).first()

    def getWalletById(self, id):
        return self.session.query(Wallet).filter_by(id=id).first()

    def addWallet(self, mifareid, cardid):
        wallet = Wallet(mifareid, cardid)
        self.session.add(wallet)
        self.session.commit()
        return wallet

    def getUserByWalletId(self, walletId):
        return self.session.query(User).filter_by(wallet=walletId).first()

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
        wallet.transactions.append(Transaction(int(time.time()), balance, "Added money"))
        self.session.commit()
        return True
    
    def redeemToken(self, wallet, tokenCode):
        if wallet == None or tokenCode == None:
            return False

        token = self.session.query(Token).filter_by(token=tokenCode, valid=True).first()
        if token is not None:
            wallet.balance += token.value
            token.valid = False
            token.used_by = wallet.id
            token.used_time = time.time()
            wallet.transactions.append(Transaction(int(time.time()), token.value, "Redeemed " + str(token.token)))
            self.session.commit()    
            return True

        return False

    def buyItem(self, wallet, price, description = ""):
        if wallet == None:
            return False

        if wallet.balance < math.fabs(price) or math.fabs(price) == 0:
            return False

        wallet.balance = wallet.balance - math.fabs(price)
        wallet.transactions.append(Transaction(int(time.time()), (price*-1), "Bought " + str(description)))
        self.session.commit()
        return True
    
    def parseRequest(self, request, response):
        response.success = False
        
        if request == None:
            return response

        if request.action == "":
            return response

        wallet = self.getWalletByCard(request.mifareid, request.cardid)

        if request.action == "getItems":
            items = self.getItems()
            item_data = []

            for item in items:
                item_data.append(item.pack())

            response.data['items'] = item_data
            response.success = True
            return response
       
        if request.action == "createWallet":
            if not wallet:
                wallet = self.addWallet(request.mifareid, request.cardid)
            if not wallet:
                return response

            response.success = True
            return response

        # This is the only command that does not need a valid wallet, it will create one on success 
        if request.action == "redeemToken":
            try:
                code = request.data['token']
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

        # Get balance by cardid
        if request.action == "getWallet":
            if wallet:
                response.data['wallet'] = wallet.pack()
                response.success = True
            return response
 
        # Get user by wallet
        if request.action == "getUser":
            if wallet:
                user = self.getUserByWalletId(wallet.id)
                if user is not None:
                    response.data['user'] = user.pack()
                    response.success = True
            return response

        # After this, a valid wallet is needed
        if not wallet:
            return response
        
        if request.action == "buyItem":
            try:
                itemId = int(request.data['item'])
            except:
                return response
            
            item = self.getItemById(itemId)

            if item != None and self.buyItem(wallet, item.price, item.desc):
                response.success = True
                return response

            return response
        return response

