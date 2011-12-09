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
    balance = Column(Float)
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
    change = Column(Float)
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
    value = Column(Float)
    valid = Column(Boolean)
    used_by = Column(Integer, ForeignKey('wallets.id'))
    used_time = Column(Integer)

    def __init__(self, token, value):
        self.token = token
        self.value = value
        self.valid = True

    def __repr__(self):
        return "<Token('%s', '%s', '%s', '%s')>" % (self.id, self.token, self.value, self.valid)


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

    def redeemCode(self, wallet, code):
        if wallet == None or code == None:
            return False

        if code == 1337:
            wallet.balance = wallet.balance + 10.0
            self.session.commit()
            return True
        
        return False

    def buyItem(self, wallet, price, description = ""):
        if wallet == None:
            return False

        if wallet.balance < math.fabs(price) or math.fabs(price) == 0:
            return False

        wallet.balance = wallet.balance - math.fabs(price)
        wallet.transactions.append(Transaction(0, price, description))
        self.session.commit()
        return True
    
    def parseCommand(self, command):
        result = {"success":"False"}
        
        if command == None:
            return json.dumps(result)

        action = None
        mifareid = None
        cardid = None
        try:
            command = json.loads(command)
            action = command['action']
            mifareid = int(command['mifareid'])
            cardid = int(command['cardid'])
        except:
            return json.dumps(result)

        if action == "" or action == None or mifareid == "" or mifareid == 0 or mifareid == None or cardid == "" or cardid == 0 or cardid == None:
            return json.dumps(result)

        wallet = self.getWalletByCard(mifareid, cardid)
        
        # This is the only command that does not need a valid wallet, it will create one on success 
        if action == "redeemCode":
            try:
                code = int(command['code'])
            except:
                return json.dumps(result)

            if not wallet:
                wallet = self.addWallet(mifareid, cardid)
            if not wallet:
                return json.dumps(result)
            
            if not self.redeemCode(wallet, code):
                return json.dumps(result)

            return jsom.dumps({"success":"True"})
 
        # Get balance by cardid, return 0 when card is not known
        if action == "getBalance":
            balance = 0
            if wallet:
                balance = wallet.balance
            result = {"success":"True", "balance":balance}
            return json.dumps(result)

  
        # After this, a valid wallet is needed
        if not wallet:
            return json.dumps(result)
        
        if action == "buyItem":
            try:
                item = int(command['item'])
            except:
                return json.dumps(result)
            
            price = 0
            desc = ""
            
            if item == 1:
                price = 0.5
                desc = "Kaffee"

            if item == 2:
                price = 1.5
                desc = "Club-Mate"

            if self.buyItem(wallet, price, desc):
                return json.dumps({"success":"True", "balance":wallet.balance})

            return json.dumps(result)

        return json.dumps(result)
#mifareid = 3
#cardid = 6

#p = Payment(debug=True)

#wallet = p.getWalletByCard(mifareid, cardid)

#if wallet == None:
#    wallet = p.addWallet(mifareid, cardid)
#    p.addUser("testuser", "testpassword", wallet)

#p.addBalance(wallet, 1)
#p.buyItem(wallet, 1.0, "Club-Mate")
#p.buyItem(wallet, 1.0, "Club-Mate")


