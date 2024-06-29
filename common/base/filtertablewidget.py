import numbers
from enum import IntEnum, auto
from typing import List, Dict, Callable, Collection, Any

from PySide2 import QtCore
from PySide2.QtCore import QModelIndex, Qt, Signal, QSize, QItemSelectionModel, QObject, QThreadPool
from PySide2.QtGui import QBrush, QFocusEvent
from PySide2.QtWidgets import QTableView, QHeaderView, QHBoxLayout, QWidget, QVBoxLayout, \
    QAbstractItemView, QGridLayout, QApplication, QToolBar

import datehelper
from base.baseqtderivates import BaseEdit, BaseDialogWithButtons, getOkCancelButtonDefinitions, BaseButton, \
    SearchField, NewIconButton, EditIconButton, DeleteIconButton, CaseSensitiveButton, WholeWordButton, YearComboBox, \
    MonthComboBox, PrintButton, ExportButton
from base.basetablefunctions import BaseTableFunctions
from base.basetablemodel import BaseTableModel
from base.basetableview import BaseTableView
from base.basetableviewframe import BaseTableViewToolBar
from base.exporthandler import ExportHandler
from base.interfaces import XBase, TestItem


#####################################################################
from base.printhandler import PrintHandler

class HeaderTableModel( BaseTableModel ):
    class XFilter( XBase ):
        def __init__(self ):
            XBase.__init__( self )

    def __init__( self, headers:List[str] ):
        def makeFilterList( headerlist ) -> List[HeaderTableModel.XFilter]:
            l = list()
            x = HeaderTableModel.XFilter()
            l.append( x ) # Liste hat nur ein Element
            filterDict = x.__dict__
            for header in headerlist:
                filterDict[header] = "Filter"
            return l
        BaseTableModel.__init__( self, makeFilterList( headers ) )
        self._headers = headers
        self._brush = QBrush( Qt.lightGray )

    def rowCount( self, parent: QModelIndex = None ) -> int:
        return 1

    def columnCount( self, parent: QModelIndex = None ) -> int:
        return len( self._headers )

    def getHeader( self, col:int ) -> str:
        return self._headers[col]

    def getHeaders( self ) -> List[str]:
        return self._headers

    def data( self, index: QModelIndex, role: int = None ):
        ret = super().data( index, role )
        if role == Qt.ForegroundRole:
            return self._brush
        # elif role == Qt.BackgroundRole:
        #     return QColor( "white" )
        return ret

###########################################################################
class FilterEdit( QWidget ):
    filter_changed = Signal( str, str ) # args = header, filtervalue
    filter_cleared = Signal( str ) # arg = header
    tab_pressed = Signal()
    def __init__( self, header:str ):
        QWidget.__init__( self )
        self._header = header
        self._layout = QHBoxLayout()
        self.setLayout( self._layout )
        self._layout.setContentsMargins( 0, 0, 0, 0 )
        self._layout.setSpacing( 0 )
        self._input = BaseEdit()
        self._input.tab_pressed.connect( self.tab_pressed.emit )
        self._layout.addWidget( self._input )
        self._btnReset = BaseButton( "x" )
        self._btnReset.setMaximumWidth( 22 )
        self._btnReset.clicked.connect( self.onReset )
        self._layout.addWidget( self._btnReset )
        self._input.textChanged.connect( lambda: self.filter_changed.emit( self._header, self._input.getValue() ) )

    def getEditField( self ) -> BaseEdit:
        return self._input

    def getFilterValue( self ) -> str:
        return self._input.getValue()

    def getFilterColumnHeader( self ) -> str:
        return self._header

    def setFocus( self ):
        self._input.setFocus()
        self._input.setStyleSheet( "background-color: white;" )

    def onReset( self ):
        self.filter_cleared.emit( self._header )


