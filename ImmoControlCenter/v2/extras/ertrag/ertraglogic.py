from typing import List, Iterable

from base.basetablemodel import SumTableModel
from v2.extras.ertrag.ertragdata import ErtragData

#############   ErtragTableModel   ########################
from v2.icc.constants import EinAusArt
from v2.icc.interfaces import XMasterobjekt, XEinAus, XMasterEinAus


###################   ErtragTableModel   ####################
class ErtragTableModel( SumTableModel ):
    def __init__( self, einauslist:List[XMasterEinAus], jahr:int ):
        SumTableModel.__init__( self, einauslist, jahr, ("qm", "einnahmen", "hg", "allg_kosten", "rep_kosten", "sonst_kosten",
                                                   "ertrag") )
        self.colIdxAllgKosten = 8
        self.colIdxRep = 9
        self.colIdxSonstKosten = 10

###################   ErtragLogic   #######################
class ErtragLogic:
    def __init__( self ):
        self._ertragData = ErtragData()

    def getErtragTableModel( self, jahr:int ) -> ErtragTableModel:
        masters:List[XMasterobjekt] = self._ertragData.getMasterobjekte()
        l = list()
        for master in masters:
            x = XMasterEinAus()
            x.master_id = master.master_id
            x.master_name = master.master_name
            x.qm = master.gesamt_wfl
            x.monate = self._ertragData.getAnzahlVermieteteMonate( x.master_name, jahr )
            # Summe Einzahlungen: Bruttomieten und NK-Abrechnungen
            x.einnahmen = self._ertragData.getSummeEinzahlungen( x.master_name, jahr )
            if x.qm > 0:
                x.netto_je_qm = self._getAktuelleNettoMieteJeQm( x.master_name, x.qm )
            # Summe Hausgeld. Die Rücklagenzuführung wird als Kosten gewertet, dafür werden
            # die Entnahmen aus der Rücklage ignoriert.
            # Das läuft in der Anlage V anders!
            x.hg = self._ertragData.getSummeHausgeld( x.master_name, jahr )
            x.sonder_u = self._ertragData.getSumme( x.master_name, jahr, EinAusArt.SONDERUMLAGE.dbvalue )
            x.rep_kosten = self._ertragData.getSumme( x.master_name, jahr, EinAusArt.REPARATUR.dbvalue )
            x.allg_kosten = self._ertragData.getSumme( x.master_name, jahr, EinAusArt.ALLGEMEINE_KOSTEN.dbvalue )
            x.allg_kosten += self._ertragData.getSumme( x.master_name, jahr, EinAusArt.GRUNDSTEUER.dbvalue )
            x.allg_kosten += self._ertragData.getSumme( x.master_name, jahr, EinAusArt.VERSICHERUNG.dbvalue )
            x.sonst_kosten = self._ertragData.getSumme( x.master_name, jahr, EinAusArt.SONSTIGE_KOSTEN.dbvalue )
            x.ertrag = x.einnahmen + x.hg + x.sonder_u + x.allg_kosten + x.rep_kosten + x.sonst_kosten
            l.append( x )

        l = sorted( l, key=lambda x: x.ertrag, reverse=True ) # größter Ertrag oben
        tm = ErtragTableModel( l, jahr )
        tm.setHeaders( ("id", "Master", "qm", "Anz.\nMonate", "Einnahmen\n(Netto+NKV+NKA)", "netto\nje qm",
                        "HG+HGA\n(inkl. RüZuFü)", "Sonder",
                        "Allg.\nKosten", "Rep.", "Sonst.\nKosten", "Ertrag") )
        return tm

    def getReparaturenEinzeln( self, master_name, jahr ) -> SumTableModel:
        """
        Auf verteilte Kosten wird keine Rücksicht genommen. Es gilt das Abflussprinzip: der volle Betrag wird
        dem Jahr zugerechnet, in dem die Rechnung bezahlt wurde.
        :param master_name:
        :param jahr:
        :return:
        """
        tm = self._getEinAusEinzelnTableModel( master_name, jahr, (EinAusArt.REPARATUR.dbvalue, ) )
        tm.setKeyHeaderMappings2( ( "mobj_id", "debi_kredi", "leistung", "buchungsdatum", "buchungstext", "betrag"),
                                  ("Objekt", "Kreditor", "Leistung", "Datum", "Reparatur", "Betrag") )
        return tm

    def _getEinAusEinzelnTableModel( self, master_name:str, jahr:int, ea_art_db_list:Iterable[str] ) -> SumTableModel:
        l: List[XEinAus] = self._ertragData.getEinAusEinzeln( master_name, jahr, ea_art_db_list )
        tm = SumTableModel( l, jahr, ("betrag",) )
        return tm

    def getAllgemeineKostenEinzeln( self, master_name, jahr ) -> SumTableModel:
        tm = self._getEinAusEinzelnTableModel( master_name, jahr, (EinAusArt.ALLGEMEINE_KOSTEN.dbvalue,
                                                                   EinAusArt.GRUNDSTEUER.dbvalue,
                                                                   EinAusArt.VERSICHERUNG.dbvalue ) )
        tm.setKeyHeaderMappings2( ("debi_kredi", "mobj_id", "buchungstext", "ea_art", "betrag"),
                                  ("Kreditor", "Objekt", "Buchungstext", "EinAusArt", "Betrag") )
        return tm

    def getSonstigeKostenEinzeln( self, master_name, jahr ) -> SumTableModel:
        tm = self._getEinAusEinzelnTableModel( master_name, jahr, (EinAusArt.SONSTIGE_KOSTEN.dbvalue, ) )
        tm.setKeyHeaderMappings2( ("debi_kredi", "mobj_id", "buchungsdatum", "buchungstext", "ea_art", "betrag"),
                                  ("Kreditor", "Objekt", "Datum", "Buchungstext", "EinAusArt", "Betrag") )
        return tm

    def _getAktuelleNettoMieteJeQm( self, master_name:str, qm:int ) -> float:
        sumnetto =self._ertragData.getNettomieteAktuell( master_name )
        nettojeqm = sumnetto / qm
        return float( format(nettojeqm, "0.2f") )


def test():
    logic = ErtragLogic()
    tm = logic.getErtragTableModel( 2022 )

    print( tm )