from typing import List

import datehelper
from base.basetablemodel import BaseTableModel, SumTableModel
from v2.einaus.einausdata import EinAusData
from v2.einaus.einauslogic import EinAusLogic
from v2.icc.constants import EinAusArt, iccMonthShortNames, Umlegbar
from v2.icc.icclogic import IccLogic
from v2.icc.interfaces import XGrundbesitzabgabe, XEinAus
from v2.sammelabgabe.sammelabgabedata import SammelabgabeData


class SammelabgabeTableModel( SumTableModel ):
    def __init__( self, rowlist:List[XGrundbesitzabgabe], jahr:int ):
        SumTableModel.__init__( self, rowlist, jahr, ("summe", "betrag_vierteljhrl") )
        self.setKeyHeaderMappings2( ("master_name", "grundsteuer", "abwasser", "strassenreinigung", "summe", "betrag_vierteljhrl"),
                                    ("Haus", "Grundsteuer", "Abwasser", "Straßenreinigg.", "Summe", "Abschlag"),
                                    )

    def getVierteljahresAbschlag( self ) -> float:
        abschlag = 0.0
        for x in self.rowList:
            abschlag += x.betrag_vierteljhrl
        return round( abschlag, 2 )

########################   SammelabgabeLogic   ######################
class SammelabgabeLogic( IccLogic ):
    def __init__( self ):
        IccLogic.__init__( self )
        self._data = SammelabgabeData()

    def getSammelabgabeTableModel( self, jahr:int ) -> SammelabgabeTableModel:
        l:List[XGrundbesitzabgabe] = self._data.getSammelabgaben( jahr )
        for x in l:
            x.computeSum()
        tm = SammelabgabeTableModel( l, jahr )
        return tm

    def checkSammelabgabe( self, buchungsdatum:str ) -> float:
        """
        prüft, ob zum gegebenen Buchungsdatum schon Abbuchungen vorliegen.
        Wenn ja, wird die Summe dieser Buchungen zurückgegeben.
        Dient zur Verhinderung von Doppel-Erfassungen (jede Erfassung führt zu n Einträgen in Tabelle <einaus>!)
        :param buchungsdatum:
        :return:
        """
        startdate = datehelper.addDaysToIsoString( buchungsdatum, -14 )
        enddate = datehelper.addDaysToIsoString( buchungsdatum, 14 )
        summe = self._data.checkSammelabgabeBetween( startdate, enddate ) # liefert nur die Summe an Grundsteuer
        return summe

    def trySaveSammelabgabe( self, jahr:int, betrag:float, buchungsdatum:str ) -> List[XEinAus]:
        """
        Ermittelt die in der DB gespeicherten Sammelabgaben und teilt sie in einzelne EinAus-Objekte auf.
        Diese werden in der Tabelle <einaus> gespeichert. Der Betrag <betrag> wird als Kommentar in das
        Bemerkungsfeld gespeichert.
        Dass möglicherweise die gesplitteten Summen nicht ganz <betrag> entsprechen, ergibt sich aus den
        ungleimäßigen Abbuchungen der Stadt NK und wird toleriert.
        :param: jahr:
        :param betrag:
        :param buchungsdatum:
        :return:
        """
        def trySaveGrundsteuer():
            xea: XEinAus = self._createXEinAusKopfdaten( x, jahr, buchungsdatum )
            #self._createXEinAusKopfdaten( x, jahr, buchungsdatum )
            self._supplyGrundsteuerDaten( xea, x.grundsteuer )
            self._supplyBemerkung( xea, betrag )
            ealogic.trySaveZahlung( xea )
            ealist.append( xea )

        def trySaveAbgaben():
            xea: XEinAus = self._createXEinAusKopfdaten( x, jahr, buchungsdatum )
            #self._createXEinAusKopfdaten( x, jahr, buchungsdatum )
            self._supplyAbwasserStrasse( xea, x )
            self._supplyBemerkung( xea, betrag )
            ealogic.trySaveZahlung( xea )
            ealist.append( xea )

        ealist = list()
        ealogic = EinAusLogic()
        l: List[XGrundbesitzabgabe] = self._data.getSammelabgaben( jahr )
        for x in l:
            # eine Grundbesitzabgabe enthält 3 Beträge: Grundsteuer, Abwasser, Straßenreinigung.
            # Für jede Grundbesitzabgabe legen wir eine Zahlung der ea_art "Grundsteuer" und
            # eine Zahlung der ea_art "Allgemeine Hauskosten" an. Letztere umfasst die Summe aus
            # Abwasser- und Straßenreinigungs-Betrag.
            trySaveGrundsteuer()
            trySaveAbgaben()
        ealogic.commit()
        return ealist

    def _createXEinAusKopfdaten( self, x:XGrundbesitzabgabe, jahr:int, buchungsdatum:str ) -> XEinAus:
        xea = XEinAus()
        xea.master_name = x.master_name
        if xea.master_name.startswith( "NK" ):
            xea.debi_kredi = "Kreisstadt Neunkirchen"
        elif xea.master_name.startswith( "OTW" ):
            xea.debi_kredi = "Gemeinde Ottweiler"
        xea.buchungsdatum = buchungsdatum
        xea.jahr = jahr
        y, m, d = datehelper.getDateParts( buchungsdatum )
        xea.monat = iccMonthShortNames[m - 1]
        xea.umlegbar = Umlegbar.JA.value
        return xea

    def _supplyGrundsteuerDaten( self, xea:XEinAus, grundsteuer:float ):
        xea.ea_art = EinAusArt.GRUNDSTEUER.display
        xea.leistung = "Grundsteuer"
        xea.betrag = round( grundsteuer/4, 2 )

    def _supplyAbwasserStrasse( self, xea:XEinAus, x:XGrundbesitzabgabe ):
        xea.ea_art = EinAusArt.ALLGEMEINE_KOSTEN.display
        xea.leistung = "Abwasser u. Str.reinigg."
        xea.betrag = round( x.abwasser/4 + x.strassenreinigung/4, 2 )

    def _supplyBemerkung( self, xea:XEinAus, betrag:float ):
        xea.buchungstext = "Abbuchung: %.2f €.\n" % betrag
        xea.buchungstext += "Zahlung entstand durch algorithmische Splittung."

def test():
    logic = SammelabgabeLogic()
    tm = logic.getSammelabgabeTableModel( 2022 )
    print( tm )

def test2():
    logic = SammelabgabeLogic()
    sum = logic.checkSammelabgabe( "2022-10-04" )
    print( sum )