###########################################################################
class HeaderTableView(BaseTableView):
    """
    Tabelle, bestehend nur aus den Headern und *einer* Zeile
    """
    filter_changed = Signal( str, str ) # args = header, filtervalue
    filter_cleared = Signal( str ) # arg = header
    def __init__(self ):
        BaseTableView.__init__( self )
        # Notlösung, weil sonst beim horiz. Scrollen die Spalten von HeaderView und DataView gegeneinander verrutschen:
        self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )
        self.verticalScrollBar().hide()
        # Notlösung Ende
        self._filterList:List[Dict] = list() # List of FilterEdit objects
        self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.btvLeftClicked.connect( self.onCellClicked )

    # def focusInEvent(self, event:QFocusEvent):
    #     super().focusInEvent( event )
    #     # sel = self.selectedIndexes()
    #     # print( "Header: focusIn: ", sel )
    #
    # def focusOutEvent(self, event:QFocusEvent):
    #     super().focusOutEvent( event )
    #     # print( "Header: focusOut" )

    def onCellClicked( self, index:QModelIndex ):
        # in eine Filter-Zelle geklickt. In diese Zelle ein FilterEdit-Objekt platzieren.
        tm:HeaderTableModel = self.model()
        col = index.column()
        header = tm.getHeader( col )
        filter = FilterEdit( header )
        filter.filter_changed.connect( self.filter_changed.emit )
        filter.filter_cleared.connect( self.onFilterReset )
        self.setIndexWidget( index, filter )
        filter.setFocus()
        filterDict = { "header": header, "column": col, "filter": filter }
        self._filterList.append( filterDict )

    def onFilterReset( self, header:str ):
        tm:HeaderTableModel = self.model()
        for filterDict in self._filterList:
            if filterDict["header"] == header:
                col = filterDict["column"]
                index = tm.createIndex( 0, col )
                self.setIndexWidget( index, None )
                self._filterList.remove( filterDict )
                del filterDict["filter"]
                break
        self.clearSelection()
        self.filter_cleared.emit( header )
        return

    def setModel( self, headers:List[str] ):
        htm = HeaderTableModel( headers )
        super().setModel( htm )
        htm.setSortable( False )
        headerheight = self.horizontalHeader().height()
        rowheight = self.rowHeight( 0 )
        self.setFixedHeight( headerheight + rowheight )
        self.setSelectionBehavior( QTableView.SelectItems )
        self.setSelectionMode( QAbstractItemView.SingleSelection )
        self.clearSelection()

###########################################################################
class DataTableView( BaseTableView ):
    #size_sync_needed = Signal( int, int, int )
    """
    Datentabelle ohne Header
    """
    def __init__(self):
        BaseTableView.__init__( self )
        hv:QHeaderView = self.horizontalHeader()
        hv.hide()
        # Notlösung, weil sonst beim horiz. Scrollen die Spalten von HeaderView und DataView gegeneinander verrutschen:
        self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )

##############################################################################
class SearchWidget2( QWidget ):
    doSearch = Signal( str )
    searchtextChanged = Signal()
    caseSensitiveToggled = Signal( bool ) # True: es wurde auf "sensitive" gestellt
    wholeWordToggled = Signal( bool ) # True: es wurde auf "nur ganzes Wort" gestellt

    def __init__( self ):
        QWidget.__init__( self )
        self._layout = QHBoxLayout()
        self._searchfield = SearchField()
        self._btnCaseSensitive = CaseSensitiveButton()
        self._btnCaseSensitive.clicked.connect( self.onCaseSensitiveToggled )
        self._btnWholeWord = WholeWordButton()
        self._btnWholeWord.clicked.connect( self.onWholeWordToggled )
        #self._btnWholeWord.releaseMouse.connect( self.setFocusToSearchField )
        # forward signals from searchfield:
        self._searchfield.doSearch.connect( self.doSearch.emit )
        self._searchfield.searchTextChanged.connect( self.searchtextChanged.emit )
        self._createGui()

    def _createGui( self ):
        l = self._layout
        self.setLayout( l )
        l.setContentsMargins( 0, 0, 0, 0 )
        l.setSpacing( 0 )
        l.addWidget( self._searchfield, alignment=Qt.AlignLeft )
        self._btnCaseSensitive.setFixedSize( QSize(26, 26) )
        self._btnCaseSensitive.setFlat( True )
        l.addWidget( self._btnCaseSensitive, alignment=Qt.AlignLeft )
        self._btnWholeWord.setFixedSize( QSize( 26, 26 ) )
        self._btnWholeWord.setFlat( True )
        l.addWidget( self._btnWholeWord, alignment=Qt.AlignLeft )

    def setSearchFieldBackgroundColor( self, htmlColor:str ) -> None:
        self._searchfield.setBackgroundColor( htmlColor )

    def setFocusToSearchField( self ):
        self._searchfield.setFocus()

    def onCaseSensitiveToggled( self, isCaseSensitive:bool ):
        self._searchfield.setBackgroundColor( "#ffffff" )
        self._searchfield.setFocus()
        self.caseSensitiveToggled.emit( isCaseSensitive )

    def onWholeWordToggled( self, isWholeWord:bool ):
        self._searchfield.setBackgroundColor( "#ffffff" )
        self._searchfield.setFocus()
        self.wholeWordToggled.emit( isWholeWord )

