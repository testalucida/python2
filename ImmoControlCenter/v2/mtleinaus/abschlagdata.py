from typing import List, Dict

from v2.icc.iccdata import IccData
from v2.icc.interfaces import XSollMiete, XSollAbschlag


class AbschlagData( IccData ):
    def __init__(self):
        IccData.__init__( self )

    def getSollabschlaege( self, jahr: int ) -> List[XSollAbschlag]:
        minbis = "%d-%02d-%02d" % (jahr, 1, 1)
        maxvon = "%d-%02d-%02d" % (jahr, 12, 31)
        sql = "select sab_id, kreditor, vnr, leistung, ea_art, master_name, coalesce(mobj_id, '') as mobj_id, " \
              "von, coalesce(bis, '') as bis, " \
              "betrag, umlegbar, coalesce(bemerkung, '') as bemerkung " \
              "from sollabschlag " \
              "where (bis is NULL or bis = '' or bis >= '%s') " \
              "and not von > '%s' " \
              "order by kreditor, mobj_id, von desc" % (minbis, maxvon)
        l:List[XSollAbschlag] = self.readAllGetObjectList( sql, XSollAbschlag )
        return l

    def getSollAbschlag( self, sab_id:int ) -> XSollAbschlag:
        sql = "select sab_id, kreditor, vnr, leistung, ea_art, master_name, mobj_id, von, coalesce(bis, '') as bis, " \
              "betrag, umlegbar, bemerkung " \
              "from sollabschlag " \
              "where sab_id = %d " % sab_id
        return self.readOneGetObject( sql, XSollAbschlag )

    def getVnrUndEaArtUndUmlegbar( self, sab_id:int ) -> Dict:
        sql = "select vnr, ea_art, umlegbar from sollabschlag where sab_id = " + str( sab_id )
        dic = self.readOneGetDict( sql )
        return dic


##################################################################################

def test():
    data = AbschlagData()
    l = data.getSollabschlaege( 2022 )
    print( l )
    u = data.getVnrUndUmlegbar( 2 )
    print( u )