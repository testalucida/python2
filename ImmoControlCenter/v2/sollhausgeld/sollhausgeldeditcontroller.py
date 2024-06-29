from PySide2.QtCore import Signal
from PySide2.QtWidgets import QApplication, QDialog

from base.messagebox import ErrorBox
from v2.icc.icccontroller import IccController
from v2.icc.iccwidgets import IccCheckTableViewFrame, IccTableView
from v2.icc.interfaces import XMtlZahlung, XEinAus, XSollMiete, XSollHausgeld

#############  SollMieteController  #####################
from v2.sollhausgeld.sollhausgeldeditview import SollHausgeldEditView, SollHausgeldEditDialog
from v2.sollhausgeld.sollhausgeldlogic import SollHausgeldLogic
from v2.sollmiete.sollmieteeditview import SollMieteEditView, SollMieteEditDialog
from v2.sollmiete.sollmietelogic import SollmieteLogic
from v2.sollmiete.sollmieteview import SollMieteView, SollMieteDialog


class SollHausgeldEditController( IccController ):
    endofcurrentsoll_modified = Signal( str )

    def __init__( self ):
        IccController.__init__( self )
        self._logic = SollHausgeldLogic()
        self._dlg:SollHausgeldEditDialog = None

    def createGui( self ) -> IccCheckTableViewFrame:
        pass

    def handleFolgeSollHausgeld( self, currentSoll:XSollHausgeld ):
        """
        currentSoll ist das derzeitige Soll-Hausgeld.
        Von der Geschäftslogik holen wir erstmal ein passendes Folge-Soll-Hausgeld-Objekt und zeigen das dann zur
        Änderung im SollHausgeldEditDialog an.
        :param currentSoll: derzeitige Sollmiete
        :return:
        """
        assert( currentSoll.shg_id > 0 )
        folgeX:XSollHausgeld = self._logic.getFolgeSollHausgeld( currentSoll )
        self.showSollHausgeldEditDialog( folgeX )

    def showSollHausgeldEditDialog( self, x:XSollHausgeld ):
        """
        Zeigt den SollHausgeldEditDialog, um ein neues Soll-Hausgeld-Intervall anzulegen bzw. ein schon für die Zukunft
        angelegtes zu bearbeiten.
        :param x: XSollHausgeld-Objekt, das hier bearbeitet werden soll
        :return:
        """
        def validate() -> bool:
            xcop = v.getDataCopyWithChanges()
            msg = self._logic.validate( xcop )
            if msg:
                box = ErrorBox( "Validierungsfehler", msg, "" )
                box.exec_()
                return False
            else:
                return True
        v = SollHausgeldEditView( x )
        v.delete_sollhausgeld.connect( self.onDeleteSollHausgeld )
        self._dlg = SollHausgeldEditDialog( v )
        self._dlg.setBeforeAcceptFunction( validate )
        if self._dlg.exec_() == QDialog.Accepted:
            # Wenn wir hier landen, wurde die Validierung bereits positiv erledigt.
            v.applyChanges()
            try:
                bis_current_sollhausgeld = self._logic.saveFolgeHausgeld( x )
                # Dem SollmieteController bescheidsagen, dass er das bis-Feld in der View ändern muss
                self.endofcurrentsoll_modified.emit( bis_current_sollhausgeld )
            except Exception as ex:
                box = ErrorBox( "Fehler beim Speichern der Soll-Hausgelds", str(ex), "" )
                box.exec_()

    def onDeleteSollHausgeld( self, x:XSollHausgeld ):
        try:
            bis_current_sollhausgeld = self._logic.deleteFolgeSollHausgeld( x )
            # Dem SollmieteController bescheidsagen, dass er das bis-Feld in der View ändern muss
            self.endofcurrentsoll_modified.emit( bis_current_sollhausgeld )
        except Exception as ex:
            box = ErrorBox( "Fehler beim Löschen des Soll-Hausgelds mit shg_id %d " % x.shg_id, str(ex), "" )
            box.exec_()
        self._dlg.close()


def test():
    app = QApplication()
    ctrl = SollHausgeldEditController()
    x = XSollHausgeld()
    x.weg_name = "WEG Wilhelm-Marx-Str. 15"
    x.mobj_id = "wilhelmmarx"
    ctrl.showSollHausgeldEditDialog( x )

    app.exec_()