def testSearchWidget():
    app = QApplication()
    sw = SearchWidget2()
    sw.show()
    app.exec_()

####################################################################################
class AbstractToolWrapper( QWidget ):
    def __init__(self, tool:QWidget, tv:BaseTableView ):
        QWidget.__init__( self )
        self._tool = tool
        self.tv = tv
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins( 0, 0, 0, 0 )
        self._layout.setSpacing( 1 )
        self._layout.addWidget( tool )
        self.setLayout( self._layout )

    def getTool( self ) -> QWidget:
        return self._tool

#####################################################################################
class SearchTool( AbstractToolWrapper ):
    def __init__(self, tv:BaseTableView ):
        AbstractToolWrapper.__init__( self, SearchWidget2(), tv )
        self._searchHandler = SearchHandler2( tv, self.getTool() )

####################################################################################
class PrintTool( AbstractToolWrapper ):
    def __init__(self, tv:BaseTableView ):
        AbstractToolWrapper.__init__( self, PrintButton(), tv )
        btnPrint = self.getTool()
        btnPrint.setToolTip( "Drucken dieser Tabellenansicht" )
        self._printHandler = PrintHandler( tv )
        # btnPrint.clicked.connect( self._printHandler.handlePrint )
        btnPrint.clicked.connect( self._printHandler.handlePreview )

####################################################################################
class ExportTool( AbstractToolWrapper ):
    def __init__(self, tv:BaseTableView ):
        btn = ExportButton()
        AbstractToolWrapper.__init__( self, btn, tv )
        btn.setToolTip( "Exportieren dieser Tabelle nach Calc" )
        self._exportHandler = ExportHandler()
        btn.clicked.connect( lambda: self._exportHandler.exportToCsv( tv.model() ) )

####################################################################################
class TableTool( IntEnum ):
    SEARCH = auto()
    PRINT = auto()
    EXPORT = auto()
    NONE = auto()

####################################################################################
class TableTools( QToolBar ):
    def __init__( self, tv:BaseTableView ):
        QToolBar.__init__( self )
        self._tv = tv
        self._toolCnt = 0
        self._searchTool:SearchTool = None
        self._printTool:PrintTool = None
        self._exportTool:ExportTool = None
        self._toolWidgets:List[QWidget] = list()

    def addStandardTableTools( self, tools:Collection[TableTool] ):
        """
        Fügt ein Standard-Tabellen-Tool hinzu.
        Standard-Tools sind SearchTool, PrintTool und ExportTool. Sie beziehen sich auf die Tabellendaten selbst und
        haben ihre eigenen Handler, sodass vom TableTools-Objekt keine Signale nach außen gegebben werden müssen.
        Um andere Tools hinzuzufügen, verwende die Methode addToolWidget().
        :param tools:
        :return:
        """
        for tool in tools:
            if self._toolCnt > 0:
                self.addSeparator()
            if tool == TableTool.SEARCH:
                self._createSearchTool()
            elif tool == TableTool.PRINT:
                self._createPrintTool()
            elif tool == TableTool.EXPORT:
                self._createExportTool()
            self._toolCnt += 1

    def addToolWidget( self, widget:QWidget ):
        """
        Fügt ein Tool hinzu, das nicht zu den Tabellen-Standard-Tools gehört (siehe addStandardTableTools()).
        Damit dieses Tool ggf. abgerufen werden kann, muss ein objectName gesetzt worden sein (siehe Methode
        getToolWidget())
        :param widget:
        :return:
        """
        if self._toolCnt > 0:
            self.addSeparator()
        self.addWidget( widget )
        self._toolWidgets.append( widget )
        self._toolCnt += 1

    def getToolWidget( self, objectName:str ) -> QWidget or None:
        for widget in self._toolWidgets:
            if widget.objectName() == objectName:
                return widget
        return None

    def _createSearchTool( self ):
        if not self._searchTool:
            self._searchTool = SearchTool( self._tv )
            self.addWidget( self._searchTool )

    def _createPrintTool( self ):
        self._printTool = PrintTool( self._tv )
        self.addWidget( self._printTool )

    def _createExportTool( self ):
        self._exportTool = ExportTool( self._tv )
        self.addWidget( self._exportTool )

