from typing import Dict, List, Any

from PySide2.QtCore import QModelIndex, QPoint
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QAction

import datehelper
from base.baseqtderivates import BaseAction, BaseDialogWithButtons, getCloseButtonDefinition
from base.basetablemodel import SumTableModel
from base.printhandler import PrintHandler

#######################  XMasterEinAus  #############################






#######################  EinAusData  #############################

###############################################################################
from v2.extras.ertrag.ertragdata import ErtragData
from v2.extras.ertrag.ertraglogic import ErtragLogic
from v2.icc.interfaces import XMasterEinAus


def test2():
    data = ErtragData()
    # reps = data.getReparaturenEinzeln( "SB_Kaiser", 2021 )
    # print( reps )


def test():
    from PySide2.QtWidgets import QApplication
    from base.basetableview import BaseTableView
    from base.basetableviewframe import BaseTableViewFrame
    #eadata = EinAusData()
    #netto = eadata.getNettomieteAktuell( 17 )
    # su = eadata.getSummeEinzahlungen( 17, 2021 )
    # print( "Ein: ", su )
    # su = eadata.getSummeAuszahlungen( 17, 'r', 2021 )
    # print( "Aus r: ", su )
    # su = eadata.getSummeHausgeld( 17, 2021 )
    # print( "Aus r: ", su )
    # su = eadata.getSummeSonderumlagen( 17, 2021 )
    # print( "Sonder: ", su )
    def onChangeYear( newYear:int ):
        print( "year changed to ", newYear )
        tm = ealogic.getErtragTableModel( newYear )
        tv.setModel( tm )

    def onExport():
        print( "onExport")

    def showDetails():
        print( "showDetails" )

    def onReparaturDetail( arg ) :
        print( arg )

    def onProvideContext( index:QModelIndex, point:QPoint, selectedIndexes:List[QModelIndex] ) -> List[BaseAction]:
        l = list()
        col = index.column()
        model = tv.model()
        x:XMasterEinAus = model.getElement( selectedIndexes[0].row() )
        if col == tm.colIdxAllgKosten:
            action = BaseAction( "Details...", ident="allg" )
            action.setData( x )
            l.append( action )
        elif col == tm.colIdxRep:
            action = BaseAction( "Details...", ident="rep" )
            action.setData( x )
            #action.triggered.connect( onReparaturDetail )
            l.append( action )
        elif col == tm.colIdxSonstKosten:
            action = BaseAction( "Details...", ident="sonst" )
            action.setData( x )
            l.append( action )
        return l

    def onSelectedAction( action:BaseAction ):
        def onClose():
            dlg.accept()

        x:XMasterEinAus = action.data()
        title = ""
        detail_tv = BaseTableView()
        tm:SumTableModel = None
        if action.ident == "rep":
            tm = ealogic.getReparaturenEinzeln( x.master_name, jahr )
            title = "Reparaturen '%s' " % x.master_name + "im Detail"
        elif action.ident == "allg":
            tm = ealogic.getAllgemeineKostenEinzeln( x.master_name, jahr )
            title = "Allgemeine Kosten '%s' " % x.master_name + "im Detail"
        elif action.ident == "sonst":
            tm = ealogic.getSonstigeKostenEinzeln( x.master_name, jahr )
            title = "Sonstige Kosten '%s' " % x.master_name + "im Detail"
        detail_tv.setModel( tm )
        dlg = BaseDialogWithButtons( title, getCloseButtonDefinition( onClose ) )
        dlg.setMainWidget( detail_tv )
        dlg.exec_()


    jahr = 2022
    ealogic = ErtragLogic()
    tm = ealogic.getErtragTableModel( jahr )
    app = QApplication()
    tv = BaseTableView()
    #tv.getContextMenuActions = getContextMenuActions
    # tv.setModel( tm )
    # tv.setAlternatingRowColors( True )
    # tv.setContextMenuCallbacks( onProvideContext, onSelectedAction )
    frame = BaseTableViewFrame( tv )
    frame.setWindowTitle( "Ertragsübersicht" )
    tb = frame.getToolBar()
    tb.addYearCombo( (jahr,), onChangeYear )
    tb.setYear( jahr )
    tb.addExportAction( "Tabelle nach Calc exportieren", onExport )
    ph = PrintHandler( tv )
    tb.addPrintAction( "Druckvorschau für diese Tabelle öffnen...", ph.handlePreview )
    tv.setModel( tm )
    tv.setAlternatingRowColors( True )
    tv.setContextMenuCallbacks( onProvideContext, onSelectedAction )
    frame.show()
    app.exec_()
