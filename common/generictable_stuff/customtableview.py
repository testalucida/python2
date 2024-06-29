import os
from numbers import Number
from typing import List

from PySide2 import QtWidgets
from PySide2.QtCore import QAbstractTableModel, Qt, Signal, QModelIndex, QPoint
from PySide2.QtGui import QMouseEvent, QGuiApplication
from PySide2.QtWidgets import QDialog, QPushButton, QTableView, QGridLayout, QApplication, QHBoxLayout, \
    QAbstractItemView, QVBoxLayout, QLabel, QWidget, QAbstractScrollArea, QHeaderView, QTextEdit, QAction, QMenu

from imagefactory import ImageFactory

#####################  Cell  #################################
class CellEvent:
    def __init__(self, mouseX:int=-1, mouseY:int=-1, row:int=-1, column:int=-1 ):
        self.mouseX = mouseX
        self.mouseY = mouseY
        self.row = row
        self.column = column

#####################  CustomHeaderView  ####################
class CustomHeaderView( QHeaderView ):
    chvMouseMove = Signal( QMouseEvent )

    def __init__( self, orientation:Qt.Orientation=Qt.Orientation.Vertical, parent=None ):
        QHeaderView.__init__( self, orientation, parent )
        self.setMouseTracking( True )

    def mouseMoveEvent(self, evt:QMouseEvent):
        # super().mouseMoveEvent( evt )
        self.chvMouseMove.emit( evt )

#####################  CustomTableView  ####################
class CustomTableView( QTableView ):
    """
    Mit dem Setzen des Models wird die Sortierbarkeit automatisch aktiviert.
    """
    ctvLeftClicked = Signal( QModelIndex )
    ctvRightClicked = Signal( QPoint )
    ctvDoubleClicked = Signal( QModelIndex )
    ctvCellEnter = Signal( CellEvent )
    ctvCellLeave = Signal( CellEvent )

    def __init__( self, parent=None ):
        QTableView.__init__( self, parent )
        # left mouse click
        self.clicked.connect( self.onLeftClick )
        self.doubleClicked.connect( self.onDoubleClick )
        # right mouse click
        self.setContextMenuPolicy( Qt.CustomContextMenu )
        self.customContextMenuRequested.connect( self.onRightClick )
        self.setMouseTracking( True )
        #self.horizontalHeader().sortIndicatorChanged.connect( self.afterSort )
        # self.ctvCellEnter.connect( self._onCellEnter )
        # self.ctvCellLeave.connect( self._onCellLeave )
        self._vheaderView = CustomHeaderView( Qt.Orientation.Vertical )
        self.setVerticalHeader( self._vheaderView )
        self._vheaderView.chvMouseMove.connect( self.onMouseMoveOutside )
        self._hheaderView = CustomHeaderView( Qt.Orientation.Horizontal )
        self._hheaderView.chvMouseMove.connect( self.onMouseMoveOutside )
        #self.setHorizontalHeader( self._hheaderView )  # mit dem CustomHeaderView funktioniert das Sortieren nicht
        self._mouseOverCol = -1
        self._mouseOverRow = -1

    # def afterSort( self, idx, sortOrder ):
    #     self.resizeColumnsToContents()
    #     self.resizeRowsToContents()
    #     self.model().layoutChanged.emit()

    def setModel( self, model:QAbstractTableModel, selectRows:bool=True, singleSelection:bool=True  ) -> None:
        super().setModel( model )
        self.setSizeAdjustPolicy( QAbstractScrollArea.AdjustToContents )
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        if selectRows:
            self.setSelectionBehavior( QTableView.SelectRows )
        if singleSelection:
            self.setSelectionMode( QAbstractItemView.SingleSelection )
        self.setSortingEnabled( True )
        model.layoutChanged.emit()

    def mouseMoveEvent(self, event:QMouseEvent):
        p = event.pos()
        col = self.columnAt( p.x() )
        row = self.rowAt( p.y() )
        if row != self._mouseOverRow or col != self._mouseOverCol:
            if self._mouseOverRow > -1 and self._mouseOverCol > -1:
                self.ctvCellLeave.emit( CellEvent( p.x(), p.y(), self._mouseOverRow, self._mouseOverCol ) )
            if row > -1 and col > -1:
                self.ctvCellEnter.emit( CellEvent( p.x(), p.y(), row, col ) )
        self._mouseOverRow = row
        self._mouseOverCol = col
        #print( "x = %d, y=%d, row = %d, col = %d" % ( p.x(), p.y(), row, col ) )

    # def _onCellEnter( self, evt:CellEvent ):
    #     print( "onCellEnter: %d, %d" % (evt.row, evt.column ) )

    # def _onCellLeave( self, evt: CellEvent ):
    #     print( "onCellLeave: %d, %d" % (evt.row, evt.column) )

    def onMouseMoveOutside( self, event:QMouseEvent ):
        if self._mouseOverRow > -1 and self._mouseOverCol > -1:
            p = event.pos()
            self.ctvCellLeave.emit( CellEvent( p.x(), p.y(), self._mouseOverRow, self._mouseOverCol ) )
            self._mouseOverRow = -1
            self._mouseOverCol = -1

    def onRightClick( self, point:QPoint ):
        #selected_indexes = self.selectedIndexes()
        #print( "GenericTableView.onRightClick:", point )
        self.ctvRightClicked.emit( point )

    def onLeftClick( self, index:QModelIndex ):
        #print( "GenericTableView.onLeftClick: %d,%d" % ( index.row(), index.column() ) )
        self.ctvLeftClicked.emit( index )

    def onDoubleClick( self, index:QModelIndex ):
        #print( "GenericTableView.onDoubleClick: %d,%d" % (index.row(), index.column()) )
        self.ctvDoubleClicked.emit( index )

    def getSelectedRows( self ) -> List[int]:
        sm = self.selectionModel()
        indexes:List[QModelIndex] = sm.selectedRows()  ## Achtung missverständlicher Methodenname
        l = list( indexes )
        print( indexes[0].row() )
        rows = [i.row() for i in l]
        return rows

    def getSelectedIndexes( self ) -> List[QModelIndex]:
        """
        returns an empty list if no item is selected
        :return:
        """
        return self.selectionModel().selectedIndexes()

    def getFirstSelectedRow( self ) -> int:
        rowlist = self.getSelectedRows()
        return rowlist[0] if len( rowlist ) > 0 else -1