##############################################################################################
class FilterTableWidget( QWidget ):
    def __init__( self ):
        QWidget.__init__( self )
        self._tools = None
        self.dataTv = DataTableView()
        self.dataTv.horizontalScrollBar().valueChanged.connect( self.onScrollDataViewHorizontally )
        #self.dataTv.verticalScrollBar().installEventFilter( self )
        self.headerTv = HeaderTableView()
        self.headerTv.filter_changed.connect( self.onFilterChanged )
        self.headerTv.filter_cleared.connect( self.onFilterCleared )
        self.headerTv.horizontalHeader().sectionClicked.connect( self.onColumnHeaderClicked )
        # self._filters:List[Filter] = list() # aktuell gesetzte Spaltenfilter
        self._sortOrder: Qt.SortOrder = None
        self._vlayout = QVBoxLayout()
        self._vlayout.setContentsMargins( 0, 0, 0, 0 )
        self._vlayout.setSpacing( 1 )
        self._vlayout.addWidget( self.headerTv )
        self._vlayout.addWidget( self.dataTv )
        self.setLayout( self._vlayout )
        self._headerTvLayoutPos = 0
        self._searchHandler = None #SearchHandler2( self.dataTv, self._searchWidget )
        self._threadpool = QThreadPool()
        self._wlist:List[int] = list() # Liste der zwischen-gemerkten Spaltenbreiten

    def onScrollDataViewHorizontally( self, val ):
        htv = self.headerTv
        # htv.viewport().scroll( dx, 0 )
        # htv.repaint()
        #htv.scrollContentsBy( dx, 0 )
        #self.headerTv.horizontalScrollBar().scroll( dx, 0 )
        # val = htv.horizontalScrollBar().value()
        #print( "scrolled from ", val, " to ", val+dx )
        htv.horizontalScrollBar().setValue( val )

    # def eventFilter( self, o, e ):
    #     if o is self.dataTv.verticalScrollBar():
    #         # cols = self.headerTv.model().columnCount()
    #         # w = self.headerTv.columnWidth( cols - 1 )
    #         if e.type() == QtCore.QEvent.Show:
    #             print( "show dataView vertical scrollbar")
    #             viewport = self.headerTv.viewport()
    #             vpsize = viewport.size()
    #             viewport.resize( QSize(vpsize.width()-25, vpsize.height() ) )
    #             # print( "Verkleiner3e4")
    #             # self.headerTv.setColumnWidth( cols-1, w-25 )
    #         elif e.type() == QtCore.QEvent.Hide:
    #             pass
    #             #print( "Vergößere")
    #             #self.headerTv.setColumnWidth( cols - 1, w + 25 )
    #     return False

    def addStandardTableTools( self, tools:Collection[TableTool] ):
        self._ensureToolsExist()
        self._tools.addStandardTableTools( tools )

    def addToolWidget( self, tool:QWidget ):
        """
        Diese Methode fügt die Tools hinzu, die nicht Standard-Tools sind, z.B. Year- und MonthCombo.
        Um die StandardTools Suchen, Drucken, Exportieren hinzuzufügen, siehe Methode addStandardTableTools.
        :param tool:
        :return:
        """
        self._ensureToolsExist()
        self._tools.addToolWidget( tool )

    def _ensureToolsExist( self ):
        if not self._tools:
            self._tools = TableTools( self.dataTv )
            self._vlayout.insertWidget( 0, self._tools, stretch=0, alignment=Qt.AlignLeft )

    def setModel( self, tm:BaseTableModel, selectRows:bool=True, singleSelection:bool=True ):
        model = self.dataTv.model()
        if model:
            model.before_multi_sorting.disconnect( self.onBeforeMultiSorting )
            model.multi_sorting_finished.disconnect( self.onMultiSortingFinished )
        self.headerTv.setModel( tm.getHeaders() )
        self.dataTv.setModel( tm, selectRows, singleSelection )
        self.setHeaderColumnWidthsAccordingDataColumns()
        if not model:
            self.headerTv.horizontalHeader().sectionResized.connect( self.onHeaderColumnResized )
        tm.before_multi_sorting.connect( self.onBeforeMultiSorting )
        tm.multi_sorting_finished.connect( self.onMultiSortingFinished )

    #### methods of QTableView and BaseTableView - forward to dataTv or headerTv ##############
    def horizontalHeader( self ) -> QHeaderView:
        return self.headerTv.horizontalHeader()

    def model( self ) -> BaseTableModel:
        return self.dataTv.model()

    def selectionModel( self ):
        return self.dataTv.selectionModel()

    def selectedIndexes( self ) -> List[int]:
        return self.dataTv.selectedIndexes()

    def setAlternatingRowColors( self, enabled=True ):
        self.dataTv.setAlternatingRowColors( enabled )

    def scrollTo( self, index ):
        self.dataTv.scrollTo( index )

    def rowHeight( self, row:int ) -> int:
        return self.dataTv.rowHeight( row )

    def columnWidth( self, col:int ) -> int:
        return self.headerTv.columnWidth( col )

    def sortByColumn( self, column:int, order:Qt.SortOrder = Qt.SortOrder.AscendingOrder ):
        self.dataTv.horizontalHeader().setSortIndicator( column, order )
        self.headerTv.horizontalHeader().setSortIndicator( column, order )

    def setContextMenuCallbacks( self, provider: Callable, onSelected: Callable ) -> None:
        self.dataTv.setContextMenuCallbacks( provider, onSelected )

    def resizeColumnsToContents(self):
        self.headerTv.horizontalHeader().sectionResized.disconnect( self.onHeaderColumnResized )
        # Spalten der Datentabelle einstellen
        self.resizeColumnsToContents()
        # Spalten der Headertabelle einstellen
        self.setHeaderColumnWidthsAccordingDataColumns( )
        # Slots wieder anmelden:
        self.headerTv.horizontalHeader().sectionResized.connect( self.onHeaderColumnResized )

    # def resizeRowsAndColumns( self ):
    #     #self.dataTv.resizeRowsToContents()
    #     self.resizeColumnsToContents()

    #### methods of QTableView - end  ##########

    def setHeaderColumnWidthsAccordingDataColumns( self  ):
        cols = self.dataTv.model().columnCount()
        for col in range( 0, cols ):
            w = self.dataTv.columnWidth( col )
            self.headerTv.setColumnWidth( col, w )

    def getPreferredWidth( self ) -> int:
        return self.dataTv.getPreferredWidth()

    def getPreferredHeight( self ) -> int:
        h = BaseTableFunctions.getPreferredHeight( self.headerTv )
        h += BaseTableFunctions.getPreferredHeight( self.dataTv )
        return h + 25

    def onColumnHeaderClicked( self, *args, **kwargs ):
        """
        Wird nach Linksclick auf einen Spoltenkopf aufgerufen. Es soll sortiert werden.
        Nach dem Sortieren müssen die vorherigen Spaltenbreiten wiederhergestellt werden.
        :param args: ein Tupel, das an Stelle 0 den Index der Spalte enthält
        :param kwargs:  leer
        :return:
        """
        # Spaltenbreiten vor Sortieren merken und hinterher wieder genauso einstellen.
        self._storeDataTableColumnWidths()
        self.horizontalHeader().setSortIndicatorShown( True )
        col = args[0]
        if self._sortOrder is None:
            self._sortOrder = Qt.SortOrder.AscendingOrder
        else:
            if self._sortOrder == Qt.SortOrder.DescendingOrder:
                self._sortOrder = Qt.SortOrder.AscendingOrder
            else:
                self._sortOrder = Qt.SortOrder.DescendingOrder
        self.dataTv.model().sort( col, self._sortOrder )
        # Jetzt die Spalten wieder auf die vorherige Größe einstellen. Dazu erstmal die
        # sectionResized-Slots abklemmen
        self.headerTv.horizontalHeader().sectionResized.disconnect( self.onHeaderColumnResized )
        # Spalten der Datentabelle einstellen
        self._restoreDataTableColumnWidths()
        # Spalten der Headertabelle einstellen
        self.setHeaderColumnWidthsAccordingDataColumns()
        # Slots wieder anmelden:
        self.headerTv.horizontalHeader().sectionResized.connect( self.onHeaderColumnResized )

    def _storeDataTableColumnWidths( self ):
        self._wlist.clear()
        for c in range( 0, self.dataTv.model().columnCount() ):
            w = self.dataTv.columnWidth( c )
            self._wlist.append( w )

    def _restoreDataTableColumnWidths( self ):
        for c in range( 0, len( self._wlist ) ):
            self.dataTv.setColumnWidth( c, self._wlist[c] )

    def getSelectedRows( self ) -> List[int]:
        return BaseTableFunctions.getSelectedRows( self.dataTv)

    def getTableView( self ) -> BaseTableView:
        return self.dataTv

    def clearSelection( self ):
        self.dataTv.clearSelection()

    def onHeaderColumnResized( self, col: int, oldW: int, newW: int ):
        #print( "headerColumnResized" )
        self.dataTv.setColumnWidth( col, newW )

    def onFilterChanged( self, header, filterval ):
        QApplication.processEvents()
        self._storeDataTableColumnWidths()
        self.dataTv.model().applyFilter( header, filterval)
        self._restoreDataTableColumnWidths()

    def onFilterCleared( self, header:str ):
        self._storeDataTableColumnWidths()
        self.dataTv.model().clearFilter( header )
        self._restoreDataTableColumnWidths()

    def onBeforeMultiSorting( self ):
        self._storeDataTableColumnWidths()
        # print( "onBeforeMultiSorting ", self._wlist )

    def onMultiSortingFinished( self ):
        # print( "onMultiSortingFinished ", self._wlist )
        self._restoreDataTableColumnWidths()
        self.horizontalHeader().setSortIndicatorShown( False )


