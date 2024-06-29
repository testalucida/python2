from typing import List

# from business import BusinessLogic
from base.messagebox import ErrorBox
from generictable_stuff.okcanceldialog import OkCancelDialog
from v2.geschaeftsreise.geschaeftsreiseeditview import GeschaeftsreiseEditView
from v2.icc.interfaces import XGeschaeftsreise
from v2.geschaeftsreise.geschaeftsreiselogic import GeschaeftsreiseLogic


class GeschaeftsreiseEditController:
    def __init__( self, x:XGeschaeftsreise=None ):
        self._xgeschaeftsreise:XGeschaeftsreise = x
        self._view:GeschaeftsreiseEditView = None
        self._dlg = OkCancelDialog()

    @staticmethod
    def validate( x: XGeschaeftsreise ) -> bool:
        msg = ""
        if not x.master_name: msg = "Masterobjekt muss angegeben sein."
        if not x.von: msg = "Beginn muss angegeben sein."
        if not x.bis: msg = "Ende muss angegeben sein."
        if x.von > x.bis: msg = "Beginn muss vor dem Ende sein."
        #if not x.ziel: msg = "Ziel muss angegeben sein."
        if not x.zweck: msg = "Zweck muss angegeben sein."
        if x.km <= 0: msg = "Kilometerangabe fehlt. Muss angegeben werden."
        if msg:
            box = ErrorBox( "Angaben unvollständig", msg, "" )
            box.exec_()
            return False
        return True

    def _createEditViewAndDialog( self ):
        masterlist = GeschaeftsreiseLogic().getMasterNamen()
        self._view = GeschaeftsreiseEditView( masterlist, self._xgeschaeftsreise )
        self._dlg = OkCancelDialog()
        self._dlg.setWindowTitle( "Geschäftsreise bearbeiten" )
        self._dlg.addWidget( self._view, 1 )
        self._dlg.setBeforeAcceptFunction( self.validate )
        self._dlg.setCancellationFunction( self.mayCancel )

    def validate( self ) -> bool:
        x = self._view.getDataCopyWithChanges()
        msg = ""
        if not x.master_name: msg = "Objekt muss angegeben sein."
        elif not x.von: msg = "Beginn muss angegeben sein."
        elif not x.bis: msg = "Ende muss angegeben sein."
        elif x.von > x.bis: msg = "Beginn muss vor dem Ende sein."
        elif not x.zweck: msg = "Zweck muss angegeben sein."
        elif x.uebernachtung and not x.uebernacht_kosten:
            msg = "Wenn ein Hotel angegeben wurde, müssen auch Übernachtungskosten angegeben werden."
        elif x.uebernacht_kosten and not x.uebernachtung:
            msg = "Wenn Übernachtungskosten angegeben werden, muss auch der Name des Hotels angegeben werden."
        elif x.km <= 0: msg = "Kilometerangabe fehlt. Muss angegeben werden."
        if msg:
            box = ErrorBox( "Angaben unvollständig", msg, "" )
            box.exec_()
            return False
        return True

    def mayCancel( self ) -> bool:
        return True

    def createGeschaeftsreise( self, jahr:int ) -> XGeschaeftsreise or None:
        self._xgeschaeftsreise = XGeschaeftsreise()
        self._xgeschaeftsreise.jahr = jahr
        self._createEditViewAndDialog()
        if self._dlg.exec_():
            self._view.applyChanges()
            return self._xgeschaeftsreise
        else:
            return None

    def editGeschaeftsreise( self ) -> bool:
        self._createEditViewAndDialog()
        if self._dlg.exec_():
            xcopy = self._view.getDataCopyWithChanges()
            if not self._xgeschaeftsreise.equals( xcopy ):
                self._view.applyChanges()
                return True
        return False



