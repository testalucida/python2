from typing import List

from PySide2.QtCore import QModelIndex, QPoint
from PySide2.QtWidgets import QWidget, QApplication

from base.baseqtderivates import BaseAction, BaseDialogWithButtons, getCloseButtonDefinition
from base.basetablemodel import SumTableModel, BaseTableModel
from base.basetableview import BaseTableView
from base.basetableviewframe import BaseTableViewFrame
from base.printhandler import PrintHandler
from generictable_stuff.okcanceldialog import OkDialog
from v2.extras.ertrag.ertraglogic import ErtragLogic, ErtragTableModel
from v2.icc.icccontroller import IccController
from v2.icc.interfaces import XMasterEinAus


class ErtragController( IccController ):
    def __init__( self ):
        IccController.__init__( self )
        self._view = BaseTableView()
        self._printHandler:PrintHandler = None
        self._logic = ErtragLogic()
        self._jahr = 0
        self._dlg = None

    def createGui( self ) -> QWidget:
        """
        Brauchen wir hier nicht
        :return:
        """
        pass

    def showErtraege( self ):
        if not self._dlg:
            v:BaseTableView = self.createView()
            dlg = OkDialog( "Ertragsübersicht" )
            dlg.addWidget( v, 0 )
            dlg.setOkButtonText( "Schließen" )
            dlg.resize( v.getPreferredWidth()+25, 800 )
            self._dlg = dlg
        # Dialog non-modal öffnen
        self._dlg.show()

    def createView( self ) -> QWidget:
        jahre = self.getJahre() # das neueste (größte) Jahr hat Index 0
        jahr = 0
        if len( jahre ) > 0:
            if len( jahre ) > 1:
                jahr = jahre[1]  # das aktuelle minus 1 - für das liegen die Daten komplett vor
            else:
                jahr = jahre[0]
        self._jahr = jahr
        model:ErtragTableModel = self._logic.getErtragTableModel( jahr )
        v = self._view
        v.setModel( model )
        v.setAlternatingRowColors( True )
        v.setContextMenuCallbacks( self.onProvideContext, self.onSelectedAction )
        frame = BaseTableViewFrame( v )
        frame.setWindowTitle( "Ertragsübersicht für " + str(jahr) )
        tb = frame.getToolBar()
        tb.addYearCombo( jahre, self.onChangeYear )
        tb.setYear( self._jahr )
        tb.addExportAction( "Tabelle nach Calc exportieren", lambda: self.onExport(model) )
        self._printHandler = PrintHandler( v )
        tb.addPrintAction( "Druckvorschau für diese Tabelle öffnen...", self._printHandler.handlePreview )
        return frame

    def onChangeYear( self, newYear:int ):
        tm = self._logic.getErtragTableModel( newYear )
        self._view.setModel( tm )
        self._jahr = newYear

    def onExport( self, tm:BaseTableModel ):
        from base.exporthandler import ExportHandler
        handler = ExportHandler()
        handler.exportToCsv( tm )

    def onProvideContext( self, index:QModelIndex, point:QPoint, selectedIndexes:List[QModelIndex] ) -> List[BaseAction]:
        tm = self._view.model()
        l = list()
        col = index.column()
        x:XMasterEinAus = tm.getElement( selectedIndexes[0].row() )
        if col == tm.colIdxAllgKosten:
            action = BaseAction( "Details...", ident="allg" )
            action.setData( x )
            l.append( action )
        elif col == tm.colIdxRep:
            action = BaseAction( "Details...", ident="rep" )
            action.setData( x )
            l.append( action )
        elif col == tm.colIdxSonstKosten:
            action = BaseAction( "Details...", ident="sonst" )
            action.setData( x )
            l.append( action )
        return l

    def onSelectedAction( self, action:BaseAction ):

        def onClose():
            dlg.accept()

        x:XMasterEinAus = action.data()
        title = ""
        detail_tv = BaseTableView()
        tvframe = BaseTableViewFrame( detail_tv )
        tb = tvframe.getToolBar()
        tb.addExportAction(  "Tabelle nach Calc exportieren", lambda: self.onExport(tm) )
        tm:SumTableModel = None
        if action.ident == "rep":
            tm = self._logic.getReparaturenEinzeln( x.master_name, self._jahr )
            title = "Reparaturen '%s' " % x.master_name + "im Detail"
        elif action.ident == "allg":
            tm = self._logic.getAllgemeineKostenEinzeln( x.master_name, self._jahr )
            title = "Allgemeine Kosten '%s' " % x.master_name + "im Detail"
        elif action.ident == "sonst":
            tm = self._logic.getSonstigeKostenEinzeln( x.master_name, self._jahr )
            title = "Sonstige Kosten '%s' " % x.master_name + "im Detail"
        detail_tv.setModel( tm )
        dlg = BaseDialogWithButtons( title, getCloseButtonDefinition( onClose ) )
        #dlg.setMainWidget( detail_tv )
        dlg.setMainWidget( tvframe )
        dlg.resize( detail_tv.getPreferredWidth()+25, detail_tv.getPreferredHeight() + 50 )
        dlg.exec_()


def test():
    app = QApplication()
    c = ErtragController()
    v = c.createView()
    v.show()
    app.exec_()
