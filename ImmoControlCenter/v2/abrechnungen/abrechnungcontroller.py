from typing import List

from PySide2.QtCore import QSize
from PySide2.QtWidgets import QMenu

import datehelper
from base.baseqtderivates import BaseAction, Separator
from base.basetablefunctions import BaseTableFunctions
from base.dynamicattributeui import DynamicAttributeDialog
from base.messagebox import WarningBox, ErrorBox, InfoBox
from v2.abrechnungen.abrechnungdialogcontroller import AbrechnungDialogController
from v2.abrechnungen.abrechnungenview import HGAbrechnungTableView, NKAbrechnungTableView, HGAbrechnungTableViewFrame, \
    NKAbrechnungTableViewFrame, AbrechnungTableViewFrame, AbrechnungTableView
from v2.abrechnungen.abrechnunglogic import HGAbrechnungLogic, HGAbrechnungTableModel, AbrechnungTableModel, \
    AbrechnungLogic, NKAbrechnungLogic
from v2.icc.constants import Action
from v2.icc.icccontroller import IccController
from v2.icc.interfaces import XAbrechnung

################   AbrechnungenController   ####################

class AbrechnungController( IccController ):
    def __init__( self, logic:AbrechnungLogic ):
        IccController.__init__( self )
        self.abrechJahr = datehelper.getCurrentYear() - 1 # Abrechnungen liegen zum laufenden Jahr nicht vor
        self.tv:AbrechnungTableView = None
        self.tvframe:AbrechnungTableViewFrame = None
        self.logic = logic

    def createGui( self ) -> HGAbrechnungTableViewFrame:
        tm: AbrechnungTableModel = self.logic.getAbrechnungTableModel( self.abrechJahr )
        self.tv.setModel( tm, selectRows=True, singleSelection=False )
        self.tv.setAlternatingRowColors( True )
        tb = self.tvframe.getToolBar()
        jahre = [self.abrechJahr, self.abrechJahr - 1, self.abrechJahr - 2]
        tb.addYearCombo( jahre, self.onYearChanged )
        tb.setYear( self.abrechJahr )
        self.tvframe.editItem.connect( self.onOpenAbrechnungDialog )
        self.tvframe.deleteItems.connect( self.onDeleteItems )
        return self.tvframe

    def getMenu( self ) -> QMenu or None:
        pass

    def onOpenAbrechnungDialog( self, row: int ):
        """
        In der Tabelle der Abrechnungen wurde eine Zeile ausgewählt und der Edit-Button der TableView gedrückt.
        Die Verarbeitung wird an den AbrechnungDialogController übergeben.
        :param row: in der Tabelle markierte Abrechnung (Zeile)
        :return:
        """
        model: AbrechnungTableModel = self.tv.model()
        x: XAbrechnung = model.getElement( row )
        if not x.ab_jahr:
            # neue Abrechnung, existiert noch nicht in der DB
            x.ab_jahr = self.abrechJahr
            x.ab_datum = datehelper.getCurrentDateIso()
        abrdlgctrl = AbrechnungDialogController( x, self.logic )
        abrdlgctrl.processAbrechnung()

    def onDeleteItems( self, rowsToDelete ):
        tm:AbrechnungTableModel = self.tv.model()
        xabrechnglist = tm.getElements( rowsToDelete )
        if xabrechnglist[0].abr_id > 0:
            box = WarningBox( "Löschen Jahresabrechnung(en)", "Abrechnung(en) wirklich löschen?",
                              "", "Ja", "Nein" )
            rc = box.exec_()
            if rc == WarningBox.Yes:
                try:
                    self.logic.deleteAbrechnungen( xabrechnglist )
                    for row in rowsToDelete:
                        tm.objectUpdatedExternally2( row )
                except Exception as ex:
                    box = ErrorBox( "Löschen einer Abrechnung fehlgeschlagen", str(ex) )
                    box.exec_()
        else:
            box = InfoBox( "Löschen der gewählten Abrechnung(en) nicht möglich",
                           "Zu den ausgewählten Abrechnungen sind noch keine Daten vorhanden."
                           "\nEs kann deshalb nichts gelöscht werden." )
            box.exec_()
        return

    def onYearChanged( self, newYear: int ):
        tm: AbrechnungTableModel = self.logic.getAbrechnungTableModel( newYear )
        self.tv.setModel( tm )
        self.abrechJahr = newYear

################  HGAbrechnungController   ####################
class HGAbrechnungController( AbrechnungController ):
    def __init__(self):
        AbrechnungController.__init__( self, HGAbrechnungLogic() )
        self.tv = HGAbrechnungTableView()
        self.tvframe = HGAbrechnungTableViewFrame( self.tv )

################  NKAbrechnungController   ####################
class NKAbrechnungController( AbrechnungController ):
    def __init__(self):
        AbrechnungController.__init__( self, NKAbrechnungLogic() )
        self.tv = NKAbrechnungTableView()
        self.tv.setContextMenuCallbacks( self.provideActions, self.onSelected )
        self.tvframe = NKAbrechnungTableViewFrame( self.tv )

    def provideActions( self, index, point, selectedIndexes ) -> List[BaseAction] or None:
        cnt_sel_rows = len( self.tv.getSelectedRows() )
        if cnt_sel_rows > 1:
            l = list()
            l.append( BaseAction( "Summe der Forderungen der markierten Zeilen berechnen...", ident="forderungen" ) )
            l.append( Separator() )
            l.append( BaseAction( "Summe der Zahlungen der markierten Zeilen berechnen...", ident="zahlungen" ) )
            return l

    def onSelected( self, action: BaseAction ):
        if action.ident == "forderungen":
            col = self.tv.model().getColumnIndexByKey( "forderung" )
            title = "Summe der Forderungen"
        else:
            col = self.tv.model().getColumnIndexByKey( "zahlung" )
            title = "Summe der Zahlungen"
        BaseTableFunctions().computeSumme( self.tv, col, col, title )

########################   TEST  TEST  TEST  TEST  TEST  ######################

def test():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    c = NKAbrechnungController()
    tvf = c.createGui()
    tvf.show()
    tvf.resize( QSize(1600, 200) )
    app.exec_()