################################################################################################
class SearchHandler2( QObject ):
    def __init__( self, tv: BaseTableView, searchWidget:SearchWidget2 ):
        QObject.__init__( self )
        self._searchValueOrig = None # so wurde der Suchbegriff vom Anwender ins Suchfeld eingetragen
        self._searchValue = None # enthält den aufbereiteten Suchbegriff (siehe _prepareSearchValue)
        self._searchValueNum = None # der Suchbegriff in numerischer Form
                                    # (not None nur, wenn z.B. nach "123" gesucht werden soll)
        self._tv = tv
        self._searchWidget = searchWidget
        self._searchFieldBackground = None
        self._searchWidget.doSearch.connect( self.onDoSearch )
        self._searchWidget.searchtextChanged.connect( self.onSearchfieldChanged )
        self._searchWidget.caseSensitiveToggled.connect( self.onCaseSensitiveToggled )
        self._searchWidget.wholeWordToggled.connect( self.onWholeWordToggled )
        # self._model:BaseTableModel = tv.model() NEIN! Der Pointer auf das Model muss in _searchNextMatch()
                                                # geholt werden, da sich das Model ändern kann (durch Filterung)
        self._caseSensitive = False
        self._exactMatch = False
        self._row = 0
        self._col = 0

    def onCaseSensitiveToggled( self, isCaseSensitive:bool ):
        self._caseSensitive = isCaseSensitive

    def onWholeWordToggled( self, isWholeWord:bool ):
        self._exactMatch = isWholeWord

    def onSearchfieldChanged( self ):
        self._searchWidget.setSearchFieldBackgroundColor( "#ffffff" )
        self._tv.clearSelection()

    def _makeComparable( self, val ):
        valNum = None
        if isinstance(val, numbers.Number):
            valNum = val
            val = str( val )
        else:  # string (hopefully)
            try:
                valNum = int( val )
            except ValueError:
                try:
                    valNum = float( val )
                except ValueError:
                    pass
        if not self._caseSensitive:
            val = val.lower()
        return val, valNum

    def onDoSearch( self, searchValue ):
        self.search( searchValue, self._caseSensitive, self._exactMatch )

    def search( self, searchValue, caseSensitive:bool=False, exactMatch:bool=False ):
        if searchValue != self._searchValueOrig or \
                self._caseSensitive != caseSensitive or \
                self._exactMatch != exactMatch:
            # Anwender hat die Suchkriterien geändert, neue Suche beginnen
            self._row = self._col = 0
            self._searchValueOrig = searchValue
            self._caseSensitive = caseSensitive
            self._exactMatch = exactMatch
            self._searchValue, self._searchValueNum = self._makeComparable( searchValue )
        self._searchNextMatch()

    def _searchNextMatch( self ):
        if self._row == 0 and self._col == 0:
            self._searchWidget.setSearchFieldBackgroundColor( "#ffffff" )
        tm = self._tv.model()
        for r in range( self._row, tm.rowCount() ):
            for c in range( self._col, tm.columnCount() ):
                tmval = tm.getValue( r, c )
                if not tmval: continue
                tmval, tmvalNum = self._makeComparable( tmval )
                match = False
                if( self._exactMatch and self._searchValue == tmval) or \
                        (not self._exactMatch and self._searchValue in tmval ):
                    match = True
                if match or (tmvalNum is not None and
                             self._searchValueNum is not None and
                             tmvalNum == self._searchValueNum):
                    self._showMatch( tm.index( r, c ) )
                    self._row, self._col = r, c+1
                    if self._col >= tm.columnCount():
                        self._row += 1
                        self._col = 0
                        if self._row >= tm.rowCount():
                            self._row = 0
                    return
            self._col = 0
        self._row = self._col = 0
        self._searchWidget.setSearchFieldBackgroundColor( "#eb8795" )

    def _showMatch( self, index: QModelIndex ):
        self._tv.selectionModel().select( index, QItemSelectionModel.ClearAndSelect )
        self._tv.scrollTo( index )

