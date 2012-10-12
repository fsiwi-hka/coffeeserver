from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    items = Table('items', meta, autoload=True)
    sold_outc = Column('sold_out', Boolean, default=False)
    sold_outc.create(items)

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    items = Table('items', meta, autoload=True)
    items.c.sold_out.drop()
