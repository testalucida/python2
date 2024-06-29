
from PySide2.QtCore import Slot, QSize
from PySide2.QtWidgets import QApplication, QDialog, QMenu, QTabWidget

from base.baseqtderivates import BaseAction
from base.basetableview import BaseTableView
from generictable_stuff.okcanceldialog import OkDialog
from v2.icc.icccontroller import IccController
from v2.icc.iccwidgets import IccCheckTableViewFrame
from v2.icc.interfaces import XSollHausgeld
from v2.sollhausgeld.sollhausgeldeditcontroller import SollHausgeldEditController
from v2.sollhausgeld.sollhausgeldlogic import SollHausgeldLogic
from v2.sollhausgeld.sollhausgeldview import SollHausgeldView, SollHausgeldDialog
from v2.sollmiete.sollmietelogic import SollmieteLogic


class SollzahlungenController( IccController ):
    def __init__( self ):
        IccController.__init__( self )
        self._dlg = None

    def getMenu( self ) -> QMenu:
        menu = QMenu( "Sollzahlungen")
        action = BaseAction( "Alle Soll-Zahlungen anzeigen...", parent=menu )
        action.triggered.connect( self.onShowSoll )
        menu.addAction( action )
        return menu

    def createGui( self ) -> IccCheckTableViewFrame:
        pass

    def onShowSoll( self ):
        """
        Zeigt einen Dialog, der sowohl Sollmieten wie auch Soll-Hausgelder enthält.
        :return:
        """
        def createSollmietenTab() -> (int, int):
            smLogic = SollmieteLogic()
            smTm = smLogic.getAlleSollMieten()
            smView = BaseTableView()
            smView.setModel( smTm, selectRows=True, singleSelection=False )
            tabs.addTab( smView, "Soll-Mieten" )
            return smView.getPreferredWidth(), smView.getPreferredHeight()
        def createSollHausgeldTab() -> (int, int):
            shgLogic = SollHausgeldLogic()
            shgTm = shgLogic.getAllSollHausgelder()
            shgView = BaseTableView()
            shgView.setModel( shgTm, selectRows=True, singleSelection=False )
            tabs.addTab( shgView, "Soll-Hausgelder" )
            return shgView.getPreferredWidth(), shgView.getPreferredHeight()
        if not self._dlg:
            self._dlg = OkDialog( "Alle Sollzahlungen" )
        d = self._dlg
        tabs = QTabWidget()
        w1, h1 = createSollmietenTab()
        w2, h2 = createSollHausgeldTab()
        d.addWidget( tabs, 0 )
        w = w1 if w1 > w2 else w2
        h = h1 if h1 > h2 else h2
        if h > 1200: h = 1200
        d.resize( QSize( w, h ) )
        d.show()


#############  SollMieteController  #####################
class SollHausgeldController( IccController ):
    def __init__( self ):
        SollzahlungenController.__init__( self )
        self._logic = SollHausgeldLogic()

    def showHgvAndRueZuFue( self, mobj_id:str, jahr:int, monthNumber:int ):
        """
        Zeigt die SollHausgeld-View mit den gewünschten Daten
        :param mobj_id:
        :param jahr:
        :param monthNumber: 1 -> Januar, ... , 12 -> Dezember
        :return:
        """
        x:XSollHausgeld = self._logic.getSollHausgeldAm( mobj_id, jahr, monthNumber )
        v = SollHausgeldView( x )
        dlg = SollHausgeldDialog( v )
        dlg.setWindowTitle( "Soll-Hausgeld für '%s' (%s)" % (x.weg_name, x.mobj_id) )
        dlg.edit_clicked.connect( lambda: self.onEditSollHausgeld( x, v ) )
        if dlg.exec_() == QDialog.Accepted:
            # Die Bemerkung könnte geändert sein. Keine Validierung, direkt an die Logik zum Speichern übergeben.
            v.applyChanges()
            self._logic.updateSollHausgeldBemerkung( x.shg_id, x.bemerkung )


    def onEditSollHausgeld( self, x: XSollHausgeld, view: SollHausgeldView ):
        """
        Im SollHausgeldDialog wurde der Button "Folge-Soll erfassen oder ändern..." gedrückt.
        Wir instanzieren den SollHausgeldEditController und lassen ihn die Anlage eines neuen
        Hausgeld-Intervalls behandeln
        :param x: das derzeitige XSollHausgeld-Objekt
        :param view: die SollHausgeldView, in der o.a. Button gedrückt wurde.
        :return:
        """
        def onBisChanged( bis: str ):
            view.setBis( bis )
        shgEditCtrl = SollHausgeldEditController()
        shgEditCtrl.endofcurrentsoll_modified.connect( onBisChanged )
        shgEditCtrl.handleFolgeSollHausgeld( x )

def test2():
    app = QApplication()
    ctrl = SollzahlungenController()
    ctrl.onShowSoll()

def test():
    app = QApplication()
    ctrl = SollHausgeldController()
    ctrl.showHgvAndRueZuFue( "remigius", 2023, 3 )
