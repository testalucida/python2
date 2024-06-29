import copy
import decimal
import numbers
import sys
from functools import cmp_to_key
from PySide2.QtCore import QAbstractTableModel, SIGNAL, Qt, QModelIndex, QSize, Signal
from typing import Any, List, Dict, Tuple, Iterator, Iterable, Type
from PySide2.QtGui import QColor, QBrush, QFont, QPixmap
from pandas import Series

from base.interfaces import XBase, Action, XSeriesItem


####################   FilterCondition   ###############
class FilterCondition:
    def __init__( self ):
        self.header = ""  # Name der Spalte
        self.value = ""   # Vergleichswert
        self.value_num = None
        self.op = "=" # Vergleichsopeartor {'startsWith', 'contains', '=', '>=', '<=', '>', '<'}
        self.caseSensitive = False

    def toString( self ):
        return "Column: " + self.header + " - op: '" + self.op + "' - comp.value: " + self.value + \
               " - caseSensitive: " + str( self.caseSensitive )

##################  KeyHeaderMapping  ################
class KeyHeaderMapping:
    def __init__( self, key=None, header=None ):
        self.key = key
        self.header = header

#############################################################################
class Filter:
    def __init__(self, key:str, filterval:str):
        self.key:str = key
        self.filterval:str = filterval

