from typing import List, Dict

from v2.icc.iccdata import IccData
from v2.icc.interfaces import XGeschaeftsreise, XPauschale


class GeschaeftsreiseData( IccData ):
    def __init__(self):
        IccData.__init__( self )

    def getDistinctJahre( self ) -> List[int]:
        sql = "select distinct jahr from geschaeftsreise order by jahr desc "
        tuplelist = self.read( sql )
        jahre = [t[0] for t in tuplelist]
        return jahre

    def getAllGeschaeftsreisen( self, jahr:int ) -> List[XGeschaeftsreise]:
        sql = "select reise_id, master_name, von, bis, jahr, zweck, km, personen, " \
              "uebernachtung, uebernacht_kosten " \
              "from geschaeftsreise " \
              "where jahr = %d" % jahr
        return self.readAllGetObjectList( sql, XGeschaeftsreise )

    def getGeschaeftsreise( self, reise_id:int ) -> XGeschaeftsreise:
        """
        Ermittelt die Daten einer Geschäftsreise
        :param reise_id:
        :return:
        """
        sql = "select reise_id, master_name, von, bis, jahr, zweck, km, personen, " \
              "uebernachtung, uebernacht_kosten " \
              "from geschaeftsreise " \
              "where reise_id = %d " % reise_id
        x = self.readOneGetObject( sql, XGeschaeftsreise )
        return x

    def getGeschaeftsreisen( self, master_name:str, jahr:int ) -> List[XGeschaeftsreise]:
        """
        Ermittelt alle Geschäftsreisen zu einem Masterobjekt.
        Da die Geschäftsreisen zu einer mobj_id erfasst sind, wird über zwei inner joins gesammelt.
        Diese Methode wird für die Anlage V gebraucht, da diese sich auf Masterobjekte bezieht.
        :param master_name:
        :param jahr:
        :return:
        """
        sql = "select reise_id, master_name, von, bis, jahr, zweck, km, personen, " \
              "uebernachtung, uebernacht_kosten " \
              "from geschaeftsreise " \
              "where master_name = '%s' " \
              "and jahr = %d " % ( master_name, jahr )
        xlist = self.readAllGetObjectList( sql, XGeschaeftsreise )
        return xlist

    def getPauschalen( self, jahr:int ) -> XPauschale:
        sql = "select km, vpfl_8, vpfl_24 " \
              "from pauschale " \
              "where jahr_von <= %d " \
              "and (jahr_bis >= %d or jahr_bis is NULL) " % (jahr, jahr)
        x = self.readOneGetObject( sql, XPauschale )
        return x

    def insertGeschaeftsreise( self, x:XGeschaeftsreise ) -> int:
        uebernachtung = x.uebernachtung if x.uebernachtung > " " else ""
        uebernacht_kosten = x.uebernacht_kosten if x.uebernacht_kosten != 0 else 0.0
        sql = "insert into geschaeftsreise " \
              "( master_name, jahr, von, bis, " \
              "zweck, km, personen, uebernachtung, uebernacht_kosten )" \
              "values" \
              "( '%s', %d, '%s', '%s'," \
              "  '%s', %d, %d, '%s', %.2f )" % (x.master_name, x.jahr, x.von, x.bis,
                                                  x.zweck, x.km, x.personen,
                                                  uebernachtung, uebernacht_kosten )
        return self.write( sql )

    def updateGeschaeftsreise( self, x:XGeschaeftsreise ) -> int:
        sql = "update geschaeftsreise " \
              "set master_name = '%s', " \
              "von = '%s', " \
              "bis = '%s', " \
              "zweck = '%s', " \
              "km = %d, " \
              "personen = %d, " \
              "uebernachtung = '%s', " \
              "uebernacht_kosten = %.2f " \
              "where reise_id = %d " % ( x.master_name, x.von, x.bis, x.zweck, x.km,
                                   x.personen, x.uebernachtung, x.uebernacht_kosten, x.reise_id)
        return self.write( sql )

    def deleteGeschaeftsreise( self, reise_id:int ) -> int:
        sql = "delete from geschaeftsreise where reise_id = %d " % reise_id
        return self.write( sql )


def test2():
    data = GeschaeftsreiseData()
    jahre = data.getDistinctJahre()
    print( jahre )

def test1():
    data = GeschaeftsreiseData()
    xlist = data.getGeschaeftsreisen( "ILL_Eich", 2021 )
    #xlist = data.getGeschaeftsreisen( "N_Mendel", 2021 )
    print( xlist )