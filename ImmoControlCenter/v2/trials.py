from typing import List, Any

from PySide2.QtCore import Qt, Signal, QModelIndex
from PySide2.QtGui import QBrush
from PySide2.QtWidgets import QMainWindow, QWidget, QAction, QAbstractItemView

import datehelper
from base.baseqtderivates import BaseTabWidget, BaseToolBar, BaseMenuBar, BaseStatusBar, BaseGridLayout, BaseLabel
from base.basetablemodel import BaseTableModel, SumTableModel
from base.basetableview import BaseTableView
from base.basetableviewframe import BaseTableViewFrame
from v2.icc.iccwidgets import IccCheckTableViewFrame
from v2.icc.interfaces import XMtlZahlung
from v2.mtleinaus.mtleinauscontroller import MieteController
# from v2.mtleinaus.mtleinauslogic import MieteLogic, MieteTableModel
from v2.mtleinaus.mtleinauslogic import HausgeldLogic
from v2.mtleinaus.mtleinausview import HausgeldTableView


class IccSignals:
    exportDbToServer = Signal()
    importDbFromServer = Signal()
    editMietobjekt = Signal()
    changeVerwalter = Signal()

    def __init__( self ):
        pass

class IccActions:
    def __init__( self ):
        # self.exportDbToServer = QAction( "Datenbank zum Server exportieren" )
        # self.quitApp = QAction( "Datenbank vom Server importieren" )
        pass # Datenbankexport jetzt automatisch bei Schließen der Anwendung

#############  IccMainMenuBar  ######################
class IccMainMenuBar( BaseMenuBar ):
    def __init__( self, parent=None ):
        BaseMenuBar.__init__( self, parent )
        self._setupMenuBar()

    def _setupMenuBar( self ):
        menu = self.addMenu( "ImmoCenter" )
        menu.addAction( "Datenbank zum Server exportieren" )
        menu.addAction( "Datenbank vom Server importieren" )

##############  IccMainToolBar  ######################
class IccMainToolBar( BaseToolBar ):
    def __init__( self, parent=None ):
        BaseToolBar.__init__( self, parent )
        self._configureGui()

    def _configureGui( self ):
        self.addWidget( BaseLabel("Letzte eingetragene Buchung: ") )

###############  IccMainStatusBar  ###################
class IccMainStatusBar( BaseStatusBar ):
    def __init__( self, parent=None ):
        BaseStatusBar.__init__( self, parent )

############### IccMainWindow2  #####################
class IccMainWindow2( QMainWindow ):
    def __init__( self, parent:QWidget=None, flags=Qt.WindowFlags()  ):
        QMainWindow.__init__( self, parent, flags )
        self._menubar = IccMainMenuBar()
        self._toolbar = IccMainToolBar()
        self._tabs = IccTabWidget()
        self.mieteCheckTableViewFrame = IccCheckTableViewFrame
        self._statusbar = IccMainStatusBar()
        self._layout = BaseGridLayout()
        self.setWindowTitle( "ImmoControlCenter V2" )
        self._configureGui()

    def _configureGui( self ):
        self._configureMenuBar()
        self._configureToolBar()
        self._configureStatusBar()
        self.setLayout( self._layout )
        self._tabs.a
        self.setCentralWidget( self._tabs )

    def _configureMenuBar( self ):
        self.setMenuBar( self._menubar )

    def _configureToolBar( self ):
        self.addToolBar( Qt.TopToolBarArea, self._toolbar )

    def _configureStatusBar( self ):
        self.setStatusBar( self._statusbar )

###############  IccTabWidget  ######################
class IccTabWidget( BaseTabWidget ):
    def __init__(self, parent=None):
        BaseTabWidget.__init__( self, parent )

# ###############  IccCheckTableViewFrame  #############
# class IccCheckTableViewFrame( BaseTableViewFrame ):
#     def __init__( self, tableView:BaseTableView ):
#         BaseTableViewFrame.__init__( self, tableView )

# ###############  MieteCheckTableViewFrame  #############
# class MieteTableViewFrame( IccCheckTableViewFrame ):
#     def __init__( self, tableView:BaseTableView ):
#         IccCheckTableViewFrame.__init__( self, tableView )



##########  TEST  TEST  TEST  TEST  TEST  ##############
def createGui() -> IccMainWindow2:
    win = IccMainWindow2()
    return win

# def onSelected( action:QAction ):
#     print( "selected action: ", str( action ) )
#
# def provideActions( index, point, selectedIndexes ) -> List[QAction]:
#     print( "context menu for column ", index.column(), ", row ", index.row() )
#     l = list()
#     l.append( QAction( "Action 1" ) )
#     l.append( QAction( "Action 2" ) )
#     sep = QAction()
#     sep.setSeparator( True )
#     l.append( sep )
#     l.append( QAction( "Action 3" ) )
#     return l

def onYearChanged( year:int ):
    print( "year changed: ", year )

def onMonthChanged( monthIdx:int, monthLongName:str ):
    print( "month changed: ", monthIdx, ": ", monthLongName )

def test2():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    ctrl = MieteController()
    frame = ctrl.createGui()
    frame.show()
    app.exec_()


def test():
    # def onOkClicked( index ):
    #     if index.column() == tm.getOkColumnIdx():
    #         value = tm.getSollValue( index.row() )
    #         tm.setValue( index.row(), tm.getEditableColumnIdx(), value, writeChangeLog=True )

    from PySide2.QtWidgets import QApplication
    app = QApplication()
    jahr = 2022
    logic = HausgeldLogic()
    hgtm = logic.createHausgeldzahlungenModel( 2022, 9 )
    tv = HausgeldTableView()
    tv.setModel( hgtm )
    tv.show()
    # l:List[XMtlZahlung] = logic.getMietzahlungen( jahr, 8 )
    # tm = MieteTableModel( l, jahr )
    # tm.setEditableMonth( "sep" )
    # tv = MieteTableView()
    # tv.setModel( tm )
    #todo: MieteController instanzieren und contextMenuCallbacks anschließen
    #todo: Reaktion auf ok/nok-Click
    # tv.setContextMenuCallbacks( provideActions, onSelected )
    # tv.okClicked.connect( onOkClicked )
    #tv.show()
    # win = MieteTableViewFrame( tv )
    # ctrl = MieteController( win, logic )
    # tb = win.getToolBar()
    # tb.addYearCombo( (2022, 2021, 2020), onYearChanged )
    # tb.setYear( 2022 )
    # tb.addMonthCombo( onMonthChanged )
    #controller

    #win = createGui()
    # win.show()
    app.exec_()