#####################  TableViewContextMenuHandler  #########
class TableViewContextMenuHandler:
    def __init__( self, tv: CustomTableView ):
        tv.setMouseTracking( True )
        tv.setContextMenuPolicy( Qt.CustomContextMenu )
        tv.customContextMenuRequested.connect( self.onRightClick )
        #tv.setCopyCallback( self._onCopy )  # wenn der User Ctrl+c drückt
        self._tv = tv
        self._actionList:List[List] = list() #Liste, die eine Liste mit Paaren action / callback enthält.
        self._actionList.append( ( QAction( "Kopiere" ), self._onCopy) ) # für Kontextmenü

    def addAction( self, action:QAction, callback ):
        self._actionList.append( ( action, callback ) )

    def onRightClick( self, point: QPoint ):
        index = self._tv.indexAt( point )
        row = index.row()
        if row < 0 or index.column() < 0: return  # nicht auf eine  Zeile geklickt
        selectedIndexes = self._tv.selectedIndexes()
        if selectedIndexes is None or len( selectedIndexes ) < 1: return
        menu = QMenu( self._tv )
        for pair in self._actionList:
            menu.addAction( pair[0] )
        action = menu.exec_( self._tv.viewport().mapToGlobal( point ) )
        if action:
            sel = [pair[1] for pair in self._actionList if pair[0] == action]
            sel[0]( action, point )

    def _onCopy( self, action:QAction, point:QPoint ):
        values:str = ""
        indexes = self._tv.selectedIndexes()
        row = -1
        for idx in indexes:
            if row == -1: row = idx.row()
            if row != idx.row():
                values += "\n"
                row = idx.row()
            elif len( values ) > 0:
                values += "\t"
            val = self._tv.model().data( idx, Qt.DisplayRole )
            val = "" if not val else val
            if isinstance( val, Number ):
                values += str( val )
            else:
                values += val
            #print( idx.row(), "/", idx.column(), ": ", val )
        #print( "valuestring: ",  values )
        clipboard = QGuiApplication.clipboard()
        clipboard.setText( values )

