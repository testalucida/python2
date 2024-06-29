import numbers
from abc import abstractmethod, ABC
from datetime import datetime
from functools import cmp_to_key
from PySide2.QtCore import QAbstractTableModel, SIGNAL, Qt, QModelIndex, QSize
from typing import Any, List, Dict, Tuple
from PySide2.QtGui import QColor, QBrush, QFont, QPixmap

from interfaces import XBase

####################  Change  #######################
class Change:
    def __init__( self, xbase, key, oldval, newval ):
        self.xbase:XBase = xbase
        self.key = key
        self.oldval = oldval
        self.newval = newval
        self.timestamp = datetime.now()

##################  ChangeLog  ###################
class ChangeLog:
    def __init__( self ):
        self._list:List[Change] = list()

    def addChange( self, x:XBase, key, oldval, newval ) -> None:
        """
        Schreibt das Änderungslogbuch
        :param indexrow:  Zeile, in der die Änderung stattgefunden hat
        :param indexcolumn:  Spalte, in der sich der Wert geändert hat
        :param x: von der Änderung betroffenes XBase-Objekt
        :param key: Attributname (Key im XBase.__dict__)
        :param oldval: Wert vor der Änderung
        :param newval: Wert nach der Änderung
        :return: None
        """
        c = Change( x, key, oldval, newval )
        self._list.append( c )

    def hasChanges( self ) -> bool:
        return len( self._list ) > 0

    def getChanges( self ) -> List[Change]:
        return self._list

    def getChangedObjects( self ):
        return [x.xbase for x in self._list]

    def getChangesForObject( self, object ) -> List[Change]:
        return [change for change in self._list if change.xbase == object]

    def getChangesForKey( self, object, key ) -> List[Change]:
        objlist = self.getChangesForObject( object )
        keylist = [obj.key for obj in objlist if obj.key == key]
        return keylist

    def getFirstAndLastValueForKey( self, object, key ) -> Tuple[Any, Any]:
        chnglist = self.getChangesForKey( object, key )
        len_ = len( chnglist )
        if len_ == 0:
            raise Exception( "ChangeLog.getInitialAndLastValueForObject(): object/key not found" )
        first = chnglist[0].oldval
        last = chnglist[len_-1].newval
        return ( first, last )

    def clear( self ):
        self._list.clear()

##################  KeyHeaderMapping  ################
class KeyHeaderMapping:
    def __init__( self, key=None, header=None ):
        self.key = key
        self.header = header

