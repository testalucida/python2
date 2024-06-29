from typing import List, Dict

from v2.icc.iccdata import IccData
from v2.icc.interfaces import XMtlHausgeld


class HausgeldData( IccData ):
    def __init__(self):
        IccData.__init__( self )

    def getMtlHausgeldListe( self, jahr:int ) -> List[XMtlHausgeld]:
        """
        Liefert die Mietobjekte, für die Hausgeld entrichtet wird (=die von einem Verwalter verwaltet werden)
        als Liste von XMtlHausgeld.
        D.h., ILL_Eich, NK_Kleist und SB_Kaiser werden nicht berücksichtigt.
        :param: jahr:
        :return:
        """
        max_von = str(jahr) + "-12-31"
        min_bis = str(jahr) + "-01-01"
        sql = "select distinct mo.master_name, mo.mobj_id, vwg.weg_name " \
              "from mietobjekt mo " \
              "inner join verwaltung vwg on vwg.master_name = mo.master_name " \
              "where vwg.von <= '%s' " \
              "and (vwg.bis is NULL or vwg.bis = '' or vwg.bis >= '%s' ) " % (max_von, min_bis)
        return self.readAllGetObjectList( sql, XMtlHausgeld )


##################################################################################

def test():
    data = HausgeldData()
    l = data.getMtlHausgeldListe()
    print( l )
    # l = data.getSollHausgelder( 2022 )
    #print( l )