#########################################################################################
class FilterTableWidgetFrame( QWidget ):
    """
    Ein Widget, das ein FilterTableWidget enthält und eine erweiterbare Toolbar.
    Auf Wunsch (withEditButtons = True) wird unterhalb der Tabelle eine Buttonleiste angezeigt,
    die einen "Neu"-, "Ändern"- und "Delete"-Button enthält.
    Wird auf einen dieser Buttons gedrückt, wird ein entsprechendes Signal gesendet.
    """
    newItem = Signal()
    editItem = Signal( int )  # row number (index.row of index)
    deleteItems = Signal( list )  # list of ints, each representing a row number (index.row of index)

    def __init__(self, filterTableWidget:FilterTableWidget, withEditButtons=False ):
        QWidget.__init__( self )
        self._ftw = filterTableWidget
        self._layout = QGridLayout()
        self._toolbar = BaseTableViewToolBar()
        self._editBtn = None
        self._newBtn = None
        self._deleteBtn = None
        self._createGui( withEditButtons )

    def _createGui( self, withEditButtons ):
        l = self._layout
        self.setLayout( l )
        l.addWidget( self._toolbar, 0, 0, alignment=QtCore.Qt.AlignTop )
        # l.setContentsMargins( 0, 0, 0, 0 )
        l.setContentsMargins( 2, 0, 2, 2 )
        l.addWidget( self._ftw, 1, 0 )
        if withEditButtons:
            hbox = QHBoxLayout()
            self._newBtn = NewIconButton()
            self._newBtn.clicked.connect( self.newItem.emit )
            self._editBtn = EditIconButton()
            self._editBtn.clicked.connect( self._onEditItem )
            self._deleteBtn = DeleteIconButton()
            self._deleteBtn.clicked.connect( self._onDeleteItems )
            hbox.addWidget( self._newBtn, stretch=0, alignment=Qt.AlignLeft )
            hbox.addWidget( self._editBtn, stretch=0, alignment=Qt.AlignLeft )
            hbox.addWidget( self._deleteBtn, stretch=0, alignment=Qt.AlignLeft )
            self._layout.addLayout( hbox, 2, 0, 1, 1, Qt.AlignLeft )

    def setNewButtonEnabled( self, enabled=True ):
        self._newBtn.setEnabled( enabled )

    def setDeleteButtonEnabled( self, enabled=True ):
        self._deleteBtn.setEnabled( enabled )

    def getPreferredWidth( self ) -> int:
        return self._ftw.getPreferredWidth() + 25

    def getPreferredHeight( self ) -> int:
        return self._ftw.getPreferredHeight() + 25

    def _onEditItem( self ):
        sel_rows = self._ftw.getSelectedRows()
        if len( sel_rows ) > 0:
            self.editItem.emit( sel_rows[0] )

    def _onDeleteItems( self ):
        sel_rows = self._ftw.getSelectedRows()
        if len( sel_rows ) > 0:
            self.deleteItems.emit( sel_rows )

    def getToolBar( self ) -> BaseTableViewToolBar:
        return self._toolbar

    def getFilterTableWidget( self ) -> FilterTableWidget:
        return self._ftw
