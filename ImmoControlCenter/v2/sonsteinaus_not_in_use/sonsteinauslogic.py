from v2.einaus.einauslogic import EinAusLogic
from v2.icc.icclogic import IccLogic
from v2.sonsteinaus_not_in_use.sonsteinausmodel import SonstEinAusTableModel


class SonstEinAusLogic( IccLogic ):
    def __init__( self ):
        IccLogic.__init__( self )
        self._ealogic = EinAusLogic()

    def getZahlungenModel( self, jahr:int ) -> SonstEinAusTableModel :
        self._ealogic.getZahlungenModel()