###################  EditableTableViewWidget  #########################
class EditableTableViewWidget( QWidget ):
    """
    Ein Widget, das im oberen Bereich ein CustomTableView enthält und darunter
    3 Buttons, mit denen man ein Item neu anlegen oder ein in der Tabelle ausgewähltes Item
    bearbeiten oder löschen kann.
    """
    createItem = Signal()
    editItem = Signal( QModelIndex )
    deleteItem = Signal( QModelIndex )

    def __init__( self, model:QAbstractTableModel=None, isEditable:bool=False, parent=None ):
        QWidget.__init__( self, parent )
        self._isEditable = isEditable
        self._layout = QGridLayout()
        if isEditable:
            self._newButton = QPushButton()
            icon = ImageFactory.inst().getPlusIcon()
            self._newButton.setIcon( icon )
            self._newButton.setToolTip( "Neuen Tabelleneintrag anlegen" )

            self._editButton = QPushButton()
            icon = ImageFactory.inst().getEditIcon()
            self._editButton.setIcon( icon )
            self._editButton.setToolTip( "Ausgewählten Tabelleneintrag bearbeiten" )

            self._deleteButton = QPushButton()
            icon = ImageFactory.inst().getDeleteIcon()
            self._deleteButton.setIcon( icon )
            self._deleteButton.setToolTip( "Ausgewählten Tabelleneintrag löschen" )

        self._tv = CustomTableView()
        self._createGui()
        if model:
            self.setTableModel( model )

    def _createGui( self ):
        if self._isEditable:
            self._createEditButtons()

        self._tv.horizontalHeader().setStretchLastSection( True )
        self._layout.addWidget( self._tv, 1, 0)
        self.setLayout( self._layout )

    def _createEditButtons( self ):
        self._newButton.clicked.connect( self._onNew )
        self._editButton.clicked.connect( self._onEdit )
        self._deleteButton.clicked.connect( self._onDelete )
        hbox = QHBoxLayout()
        hbox.addWidget( self._newButton )
        hbox.addWidget( self._editButton )
        hbox.addWidget( self._deleteButton )
        self._layout.addLayout( hbox, 2, 0, alignment=Qt.AlignLeft )

    def setTableModel( self, model:QAbstractTableModel,  selectRows:bool=True, singleSelection:bool=True  ):
        self._tv.setModel( model, selectRows, singleSelection )
        if self._isEditable:
            self._newButton.setFocus()

    def getTableModel( self ):
        return self._tv.model()

    def getTableView( self ) -> CustomTableView:
        return self._tv

    def _onNew( self ):
        self.createItem.emit()

    def _onEdit( self ):
        indexlist = self.getSelectedIndexes()
        if len( indexlist ) == 0:
            raise Exception( "GenericTableViewDialog: no item selected to edit" )
        self.editItem.emit( indexlist[0] )

    def _onDelete( self ):
        indexlist = self.getSelectedIndexes()
        if len( indexlist ) == 0:
            raise Exception( "GenericTableViewDialog: no item selected to delete" )
        self.deleteItem.emit( indexlist[0] )

    def getSelectedIndexes( self ) -> List[QModelIndex]:
        """
        returns an empty list if no item is selected
        :return:
        """
        sm = self._tv.selectionModel()
        if sm:
            return sm.selectedIndexes()
        return list()

    def getSelectedRows( self ) -> List[int]:
        indexes = self.getSelectedIndexes()
        l = list()
        for i in indexes:
            l.append( i.row() )
        return l

    def getFirstSelectedRow( self ) -> int:
        rowlist = self.getSelectedRows()
        return rowlist[0] if len( rowlist ) > 0 else -1

