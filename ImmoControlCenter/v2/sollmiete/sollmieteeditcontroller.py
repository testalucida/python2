from PySide2.QtCore import Signal
from PySide2.QtWidgets import QApplication, QDialog

from base.messagebox import ErrorBox
from v2.icc.icccontroller import IccController
from v2.icc.iccwidgets import IccCheckTableViewFrame, IccTableView
from v2.icc.interfaces import XSollMiete
from v2.sollmiete.sollmieteeditview import SollMieteEditView, SollMieteEditDialog
from v2.sollmiete.sollmietelogic import SollmieteLogic

#############  SollMieteEditController  #####################
class SollMieteEditController( IccController ):
    endofcurrentsoll_modified = Signal( str )

    def __init__( self ):
        IccController.__init__( self )
        self._logic = SollmieteLogic()
        self._dlg:SollMieteEditDialog = None

    def createGui( self ) -> IccCheckTableViewFrame:
        pass

    def handleFolgeSollmiete( self, currentSoll:XSollMiete ):
        """
        currentSoll ist die derzeitige Sollmiete.
        Von der Geschäftslogik holen wir erstmal ein passendes Folge-Sollmiete-Objekt und zeigen das dann zur
        Änderung im SollMieteEditDialog an.
        :param currentSoll: derzeitige Sollmiete
        :return:
        """
        assert( currentSoll.sm_id > 0 )
        folgeX:XSollMiete = self._logic.getFolgeSollmiete( currentSoll )
        self.showSollMieteEditDialog( folgeX )

    def showSollMieteEditDialog( self, x:XSollMiete ):
        """
        Zeigt den SollmieteEditDialog, um ein neues Sollmiete-Intervall anzulegen bzw. ein schon für die Zukunft
        angelegtes zu bearbeiten.
        :param x: XSollMiete-Objekt, das hier bearbeitet werden soll
        :return:
        """
        def validate() -> bool:
            msg = self._logic.validate( x )
            if msg:
                box = ErrorBox( "Validierungsfehler", msg, "" )
                box.exec_()
                return False
            else:
                return True
        v = SollMieteEditView( x )
        v.delete_sollmiete.connect( self.onDeleteSollmiete )
        self._dlg = SollMieteEditDialog( v )
        self._dlg.setBeforeAcceptFunction( validate )
        if self._dlg.exec_() == QDialog.Accepted:
            # Wenn wir hier landen, wurde die Validierung bereits positiv erledigt.
            v.applyChanges()
            try:
                bis_current_sollmiete = self._logic.saveFolgeSollmiete( x )
                # Dem SollmieteController bescheidsagen, dass er das bis-Feld in der View ändern muss
                self.endofcurrentsoll_modified.emit( bis_current_sollmiete )
            except Exception as ex:
                box = ErrorBox( "Fehler beim Speichern der Sollmiete", str(ex), "" )
                box.exec_()

    def onDeleteSollmiete( self, x:XSollMiete ):
        try:
            bis_current_sollmiete = self._logic.deleteFolgeSollmiete( x )
            # Dem SollmieteController bescheidsagen, dass er das bis-Feld in der View ändern muss
            self.endofcurrentsoll_modified.emit( bis_current_sollmiete )
        except Exception as ex:
            box = ErrorBox( "Fehler beim Löschen der Sollmiete mit sm_id %d " % x.sm_id, str(ex), "" )
            box.exec_()
        self._dlg.close()


def test():
    app = QApplication()
    ctrl = SollMieteEditController()
    #ctrl.showSollMieteEditDialog( "lukas_franz", 2022, 5 )

    app.exec_()