import json
from types import SimpleNamespace
from typing import Dict, List

from generictable_stuff.xbasetablemodel import XBaseTableModel
from interfaces import XBase, XGeplant


def objectToJson( obj ):
    try:
        json_ = json.dumps( obj.__dict__ )
    except:
        json_ = json.dumps( obj )
    return json_

def exceptionToJson( ex:Exception ) -> str:
    d = dict( type=ex.__class__.__name__,
              message=str( ex ) )
    json_ = json.dumps( d )
    return json_

def jsonToObject( json_string:str, cls=None ):
    """
    Wenn das decodierte Objekt eine Liste oder ein Dict sein soll, darf das Argument <cls> nicht gesetzt sein.
    Wenn es gesetzt wird, wird ein Objekt von <cls> instanziert und sein __dict__ - Attribut durch das
    decodierte Dictionary ersetzt.
    Achtung: <cls> muss einen argumentlosen Konstruktor besitzen.
    :param json_string:
    :param cls:
    :return:
    """
    if not cls:
        return json.loads( json_string )

    def hook( **dict ):
        print( dict )
        #obj.__dict__ = dict
        return dict

    obj = cls()
    res = json.loads( json_string, object_hook=lambda d: hook( **d ) )
    d = {}
    for key in res.keys():
        print( key, ": ", res[key] )
        obj.__dict__[key] = res[key]
    return obj

def xbaseListToJson( xlist:List[XBase]) -> str:
    json_ = json.dumps( [x.__dict__ for x in xlist] )
    return json_

def xbaseTableModelToJson( model:XBaseTableModel) -> str:
    def obj_dict( obj ):
        return obj.__dict__
    json_ = json.dumps( model, default=obj_dict )
    return json_

def jsonToXBaseTableModel( json_:str ) -> XBaseTableModel:
    pass

####################  T E S T S  #####################################

### List of objects to JSON with Python:  https://stackoverflow.com/questions/26033239/list-of-objects-to-json-with-python
####### interesseant ist der default-Parameter, den man json.dumps mitgeben kann!!
### und in diesem Artikel auch jsonpickle

def test4():
    x1 = XGeplant()
    x1.id = 1
    x1.mobj_id = "lamm"
    x1.leistung = "Alles Mögliche"
    x1.firma = "Tausendsassa"
    x1.kosten = 1234.56
    x1.jahr = 2022
    x1.monat = 5

    x2 = XGeplant()
    x2.id = 2
    x2.mobj_id = "lamm"
    x2.leistung = "Wohnzimmer striechen"
    x2.firma = "Maler Meier"
    x2.kosten = 980
    x2.jahr = 2021
    x2.monat = 12

    l = list()
    l.append( x1 )
    l.append( x2 )
    model = XBaseTableModel( l)
    d = model.__dict__
    print( d )
    json_ = xbaseTableModelToJson( model )
    print( json_ )
    model2:XBaseTableModel = jsonToObject( json_, XBaseTableModel )
    model2 = json.loads( json_ )
    print( model2 )

def test3():
    ex = Exception( "class.method()", "failed" )
    json_ = exceptionToJson( ex )
    print( json_ )

def test2():
    li = [1, 2, "mei"]
    json_ = json.dumps( li )
    print( json_ )

    dic = dict( name="Panther", vorname="Paul", alter=22, ort=dict( plz="91077", ort="Dormitz") )
    json_ = json.dumps( dic )
    print( json_ )
    jload = json.loads( json_ )
    print( jload )
    obj = jsonToObject( json_ )
    print( obj )

    class Person:
        def __init__( self, name=None, vorname=None, alter=None, plz=None, ort=None ):
            self.name = name
            self.vorname = vorname
            self.alter = alter
            self.ort = {
                "plz": plz,
                "ort": ort
            }

    p = Person( "Bloody", "Mary", 110, "00987", "Glasgow" )
    json_ = json.dumps( p.__dict__ )
    print( json_ )
    p = jsonToObject( json_, Person )
    print( p )

def test():
    from interfaces import XMietverhaeltnis
    xmv = XMietverhaeltnis()
    xmv.mv_id = "dummy_puppy"
    xmv.id = 16
    xmv.von = "2020-05-21"
    xmv.nettomiete = 234.55

    json_ = objectToJson( xmv )
    print( json_ )

    x = jsonToObject( json_, XMietverhaeltnis )
    print( x )

    d = dict( name="Müller", vorname="Paul")
    json_ = objectToJson( d )
    print( "json: ", json_ )

    x = jsonToObject( json_, dict )
    print( x )