##################  BaseTableModel  ##################
class BaseTableModel( QAbstractTableModel ):
    """
    Neue Version des BaseTableModel mit neuer Filtermethodik (wird verwendet vom FilterTableWidget).
    """
    before_sorting = Signal()
    sorting_finished = Signal()
    before_multi_sorting = Signal()
    multi_sorting_finished = Signal()
    rowsAddedSignal = Signal() # damit die View ggf. ihre Zeilenhöhe anpassen kann
    def __init__( self, rowList:List[XBase]=None, jahr:int=None ):
        QAbstractTableModel.__init__( self )
        self.rowList:List[XBase] = rowList
        self._visibleElements: List[XBase] = list() # per Default alle (==self.rowList). Kann durch Filterung eingeschränkt werden.
        #self._rowListUnfiltered:List[XBase] = None
        self._jahr:int = jahr # das Jahr ist bei manchen Models interessant, bei manchen nicht - kann also auf None stehen.
        self.headers:List = list()
        self.keys:List = list() # brauchen wir fürs Key-Header-Mapping
        self.headerColor = QColor( "#FDBC6A" )
        self.headerBrush = QBrush( self.headerColor )
        self.negNumberBrush = QBrush( Qt.red )
        self.darkRedBrush = QBrush( Qt.darkRed )
        self.greyBrush = QBrush( Qt.lightGray )
        self.darkGreyBrush = QBrush( Qt.darkGray )
        self.inactiveBrush = QBrush( Qt.black )
        self.inactiveBrush.setStyle( Qt.BDiagPattern )
        self.boldFont = QFont( "Arial", 11, QFont.Bold )
        self.yellow = QColor( "yellow" )
        self.yellowBrush = QBrush( self.yellow )
        self.sortable = True
        self.sort_col = -1
        self._sortkey = ""
        self._sortkeys:List[str] = None
        self.sort_descending = False
        self._filters: List[Filter] = list()  # aktuell gesetzte Spaltenfilter
        #self._visibleRowIndexes:List[int] = list() # Indizes der Rows, die sichtbar sind. Per Default alle,
                                                    # das kann aber durch Filterung eingeschränkt werden
        if rowList:
            self.setRowList( rowList )

    @classmethod
    def fromSeries( cls, series:Series, indexLen:int=-1, jahr:int=None ):
        """
        Erzeugt ein BaseTableModel-Objekt aus einer pandas.Series.
        :param series:
        :param indexLen: Die Länge des Index, die für das TableModel verwendet werden soll.
                         Wenn der Index z.B. ein Timestamp ist, aber nur das Datum verwendet werden soll,
                         muss indexLen = 10 sein.
                         Wenn indexLen == -1, wird der gesamte Index verwendet.
        :param jahr:
        :return:
        """
        itemlist = BaseTableModel.createRowListFromSeries( series, indexLen )
        return cls( itemlist, jahr )

    @staticmethod
    def createRowListFromSeries( series:Series, indexLen:int ) -> List[XSeriesItem]:
        """
        Erzeugt aus einer pandas.Series eine Liste von XSeriesItem, die für die Instanzierung
        eines BaseTableModel verwendet werden kann
        :param series:
        :param indexLen: Die Länge des Index, die für das TableModel verwendet werden soll.
                         Wenn der Index z.B. ein Timestamp ist, aber nur das Datum verwendet werden soll,
                         muss indexLen = 10 sein.
                         Ist indexLen == -1, wird der gesamte Index verwendet.
        :return:
        """
        itemlist: List[XSeriesItem] = list()
        for index, value in series.items():
            if value and str(value) > "":
                idx = str( index )
                if indexLen > -1:
                    idx = idx[:indexLen]
                x = XSeriesItem( idx, value )
                itemlist.append( x )
        return itemlist

    def _setDefaultKeyHeaderMapping( self ):
        """
        Per default verwenden wir die Keys eines der übergebenen Dictionaries als Keys und Headers
        :return:
        """
        x:XBase = self.rowList[0]
        for k in x.getKeys():
            self.keys.append( k )
            self.headers.append( k )

    def setRowList( self, rowList:List[XBase] ):
        self.rowList = rowList
        if len( rowList ) > 0:
            self._setDefaultKeyHeaderMapping()
            self._initVisibleElements()

    def _initVisibleElements( self ):
        for x in self.rowList:
            self._visibleElements.append( x )

    def setKeyHeaderMappings( self, mappings:List[KeyHeaderMapping] ):
        self.headers = [x.header for x in mappings]
        self.keys = [x.key for x in mappings]

    def setKeyHeaderMappings2( self, keys:Iterable[str], headers:Iterable[str] ):
        self.keys = keys
        self.headers = headers

    def setHeaders( self, headerlist:Iterable[str] ):
        """
        Definiert die Spalten-Überschriften.
        Die Reihenfolge muss der Reihenfolge der Keys (Attribute) des XBase-Objekts entsprechen.
        :param headerlist:
        :return:
        """
        self.headers = headerlist

    def getSortColumn( self ) -> int:
        return self.sort_col

    def getSortOrder( self ) -> Qt.SortOrder:
        return Qt.DescendingOrder if self.sort_descending else Qt.AscendingOrder

    def getColumnIndex( self, header ) -> int:
        return self.headers.index( header )

    def getColumnIndexByKey( self, key:str ) -> int:
        return self.keys.index( key )

    def getHeaders( self ) -> List[str]:
        return self.headers

    def getHeader( self, col:int ) -> Any:
        return self.headerData( col, orientation=Qt.Horizontal, role=Qt.DisplayRole )

    def getKeyByHeader( self, header:Any ) -> Any:
        headerIndex = self.headers.index( header )
        return self.keys[headerIndex]

    def getAllElements( self ) -> List[XBase]:
        """
        Liefert die Elemente der originalen rowList dieses Models.
        Achtung: auch Elemente, die möglicherweise aufgrund einer Filterung nicht zu sehen sind, werden geliefert!
        Siehe auch getVisibleRows()
        :return: die rohe Liste der XBase-Elemente
        """
        return self.rowList

    def getVisibleElements( self ) -> List[XBase]:
        """
        Liefert nur die gerade sichtbaren Elemente.
        Wenn das Model nicht gefiltert ist, werden alle Elemente geliefert.
        Siehe auch getRowList()
        :return:
        """
        return self._visibleElements

    def getJahr( self ) -> int:
        return self._jahr

    def getRow( self, x:XBase ) -> int:
        """
        Liefert die Zeile, in der das spezifizierte XBase-Objekt dargestellt wird
        ACHTUNG: Die hier verwendete rowList.index() versucht, das Element <x> durch Adressenvergleich
        zu identifizieren (x1 == x2).
        Eine Kopie von <x> wird hier nicht gefunden!
        :param x:
        :return: the rowIndex of <x> resp. -1 if <x> cannot be found.
                 That may be caused by a filtered TableModel where <x> doesn't meet the filter conditions
        """
        #idx = self.rowList.index( x )
        try:
            return self._visibleElements.index( x )
            #return self._visibleRowIndexes.index( idx )
        except ValueError:
            return -1

    def getElementByUniqueKeyValue( self, key:str, value:Any ) -> XBase or None:
        """
        Liefert das erste Objekt in self.rowList, dessen Key <key> den Wert <value> hat.
        Man sollte diese Methode also nur verwenden, um ein Objekt (Element) anhand seiner eindeutigen ID zu finden.
        Wird der gewünschte Key nicht gefunden, oder kein Element, dessen Key den Wert <value> aufweist, wird None
        zurückgegeben.
        :param key:
        :param value:
        :return:
        """
        for x in self.rowList:
            try:
                val = x.getValue( key )
                if val == value: return x
            except:
                continue
        return None

    def getElement( self, indexrow: int ) -> XBase:
        """
        Liefert das Element, das an Zeile indexrow angezeigt wird.
        !!Das entspricht der Position in der rowList *nur dann, wenn die Tabelle weder sortiert noch gefiltert ist*!!
        Wirft einen IndexError, wenn indexrow größer oder gleich der Länge der _visibleRowIndexes ist.
        @return XBase in Zeile indexrow
        """
        # todo: Änderung wegen neuer Filterlogik --> erledigt
        try:
            #return self.rowList[self._visibleRowIndexes[indexrow]]
            return self._visibleElements[indexrow]
        except Exception as ex:
            print( "Exception bei indexrow ", indexrow )
            raise ex
        #return self.rowList[indexrow]

    def getElements( self, indexrows:List[int] ) -> List[XBase]:
        """
        Liefert die Elemente der Zeilen <indexrows>.
        Geliefert werden nur sichtbare (nicht weg-gefilterte) Objekte.
        Ist eine indexrow größer als der größte Index eines angezeigten Objekts, wird ein ValueEroor geworfen.
        :param indexrows:
        :return:
        """
        # todo: Änderung wegen neuer Filterlogik --> erl.
        retlist = list()
        for r in indexrows:
            retlist.append( self.getElement( r ) )
            #retlist.append( self.rowList[self._visibleRowIndexes[r]] )
            #retlist.append( self.rowList[r] )
        return retlist

    def getKey( self, indexcolumn:int ):
        return self.keys[indexcolumn]

    def getValue( self, indexrow: int, indexcolumn: int ) -> Any:
        e:XBase = self.getElement( indexrow )
        val = e.getValue( self.keys[indexcolumn] )
        return "" if val is None else val

    def getText( self, indexrow: int, indexcolumn: int ) -> str:
        item = self.getValue( indexrow, indexcolumn )
        return item if isinstance( item, str ) else str(item)

    def getValueByName( self, indexrow:int, attrName:str ) -> Any:
        e:XBase = self.getElement( indexrow )
        return e.getValue( attrName )

    def getValueByColumnName( self, indexrow:int, colname:str ) -> Any:
        colidx = self.headers.index( colname )
        return self.getValue( indexrow, colidx )

    def setValue( self, indexrow: int, indexcolumn: int, value: Any ) -> None:
        """
        Ändert einen Wert in dem durch indexrow spezifiz. XBase-Element.
        (Durch indexcolumn wird ein Attribut in diesem XBase-Element spezifiziert.)
        Löst ein dataChanged-Signal aus. (Damit die View sich updaten kann.)
        *** ACHTUNG ***
        Leider kann nicht verhindert werden, dass XBase-Objekte, die Bestandteil dieses Models sind,
        außerhalb des Models verändert werden.
        Da das Model von einer solchen Änderung keine Kenntnis erhält, wird auch kein dataChanged-Signal ausgelöst!
        Wenn es notwendig ist, Objekte außerhalb des Models zu ändern, die View aber trotzdem aktualisiert
        werden soll, muss nach der externen Änderung die Methode objectUpdatedExternally(...) aufgerufen werden.
        ***************
        :param indexrow: Spezifiziert die Zeile der zu ändernden Zelle
        :param indexcolumn: Spezifiziert die Spalte der zu ändernden Zelle
        :param value: der neue Wert, der an dieser Stelle zu setzen ist.
        :return:
        """
        oldval = self.getValue( indexrow, indexcolumn )
        if oldval == value: return
        e: XBase = self.getElement( indexrow )
        key = self.keys[indexcolumn]
        e.setValue( key, value )
        index = self.createIndex( indexrow, indexcolumn )
        self.dataChanged.emit( index, index, [Qt.DisplayRole] )

    def objectUpdatedExternally( self, x:XBase ):
        """
        Diese Methode behandelt ein XBase-Objekt, das außerhalb dieses Models geändert wurde.
        Sie löst ein dataChanged-Signal aus, damit die Anzeige aktualisiert wird.
        """
        row = self.getRow( x ) # hier kann es eine Exception geben, wenn x nicht unter den sichtbaren Elementen ist
        indexA = self.createIndex( row, 0 )
        indexZ = self.createIndex( row, self.columnCount() - 1 )
        self.dataChanged.emit( indexA, indexZ, [Qt.DisplayRole] )

    def objectUpdatedExternally2( self, row:int ):
        """
        Diese Methode löst ein dataChanged-Signal für row <row> aus, damit die Anzeige aktualisiert wird.
        """
        indexA = self.createIndex( row, 0 )
        indexZ = self.createIndex( row, self.columnCount() - 1 )
        self.dataChanged.emit( indexA, indexZ, [Qt.DisplayRole] )

    def addObject( self, x:XBase ):
        """
        Wird aufgerufen, um ein neues Objekt (eine neue Tabellenzeile) hinzuzufügen.
        Löst ein dataChanged-, ein layoutChanged- und ein rowAdded-Signal aus.
        :param x: das neue Objekt
        :return:
        """
        row = 0
        if self.sort_col < 0:
            # rowList nicht sortiert
            # todo: Änderung wegen neuer Filterlogik --> erl.
            self.rowList.append( x )
            if self._meetsFilterConditions( x ):
                # an die visible Elements nur anhängen, wenn x den FilterConditions entspricht.
                # _meetsFilterConditions returns True, wenn keine Filter gesetzt sind.
                self._visibleElements.append( x )
        else:
            # Daten sind sortiert, neues Objekt an der richtigen Stelle einfügen.
            self._insertObject( x, self.rowList )
            #  todo: Änderung wegen neuer Filterlogik: Prüfen, ob neues Element auch in die _visibleElements
            #  aufgenommen werden muss --> erl.
            if self._meetsFilterConditions( x ):
                # _meetsFilterConditions returns True, wenn keine Filter gesetzt sind.
                self._insertObject( x, self._visibleElements )
        if self.sort_col < 0:
            row = self.rowCount() - 1
        indexA = self.createIndex( row, 0 )
        indexZ = self.createIndex( row, self.columnCount()-1 )
        self.dataChanged.emit( indexA, indexZ, [Qt.DisplayRole] )

        self.layoutChanged.emit() # muss hier aufgerufen werden, damit in der View eine neue Row angezeigt wird.
        self.rowsAddedSignal.emit() # muss aufgerufen werden, damit die View die Zeilenhöhe anpasst. Das passiert
                                    # nämlich nach layoutChanged leider nicht.

    def _insertObject( self, x:XBase, targetList:List[XBase] ) -> int:
        """
        Fügt <x> an der der Sortierung entsprechenden Stelle in <targetList> ein.
        Ist die Liste unsortiert, ist die Einfügeposition nicht vorhersehbar.
        :param x:
        :param targetList:
        :return:
        """
        for e in targetList:
            cmp = self.compare( x, e )
            if cmp <= 0:
                pos = targetList.index( e )
                targetList.insert( pos, x )
                return pos

        # hinten anfügen:
        targetList.append( x )
        return len( targetList ) - 1

    def removeObject( self, x:XBase ):
        """
        Wird aufgerufen, um ein Objekt (eine Tabellenzeile) aus der Tabelle zu löschen.
        Beachte: es muss sich um ein in der Tabelle sichtbares Objekt handeln, sonst wird ein ValueError geworfen.
        Löst ein dataChanged- und ein layoutChanged-Signal aus.
        :param x: das zu löschende Objekt
        :return:
        """

        try:
            row = self.getRow( x )  # Wenn x nicht zu den _visibleElements gehört, gibt's eine Exception
            self.rowList.remove( x )
            # aus der Liste der _visibleElements löschen. Da muss es drin sein, sonst hätten wir die row gar nicht gefunden.
            self._visibleElements.remove( x )
        except:
            # kann passieren wegen des EinAusWriteDispatcher.ea_deleted Signals.
            return
        indexA = self.createIndex( row, 0 )
        indexZ = self.createIndex( row, self.columnCount()-1 )
        self.dataChanged.emit( indexA, indexZ, [Qt.DisplayRole] )
        # method = sys._getframe().f_code.co_name
        self.layoutChanged.emit() # muss hier aufgerufen werden, damit in der View eine Zeile weniger angezeigt wird.

    def removeObjects( self, xlist:List[XBase] ):
        for x in xlist:
            self.removeObject( x )

    def removeObjectsByKeyValue( self, key:str, value:Any ):
        # todo: Änderung wegen neuer Filterlogik --> nicht notwendig, denn self.removeObject()
        #  berücksichtigt sowohl die rowList wie auch die _visibleElements
        """
        Entfernt alle Objekte aus der rowlist, auf die die Bedingung x.__dict__[key] == value zutrifft.
        :param key:
        :param value:
        :return:
        """
        for x in self.rowList:
            if x.getValue( key ) == value:
                self.removeObject( x )

    def rowCount( self, parent:QModelIndex=None ) -> int:
        # todo: Änderung wegen neuer Filterlogik --> erl.
        return len( self._visibleElements )
        #return len( self._visibleRowIndexes )
        #return len( self.rowList )

    def columnCount( self, parent:QModelIndex=None ) -> int:
        return len( self.headers )

    def data( self, index: QModelIndex, role: int = None ):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            val = self.getValue( index.row(), index.column() )
            if isinstance( val, float ):
                return "%.2f" % val
                #return '{:.2f}'.format( round( val, 2 ) )
            return val
        elif role == Qt.TextAlignmentRole:
            return self.getAlignment( index.row(), index.column() )
            # v = self.getValue( index.row(), index.column() )
            # if isinstance( v, numbers.Number ): return int( Qt.AlignRight | Qt.AlignVCenter )
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

    def getAlignment( self, indexrow:int, indexcolumn:int ) -> Qt.Alignment or None:
        v = self.getValue( indexrow, indexcolumn )
        if isinstance( v, numbers.Number ): return int( Qt.AlignRight | Qt.AlignVCenter )

    def getBackgroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        return None

    def getForegroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        if self.negNumberBrush:
            val = self.getValue( indexrow, indexcolumn )
            if isinstance( val, numbers.Number ) and val < 0:
                return QBrush( Qt.red )
        return None

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

    #################   filtering  ##############################
    ## Neue Filterlogik
    def clearFilter( self, header:str ):
        """
        Der Filter für Spalte <header> wurde aufgehoben
        :param header:
        :return:
        """
        key = self.getKeyByHeader( header )
        for filtr in self._filters:
            if filtr.key == key:
                self._filters.remove( filtr )
                break
        if len( self._filters ) == 0:
            self._initVisibleElements()
        else:
            self._buildFilterIndexList()
        self.layoutChanged.emit()

    def applyFilter( self, header:str, filterval:str ):
        f:Filter = self._updateFilters( header, filterval )
        if f:
            # neuer Filter, wir brauchen die filterIndexList nicht ganz neu aufbauen, sondern nur ergänzen,
            # sprich: die Objekte rauswerfen, die dem neuen Filter nicht genügen
            self._updateFilterIndexList( f.key, f.filterval )
        else:
            # ein bereits bestehender Filter hat sich geändert. Die ganze filterIndexList neu aufbauen
            self._buildFilterIndexList()
        self.layoutChanged.emit()

    def _updateFilterIndexList( self, key:str, filterval:str ):
        """
        Diese Methode wird aufgerufen, wenn ein neuer Filter (für <header> mit dem Wert <filterval> gesetzt worden ist.
        Sie prüft, welche Objekte in der _visibleElements-List dem neuen Filterwert
        entsprechen und entfernt diejenigen Objektreferenzen, die das nicht tun.
        :param key:
        :param filterval:
        :return:
        """
        self._visibleElements = [x for x in self._visibleElements if self._meetsFilterCondition( x, key, filterval)]

    def _buildFilterIndexList( self ):
        """
        Baut die _visibleElements-Liste auf unter Verwendung aller aktiven Filter (filterList)
        :return:
        """
        self._visibleElements.clear()
        for x in self.rowList:
            if self._meetsFilterConditions( x ):
                self._visibleElements.append( x )

    def _meetsFilterConditions( self, x:XBase ) -> bool:
        for f in self._filters:
            if not self._meetsFilterCondition( x, f.key, f.filterval ):
                return False
        return True

    @staticmethod
    def _meetsFilterCondition( x:XBase, key:str, filterval:str ) -> bool:
        val = x.getValue( key )
        if isinstance( val, str ):
            val = val.lower()
        return filterval in val

    def _updateFilters( self, header: str, filterval: str ) -> Filter or None:
        """
        Prüft, ob für Spalte <header> schon ein Filter gesetzt ist.
        Wenn ja, wird dessen Wert mit <filterval> aktualisiert.
        Wenn nein, wird ein neuer Filter für <header> angelegt und der Filterliste hinzugefügt.
        :param header:
        :param filterval:
        :return: das neue Filter-Objekt, wenn der Filter für <header> neu ist, sonst None
        """
        key = self.getKeyByHeader( header )
        for filtr in self._filters:
            if filtr.key == key: # Filter existiert schon, ggf. seinen Wert mit <filterval> aktualisieren
                if not filtr.filterval == filterval:
                    filtr.filterval = filterval.lower()
                return None
        f = Filter( key, filterval.lower() )
        self._filters.append( f )
        return f

    def setSortable( self, sortable:bool=True ):
        self.sortable = sortable

    class Tmp:
        def __init__( self, row: int, x: XBase ):
            self.row = row
            self.x = x

    def sortMultipleColumns( self, keys:Iterable[str], order:Qt.SortOrder=None ) -> List[int]:
        """
        Sortiert die Elemente in der _visibleElements-List.
        :param keys:
        :param order:
        :return:
        """
        self._sortkeys = keys
        self.layoutAboutToBeChanged.emit()
        self.before_multi_sorting.emit()
        if order:
            self.sort_descending = (order == Qt.SortOrder.DescendingOrder)
        else:
            self.sort_descending = not self.sort_descending
        self._visibleElements = sorted( self._visibleElements, key=cmp_to_key( self._compareMultiple ) )
        self.layoutChanged.emit()
        self.multi_sorting_finished.emit()

    def _compareMultiple( self, x1:XBase, x2:XBase ):
        for key in self._sortkeys:
            self._sortkey = key
            rc = self.compare( x1, x2 )
            if rc != 0: return rc
        return 0

    def sort( self, col:int, order: Qt.SortOrder=Qt.SortOrder.DescendingOrder ) -> None:
        # todo: Änderung wegen neuer Filterlogik --> erl.
        if not self.sortable: return
        self.sort_col = col
        if col < 0: return
        self._sortkey = self.getKey( self.sort_col )
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        self.before_sorting.emit()
        self.sort_descending = True if order == Qt.SortOrder.DescendingOrder else False
        self._visibleElements = sorted( self._visibleElements, key=cmp_to_key( self.compare ) )
        self.sorting_finished.emit()
        self.layoutChanged.emit()

    # def compare2( self, row1:int, row2:int ) -> int:
    #     x1 = self.rowList[row1]
    #     x2 = self.rowList[row2]
    #     return self.compare( x1, x2 )

    def compare( self, x1:XBase, x2:XBase ) -> int:
        """
        Vergleicht die Werte von self.sort_col der Objekte x1 und x2.
        :param x1: Objekt 1
        :param x2: Objekt 2
        :return: der Returnwert ist abhängig davon, ob auf- oder absteigendes Sortieren gewünscht wird.
                 Wenn absteigend:
                    wenn value x1 < value x2: 1
                    wenn value x1 > value x2: -1
                 Wenn aufsteigend:
                    wenn value x1 < value x2: -1
                    wenn value x1 > value x2: 1
                 Bei Gleichheit der beiden Werte: 0
        """
        v1 = x1.getValue( self._sortkey )
        v2 = x2.getValue( self._sortkey )
        if v1 is None: return -1 if self.sort_descending else 1
        if v2 is None: return 1 if self.sort_descending else -1
        if isinstance( v1, str ):
            v1 = v1.lower()
            v2 = v2.lower()
        if v1 < v2: return -1 if self.sort_descending else 1
        if v1 > v2: return 1 if self.sort_descending else -1
        return 0 # v1 == v2