####################################################################################


def testFilterTableWidget():
    from PySide2.QtWidgets import QApplication
    from PySide2.QtCore import QSize
    def onOk():
        print( "ok" )
    def onCancel():
        print( "cancel" )
    def onYearChanged( year:int ):
        print( "Year changed to ", year )
    def onMonthChanged( monthIdx:int, monthShortName:str, monthLongName:str ):
        print( "Month changed to %d - %s - %s" % (monthIdx, monthShortName, monthLongName) )
    def onMultipleSort():
        tm.sortMultipleColumns( ("nachname", "ort", "groesse") )
        tv.horizontalHeader().setSortIndicatorShown( False )

    app = QApplication()
    dlg = BaseDialogWithButtons( "Test FilterTableWidget", getOkCancelButtonDefinitions( onOk, onCancel ) )
    tv = FilterTableWidget()
    ## Jahre, die in der Jahres-Combo angezeigt werden sollen
    years = list()
    year = datehelper.getCurrentYear()
    for y in range( year, 2019, -1 ):
        years.append( y )
    cbo = YearComboBox( years )
    cbo.year_changed.connect( onYearChanged )
    cbo.setYear( year )
    tv.addToolWidget( cbo )
    cbo = MonthComboBox()
    cbo.month_changed.connect( onMonthChanged )
    cbo.setMonthIdx( 6 ) # Juli
    tv.addToolWidget( cbo )
    btn = BaseButton( "Sort" )
    btn.clicked.connect( onMultipleSort )
    tv.addToolWidget( btn )
    tv.addStandardTableTools( (TableTool.SEARCH, TableTool.PRINT, TableTool.EXPORT) )
    tm = createTestModel()
    tv.setModel( tm )
    tv.setAlternatingRowColors()
    #tv.sortByColumn( 1 )
    w = tv.getPreferredWidth()
    dlg.setMainWidget( tv )
    dlg.resize( QSize( w + 50, 250 ) )
    dlg.exec_()

