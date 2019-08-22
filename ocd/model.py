
from sqlalchemy import (Table, Column, Integer, Boolean,
    String, MetaData, ForeignKey, Float)

meta = MetaData()

boulder = Table('boulder', meta,
    Column('id', Integer, primary_key=True),
    Column('lattitude', Float),
    Column('longitude', Float),
    Column('elevation', Integer), # elevation in meters over see level
    Column('name', String), # optional
    Column('sector', Integer, ForeignKey('sector.id')),
    Column('timestamp', Integer)
)

problem = Table('problem', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('description', String),
    Column('grade', String),
    Column('boulder', Integer, ForeignKey('boulder.id')),
    Column('timestamp', Integer)
)

sector = Table('sector', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('lattitude', Float), # center of the sector
    Column('longitude', Float), # center of the sector
    Column('area', Integer, ForeignKey('area.id')),
    Column('timestamp', Integer)
)

area = Table('area', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('lattitude', Float), # center of the area
    Column('longitude', Float), # center of the area
    Column('timestamp', Integer)
)

photo = Table('photo', meta,
    Column('id', Integer, primary_key=True),
    Column('title', String),
    Column('description', String),
    Column('filename', String), # filename on HD, not the same as title
    Column('association', String), # can be one of boulder, problem, sector, area
    Column('reference', Integer), # reference to association
    Column('timestamp', Integer)
)

tables = {
    'photo': photo,
    'area': area,
    'sector': sector,
    'problem': problem,
    'boulder': boulder
}
