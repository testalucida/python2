from numbers import Number
from typing import List, Callable, Tuple
from PySide2.QtCore import QAbstractTableModel, Qt, Signal, QModelIndex, QPoint, QItemSelectionModel, QItemSelection, \
    QSize
from PySide2.QtGui import QMouseEvent, QGuiApplication, QIcon
from PySide2.QtWidgets import QTableView, QAbstractItemView, QAbstractScrollArea, QHeaderView, QApplication, QMenu, \
    QAction, QComboBox

#####################  CellEvent  #################################
from base.baseqtderivates import BaseAction
from base.basetablefunctions import BaseTableFunctions
from base.interfaces import XBase, TestItem
from base.basetablemodel import BaseTableModel


class CellEvent:
    def __init__(self, mouseX:int=-1, mouseY:int=-1, row:int=-1, column:int=-1 ):
        self.mouseX = mouseX
        self.mouseY = mouseY
        self.row = row
        self.column = column

#####################  BaseHeaderView  ####################
class BaseHeaderView( QHeaderView ):
    bhvMouseMove = Signal( QMouseEvent )

    def __init__( self, orientation:Qt.Orientation=Qt.Orientation.Vertical, parent=None ):
        QHeaderView.__init__( self, orientation, parent )
        self.setMouseTracking( True )

    def mouseMoveEvent(self, evt:QMouseEvent):
        self.bhvMouseMove.emit( evt )

