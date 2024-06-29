from typing import List

from PySide2.QtCore import QModelIndex, QPoint

import datehelper
from base.baseqtderivates import YearComboBox, BaseAction, BaseDialogWithButtons, getCloseButtonDefinition, Separator
from base.basetablemodel import SumTableModel
from base.basetableview import BaseTableView
from base.basetableviewframe import BaseTableViewFrame
from base.messagebox import InfoBox
from v2.anlagev.anlagevlogic import AnlageVLogic
from v2.anlagev.anlagevtablemodel import AnlageVTableModel, XAnlageV
from v2.anlagev.anlagevview import AnlageVView, AnlageVTabs, AnlageVDialog
from v2.icc.icccontroller import IccController


class AnlageVController( IccController ):
    def __init__( self ):
        IccController.__init__( self )
        self._avTabs: AnlageVTabs = None
        self._avDlg: AnlageVDialog = None
        self._vj = 0
        self._avlogic:AnlageVLogic = None

    def createGui( self ) -> AnlageVDialog:
        jahre = AnlageVLogic.getAvailableVeranlagungsjahre()
        vj = AnlageVLogic.getDefaultVeranlagungsjahr()
        self._avTabs = AnlageVTabs( vj )
        self._avlogic = AnlageVLogic( vj )
        self._vj = vj
        tmlist = self._avlogic.getAnlageVTableModels()
        for tm in tmlist:
            v = AnlageVView()
            v.addAndSetVeranlagungsjahre( jahre, vj )
            v.setModel( tm )
            tv = v.getAnlageVTableView()
            tv.setContextMenuCallbacks( self.provideContextMenu, self.onContextMenuItemSelected )
            v.year_changed.connect( self.onYearChanged )
            self._avTabs.addAnlageV( v )
        self._avDlg = AnlageVDialog( self._avTabs )
        self._avDlg.setPreferredSize()
        return self._avDlg

    def showAnlagenV( self ):
        if not self._avDlg:
            self.createGui()
        self._avDlg.show()

    def onYearChanged( self, master_name:str, newYear:int ):
        #print( master_name, newYear )
        avview = self._avTabs.getAnlageVView( master_name )
        self._avlogic = AnlageVLogic( newYear )
        tm = self._avlogic.getAnlageVTableModel( master_name )
        avview.setModel( tm )
        self._vj = newYear

    def provideContextMenu( self, index: QModelIndex, point: QPoint, selectedIndexes ) -> List[BaseAction]:
        actionlist = []
        action = BaseAction( "Erhaltungsaufwendungen voll abziehbar...", callback=self.onVollAbziehbareAufwaende )
        actionlist.append( action )
        action = BaseAction( "Erhaltungsaufwendungen, zu verteilen...", callback=self.onVerteilteAufwaende )
        actionlist.append( action )
        actionlist.append( Separator() )
        action = BaseAction( "Allgemeine Hauskosten...", callback=self.onAllgemeineAufwaende )
        actionlist.append( action )
        actionlist.append( Separator() )
        action = BaseAction( "Sonstige Kosten...", callback=self.onSonstigeDetail )
        actionlist.append( action )
        return actionlist

    def onContextMenuItemSelected( self, action: BaseAction ):
        currTm: AnlageVTableModel = self.getCurrentAnlageVTableModel()
        master_name = currTm.getMasterName()
        action.callback( currTm, master_name )

    def onVollAbziehbareAufwaende( self, tm:AnlageVTableModel, master_name:str ):
        # currTm:AnlageVTableModel = self.getCurrentAnlageVTableModel()
        # master_name = currTm.getMasterName()
        tm:SumTableModel = self._avlogic.getReparaturenEinzeln( master_name )
        if not tm:
            self._showNoData( master_name, "Erhaltungsaufwand, voll abziehbar" )
            return
        self._showDetailsView( tm, "Voll abziehbare Kosten im Jahr %d für Masterobjekt '%s'" % (self._vj, master_name) )

    def onVerteilteAufwaende( self, tm:AnlageVTableModel, master_name:str  ):
        tm:SumTableModel = self._avlogic.getVerteilteAufwaendeEinzeln( master_name )
        if not tm:
            self._showNoData( master_name, "Erhaltungsaufwand, zu verteilen" )
            return
        self._showDetailsView( tm, "Verteilte Erhaltungsaufwände im Jahr %d für Masterobjekt '%s'"
                               % (self._vj, master_name) )

    def onAllgemeineAufwaende( self, tm:AnlageVTableModel, master_name:str  ):
        tm:SumTableModel = self._avlogic.getAllgemeineHauskostenEinzeln( master_name )
        if not tm:
            self._showNoData( master_name, "Allgemeine Hauskosten" )
            return
        self._showDetailsView( tm, "Allgemeine Hauskosten im Jahr %d für Masterobjekt '%s'" % (self._vj, master_name) )

    def onSonstigeDetail( self, tm:AnlageVTableModel, master_name:str  ):
        tm:SumTableModel = self._avlogic.getSonstigeEinzeln( master_name )
        if not tm:
            self._showNoData( master_name, "Sonstige Kosten" )
            return
        self._showDetailsView( tm, "Sonstige Kosten im Jahr %d für Masterobjekt '%s'" % (self._vj, master_name) )

    def getCurrentAnlageVTableModel( self ) -> AnlageVTableModel:
        avView = self._avTabs.getCurrentAnlageVView()
        return avView.getAnlageVTableModel()

    def _showNoData( self, master_name:str, unterabschnitt:str ):
        box = InfoBox( "'%s': Keine Details vorhanden" % master_name,
                       "Im Unterabschnitt \n'%s'\nsind im Vj %d keine Zahlungen vorhanden."
                       % (unterabschnitt, self._vj) )
        box.exec_()

    @staticmethod
    def _showDetailsView( tm:SumTableModel, title:str ):
        def onClose():
            dlg.accept()
        def onExport( tm: SumTableModel ):
            from base.exporthandler import ExportHandler
            handler = ExportHandler()
            handler.exportToCsv( tm )
        detail_tv = BaseTableView()
        detail_tv.setModel( tm, selectRows=True, singleSelection=False )
        tvframe = BaseTableViewFrame( detail_tv )
        tb = tvframe.getToolBar()
        tb.addExportAction( "Tabelle nach Calc exportieren", lambda: onExport( tm ) )
        dlg = BaseDialogWithButtons( title, getCloseButtonDefinition( onClose ) )
        dlg.setMainWidget( tvframe )
        dlg.resize( detail_tv.getPreferredWidth() + 25, detail_tv.getPreferredHeight() + 90 )
        dlg.show()

##################################################
def test2():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    ctrl = AnlageVController()
    ctrl.showAnlagenV()
    app.exec_()

def test():
    from PySide2.QtWidgets import QApplication
    from v2.anlagev.anlagevlogic import AnlageVLogic
    app = QApplication()
    avTabs = AnlageVTabs()
    jahre = AnlageVLogic.getAvailableVeranlagungsjahre()
    vj = AnlageVLogic.getDefaultVeranlagungsjahr()
    log = AnlageVLogic( vj )
    tmlist = log.getAnlageVTableModels()
    for tm in tmlist:
        v = AnlageVView()
        v.addAndSetVeranlagungsjahre( jahre, vj )
        v.setModel( tm )
        avTabs.addAnlageV( v )
    avTabs.setPreferredSize()
    avTabs.show()
    app.exec_()