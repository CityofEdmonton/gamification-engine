import pytz
from pytz.exceptions import UnknownTimeZoneError
from sqlalchemy.inspection import inspect
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.functions import func
from zope.sqlalchemy.datamanager import mark_changed

from gengine.metadata import DBSession
from gengine.base.cache import cache_general

class ABaseMeta(type):
    def __init__(cls, name, bases, nmspc):
        super(ABaseMeta, cls).__init__(name, bases, nmspc)

    def __getattr__(cls, item):
        if item == "__table__":
            return inspect(cls).local_table
        raise AttributeError(item)

class ABase(object, metaclass=ABaseMeta):
    """abstract base class which introduces a nice constructor for the model classes."""

    def __init__(self, *args, **kw):
        """ create a model object.

        pass attributes by using named parameters, e.g. name="foo", value=123
        """

        for k, v in kw.items():
            setattr(self, k, v)

    def __str__(self):
        if hasattr(self, "__unicode__"):
            return self.__unicode__()

def calc_distance(latlong1, latlong2):
    """generates a sqlalchemy expression for distance query in km

       :param latlong1: the location from which we look for rows, as tuple (lat,lng)

       :param latlong2: the columns containing the latitude and longitude, as tuple (lat,lng)
    """

    # explain: http://geokoder.com/distances

    # return func.sqrt(func.pow(69.1 * (latlong1[0] - latlong2[0]),2)
    #               + func.pow(53.0 * (latlong1[1] - latlong2[1]),2))

    return func.sqrt(func.pow(111.2 * (latlong1[0] - latlong2[0]), 2)
                     + func.pow(111.2 * (latlong1[1] - latlong2[1]) * func.cos(latlong2[0]), 2))


def coords(row):
    return (row["lat"], row["lng"])


def combine_updated_at(list_of_dates):
    return max(list_of_dates)


def get_insert_id_by_result(r):
    return r.last_inserted_ids()[0]


def get_insert_ids_by_result(r):
    return r.last_inserted_ids()


def exists_by_expr(t, expr):
    # TODO: use exists instead of count
    q = select([func.count("*").label("c")], from_obj=t).where(expr)
    r = DBSession.execute(q).fetchone()
    if r.c > 0:
        return True
    else:
        return False


@cache_general.cache_on_arguments()
def datetime_trunc(field, timezone):
    return "date_trunc('%(field)s', CAST(to_char(NOW() AT TIME ZONE %(timezone)s, 'YYYY-MM-DD HH24:MI:SS') AS TIMESTAMP)) AT TIME ZONE %(timezone)s" % {
        "field": field,
        "timezone": timezone
    }


@cache_general.cache_on_arguments()
def valid_timezone(timezone):
    try:
        pytz.timezone(timezone)
    except UnknownTimeZoneError:
        return False
    return True

def update_connection():
    session = DBSession()
    mark_changed(session)
    return session
