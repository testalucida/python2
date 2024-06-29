from typing import List, Iterable

import datehelper
from v2.icc.constants import EinAusArt
from v2.icc.iccdata import IccData
from v2.icc.interfaces import XEinAus


class ErtragData( IccData ):
    def __init__( self ):
        IccData.__init__( self )

    def getSummeEinzahlungen( self, master_name:str, jahr:int ) -> int:
        sql = "select sum(betrag) " \
              "from einaus " \
              "where master_name = '%s' " \
              "and jahr = %d " \
              "and ea_art in ( '%s', '%s' ) " \
              % (master_name, jahr, EinAusArt.BRUTTOMIETE.dbvalue, EinAusArt.NEBENKOSTEN_ABRECHNG.dbvalue)
        tuplelist = self.read( sql )
        summe = tuplelist[0][0]
        return int( round( summe ) ) if summe else 0

    def getAnzahlVermieteteMonate( self, master_name:str, jahr:int ) -> int:
        sql = "select count(*) " \
              "from einaus " \
              "where master_name = '%s' " \
              "and jahr = %d " \
              "and ea_art = '%s' " % (master_name, jahr, EinAusArt.BRUTTOMIETE.dbvalue)
        tuplelist = self.read( sql )
        summe = tuplelist[0][0]
        return int( round( summe ) ) if summe else 0.0

    def getSumme( self, master_name:str, jahr:int, ea_art_db:str ) -> int:
        sql = "select sum(betrag) " \
              "from einaus " \
              "where master_name = '%s' " \
              "and jahr = %d " \
              "and ea_art = '%s' " % (master_name, jahr, ea_art_db )
        tuplelist = self.read( sql )
        summe = tuplelist[0][0]
        return int( round( summe ) ) if summe else 0

    # def getReparaturenEinzeln( self, master_name:str, jahr:int ) -> List[XEinAus]:
    #     sql = "select master_name, mobj_id, debi_kredi, buchungsdatum, buchungstext, ea_art, betrag " \
    #           "from einaus " \
    #           "where jahr = %d " \
    #           "and master_name = '%s' " \
    #           "and ea_art = '%s' " % ( jahr, master_name, EinAusArt.REPARATUR.dbvalue )
    #     reps = self.readAllGetObjectList( sql, XEinAus )
    #     return reps

    def getEinAusEinzeln( self, master_name: str, jahr: int, ea_art_db_list: Iterable[str] ) -> List[XEinAus]:
        """
        Liefert die Ein-/Auszahlungen der gewünschten EinAusArten.
        :param master_name:
        :param jahr:
        :param ea_art_db_list:
        :return: Eine Liste mit XEinAus-Objekten. Wurde keine Ausgabe gefunden, wird eine leere Liste
                zurückgegeben.
        """
        ea_arten_db = ""
        for ea_art_db in ea_art_db_list:
            ea_arten_db += "'"
            ea_arten_db += ea_art_db
            ea_arten_db += "'"
            ea_arten_db += ","
        ea_arten_db = ea_arten_db[:-1]
        sql = "select  master_name, mobj_id, ea_art, leistung, debi_kredi, buchungstext, buchungsdatum, betrag " \
              "from einaus " \
              "where master_name = '%s' " \
              "and jahr = %d " \
              "and ea_art in (%s) " \
              "order by ea_art, debi_kredi, betrag " % (master_name, jahr, ea_arten_db)
        l = self.readAllGetObjectList( sql, XEinAus )
        return l

    def getSummeHausgeld( self, master_name:str, jahr:int ) -> int:
        sql = "select sum(betrag) " \
              "from einaus " \
              "where master_name = '%s' " \
              "and jahr = %d " \
              "and ea_art in ('%s', '%s') " \
              % ( master_name, jahr, EinAusArt.HAUSGELD_VORAUS.dbvalue, EinAusArt.HAUSGELD_ABRECHNG.dbvalue )
        tuplelist = self.read( sql )
        summe = tuplelist[0][0]
        return int( round( summe ) ) if summe else 0

    def getNettomieteAktuell( self, master_name:str ) -> float:
        current_date = datehelper.getCurrentDateIso()
        sql = "select sum( netto ) " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "inner join mietobjekt mobj on mobj.mobj_id = mv.mobj_id " \
              "where mobj.master_name = '%s' " \
              "and sm.von <= '%s' " \
              "and (sm.bis is '' or sm.bis is NULL or sm.bis >= '%s') " % (master_name, current_date, current_date)
        tuplelist = self.read( sql )
        summe = tuplelist[0][0]
        return summe if summe else 0