#####################  BaseTableView  ####################
class BaseTableView( QTableView ):
    """
    Eine TableView, die eine Liste von XBase-Objekten anzeigt.
    Wird mit der linken Maus in eine Zelle geklickt, wird ein btvLeftClicked-Signal gesendet.
    Wird mit der rechten Maus geklickt (Kontextmenü soll geöffnet werden), werden über eine Callback-Function
    die anzuzeigenden QActions geholt und angezeigt. Die ausgewählte Action wird über eine andere
    Callback-Function zurückgeliefert.
    Die Callback-Functions werden mit setContextMenuCallbacks() angemeldet.
    """
    btvLeftClicked = Signal( QModelIndex )
    btvRightClicked = Signal( QPoint )
    btvDoubleClicked = Signal( QModelIndex )
    # btvCellEnter = Signal( CellEvent )
    # btvCellLeave = Signal( CellEvent )

    def __init__( self, parent=None ):
        QTableView.__init__( self, parent )
        # left mouse click
        self.clicked.connect( self.onLeftClick ) # left click in a tableview cell (not header)
        self.doubleClicked.connect( self.onDoubleClick )
        # right mouse click
        self.setContextMenuPolicy( Qt.CustomContextMenu )
        self.customContextMenuRequested.connect( self.onRightClick )
        self.setMouseTracking( True )
        # self.horizontalHeader().sortIndicatorChanged.connect( self.afterSort )
        # self.btvCellEnter.connect( self._onCellEnter )
        # self.btvCellLeave.connect( self._onCellLeave )
        # self._vheaderView = BaseHeaderView( Qt.Orientation.Vertical )
        # self.setVerticalHeader( self._vheaderView )
        # self._vheaderView.bhvMouseMove.connect( self.onMouseMoveOutside )
        # self._hheaderView = BaseHeaderView( Qt.Orientation.Horizontal )
        # self._hheaderView.bhvMouseMove.connect( self.onMouseMoveOutside )
        # self.setHorizontalHeader( self._hheaderView )  # mit dem CustomHeaderView funktioniert das Sortieren nicht
        self._mouseOverCol = -1
        self._mouseOverRow = -1
        # callback mit der Signatur indexrow:int, indexcolumn:int, point:QPoint.
        # Liefert die QAction-Objekte zurück, die im Kontextmenü angezeigt werden sollen.
        self._contextMenuActionsProvider: Callable = None
        self._contextMenuActionActor: Callable = None
        self._selectedElements: List[XBase] = list()
        self._selectedColumnsMemo = list()
        self.setSortingEnabled( True )
        self.sortByColumn( -1 ) # damit kein SortIndicator angezeigt wird


    def setContextMenuCallbacks( self, provider:Callable, onSelected:Callable ) -> None:
        """
        Registriert zwei callback-functions:
        Die eine, provider, wird von BaseTableView nach einem rechten Mausklick mit relevanten Paramtern
         (siehe param provider) aufgerufen.
        Dieser callback muss eine Liste von QActions zurückgeben, die dann im Kontextmenü angezeigt werden.
        Die andere, onSelected (siehe param onSelected), wird von BaseTableView nach Auswahl
        eines Kontextmenüpunktes aufgerufen.
        :param provider: callback function, die folgende Argumente akzeptieren muss:
                index:QModelIndex, point:QPoint, selectedIndexes
                Zurückgeben muss sie eine List[QAction] oder None
        :param onSelected: callback function, die folgende Argumente akzeptieren muss:
                action:QAction
        :return: None
        """
        self._contextMenuActionsProvider = provider
        self._contextMenuActionActor = onSelected

    def setModel( self, model:BaseTableModel,
                  selectRows:bool=True, singleSelection:bool=True ) -> None:
        super().setModel( model )
        if selectRows:
            self.setSelectionBehavior( QTableView.SelectRows )
        else:
            self.setSelectionBehavior( QTableView.SelectItems )
        if singleSelection:
            self.setSelectionMode( QAbstractItemView.SingleSelection )
        else:
            self.setSelectionMode( QTableView.SelectionMode.ContiguousSelection )
        model.layoutChanged.connect( self.onLayoutChanged )
        model.before_sorting.connect( self.onBeforeSort )
        #model.sorting_finished.connect( self.onSortingFinished )
        model.rowsAddedSignal.connect( self.onRowsAdded )
        self.resizeRowsAndColumns()
        # h = self.getPreferredHeight()
        # w = self.getPreferredWidth()
        # self.resize( QSize(w, h) )

    def onBeforeSort( self ):
        selectionlist = self.selectedIndexes()
        if selectionlist and len(selectionlist) > 0:
            rowIdx = -1
            for idx in selectionlist:
                if rowIdx < 0:
                    rowIdx = idx.row()
                    xbase = self.model().getElement( rowIdx )
                    self._selectedElements.append( xbase )
                    #print( "onBeforeSorting - added to selectionmemo: ", xbase )
                if idx.row() == rowIdx:
                    self._selectedColumnsMemo.append( idx.column() )
        index = self.model().createIndex( -1, -1 )
        self.selectionModel().setCurrentIndex( index, QItemSelectionModel.Select )

    # def onSortingFinished( self ):
    #     self.resizeRowsAndColumns()

    # def clearSelection( self ):
    #     super().clearSelection() # funktioniert nicht, aber trotzdem Aufruf - wer weiß, was da im Hintergrund noch abgeht
    #     self.selectionModel().clear()

    def sortByColumn(self, column:int, order:Qt.SortOrder = Qt.SortOrder.AscendingOrder ):
        self.horizontalHeader().setSortIndicator( column, order )

    def onLayoutChanged( self ):
        if len( self._selectedElements ) > 0:
            xbase:XBase = self._selectedElements[0]
            rowIdx = self.model().getRow( xbase )
            #print( "onLayoutChanged - retrieve selected: ", xbase, " - now on row ", rowIdx )
            currentIndex = None
            for colIdx in self._selectedColumnsMemo:
                index = self.model().createIndex( rowIdx, colIdx )
                if not currentIndex:
                    currentIndex = index
                    self.setCurrentIndex( currentIndex )
                self.selectionModel().select( index, QItemSelectionModel.Select )
            self._selectedElements.clear()
            self._selectedColumnsMemo.clear()
            self.scrollTo( currentIndex )
            #print( "scrolled to index ", currentIndex )
        self.resizeRowsAndColumns()

    def onRowsAdded( self ):
        self.resizeRowsToContents()

    def resizeRowsAndColumns( self ):
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def resizeColumnsToContents(self):
        super().resizeColumnsToContents()
        cols = self.model().columnCount()
        for c in range( 0, cols ):
            if self.columnWidth( c ) > 300:
                self.setColumnWidth( c, 300 )

    def mouseMoveEvent(self, event:QMouseEvent):
        super().mouseMoveEvent( event )
        # p = event.pos()
        # col = self.columnAt( p.x() )
        # row = self.rowAt( p.y() )
        # if row != self._mouseOverRow or col != self._mouseOverCol:
        #     if self._mouseOverRow > -1 and self._mouseOverCol > -1:
        #         self.btvCellLeave.emit( CellEvent( p.x(), p.y(), self._mouseOverRow, self._mouseOverCol ) )
        #     if row > -1 and col > -1:
        #         self.btvCellEnter.emit( CellEvent( p.x(), p.y(), row, col ) )
        # self._mouseOverRow = row
        # self._mouseOverCol = col
        #print( "x = %d, y=%d, row = %d, col = %d" % ( p.x(), p.y(), row, col ) )

    # def _onCellEnter( self, evt:CellEvent ):
    #     print( "onCellEnter: %d, %d" % (evt.row, evt.column ) )

    # def _onCellLeave( self, evt: CellEvent ):
    #     print( "onCellLeave: %d, %d" % (evt.row, evt.column) )

    def onMouseMoveOutside( self, event:QMouseEvent ):
        if self._mouseOverRow > -1 and self._mouseOverCol > -1:
            p = event.pos()
            self.btvCellLeave.emit( CellEvent( p.x(), p.y(), self._mouseOverRow, self._mouseOverCol ) )
            self._mouseOverRow = -1
            self._mouseOverCol = -1

    def onRightClick( self, point:QPoint ):
        #print( "BaseTableView.onRightClick:", point )
        index = self.indexAt( point )
        if not index.isValid(): return
        selectedIndexes = self.selectedIndexes()
        if self._contextMenuActionsProvider:
            actions = self._contextMenuActionsProvider( index, point, selectedIndexes )
            if actions and len( actions ) > 0:
                menu = QMenu()
                for action in actions:
                    menu.addAction( action )
                selectedAction = menu.exec_( self.viewport().mapToGlobal( point ) )
                if selectedAction and self._contextMenuActionActor:
                    self._contextMenuActionActor( selectedAction )
        else:
            actions = self.getContextMenuActions( index, point, selectedIndexes )
            if actions and len( actions ) > 0:
                menu = QMenu()
                for action in actions:
                    menu.addAction( action )
                menu.exec_( self.viewport().mapToGlobal( point ) )

    def getContextMenuActions( self, index:QModelIndex, point:QPoint, selectedIndexes:List[int] ) -> List[BaseAction] or None:
        """
        TableViews, die von BaseTableView abgeleitet sind und bei Rechtsklick ein Kontextmenü zeigen möchten,
        müssen diese Methode überschreiben (oder sie nutzen das alte Verfahren mit setContextMenuCallbacks).
        :param index: Index der Zeile, auf die geklickt wurde
        :param point:
        :param selectedIndexes:
        :return:
        """
        return None

    def onLeftClick( self, index:QModelIndex ):
        # wird aufgerufen, wenn die Maustaste losgelassen wird
        #print( "BaseTableView.onLeftClick: %d,%d" % ( index.row(), index.column() ) )
        self.btvLeftClicked.emit( index )

    def onDoubleClick( self, index:QModelIndex ):
        #print( "GenericTableView.onDoubleClick: %d,%d" % (index.row(), index.column()) )
        self.btvDoubleClicked.emit( index )

    def getPreferredHeight( self ) -> int:
        rowcount = self.model().rowCount()
        h = self.horizontalHeader().height()
        #h = 0
        for row in range( 0, rowcount ):
            h += self.rowHeight( row )
        return h + 25

    def getPreferredWidth( self ) -> int:
        colcount = self.model().columnCount()
        w = 0
        for col in range( 0, colcount ):
            w += self.columnWidth( col )
        return w + 25

    def getSelectedRows( self ) -> List[int]:
        return BaseTableFunctions.getSelectedRows( self )

    def getSelectedIndexes( self ) -> List[QModelIndex]:
        """
        returns an empty list if no item is selected
        :return:
        """
        return self.selectionModel().selectedIndexes()

    def getFirstSelectedRow( self ) -> int:
        rowlist = self.getSelectedRows()
        return rowlist[0] if len( rowlist ) > 0 else -1

    def copySelectionToClipboard( self ) -> None:
        BaseTableFunctions.copySelectionToClipboard( self )

