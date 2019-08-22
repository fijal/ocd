
import json, re
from sqlalchemy import select

from ocd.model import boulder

class VerificationError(Exception):
    pass

def verify(required_args={}, optional_args={}):
    def check_type(arg, val, tp):
        try:
            tp(val)
        except (ValueError, TypeError):
            raise VerificationError('invalid type of argument %s, %s required' % (arg, tp))

    def wrap(func):
        def f(self, request, *args):
            remaining_args = required_args.copy()
            try:
                request.setHeader("Content-type", "application/json")
                for arg, val in request.args.iteritems():
                    val = val[0]
                    if arg in remaining_args:
                        check_type(arg, val, remaining_args[arg])
                        del remaining_args[arg]
                        continue
                    if arg not in optional_args:
                        raise VerificationError('argument %s not allowed' % arg)
                    check_type(arg, val, optional_args[arg])
                if remaining_args:
                    raise VerificationError('arguments %s required but '
                                     'not passed' % ", ".join(remaining_args))
            except VerificationError as e:
                return json.dumps({'ok': False, 'error': e.args[0]}) + "\n"
            res = func(self, request, *args)
            assert not isinstance(res, str)
            return json.dumps(res) + "\n"
        f.__doc__ = func.__doc__
        f.__name__ = func.__name__
        return f
    return wrap

def get_klein(klein, connection):
    class App(object):
        app = klein
        con = connection

        @app.route('/boulder')
        @verify(optional_args={'q': str,
                               'problems': bool})
        def boulder_list(self, request):
            """ Returns a list of boulders with selector applied

            Arguments:

            q: str - selector for boulders. Possible selectors:
            problems: bool - whether to return list of problems per boulder

            rect[start_lat, start_lon, end_lat, end_lon] - select a rectangle
                                                           between lat/lon
            circle[lat, lon, diameter] - select from a circle with center in lat/lon
                                         and diameter float degrees
            sector[id] - take boulders from specific sector

            The returned list is a list of boulders, with the following parameters:

            id: int
            lattitude: float
            longitude: float
            elevation: int
            name: str
            sector: int
            problems - if requested, a list of problems
            """
            def selector_always(lattitude, longitude, sector):
                return True

            def selector_rect(lattitude, longitude, sector):
                return ((req_rect[0] <= lattitude <= req_rect[2]) and
                        (req_rect[1] <= longitude <= req_rect[3]))

            def selector_sector(lattitude, longitude, sector):
                return sector == req_sector

            def selector_circle(lattitude, longitude, sector):
                diff_x = lattitude - req_circle[0]
                diff_y = longitude - req_circle[1]
                return ((diff_x ** 2 + diff_y ** 2) ** 0.5) < req_circle[2]

            res = []
            selector = None
            if 'q' in request.args:
                select_string = request.args['q'][0]
                m = re.match("rect\[(.*),(.*),(.*),(.*)\]", select_string)
                if m:
                    selector = selector_rect
                    req_rect = (float(m.group(1)), float(m.group(2)),
                                float(m.group(3)), float(m.group(4)))
                m = re.match("sector\[(\d+)\]", select_string)
                if m:
                    selector = selector_sector
                    req_sector = int(m.group(1))
                m = re.match("circle\[(.*),(.*),(.*)\]", select_string)
                if m:
                    selector = selector_circle
                    req_circle = (float(m.group(1)), float(m.group(2)),
                                  float(m.group(3)))
                if selector is None:
                    return {'ok': False, 'error': 'unknown select query %s' % select_string}
            else:
                selector = selector_always
            for id, lattitude, longitude, elevation, name, sector in self.con.execute(select([boulder])):
                if not selector(lattitude, longitude, sector):
                    continue
                res.append({
                    'id': id,
                    'lattitude': lattitude,
                    'longitude': longitude,
                    'elevation': elevation,
                    'name': name,
                    'sector': sector
                    })
            return {'ok': True, 
                    'result': res}

        @app.route('/boulder/<int:id>')
        @verify()
        def boulder_get(self, request, id):
            """ Get details about a boulder

            id[boulder_id]

            Returns:

            id: int
            lattitude: float
            longitude: float
            elevation: int
            name: str
            sector: int
            """
            lst = list(self.con.execute(select([boulder]).where(boulder.c.id == id)))
            if len(lst) == 0:
                return {'ok': False, 'error': 'no record found for id %s' % id}
            return {'ok': True, 'result': {
               'lattitude': lst[0][1],
               'longitude': lst[0][2],
               'elevation': lst[0][3],
               'name': lst[0][4],
               'sector': lst[0][5]
               }
            }

        @app.route('/boulder/add', methods=['POST'])
        @verify(
            required_args = {'lattitude': float,
                             'longitude': float,
                             'elevation': int,
                             'sector': int},
            optional_args = {
                            'name': str,
            }
        )
        def boulder_add(self, request):
            """ Add a boulder.

            Arguments:

            lattitude: float   - lattitude in degrees
            longitude: float   - longitude in degrees
            elevation: integer - elevation in meters
            name               - (optional) name of the boulder
            sector: integer    - an ID of sector. 0 if not in any sector

            Returns:

            boulder_id - the ID of newly created boulder, useful for adding problems
            """
            res = self.con.execute(boulder.insert().values({
                'lattitude': request.args['lattitude'][0],
                'longitude': request.args['longitude'][0],
                'elevation': request.args['elevation'][0],
                'name': request.args['name'][0],
                'sector': int(request.args['sector'][0])
                }))
            return {'ok': True, 'boulder_id': res.inserted_primary_key[0]}

    return App()
