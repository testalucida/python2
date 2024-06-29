from v2.icc.constants import ValueMapperHelper, Heizung
from v2.icc.icclogic import IccLogic
from v2.icc.interfaces import XMasterobjekt
from v2.masterobjekt.masterobjektdata import MasterobjektData


class MasterobjektLogic( IccLogic ):
    def __init__( self ):
        IccLogic.__init__( self )
        self._data = MasterobjektData()

    def getMasterData(self, mobj_id:str) -> XMasterobjekt:
        xmaster = self._data.getMasterData( mobj_id )
        if xmaster.heizung:
            xmaster.heizung = ValueMapperHelper.getDisplay(Heizung, xmaster.heizung)
        return xmaster

    def updateMasterobjekt(self, xmaster:XMasterobjekt, commit=False):
        if xmaster.heizung:
            heizung_db = ValueMapperHelper.getDbValue(Heizung, xmaster.heizung)
        else:
            heizung_db = ""
        self._data.updateMasterobjekt1(xmaster.master_id,
                                       xmaster.hauswart, xmaster.hauswart_telefon, xmaster.hauswart_mailto,
                                       heizung_db, xmaster.energieeffz,
                                       xmaster.veraeussert_am, xmaster.bemerkung)
        if commit:
            self._data.commit()