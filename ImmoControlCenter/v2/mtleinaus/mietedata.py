from typing import List, Dict

from v2.icc.iccdata import IccData
from v2.icc.interfaces import XSollMiete


class MieteData( IccData ):
    def __init__(self):
        IccData.__init__( self )

    # def getSollmieten( self, jahr: int ) -> List[XSollMiete]:
    #     minbis = "%d-%02d-%02d" % (jahr, 1, 1)
    #     maxvon = "%d-%02d-%02d" % (jahr, 12, 31)
    #     sql = "select sm.sm_id, sm.mv_id, sm.von, coalesce(sm.bis, '') as bis, " \
    #           "sm.netto, sm.nkv, (sm.netto + sm.nkv) as brutto, " \
    #           "coalesce(sm.bemerkung, '') as bemerkung, mv.mobj_id " \
    #           "from sollmiete sm " \
    #           "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
    #           "where (sm.bis is NULL or sm.bis = '' or sm.bis >= '%s') " \
    #           "and not sm.von > '%s' " \
    #           "order by sm.mv_id, sm.von desc" % (minbis, maxvon)
    #     l:List[XSollMiete] = self.readAllGetObjectList( sql, XSollMiete )
    #     return l

##################################################################################

def test():
    data = MieteData()
    #l = data.getSollmieten( 2022 )
    print( l )