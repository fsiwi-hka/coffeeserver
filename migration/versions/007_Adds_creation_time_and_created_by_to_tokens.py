from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tokens = Table('tokens', meta, autoload=True)
    created_byc = Column('created_by', Integer)
    created_byc.create(tokens)
    creation_timec = Column('creation_time', Integer)
    creation_timec.create(tokens)

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tokens = Table('tokens', meta, autoload=True)
    tokens.c.created_by.drop()
    tokens.c.creation_time.drop()
