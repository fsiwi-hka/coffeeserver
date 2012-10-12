from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    items = Table('items', meta, autoload=True)
    enabledc = Column('enabled', Boolean)
    enabledc.create(items)

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    items = Table('items', meta, autoload=True)
    items.c.enabled.drop()
