from typing import Any, List

from PySide2.QtCore import Signal, QModelIndex
from PySide2.QtGui import QFont, Qt, QIcon
from PySide2.QtWidgets import QTableView, QGridLayout, QPushButton, QComboBox, QApplication, QHBoxLayout

from generictable_stuff.customtableview import EditableTableViewWidget, CustomTableView
from v2.geschaeftsreise.geschaeftsreisetablemodel import GeschaeftsreiseTableModel
from v2.icc.iccwidgets import IccTableView
from v2.icc.interfaces import XGeschaeftsreise


class GeschaeftsreisenView( IccTableView ):
    """
    Eine View, die aus einer Toolbar, einer TableView und einer Button-Leiste zum Editieren besteht.
    """
    #save = Signal()
    yearChanged = Signal( int )
    createItem = Signal()
    editItem = Signal( XGeschaeftsreise )
    deleteItem = Signal( XGeschaeftsreise )
    def __init__( self, geschaeftsreisenTableModel:GeschaeftsreiseTableModel=None ):
        IccTableView.__init__(self )
        self._layout = QGridLayout()
        self.setLayout( self._layout )
        # self._btnSave = QPushButton()
        self._cboJahr = QComboBox()
        self._etv = EditableTableViewWidget( model=None, isEditable=True)
        if geschaeftsreisenTableModel:
            self.setModel( geschaeftsreisenTableModel )
        self._createGui()

    def setJahre( self, jahre:List[int] ):
        for j in jahre:
            self._cboJahr.addItem( str( j ) )

    def setJahr( self, jahr:int ):
        self._cboJahr.setCurrentText( ( str( jahr ) ) )

    def getJahr( self ) -> int:
        return int( self._cboJahr.currentText() )

    def _createGui( self ):
        self._createToolBar( 0 )
        ctv:CustomTableView = self._etv.getTableView()
        ctv.setSortingEnabled( True )
        ctv.setAlternatingRowColors( True )
        self._etv.createItem.connect( self.onCreate )
        self._etv.editItem.connect( self.onEdit )
        self._etv.deleteItem.connect( self.onDelete )
        self._layout.addWidget( self._etv, 1, 0 )

    def _createToolBar( self, r:int=0 ):
        lay = QHBoxLayout()
        self._layout.addLayout( lay, r, 0, alignment=Qt.AlignLeft | Qt.AlignTop )
        self._cboJahr.currentIndexChanged.connect( self._onYearChanged )
        self._cboJahr.setFont( QFont( "Arial", 14, weight=QFont.Bold ) )
        self._cboJahr.setToolTip( "Die angezeigten Dienstreisen fanden in dem hier eingestellten Jahr statt." )
        lay.addWidget( self._cboJahr )
        # self._btnSave.clicked.connect( self.save.emit )
        # self._btnSave.setIcon( QIcon( ICON_DIR + "save.png" ) )
        # self._btnSave.setToolTip( "Änderungen an Geschäftsreisen speichern" )
        # lay.addWidget( self._btnSave )

    def _onYearChanged( self, arg ):
        self.yearChanged.emit( int( self._cboJahr.currentText() ) )

    def getPreferredWidth( self ) -> int:
        ctv = self.getTableView()
        w = 0
        for c in range( ctv.horizontalHeader().count() ):
            w += (ctv.columnWidth( c ) + 2)
        return w

    def getModel( self ) -> Any:
        return self._etv.getTableModel()

    def setModel( self, model: GeschaeftsreiseTableModel ) -> None:
        self._etv.setTableModel( model )
        #model.sortingFinished.connect( self.afterSort )
        model.setSortable( True )
        ## mehrzeilige Texte auch nach dem Sortieren richtig anzeigen:
        model.layoutChanged.connect( self.getTableView().resizeRowsToContents() )

    def afterSort( self ):
        self._etv.getTableView().resizeColumnsToContents()
        self._etv.getTableView().resizeRowsToContents()

    def addJahr( self, jahr: int ) -> None:
        pass

    def getTableView( self ) -> QTableView:
        return self._etv.getTableView()

    def onCreate( self ):
        self.createItem.emit()

    def onEdit( self, index:QModelIndex ):
        xgeschaeftsreise = self._etv.getTableModel().getElement( index.row() )
        self.editItem.emit( xgeschaeftsreise )

    def onDelete( self, index:QModelIndex ):
        xgeschaeftsreise = self._etv.getTableModel().getElement( index.row() )
        self.deleteItem.emit( xgeschaeftsreise )

def jahrChanged( arg ):
    print( "Jahr geändert: ", arg )

def save():
    print( "Speichern" )

def test():
    app = QApplication()
    v = GeschaeftsreisenView()
    v.yearChanged.connect( jahrChanged )
    #v.save.connect( save )
    v.setJahre( (2021, 2022) )
    v.setJahr( 2021 )
    v.show()
    app.exec_()

if __name__ == "__main__":
    test()