####################################################  T  E  S  T  S  #################################################

def makeTestModel() -> BaseTableModel:
    nachnamen = ("Kendel", "Knabe", "Verhoeven", "Adler", "Strack-Zimmermann")
    vornamen = ("Martin", "Gudrun", "Paul", "Henriette", "Marie-Agnes")
    plzn = ("91077", "91077", "77654", "88954", "66538")
    orte = ("Kleinsendelbach", "Kleinsendelbach", "Niederstetten", "Oberhimpflhausen", "Neunkirchen")
    strn = ("Birnenweg 2", "Birnenweg 2", "Rebenweg 3", "Hubertusweg 22", "Wellesweilerstr. 56")
    alter = ( 67, 65, 54, 49, 60)
    groessen = (180, 170, 179, 185, 161.5)
    itemlist = list()
    for n in range( 0, len(nachnamen) ):
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
    return tm


def actor( action:QAction ):
    print( "selected action: ", str( action ) )

def provideActions( index, point, selectedIndexes ) -> List[QAction]:
    print( "context menu for column ", index.column(), ", row ", index.row() )
    l = list()
    l.append( QAction( "Action 1" ) )
    l.append( QAction( "Action 2" ) )
    sep = QAction()
    sep.setSeparator( True )
    l.append( sep )
    l.append( QAction( "Action 3" ) )
    return l

