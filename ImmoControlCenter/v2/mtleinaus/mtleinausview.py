
##################  MieteTableView  ##############
from abc import abstractmethod
from typing import List, Callable

from PySide2 import QtWidgets
from PySide2.QtCore import Signal, QModelIndex, Qt
from PySide2.QtGui import QDoubleValidator
from PySide2.QtWidgets import QDialog, QGridLayout, QPushButton, QApplication, QWidget, QHBoxLayout

from base.baseqtderivates import BaseEdit, BaseDialog, BaseDialogWithButtons, getOkCancelButtonDefinitions, \
    getCloseButtonDefinition
from v2.einaus.einausview import EinAusTableView, EinAusTableViewFrame, TeilzahlungDialog
from v2.icc.iccwidgets import IccTableView, IccCheckTableViewFrame
from v2.mtleinaus.mtleinauslogic import MieteTableModel, MtlEinAusTableModel


##############   MtlEinAusTableView   #################
class MtlEinAusTableView( IccTableView ):
    okClicked = Signal( QModelIndex )
    nokClicked = Signal( QModelIndex )
    def __init__( self ):
        IccTableView.__init__( self )
        self.setAlternatingRowColors( True )
        self.btvLeftClicked.connect( self.onLeftClicked )
        self._columnsWidth: List[int] = list()

    def setModel( self, model: MtlEinAusTableModel ):
        super().setModel( model, selectRows=False, singleSelection=False )
        if len( self._columnsWidth ) == 0:
            oknoksize = 30
            self.horizontalHeader().setMinimumSectionSize( oknoksize )
            self.setColumnWidth( model.getOkColumnIdx(), oknoksize )
            self.setColumnWidth( model.getNokColumnIdx(), oknoksize )
            for c in range( 0, model.columnCount() ):
                self._columnsWidth.append( self.columnWidth( c ) )
        else:
            for c in range( 0, model.columnCount() ):
                self.setColumnWidth( c, self._columnsWidth[c] )

    def onLeftClicked( self, index: QModelIndex ):
        isOkColumn, isNokColumn = False, False
        if index.column() == self.model().getOkColumnIdx():
            isOkColumn = True
            self.okClicked.emit( index )
        elif index.column() == self.model().getNokColumnIdx():
            isNokColumn = True
            self.nokClicked.emit( index )
        if True in (isOkColumn, isNokColumn):
            self.clearSelection()

##############   MieteTableView   #################
class MieteTableView( MtlEinAusTableView ):
    def __init__( self ):
        MtlEinAusTableView.__init__( self )

###############  MieteTableViewFrame  #############
class MieteTableViewFrame( IccCheckTableViewFrame ):
    def __init__( self, tableView:MieteTableView ):
        IccCheckTableViewFrame.__init__( self, tableView )

##############   HausgeldTableView   #################
class HausgeldTableView( MtlEinAusTableView ):
    def __init__( self ):
        MtlEinAusTableView.__init__( self )

###############  HausgeldTableViewFrame  #############
class HausgeldTableViewFrame( IccCheckTableViewFrame ):
    def __init__( self, tableView:MieteTableView ):
        IccCheckTableViewFrame.__init__( self, tableView )

##############   AbschlagTableView   #################
class AbschlagTableView( MtlEinAusTableView ):
    def __init__( self ):
        MtlEinAusTableView.__init__( self )

###############  AbschlagTableViewFrame  #############
class AbschlagTableViewFrame( IccCheckTableViewFrame ):
    def __init__( self, tableView:AbschlagTableView ):
        IccCheckTableViewFrame.__init__( self, tableView )

###################  TEST   TEST   TEST   #################

def test2():
    # def validation() -> bool:
    #     #return True
    #     return False

    app = QApplication()
    dlg = TeilzahlungDialog( EinAusTableView() )
    if dlg.exec_() == QDialog.Accepted:
        print( "storing modifications")