def testFilterTableWidgetFrame():
    from PySide2.QtWidgets import QApplication
    from PySide2.QtCore import QSize
    def onOk():
        print( "ok" )
    def onCancel():
        print( "cancel" )
    app = QApplication()
    dlg = BaseDialogWithButtons( "Test BaseTableView", getOkCancelButtonDefinitions( onOk, onCancel ) )
    tv = FilterTableWidget()
    tm = createTestModel()
    tv.setModel( tm )
    frame = FilterTableWidgetFrame( tv, withEditButtons=True )
    sw = SearchWidget2()
    frame.getToolBar().addWidget( sw )
    w = tv.getPreferredWidth()
    dlg.setMainWidget( frame )
    dlg.resize( QSize( w + 50, 250 ) )
    dlg.exec_()

#########################################################################################
#           TEST  TEST  TEST   #
def createTestModel2() -> BaseTableModel:
    nachnamen = ("Hinterhuberhapfinger", "Wollemerseroilasse", "alter Adel\nVerdi", "Nemo", "Willibaldessen", "Sagamol")
    vornamen = ("Sepp", "Georg-Hubert-Franz", "Paul", "Werner-Sigismumnd", "Kalle", "Willi", "Ansgaroid" )
    plzn = ("91077", "91077", "77654", "88954", "66538", "91077")
    orte = ("Kleinsteinhausen", "Kleinmain", "Au", "Hausen", "Saarbrücken", "Steinbach")
    strn = ("Apfelweg 2", "Birnenweg 2", "Rebenweg 3", "Hubertusweg 22", "Wellesweilerstr. 56", "Ahornweg 2")
    alter = (67, 65, 54, 49, 60, 41)
    groessen = (180, 170, 179, 185, 161.5, 161.5)
    itemlist = list()
    for n in range( 0, len( nachnamen ) ):
        i = TestItem()
        i.nachname = nachnamen[n]
        i.vorname = vornamen[n]
        i.plz = plzn[n]
        i.ort = orte[n]
        i.str = strn[n]
        i.alter = alter[n]
        i.groesse = groessen[n]
        itemlist.append( i )
    tm = BaseTableModel( itemlist )
    tm.headers = ("Nachname", "Vorname", "PLZ", "Ort", "Straße", "Alter", "Größe")
    return tm


def createTestModel() -> BaseTableModel:
    nachnamen = ("Kendel", "Kendel", "Verhoeven", "von Adler", "Strack-Zimmermann", "Kendel")
    vornamen = ("Martin", "Gudrun", "Paul", "Henriette\nalterAdel", "Marie-Agnes", "Friedi")
    plzn = ("91077", "91077", "77654", "88954", "66538", "91077")
    orte = ("Kleinsendelbach", "Kleinsendelbach", "Niederstetten", "Oberhimpflhausen", "Neunkirchen", "Steinbach")
    strn = ("Birnenweg 2", "Birnenweg 2", "Rebenweg 3", "Hubertusweg 22", "Wellesweilerstr. 56", "Ahornweg 2")
    alter = (67, 65, 54, 49, 60, 41)
    groessen = (180, 170, 179, 185, 161.5, 161.5)
    itemlist = list()
    for n in range( 0, len( nachnamen ) ):
        i = TestItem()
        i.nachname = nachnamen[n]
        i.vorname = vornamen[n]
        i.plz = plzn[n]
        i.ort = orte[n]
        i.str = strn[n]
        i.alter = alter[n]
        i.groesse = groessen[n]
        itemlist.append( i )
    tm = BaseTableModel( itemlist )
    tm.headers = ("Nachname", "Vorname", "PLZ", "Ort", "Straße", "Alter", "Größe")
    return tm


def testMyTableView():
    from PySide2.QtWidgets import QApplication
    from PySide2.QtCore import QSize
    def onOk():
        print( "ok" )
    def onCancel():
        tm = createTestModel2()
        tv.setModel( tm )
    app = QApplication()
    dlg = BaseDialogWithButtons( "Test MyTableView", getOkCancelButtonDefinitions( onOk, onCancel ) )
    tv = FilterTableWidget()
    tm = createTestModel()
    tv.setModel( tm )
    w = tv.getPreferredWidth()
    dlg.setMainWidget( tv )
    dlg.resize( QSize(w+50, 250))
    dlg.exec_()