def prepareTableView() -> BaseTableView:
    tm = makeTestModel()
    tv = BaseTableView()
    tv.setContextMenuCallbacks( provideActions, actor )
    tv.setModel( tm, selectRows=True, singleSelection=False )
    return tv

def test():
    app = QApplication()
    tv = prepareTableView()
    tv.show()
    #tv.setProperty( 'hideSortIndicatorColumn', 1 )
    tv.horizontalHeader().setSortIndicatorShown( False )
    #tv.setSortingEnabled( True )
    app.exec_()

##########################################################################################
##########################################################################################

class TestTableModel( QAbstractTableModel ):
    before_sorting = Signal()
    sorting_finished = Signal()
    def __init__( self ):
        QAbstractTableModel.__init__( self )
        self._data = ( ("theo", 6, "c"), ("abraham was\n the first", 4, "a"), ("sigi", 8, "b") )
        #print( type(self._data ) )
        # r = self._data[0]
        # print( r )

    def rowCount( self, parent: QModelIndex = None ) -> int:
        return len( self._data )

    def columnCount( self, parent: QModelIndex = None ) -> int:
        return len( self._data[0] )

    def getRow( self, rowIndex ):
        return self._data[rowIndex]

    def getRowIndex( self, row:List[Tuple] ):
        for r in range( 0, self.rowCount() ):
            data = self._data[r]
            if data == row:
                return r
        raise Exception( "TestTableModel.getRowIndex(): Row nicht gefunden." )

    def data( self, index: QModelIndex, role: int = None ):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            r, c = index.row(), index.column()
            return self._data[r][c]
        return None

    def sort( self, col, order=Qt.SortOrder.DescendingOrder ):
        from functools import cmp_to_key
        self.before_sorting.emit()
        #print( "col: ", col, " - order: ", order )
        def compare( r1, r2 ):
            i = r1[col]
            k = r2[col]
            if i == k: return 0
            if order == Qt.SortOrder.DescendingOrder:
                if i < k:
                    rc = -1
                else:
                    rc = 1
            elif order == Qt.SortOrder.AscendingOrder:
                if i < k:
                    rc = 1
                else:
                    rc = -1
            #print( "compare: ", i, " with: ", k, " -- rc= ", rc )
            return rc

        if col < 0: return 0
        self._data = sorted( self._data, key=cmp_to_key(compare) )
        self.sorting_finished.emit()
        self.layoutChanged.emit()

