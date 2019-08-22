
import sys
from sqlalchemy import create_engine

from ocd.model import meta

def create_db(url):
    eng = create_engine(url)

    with eng.connect():
        meta.create_all(eng)
    return eng

if __name__ == '__main__':
    create_db(sys.argv[1])