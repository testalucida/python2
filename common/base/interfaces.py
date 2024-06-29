
from enum import Enum
from typing import Dict, Any, List, Type, Iterable, Callable

from PySide2.QtCore import QObject


class XBase:
    """
    Die Mutter aller Interfaces.
    Jedes Interface sollte von XBase abgeleitet werden, z.B. weil es einen DB-Lesezugriff gibt,
    der die gelesenen DB-Spalten einer DB-Row direkt in ein passendes von XBase abgeleitetes Interface verpackt.
    Außerdem werden die get- und setValue Methoden im BaseTableModel benötigt.

    XBase wird *intensivst* vom ImmoControlCenter benutzt, also Vorsicht beim Ändern.
    """
    def __init__( self, valuedict:Dict=None ):
        if valuedict:
            self.setFromDict( valuedict )

    def __eq__( self, other ) -> bool:
        if other is None: return False
        return True if self.__dict__ == other.__dict__ else False

    def getValue( self, key ) -> Any:
        return self.__dict__[key]

    def setValue( self, key, value ):
        self.__dict__[key] = value

    def setFromDict( self, d: Dict ):
        _d = self.__dict__
        for k, v in d.items():
            _d[k] = v

    def updateFromOther( self, other ):
        self.setFromDict( other.__dict__ )

    def getDifferences(self, other) -> Dict:
        diffs = dict()
        for key, value in self.__dict__.items():
            otherval = other.__dict__[key]
            if otherval != value:
                diffs[key] = otherval
        return diffs

    def equals( self, other ) -> bool:
        return self.__eq__(other)

    def copyByKey(self, x):
        """
        Übernimmt die Werte gleicher Keys von <x> in dieses Objekt.
        :param x: ein anderes XBase-Objekt, das nicht den gleichen Typ haben muss wie dieses Objekt
        :return:
        """
        for k, v in self.__dict__.items():
            if k in x.__dict__:
                self.__dict__[k] = x.__dict__[k]

    def getKeys( self ) -> List:
        return list( self.__dict__.keys() )

    def toString( self, printWithClassname=False ) -> str:
        s = ( str( self.__class__ ) + ": " ) if printWithClassname else ""
        s += str( self.__dict__ )
        return s

    def print( self ):
        print( self.toString( printWithClassname=True ) )

def test_getDifferences():
    class Test:
        def __init__(self, i:int, s:str):
            self.i = i
            self.s = s

        def __eq__(self, other):
            return self.i == other.i and self.s == other.s

    class XA(XBase):
        def __init__(self, v1:str, t:Test):
            XBase.__init__(self)
            self.v1 = v1
            self.test:Test = t

        def __eq__(self, other):
            return self.v1 == other.v1 and self.test == other.test

    xa1 = XA("abc", Test(1, "def"))
    xa2 = XA("abc", Test(1, "def"))
    equals = xa1.equals(xa2)
    print( "sind gleich: ", equals)

test_getDifferences()

#################   ButtonDefinition   #######################
class ButtonDefinition:
    def __init__( self, text:str, callback:Callable, tooltip:str=None, ident:Any=None, iconpath:str=None,
                  maxW:int=None, maxH:int=None ):
        self.text = text
        self.callback = callback
        self.tooltip = tooltip
        self.ident = ident
        self.iconpath = iconpath
        self.maxW = maxW
        self.maxH = maxH