class TestTableView( QTableView ):
    def __init__( self ):
        QTableView.__init__( self )
        self._selectionMemo = list() # enthält die *Werte* der ersten selektierten Zeile
        self._selectedColumnsMemo = list() # enthält die Indizes der selektierten Spalten der ersten selektierten Zeile.
        self.setSortingEnabled( True )
        self.sortByColumn( -1 )

    def setModel( self, model ):
        super().setModel( model )
        model.layoutChanged.connect( self.onLayoutChanged )
        model.before_sorting.connect( self.onBeforeSorting )
        model.sorting_finished.connect( self.onSortingFinished )

    def sortByColumn(self, column:int, order:Qt.SortOrder = Qt.SortOrder.AscendingOrder ):
        self.horizontalHeader().setSortIndicator( column, order )

    def onLayoutChanged( self ):
        if self._selectionMemo and len( self._selectionMemo ) > 0:
            row = self._selectionMemo[0]
            rowIdx = self.model().getRowIndex( row )
            #print( "onLayoutChanged - retrieve selected: ", row, " - now on row ", rowIdx )
            currentIndex = None
            for colIdx in self._selectedColumnsMemo:
                index = self.model().createIndex( rowIdx, colIdx )
                if not currentIndex:
                    currentIndex = index
                    self.setCurrentIndex( currentIndex )
                self.selectionModel().select( index, QItemSelectionModel.Select )
            self._selectionMemo.clear()
            self._selectedColumnsMemo.clear()

    def onLayoutChanged___( self ):
        index = self.model().createIndex( 1, 1 )
        self.selectionModel().select( index, QItemSelectionModel.Select )
        self.setCurrentIndex( index )

    def onBeforeSorting( self ):
        selectionlist = self.selectedIndexes()
        if selectionlist and len(selectionlist) > 0:
            rowIdx = -1
            for idx in selectionlist:
                if rowIdx < 0:
                    rowIdx = idx.row()
                    row = self.model().getRow( rowIdx )
                    self._selectionMemo.append( row )
                    #print( "onBeforeSorting - added to selectionmemo: ", row )
                if idx.row() == rowIdx:
                    self._selectedColumnsMemo.append( idx.column() )
        index = self.model().createIndex( -1, -1 )
        self.selectionModel().setCurrentIndex( index, QItemSelectionModel.Select )

    def onSortingFinished( self ):
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

def testSortAndSelect():
    app = QApplication()
    v = TestTableView()
    tm = TestTableModel()
    v.setModel( tm )
    v.show()
    v.setMinimumWidth( 350 )
    app.exec_()


def testSortIndicator():
    app = QApplication()
    v = TestTableView()
    tm = TestTableModel()
    v.setModel( tm )
    v.sortByColumn( 1, Qt.SortOrder.AscendingOrder ) # ordnet "descending" - warum auch immer
    v.resizeRowsToContents()
    v.resizeColumnsToContents()
    v.show()
    v.setMinimumWidth( 300 )
    app.exec_()