##################  SumTableModel  #########################
class SumTableModel( BaseTableModel ):
    """
    A BaseTableModel displaying a sum row below all other rows
    """
    def __init__( self, objectList:List[XBase], jahr:int, colsToSum:Iterable[str] ):
        BaseTableModel.__init__( self, objectList, jahr )
        if not objectList or len(objectList) == 0:
            raise Exception( "SumTableModel: Construction needs an objectList with at least one element." )
        self._colsToSum = colsToSum # Liste mit den keys (Attributnamen des XBase-Objekts) der Spalten,
                                    # die summiert werden sollen
        self._summen:List[Dict] = list() # enthält die Summen,
                                         # die unter den in _colsToSum spezifierten Spalten anzuzeigen sind
        self._rowCount = len( objectList ) + 1  # wegen Summenzeile
        self._fontSumme = QFont( "Arial", 12, weight=QFont.Bold )
        for col in self._colsToSum:
            summe = sum([e.getValue( col ) for e in objectList])
            dic = {"key": col, "sum" : summe}
            self._summen.append( dic )

    @classmethod
    def fromSeries( cls, series:Series, indexLen:int, jahr:int, colsToSum:Iterable[str] ):
        itemlist = BaseTableModel.createRowListFromSeries( series, indexLen )
        return cls( itemlist, jahr, colsToSum )

    def rowCount( self, parent: QModelIndex = None ) -> int:
        return self._rowCount

    def getValue( self, indexrow: int, indexcolumn: int ) -> Any:
        if indexrow == self._rowCount - 1: # letzte Zeile, in der ersten Spalte "SUMME" ausgeben.
                                           # in den Spalten, deren Werte summiert werden sollen, die Summen ausgeben.
            if indexcolumn == 0:
                return "SUMME"
            else:
                key = self.keys[indexcolumn]
                if key in self._colsToSum: # die Summe der Spalte, die die Werte von key enthält, soll angezeigt werden
                    dic = [d for d in self._summen if d["key"] == key][0]
                    return dic["sum"]
                else:
                    return ""
        key = self.keys[indexcolumn]
        return self.internalGetValue( indexrow, indexcolumn )

    def internalGetValue( self, indexrow:int, indexcolumn:int ) -> Any:
        """
        For internal use only.
        May be overridden by inherited classes
        :param indexrow:
        :param indexcolumn:
        :return:
        """
        e: XBase = self.getElement( indexrow )
        return e.getValue( self.keys[indexcolumn] )

    def getFont( self, indexrow: int, indexcolumn: int ) -> QFont or None:
        if indexrow == self._rowCount - 1:
            key = self.keys[indexcolumn]
            if key in self._colsToSum:
                return self._fontSumme
            else:
                return None