###################  GenericTableViewDialog  ##############################
class GenericTableViewDialog( QDialog ):
    createItem = Signal()
    editItem = Signal( QModelIndex )
    deleteItem = Signal( QModelIndex )
    # okPressed = Signal()
    # cancelled = Signal()

    def __init__( self, model:QAbstractTableModel=None, isEditable:bool=False, parent=None ):
        QDialog.__init__( self, parent )
        self._isEditable = isEditable
        self._layout = QGridLayout( self )
        #self._imagePath =
        self._okButton = QPushButton( "OK" )
        self._cancelButton = QPushButton( "Abbrechen" )
        if isEditable:
            self._newButton = QPushButton()
            icon = ImageFactory.inst().getPlusIcon()
            self._newButton.setIcon( icon )
            self._newButton.setToolTip( "Neuen Tabelleneintrag anlegen" )

            self._editButton = QPushButton()
            icon = ImageFactory.inst().getEditIcon()
            self._editButton.setIcon( icon )
            self._editButton.setToolTip( "Ausgewählten Tabelleneintrag bearbeiten" )

            self._deleteButton = QPushButton()
            icon = ImageFactory.inst().getDeleteIcon()
            self._deleteButton.setIcon( icon )
            self._deleteButton.setToolTip( "Ausgewählten Tabelleneintrag löschen" )

        self._tv = CustomTableView( self )
        self._createGui()
        self.setModal( True )
        if model:
            self.setTableModel( model )

    def _createGui( self ):
        if self._isEditable:
            self._createEditButtons()
        self._okButton.clicked.connect( self._onOk )
        self._cancelButton.clicked.connect( self._onCancel )
        hbox = QHBoxLayout()
        hbox.addWidget( self._okButton )
        hbox.addWidget( self._cancelButton )

        self._tv.horizontalHeader().setStretchLastSection( True )
        self._layout.addWidget( self._tv, 1, 0)
        self._layout.addLayout( hbox, 3, 0, alignment=Qt.AlignLeft )
        self.setLayout( self._layout )

    def _createEditButtons( self ):
        self._newButton.clicked.connect( self._onNew )
        self._editButton.clicked.connect( self._onEdit )
        self._deleteButton.clicked.connect( self._onDelete )
        hbox = QHBoxLayout()
        hbox.addWidget( self._newButton )
        hbox.addWidget( self._editButton )
        hbox.addWidget( self._deleteButton )
        self._layout.addLayout( hbox, 2, 0, alignment=Qt.AlignLeft )

    def setCancelButtonVisible( self, visible:bool=True ):
        self._cancelButton.setVisible( False )

    def setOkButtonText( self, text:str ):
        self._okButton.setText( text )

    def setTableModel( self, model:QAbstractTableModel, selectRows:bool=True, singleSelection:bool=True ):
        self._tv.setModel( model )
        # self._tv.setSizeAdjustPolicy( QtWidgets.QAbstractScrollArea.AdjustToContents )
        # self._tv.resizeColumnsToContents()
        self._tv.setSelectionBehavior( QTableView.SelectRows )
        self._tv.setSelectionMode( QAbstractItemView.SingleSelection )
        if self._isEditable:
            self._newButton.setFocus()
        else:
            self._okButton.setFocus()

    def _onNew( self ):
        self.createItem.emit()

    def _onEdit( self ):
        indexlist = self._tv.getSelectedIndexes()
        if len( indexlist ) == 0:
            raise Exception( "GenericTableViewDialog: no item selected to edit" )
        self.editItem.emit( indexlist[0] )

    def _onDelete( self ):
        indexlist = self._tv.getSelectedIndexes()
        if len( indexlist ) == 0:
            raise Exception( "GenericTableViewDialog: no item selected to delete" )
        self.deleteItem.emit( indexlist[0] )

    def _onOk( self ):
        #self.okPressed.emit()
        self.accept()

    def _onCancel( self ):
        #self.cancelled.emit()
        self.reject()

    def getTableView( self ) -> CustomTableView:
        return self._tv

####################  ZoomView  #######################################
class ZoomView( QDialog ):
    def __init__( self, text:str, parent=None ):
        QDialog.__init__( self, parent )
        self.setWindowFlags( Qt.FramelessWindowHint )
        self.layout = QHBoxLayout()
        self.zoom = QTextEdit()
        self.layout.addWidget( self.zoom )
        self.setLayout( self.layout )
        self.zoom.setText( text )

#######################################################################
def doEdit( idx:QModelIndex ):
    print( "Edit %d/%d" % (idx.row(), idx.column() ) )

def test():
    def onCellEnter( evt:CellEvent ):
        m = tv.model()
        idx = m.index( evt.row, evt.column )
        txt = m.data( idx, Qt.DisplayRole )
        print( "onCellEnter. Text = %s" % ( txt ) )
        z = ZoomView( txt )
        #z.setModal( False )
        #z.setGeometry( 1200, 100, 400, 100 )
        z.exec_()

    class TestModel( QAbstractTableModel ):
        def __init__( self ):
            QAbstractTableModel.__init__( self )
            self._rows = [("00", "01", "02"),
                          ("10", "11", "12"),
                          ("20", "21", "22"),
                          ("30", "31", "32")]

        def rowCount( self, parent=None ):
            return 4

        def columnCount( self, parent=None ):
            return 3

        def data( self, index, role=None ):
            if not index.isValid():
                return None
            if role == Qt.DisplayRole:
                return self._rows[index.row()][index.column()]
            return None

        def headerData( self, col, orientation, role=None ):
            if orientation == Qt.Horizontal:
                if role == Qt.DisplayRole:
                    return "Spalte %d" % col
                if role == Qt.BackgroundRole:
                    pass
                    # if self.headerBrush:
                    #     return self.headerBrush
            return None

    app = QApplication()
    #os.chdir( "" )
    tm = TestModel()
    # dlg = GenericTableViewDialog( isEditable=True )
    # dlg.setWindowTitle( "testdialog" )
    # dlg.setTableModel( tm )
    # dlg.editItem.connect( doEdit )
    # #dlg.setCancelButtonVisible( False )
    # dlg.setOkButtonText( "Speichern" )
    # dlg.show()

    v = EditableTableViewWidget( tm, isEditable=True )
    tv = v.getTableView()
    #tv.ctvCellEnter.connect( onCellEnter )
    v.show()
    v.getSelectedRows()
    app.exec_()


if __name__ == "__main__":
    test()