#################   VisibleAttribute   ##########################
class VisibleAttribute:
    def __init__( self, key:str, type_:Type, label:str, editable=True,
                  widgetWidth=-1, widgetHeight=-1, nextRow=True, columnspan=1,
                  comboValues:Iterable[str]=None, comboCallback=None, trailingButton:ButtonDefinition=None,
                  tooltip:str=""):
        self.key = key
        self.type = type_
        self.label = label
        self._comboValues:Iterable[str] = comboValues
        self.comboCallback:Callable = comboCallback
        self.editable = editable
        self.tooltip = tooltip
        self.nextRow = nextRow
        self.columnspan = columnspan
        self._widgetHeight = widgetHeight # default -1: Qt bestimmt die Höhe
        self._widgetWidth = widgetWidth  # default -1: Qt bestimmt die Breite
        self.trailingButton = trailingButton

    def setTextSpec( self, widgetWidth:int, widgetHeight:int ):
        self._widgetHeight = widgetHeight
        self._widgetWidth = widgetWidth

    def setComboValues( self, valueList:Iterable[str] ):
        """
        Achtung: wenn für dieses Attribut eine Auswahlliste angeboten wird, muss eine etwaige
        Vorbelegung in der Auswahlliste enthalten sein.
        :param valueList:
        :return:
        """
        self._comboValues = valueList

    def getComboValues( self ) -> Iterable[str]:
        return self._comboValues

    def getWidgetHeight( self ) -> int:
        return self._widgetHeight

    def getWidgetWidth( self ) -> int:
        return self._widgetWidth

#####################   XBaseUI   ################################
class XBaseUI:
    def __init__( self, xbase:XBase ):
        self._xbase = xbase
        self._attrList:List[VisibleAttribute] = list()

    def getXBase( self ) -> XBase:
        return self._xbase

    def addVisibleAttribute( self, attr:VisibleAttribute ):
        self._attrList.append( attr )

    def addVisibleAttributes( self, attrList:Iterable[VisibleAttribute] ):
        for attr in attrList:
            self._attrList.append( attr )

    def getVisibleAttributes( self ) -> List[VisibleAttribute]:
        return self._attrList

####################   XAttribute   #####################
class XAttribute( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self, valuedict )
        self.key = ""
        self.type = "" # one of int, float, string
        self.label = ""
        self.value = None
        self.options = list()
        self.editable = True

####################  Action  #######################
class Action( Enum ):
    INSERT = 1,
    UPDATE = 2,
    DELETE = 3,
    NONE = 4

    @staticmethod
    def toString( action ) -> str :
        if action == Action.INSERT: return "inserted"
        if action == Action.UPDATE: return "modified"
        if action == Action.DELETE: return "deleted"
        if action == Action.NONE: return "noaction"

class TestItem( XBase ):
    def __init__( self ):
        XBase.__init__( self )
        import sys
        #print( sys._getframe().f_code.co_name )
        self.nachname = ""
        self.vorname = ""
        self.plz = ""
        self.ort = ""
        self.str = ""
        self.alter = 0
        self.groesse = 0
        self.testi:TestItem = None


def test7():
    t = TestItem()
    t.nachname = "Kendel"
    t.vorname = "Martin"
    t.plz = "91077"
    t.ort = "Kleinsendelbach"
    t.testi = TestItem()
    t2 = t.testi
    t2.nachname = "Müller"
    t2.vorname = "Paul"
    print( t.toString( printWithClassname=True ) )
    #print( t.__dict__ )

def test5():
    import sys
    myname = sys._getframe().f_code.co_name
    print( myname )

def test3():
    def makeInstance( tp:Type ):
        if tp == TestItem:
            return tp()
        else: return None

    t = TestItem()
    print( type( t ) )
    print( str( t.__class__) )
    # tp:Type = XChange
    # print( str(tp) )
    # t2 = makeInstance( tp )
    # print( t2 )

def test2():
    # c1 = XChange()
    # c2 = XChange()
    # c3 = XChange()
    # print( c1.getId() )
    # print( c2.getId() )
    # print( c3.getId() )
    pass


def test():
    ti = TestItem()
    ti.vorname = "Paul"
    ti.nachname = "Schörder"
    # change = XChange( "Person", Action.UPDATE, ti, "vorname", ti.vorname, ti.nachname, "test blabla")
    # print( change.getAsString( "\n", printWholeObject=True ) )