################################################################

def test2():
    tm = SumTableModel

def test():
    class X(XBase):
        def __init__(self, v1, v2 ):
            XBase.__init__( self )
            self.var1 = v1
            self.var2 = v2

    def onNewItem():
        xn = X( "Adam", 99 )
        tm.addObject( xn )

    def onDeleteItem( rowlist ):
        if len( rowlist ) > 0:
            obj = tm.getElement( rowlist[0] )
            tm.removeObject( obj )

    def onEditItem( row ):
        obj = tm.getElement( row )
        ## so nicht:
        #obj.var1 = "Meister Karl"  # Mist!! Es wird kein ChangeLog geschrieben und
                                   # die Änderung wird nicht in der Tabelle angezeigt bis zum nächsten
                                   # layoutChanged-Signal
        ## entweder so:
        ##col = tm.getColumnIndexByKey( "var1" )
        ##tm.setValue( row, col, "Master Karl" )
        ## oder so:
        obj.var1 = "Meister Karl"
        tm.objectUpdatedExternally( obj )

    x1 = X( "Berta", 34 )
    x2 = X( "Wolfi", 57 )
    x3 = X( "Dora", 40 )
    x4 = X( "Maik", 44 )
    l = [x1, x2, x3, x4]
    tm = BaseTableModel( l )
    e = tm.getElement( 5 )
    for r in range(0, 4):
        e:X = tm.getElement( r )
        print( e.var1 )

    # from PySide2.QtWidgets import QApplication
    # from base.basetableview import BaseTableView
    # from base.basetableviewframe import BaseTableViewFrame
    # app = QApplication()
    # v = BaseTableView()
    # v.setModel( tm )
    # frame = BaseTableViewFrame( v, True )
    # frame.newItem.connect( onNewItem )
    # frame.editItem.connect( onEditItem )
    # frame.deleteItems.connect( onDeleteItem )
    # frame.show()
    # app.exec_()
