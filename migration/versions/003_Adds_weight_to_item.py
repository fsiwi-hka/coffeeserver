from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    items = Table('items', meta, autoload=True)
    weightc = Column('weight', Integer, default=0)
    weightc.create(items)

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    items = Table('items', meta, autoload=True)
    items.c.weight.drop()
