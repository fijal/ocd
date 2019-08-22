
from klein import Klein
import json
from sqlalchemy import create_engine

from ocd.model import meta, area, sector, boulder, problem
from ocd.app import get_klein

test_area = {
    'name': 'area name', 'lattitude': 15.0, 'longitude': 15.0
}

test_sector = {
    'name': 'test sector', 'lattitude': 15.0, 'longitude': 15.0,
    'area': 0,
}

test_boulders = [{
    'id': 0, 'lattitude': 15.1, 'longitude': 15.0, 'elevation': 100,
    'name': 'boulder1', 'sector': 0
},{
    'id': 1, 'lattitude': 15.2, 'longitude': 15.1, 'elevation': 100,
    'name': 'boulder2', 'sector': 0
},{
    'id': 2, 'lattitude': 15.2, 'longitude': 15.2, 'elevation': 100,
    'name': 'boulder3', 'sector': 0
}
]

test_problems = [{
    'id': 0, 'name': 'problem1', 'description': 'foo bar', 'grade': '7a',
    'boulder': 0
}]

def get_test_db():
    eng = create_engine("sqlite://")

    con = eng.connect()
    meta.create_all(eng)

    con.execute(area.insert().values(test_area))
    con.execute(sector.insert().values(test_sector))
    for b in test_boulders:
        con.execute(boulder.insert().values(b))
    for p in test_problems:
        con.execute(problem.insert().values(p))

    return get_klein(Klein(), con)


class Request(object):
    def __init__(self, **kwds):
        self.args = {}
        for k, v in kwds.iteritems():
            self.args[k] = [v]

    def setHeader(self, name, val):
        pass

class TestQueries(object):
    def test_boulders(self):
        app = get_test_db()
        res = json.loads(app.boulder_add(Request(
            lattitude = "16.0",
            longitude = "16.0",
            elevation = "100",
            name = "name",
            sector = 0
            )))
        assert res['ok'], res['error']
        res = json.loads(app.boulder_get(Request(), int(res['boulder_id'])))
        assert res['ok'], res['error']
        assert res['result']['name'] == 'name'

    def test_boulder_selectors(self):
        app = get_test_db()
        res = json.loads(app.boulder_list(Request()))
        assert res['ok']
        assert len(res['result']) == 3
        res = json.loads(app.boulder_list(Request(q="sector[0]")))
        assert res['ok'], res['error']
        assert len(res['result']) == 3
        res = json.loads(app.boulder_list(Request(q='rect[14.99, 14.99, 15.11, 15.11]')))
        assert res['ok'], res['error']
        assert len(res['result']) == 1
        assert res['result'][0]['name'] == 'boulder1'
        res = json.loads(app.boulder_list(Request(q='circle[15.0, 15.0, 0.25]')))
        assert res['ok'], res['error']
        assert len(res['result']) == 2
        assert 'problems' not in res['result'][0]
        res = json.loads(app.boulder_list(Request(q='circle[15.0, 15.0, 0.25]',
            problems="1")))
        assert res['ok'], res['error']
        assert len(res['result']) == 2
        assert len(res['result'][0]['problems']) == 1

    def test_boulder_selection_problems(self):
        app = get_test_db()
        res = json.loads(app.problem_add(Request(boulder="0", name="problem2",
            description="foo", grade="6a")))
        assert res['ok'], res['error']
        res = json.loads(app.boulder_get(Request(), "0"))
        assert res['ok'], res['error']
        problems = res['result']['problems']
        assert len(problems) == 2