######################  CustomTableModel  ##################
class XBaseTableModel( QAbstractTableModel ):
    def __init__( self, rowList:List[XBase]=None, jahr:int=None ):
        QAbstractTableModel.__init__( self )
        #super( XBaseTableModel, self ).__init__(  )
        self.rowList:List[XBase] = rowList
        self._jahr:int = jahr # das Jahr ist bei manchen Models interessant, bei manchen nicht - kann also auf None stehen.
        self.headers:List = list()
        self.keys:List = list()
        self.headerColor = QColor( "#FDBC6A" )
        self.headerBrush = QBrush( self.headerColor )
        self.negNumberBrush = QBrush( Qt.red )
        self.greyBrush = QBrush( Qt.lightGray )
        self.inactiveBrush = QBrush( Qt.black )
        self.inactiveBrush.setStyle( Qt.BDiagPattern )
        self.boldFont = QFont( "Arial", 11, QFont.Bold )
        self.yellow = QColor( "yellow" )
        self.yellowBrush = QBrush( self.yellow )
        self.sortable = False
        self.sort_col = 0
        self.sort_ascending = False
        self._changes = ChangeLog()
        if rowList:
            self.setRowList( rowList )

    def _setDefaultKeyHeaderMapping( self ):
        """
        Per default verwenden wir die Keys eines der übergebenen Dictionaries als Keys und Headers
        :return:
        """
        xbase = self.rowList[0]
        for k in xbase.getKeys():
            self.keys.append( k )
            self.headers.append( k )

    def setRowList( self, rowList:List[XBase] ):
        self.rowList = rowList
        if len( rowList ) > 0:
            self._setDefaultKeyHeaderMapping()

    def setKeyHeaderMappings( self, mappings:List[KeyHeaderMapping] ):
        self.headers = [x.header for x in mappings]
        self.keys = [x.key for x in mappings]

    def getColumnIndex( self, header ) -> int:
        return self.headers.index( header )

    def getHeaders( self ) -> List[str]:
        return self.headers

    def getHeader( self, col:int ) -> Any:
        return self.headerData( col, orientation=Qt.Horizontal, role=Qt.DisplayRole )

    def getKeyByHeader( self, header:Any ) -> Any:
        headerIndex = self.headers.index( header )
        return self.keys[headerIndex]

    def getRowList( self ) -> List[XBase]:
        """
        :return: die rohe Liste der XBase-Elemente
        """
        return self.rowList

    def getJahr( self ) -> int:
        return self._jahr

    def getRow( self, x:XBase ) -> int:
        """
        Liefert die Zeile, in der das spezifizierte XBase-Objekt dargestellt wird
        :param x:
        :return:
        """
        return self.rowList.index( x )

    def getElement( self, indexrow: int ) -> XBase:
        return self.rowList[indexrow]

    def getKey( self, indexcolumn:int ):
        return self.keys[indexcolumn]

    def getValue( self, indexrow: int, indexcolumn: int ) -> Any:
        e:XBase = self.getElement( indexrow )
        return e.getValue( self.keys[indexcolumn] )

    def getValueByName( self, indexrow:int, attrName:str ) -> Any:
        e:XBase = self.getElement( indexrow )
        return e.getValue( attrName )

    def setValue( self, indexrow:int, indexcolumn:int, value:Any, writeChangeLog:bool=True ) -> None:
        """
        Ändert einen Wert in dem durch indexrow spezifiz. XBase-Element und
        schreibt das Change-Log
        Löst *kein* dataChanged-Signal aus.
        Um ein dataChanged-Signal auszulösen, muss die setData-Methode verwendet werden.
        :param indexrow:
        :param indexcolumn:
        :param value:
        :return:
        """
        oldval = self.getValue( indexrow, indexcolumn )
        if oldval == value: return
        e:XBase = self.getElement( indexrow )
        key = self.keys[indexcolumn]
        e.setValue( key, value )
        if writeChangeLog:
            self.addChange( e, key, oldval, value )

    def addChange( self, e:XBase, key, oldval, value ):
        self._changes.addChange( e, key, oldval, value )

    # def setData( self, index, value ) -> None:
    #     """
    #     Ändert einen Wert in dem durch index.row() spezifiz. XBase-Element und schreibt
    #     das Change-Log
    #     Löst nach der Änderung ein dataChanged-Signal aus.
    #     :param index:
    #     :param value:
    #     :return:
    #     """
    #     self.setValue( index.row(), index.column(), value, writeChangeLog=True )
    #     self.dataChanged.emit( index, index )

    def rowCount( self, parent:QModelIndex=None ) -> int:
        return len( self.rowList )

    def columnCount( self, parent:QModelIndex=None ) -> int:
        return len( self.headers )

    def data( self, index: QModelIndex, role: int = None ):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self.getValue( index.row(), index.column() )
        elif role == Qt.TextAlignmentRole:
            v = self.getValue( index.row(), index.column() )
            if isinstance( v, numbers.Number ): return int( Qt.AlignRight | Qt.AlignVCenter )
        elif role == Qt.BackgroundRole:
            return self.getBackgroundBrush( index.row(), index.column() )
        elif role == Qt.ForegroundRole:
            return self.getForegroundBrush( index.row(), index.column() )
        elif role == Qt.FontRole:
            return self.getFont( index.row(), index.column() )
        elif role == Qt.DecorationRole:
            return self.getDecoration( index.row(), index.column() )
        elif role == Qt.SizeHintRole:
            return self.getSizeHint( index.row(), index.column() )
        return None

    def headerData(self, col, orientation, role=None):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.headers[col]
            if role == Qt.BackgroundRole:
                if self.headerBrush:
                    return self.headerBrush
        return None

    def getBackgroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        return None

    def getForegroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        if self.negNumberBrush:
            val = self.getValue( indexrow, indexcolumn )
            if isinstance( val, numbers.Number ) and val < 0:
                return QBrush( Qt.red )

    def getFont( self, indexrow: int, indexcolumn: int ) -> QFont or None:
        return None

    def getDecoration( self, indexrow: int, indexcolumn: int ) -> QPixmap or None:
        return None

    def getSizeHint( self, indexrow:int, indexcolumn:int ) -> QSize or None :
        return None

    def setHeaderColor( self, color:QColor ):
        self.headerColor = color

    def displayNegNumbersRed( self, on:bool=False ):
        if on:
            self.negNumberBrush = QBrush( Qt.red )
        else:
            self.negNumberBrush = None

    def isChanged( self ) -> bool:
        return self._changes.hasChanges()

    def getChanges( self ) -> ChangeLog:
        return self._changes

    def clearChanges( self ):
        self._changes.clear()

    def setSortable( self, sortable:bool=True ):
        self.sortable = sortable

    def sort( self, col:int, order: Qt.SortOrder ) -> None:
        if not self.sortable: return
        """sort table by given column number col"""
        #self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.layoutAboutToBeChanged.emit()
        self.sort_col = col
        self.sort_ascending = True if order == Qt.SortOrder.AscendingOrder else False
        self.rowList = sorted( self.rowList, key=cmp_to_key( self.compare ) )
        #elf.emit(SIGNAL("layoutChanged()"))
        self.layoutChanged.emit()

    def compare( self, x1:XBase, x2:XBase ) -> int:
        key = self.getKey( self.sort_col )
        v1 = x1.getValue( key )
        v2 = x2.getValue( key )
        if isinstance( v1, str ):
            v1 = v1.lower()
            v2 = v2.lower()
        if v1 < v2: return 1 if self.sort_ascending else -1
        if v1 > v2: return -1 if self.sort_ascending else 1
        if v1 == v2: return 0
