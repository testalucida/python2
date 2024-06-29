from typing import List, Dict

import datehelper

from v2.icc.constants import EinAusArt
from v2.icc.iccdata import IccData
from v2.icc.interfaces import XGrundbesitzabgabe


class SammelabgabeData( IccData ):
    def __init__(self):
        IccData.__init__( self )

    def getSammelabgaben( self, jahr:int ) -> List[XGrundbesitzabgabe]:
        sql = "select id, master_name, grundsteuer, abwasser, strassenreinigung, bemerkung " \
              "from sammelabgabe_detail " \
              "where jahr = %d " % jahr
        xlist = self.readAllGetObjectList( sql, XGrundbesitzabgabe )
        return xlist

    def checkSammelabgabeBetween( self, startdate: str, enddate: str ) -> float:
        """
        liefert die Summe von Grundsteuer-Zahlungen an die Gemeinde Neunkirchen zwischen startdate und enddate (jeweils inklusive)
        :param startdate:
        :param enddate:
        :return: die SUmme als float
        """
        ea_db_art = EinAusArt.GRUNDSTEUER.dbvalue
        sql = "select sum(betrag) " \
              "from einaus " \
              "where debi_kredi = 'Kreisstadt Neunkirchen' " \
              "and ea_art = '%s' " \
              "and buchungsdatum >= '%s' " \
              "and buchungsdatum <= '%s' " % (ea_db_art, startdate, enddate)
        tpl = self.read( sql )
        summe = tpl[0][0]
        return 0.0 if not summe else summe


