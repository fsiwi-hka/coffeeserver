import json, math, time, sys, os, datetime, random, hashlib

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
    email = Column(String)
    admin = Column(Boolean)
    hochschulId = Column(String)
    walletid = Column(Integer, ForeignKey('wallets.id'))
    walletObj = None

    def __init__(self, username, password, email, hsid):
        self.username = username
        self.email = email
        self.hochschulId = hsid
        
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
        packed['email'] = self.email
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
    weight = Column(Integer)
    enabled = Column(Boolean, default=True)
    sold_out = Column(Boolean, default=False)

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
        packed['sold_out'] = self.sold_out
        packed['weight'] = self.weight
        return packed
 
    def __repr__(self):
        return "<Item('%s', '%s', '%s', '%s', '%s')>" % (self.price, self.desc, self.image, self.enabled, self.sold_out)

class ItemTransaction(Base):
    __tablename__ = "item_transactions"

    id = Column(Integer, primary_key=True)
    itemid = Column(Integer, ForeignKey('items.id'))
    price = Column(Integer)
    walletid = Column(Integer, ForeignKey('wallets.id'))
    itemTransactions = relationship(Wallet, backref=backref('itemTransactions', order_by=id))
    time = Column(Integer)

    def __init__(self, itemid, price, time):
        self.itemid = itemid
        self.price = price
        self.time = time

    def pack(self):
        packed = {}
        packed['itemid'] = self.itemid
        packed['price'] = self.price
        packed['walletid'] = self.walletid
        packed['time'] = self.time

    def __repr__(self):
        return "<ItemTransaction('%s', '%s', '%s', '%s', '%s')>" % (self.id, self.itemid, self.price, self.walletid, self.time)

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
        return self.session.query(Item).order_by(Item.weight.desc()).all()

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

    def getUserById(self, id):
        return self.session.query(User).filter_by(id=id).first()

    def getUserWithLogin(self, username, password):
        user = self.session.query(User).filter_by(username=username).first()
        if user is None:
            return None
        print user.password
        print user.hash(password)
        if user.password == user.hash(password):
            return user
        return None

    def addUser(self, username, password, email, hsid, wallet):
        if username == "" or password == "":
            return False

        user = User(username, password, email, hsid)
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
    
    def buyItem(self, wallet, item):
        if wallet == None:
            return False

        if wallet.balance < math.fabs(item.price) or math.fabs(item.price) == 0:
            return False

        wallet.balance = wallet.balance - math.fabs(item.price)
        wallet.transactions.append(Transaction(int(time.time()), (item.price*-1), "Bought " + str(item.desc)))
        wallet.itemTransactions.append(ItemTransaction(item.id, math.fabs(item.price), int(time.time())))
        self.session.commit()
        return True

    def getStatistics(self, time_from, time_end):
        data = {'items': {}}
        items = self.getItems()
        for item in items:
            item_data = {}
            transactions = self.session.query(ItemTransaction).filter_by(itemid=item.id).filter(ItemTransaction.time>=time_from).filter(ItemTransaction.time<=time_end).all()

            item_data['count'] = len(transactions)
            item_data['revenue'] = 0
            for transaction in transactions:
                item_data['revenue'] += transaction.price
            data['items'][item.id] = item_data

        tokens = self.session.query(Token).filter(Token.used_time>=time_from).filter(Token.used_time<=time_end).all()
        data['used_tokens'] = len(tokens)
        data['used_tokens_value'] = 0
        for token in tokens:
            data['used_tokens_value'] += token.value
        return data 

    def sendStatistics(self, email):
        items = self.getItems()
        transactions = self.session.query(ItemTransaction).all()
        tokens = self.session.query(Token).filter(Token.used_time>0).all()

        transactionFile = "Time; WalletID; ItemID; ItemDesc; Price;\n"

        for t in transactions:
            transactionFile += str(t.time)
            transactionFile += str(t.walletid)
            transactionFile += str(t.itemid)
            transactionFile += str(t.time)
            transactionFile += str(t.revenue)
            transactionFile += "\n"

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

            if item != None and self.buyItem(wallet, item):
                response.success = True
                return response

            return response

        # Admin actions
        user = self.getUserByWalletId(wallet.id)

        if user is not None and user.admin is True:
            if request.action == "updateItem":
                try:
                    itemId = int(request.data['item'])
                    enabled = bool(request.data['enabled'])
                    sold_out = bool(request.data['sold_out'])
                except:
                    return response
                
                item = self.getItemById(itemId)
                item.enabled = enabled
                item.sold_out = sold_out
                self.session.commit()
                response.success = True
                return response
            
            if request.action == "getStatistics":
                oneday = 60 * 60* 24
                weekday = datetime.datetime.today().isocalendar()[2]

                today = datetime.datetime.today()
                today = time.mktime(datetime.date(today.year, today.month, today.day).timetuple())
                weekday_offset = (weekday-1) * oneday 
                        
                data = {}
                data['day'] = self.getStatistics(today, time.time())
                data['week'] = self.getStatistics(today-weekday_offset, time.time())
                data['total'] = self.getStatistics(0, time.time())
                response.data['statistics'] = data
                response.success = True
                return response
        return response
