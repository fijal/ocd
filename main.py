
from klein import Klein
from sqlalchemy import create_engine

from ocd.model import meta
from ocd.app import get_klein

eng = create_engine('sqlite:///ocd.db')
con = eng.connect()
meta.reflect(bind=eng)

if __name__ == '__main__':
    k = Klein()
    get_klein(k, con)
    k.run("0.0.0.0", 8088)
