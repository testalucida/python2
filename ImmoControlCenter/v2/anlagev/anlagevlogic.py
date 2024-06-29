from typing import List, Dict

import datehelper
from base.basetablemodel import SumTableModel
from v2.anlagev.anlagevdata import AnlageVData
from v2.anlagev.anlagevtablemodel import AnlageVTableModel, XAnlageV
from v2.einaus.einausdata import EinAusData
from v2.extras.ertrag.ertraglogic import ErtragLogic
from v2.geschaeftsreise.geschaeftsreiselogic import GeschaeftsreiseLogic
from v2.icc.constants import EinAusArt
from v2.icc.interfaces import XMasterobjekt, XMietobjekt, XEinAus, XSollMiete, XNKAbrechnung, XSollHausgeld, \
    XGeschaeftsreise
from v2.sollhausgeld.sollhausgelddata import SollHausgeldData
from v2.sollmiete.sollmietedata import SollmieteData


class AnlageVLogic:
    def __init__(self, vj:int ):
        """
        :param vj: das Veranlagungsjahr, um das es sich in allen Methoden dieser Instanz dreht.
        """
        self._vj = vj
        self._avdata = AnlageVData()
        self._eadata = EinAusData()
        self._smdata = SollmieteData()
        self._shgdata = SollHausgeldData()
        self._sollmieten:List[XSollMiete] = self._smdata.getSollMieten( vj )
        self._sollmieten = sorted( self._sollmieten, key=lambda x: (x.mobj_id, x.von) )
        self._sollhausgelder: List[XSollHausgeld] = self._shgdata.getSollHausgelder( vj )
        self._sollhausgelder = sorted( self._sollhausgelder, key=lambda x: (x.mobj_id, x.von) )

    @staticmethod
    def getAvailableVeranlagungsjahre() -> List[int]:
        currYear = datehelper.getCurrentYear()
        years = []
        for y in range( currYear-1, 2020, -1 ):
            years.append( y )
        return years

    @staticmethod
    def getDefaultVeranlagungsjahr() -> int:
        currYear = datehelper.getCurrentYear()
        return currYear - 1

    def getAnlageVTableModels( self ) -> List[AnlageVTableModel]:
        xavlist = self.getAnlageVDataAlle()
        tmlist = list()
        for av in xavlist:
            tmlist.append( AnlageVTableModel( av ) )
        return tmlist

    def getAnlageVTableModel( self, master_name:str ) -> AnlageVTableModel:
        x = self.getAnlageVData( master_name )
        tm = AnlageVTableModel( x )
        return tm

    def getAnlageVDataAlle( self ) -> List[XAnlageV]:
        """
        Liefert eine Liste von XAnlageV-Interfaces.
        Für jedes Masterobjekt ist ein XAnlageV-Objekt in der Liste enthalten.
        :return:
        """
        masterobjects = self._avdata.getMasterobjekte()
        l = list()
        for master in masterobjects:
            xav = self.getAnlageVData( master.master_name )
            l.append( xav )
        return l

    def getAnlageVData( self, master_name:str ) -> XAnlageV:
        """
        Liefert das AnlageVTableModel für alle Mietobjekte eines MasterObjekts
        :param master_name:
        :return:
        """
        x = XAnlageV()
        x.vj = self._vj
        x.master_name = master_name

        # Aufwände, die für das ganze steuerliche Objekt (master_objekt, repr.durch master_name) ermittelt werden
        x.afa = self._avdata.getAfa( master_name )
        # Erhalt.-Aufwände, die sofort und voll abgesetzt werden:
        xealist = self._eadata.getEinAusZahlungen( EinAusArt.REPARATUR.display, self._vj,
                                                   "and master_name = '%s' and verteilt_auf = 1 " % master_name )
        x.erhaltg_voll = int( round( sum( [xea.betrag for xea in xealist] ), 0 ) )
        x.entnahme_rue = self._avdata.getEntnahmeRuecklagen( master_name, self._vj )
        # zu verteilende Erhaltungsaufwände:
        self.provideVerteilteAufwaende( master_name, x )
        self.provideAllgemeineHauskosten( master_name, x )
        x.reisekosten = self._avdata.getReisekosten( master_name, self._vj )
        x.sonstige = self._avdata.getSonstigeKostenOhneReisekosten( master_name, self._vj )

        # Aufwände, die für die einzelne Wohnung ermittelt (und auf den master aufsummiert) werden müssen
        mobj_list:List[XMietobjekt] = self._avdata.getMietobjekte( master_name )
        for mobj in mobj_list:
            #########  Einnahmen  ############
            bruttoMiete, anzahlMonate = self.getJahresBruttomiete( mobj.mobj_id ) # tatsächlich eingegangene Bruttomiete
            x.bruttoMiete += bruttoMiete
            x.anzahlMonate += anzahlMonate
            nkv = self.getJahresSollNkv( mobj.mobj_id )
            nettoMiete = bruttoMiete - nkv
            #nettoMiete, nkv = self.getJahresSollNettoMieteUndNkv( mobj.mobj_id ) # wird aus den Soll-Mieten errechnet
            x.nettoMiete += nettoMiete
            x.nkv += nkv
            nka = self.getNka( mobj.mobj_id )
            x.nka += nka
            #########  Ausgaben  ############
            hgv_netto = self.getJahresSollNettoHausgeld( mobj.mobj_id )
            x.hgv_netto += hgv_netto
            hga = self.getHga( mobj.mobj_id )
            x.hga += hga
        return x

    def provideVerteilteAufwaende( self, master_name:str, xav:XAnlageV ):
        """
        # Versorgt xav mit *allen* zu verteilenden Aufwänden.
        # Das sind sowohl die, die aus Vj stammen, als auch die, die aus den Vj-Vorjahren kommen.
        :param master_name:
        :param xav:
        :return:
        """
        #vertAufwDictList: List[Dict] = self._avdata.getVerteilteAufwaende( master_name )
        vertAufwaende: List[XEinAus] = self._avdata.getVerteilteAufwaende( master_name )
        # Achtung:
        # da sind auch Aufwände dabei,
        #    - die aus einem Jahr > Vj stammen, die erst nächstes Vj berücksichtigt werden dürfen
        #    - die aus einem ganz alten Jahr stammen, die nicht mehr berücksichtigt werden dürfen
        if not vertAufwaende or len( vertAufwaende ) < 1:
            return
        gesamtaufwand_in_vj = 0
        for aufw in vertAufwaende:
            aufwJahr = aufw.jahr
            aufwBetrag = aufw.betrag
            aufwVerteiltAuf = aufw.verteilt_auf
            aufwAnteilig = int(round(aufwBetrag/aufwVerteiltAuf, 0))
            diff = self._vj - aufwJahr
            if diff < 0:
                # Aufwand in einem Vj-Folgejahr, irrelevant
                continue
            if diff == 0:
                # dieser Aufwand wurde im Vj erbracht. Er ist als (Teil vom) Gesamtaufwand auszuweisen
                # und anteilig im Feld "davon im Vj abzuziehen"
                xav.verteil_aufwand_im_vj_angefallen += aufwBetrag
                xav.erhaltg_anteil_vj += aufwAnteilig
            elif diff == 1:
                xav.erhaltg_anteil_vjminus1 += aufwAnteilig
            elif diff == 2:
                xav.erhaltg_anteil_vjminus2 += aufwAnteilig
            elif diff == 3:
                xav.erhaltg_anteil_vjminus3 += aufwAnteilig
            elif diff == 4:
                xav.erhaltg_anteil_vjminus4 += aufwAnteilig

    def provideAllgemeineHauskosten( self, master_name:str, xav:XAnlageV ):
        dic = self._avdata.getGrundsteuerVersicherungenDivAllg( master_name, self._vj )
        xav.grundsteuer = dic.get( EinAusArt.GRUNDSTEUER.dbvalue, 0 )
        xav.versicherungen = dic.get( EinAusArt.VERSICHERUNG.dbvalue, 0 )
        xav.divAllgHk = dic.get( EinAusArt.ALLGEMEINE_KOSTEN.dbvalue, 0 )

    def getJahresBruttomiete( self, mobj_id:str ) -> (int, int):
        addWhere = "and mobj_id = '%s'" % mobj_id
        xealist:List[XEinAus] = \
            self._eadata.getEinAusZahlungen( EinAusArt.BRUTTOMIETE.display, self._vj, addWhere )
        monate = len( xealist )
        summe = 0
        for xea in xealist:
            summe += xea.betrag
        return int( round( summe, 0) ), monate

    def getJahresSollNkv( self, mobj_id:str ) -> int:
        smlist:List[XSollMiete] = [sm for sm in self._sollmieten if sm.mobj_id == mobj_id]
        summeNkv = 0
        for sm in smlist:
            months = datehelper.getNumberOfMonths( sm.von, sm.bis, self._vj )
            summeNkv += months * sm.nkv
        return int( round( summeNkv, 0 ) )

    # def getJahresSollNettoMieteUndNkv( self, mobj_id:str ) -> (int, int):
    #     smlist:List[XSollMiete] = [sm for sm in self._sollmieten if sm.mobj_id == mobj_id]
    #     summeNetto = 0
    #     summeNkv = 0
    #     for sm in smlist:
    #         months = datehelper.getNumberOfMonths( sm.von, sm.bis, self._vj )
    #         summeNetto += months * sm.netto
    #         summeNkv += months * sm.nkv
    #     return int( round( summeNetto, 0 ) ), int( round( summeNkv, 0 ) )

    def getNka( self, mobj_id:str ) -> int:
        """
        Geliefert wird das Ergebnis der Nebenkostenabrechnung des Jahres vor self._vj, denn deren
        Ergebnis wurde in self._vj entrichtet.
        :param mobj_id:
        :return:
        """
        ##year = self._vj - 1
        nkaList:List[XEinAus] = \
            self._eadata.getEinAusZahlungen( EinAusArt.NEBENKOSTEN_ABRECHNG.display, self._vj, "and mobj_id = '%s' "
            % mobj_id )
        nka = int( round( sum([xea.betrag for xea in nkaList]), 0 ) )
        return nka

    def getBruttoHausgeld( self, mobj_id:str ) -> int:
        ealist:List[XEinAus] = self._eadata.getEinAusZahlungen( EinAusArt.HAUSGELD_VORAUS.display, self._vj, "and mobj_id = '%s' "
                                                  % mobj_id)
        brutto = int( round( sum( [x.betrag for x in ealist] ) ) )
        return brutto

    def getJahresSollNettoHausgeld( self, mobj_id: str ) -> int:
        """
        Liefert die Summe des Netto-Hausgelds (ohne RüZuFü), das im Veranlagungsjahr gem. Soll-Hausgeld hätte
        entrichtet werden sollen.
        :param mobj_id:
        :return:
        """
        brutto = self.getBruttoHausgeld( mobj_id )
        shgvlist:List[XSollHausgeld] = [shgv for shgv in self._sollhausgelder if shgv.mobj_id == mobj_id]
        summeRueZuFue = 0
        for shgv in shgvlist:
            months = datehelper.getNumberOfMonths( shgv.von, shgv.bis, self._vj )
            summeRueZuFue += months * shgv.ruezufue
        netto = brutto - int( round(summeRueZuFue, 0 ) )
        return netto

    def getHga( self, mobj_id:str ) -> int:
        """
        Geliefert wird das Ergebnis der Hausgeldabrechnung des Jahres vor self._vj, denn deren
        Ergebnis wurde in self._vj entrichtet.
        :param mobj_id:
        :return:
        """
        #year = self._vj - 1
        hgaList:List[XEinAus] = \
            self._eadata.getEinAusZahlungen( EinAusArt.HAUSGELD_ABRECHNG.display, self._vj, "and mobj_id = '%s' "
            % mobj_id )
        hga = int( round( sum([xea.betrag for xea in hgaList]), 0 ) )
        return hga

    def getReparaturenEinzeln( self, master_name:str ) -> SumTableModel or None:
        ealist:List[XEinAus] = self._eadata.getEinAusZahlungen( EinAusArt.REPARATUR.display, self._vj,
                                                                "and master_name = '%s' " % master_name )
        ealist = [ea for ea in ealist if ea.verteilt_auf == 1]
        if len( ealist ) == 0:
            return None
        tm = SumTableModel(ealist, self._vj, ("betrag",))
        tm.setKeyHeaderMappings2( ("mobj_id", "debi_kredi", "leistung", "buchungsdatum", "buchungstext", "betrag"),
                                  ("Objekt", "Kreditor", "Leistung", "Datum", "Reparatur", "Betrag") )
        return tm

    def getAllgemeineHauskostenEinzeln( self, master_name:str ) -> SumTableModel or None:
        """
        Liefert
            - Grundsteuerzahlungen
            - Versicherungszahlungen
            - Strom, Wasser, Öl, etc. (EinAusArt "allg")
            - HGV-Zahlungen
            - HGA-Zahlung von Vj - 1, entrichtet in Vj
        :param master_name:
        :return:  SumTableModel
        """
        gslist: List[XEinAus] = self._eadata.getEinAusZahlungen( EinAusArt.GRUNDSTEUER.display, self._vj,
                                                                 "and master_name = '%s' " % master_name )
        verslist: List[XEinAus] = self._eadata.getEinAusZahlungen( EinAusArt.VERSICHERUNG.display, self._vj,
                                                                 "and master_name = '%s' " % master_name )
        allglist: List[XEinAus] = self._eadata.getEinAusZahlungen( EinAusArt.ALLGEMEINE_KOSTEN.display, self._vj,
                                                                   "and master_name = '%s' " % master_name )
        hgvlist = self._getHgvListOhneRueZuFue( master_name )
        hgalist: List[XEinAus] = self._eadata.getEinAusZahlungen( EinAusArt.HAUSGELD_ABRECHNG.display, self._vj,
                                                                      "and master_name = '%s' " % master_name )
        geslist = gslist + verslist + allglist + hgvlist + hgalist
        tm = SumTableModel( geslist, self._vj, ("betrag",) )
        tm.setKeyHeaderMappings2( ("master_name", "debi_kredi", "leistung", "ea_art", "buchungsdatum", "buchungstext", "betrag"),
                                  ("Haus",  "Kreditor",   "Leistung", "Art",    "Datum",         "Buchungstext", "Betrag") )
        return tm

    def _getHgvListOhneRueZuFue( self, master_name:str ) -> List[XEinAus]:
        # Bruttozahlungen ermitteln:
        hgvlist: List[XEinAus] = self._eadata.getEinAusZahlungen( EinAusArt.HAUSGELD_VORAUS.display, self._vj,
                                                                  "and master_name = '%s' " % master_name )
        # Anhand der Soll-Zahlungen die Netto-Zahlungen ohne RüZuFü ermitteln:
        mobj_list: List[XMietobjekt] = self._avdata.getMietobjekte( master_name )
        nettoHg = 0
        for mobj in mobj_list:
            nettoHg += self.getJahresSollNettoHausgeld( mobj.mobj_id )
        bruttoHg = sum( [hga.betrag for hga in hgvlist] )
        ruezufue = bruttoHg - nettoHg
        # künstlichen Satz für die Rücklagenzuführung erzeugen
        xea = XEinAus()
        xea.master_name = master_name
        xea.ea_art = "Summe RüZuFü über alle Monate"
        xea.betrag = ruezufue * -1
        # ...und der HGV-Liste hinzufügen
        hgvlist.append( xea )
        return hgvlist

    def getSonstigeEinzeln( self, master_name:str ) -> SumTableModel or None:
        """
        Liefert für <master_name> die Sonstigen Kosten, getrennt nach Dienstreisen und
        übrigen Sonstigen Kosten.
        :param master_name:
        :return:
        """
        # first Reisekosten
        reise_ealist = self._getReisekostenEinzeln( master_name )
        # second Übrige
        sonst_ealist = self._eadata.getEinAusZahlungen( EinAusArt.SONSTIGE_KOSTEN.display, self._vj,
                                                        "and master_name = '%s' and (reise_id is NULL or reise_id = 0)"
                                                        % master_name )
        ealist = list()
        if reise_ealist:
            ealist += reise_ealist
        if sonst_ealist:
            ealist += sonst_ealist
        if len( ealist ) > 0:
            stm = SumTableModel( ealist, self._vj, ["betrag",] )
            stm.setKeyHeaderMappings2(
                ("debi_kredi", "leistung", "reise_id", "buchungsdatum", "buchungstext", "betrag"),
                ("Kreditor", "Leistung", "Reise-ID", "gebucht", "Buchungstext", "Betrag") )
            return stm
        return None

    def _getReisekostenEinzeln( self, master_name:str ) -> List[XEinAus]:
        reiselogic = GeschaeftsreiseLogic()
        reisen:List[XGeschaeftsreise] = reiselogic.getGeschaeftsreisen( master_name, self._vj )
        ea_reisen:List[XEinAus] = self._eadata.getEinAusZahlungen( EinAusArt.SONSTIGE_KOSTEN.display,
                                                                   self._vj,
                                                                   "and master_name = '%s' and reise_id > 0 " % master_name )
        ealist:List[XEinAus] = list()
        for reise in reisen:
            for ea in ea_reisen:
                if reise.reise_id == ea.reise_id:
                    ea.buchungstext = reise.zweck + "\nÜbernachtung: " + reise.uebernachtung + \
                                      "\nvon: " + reise.von + " bis: " + reise.bis
                    ealist.append( ea )
                    break
        return ealist

    def getVerteilteAufwaendeEinzeln( self, master_name: str ) -> SumTableModel or None:
        """
        # Liefert die einzelnen verteilten Aufwände.
        # Das sind sowohl die, die aus Vj stammen, als auch die, die aus den Vj-Vorjahren kommen.
        :param master_name:
        :return:
        """
        vertAufwaende: List[XEinAus] = self._avdata.getVerteilteAufwaende( master_name )
        # Achtung:
        # da sind auch Aufwände dabei,
        #    - die aus einem Jahr > Vj stammen, die erst nächstes Vj berücksichtigt werden dürfen
        #    - die aus einem ganz alten Jahr stammen, die nicht mehr berücksichtigt werden dürfen
        if vertAufwaende and len( vertAufwaende ) > 0:
            ealist = [ea for ea in vertAufwaende if ea.jahr < self._vj <= ea.jahr + 4]
            if ealist and len( ealist ) > 0:
                # den anteiligen Jahresbetrag ausrechnen und XEinAus-Objekte vergewaltigen:
                for ea in ealist:
                    ea.__dict__["anteilig"] = int( round( ea.betrag / ea.verteilt_auf, 0 ) )
                stm = SumTableModel( ealist, self._vj, ["betrag", "anteilig"] )
                stm.setKeyHeaderMappings2(
                    ("mobj_id", "debi_kredi", "leistung", "jahr", "verteilt_auf", "buchungsdatum", "buchungstext", "betrag", "anteilig"),
                    ("Wohnung", "Kreditor", "Leistung", "Jahr", "vert.\nauf", "Datum", "Buchungstext", "Betrag", "anteilig") )
                return stm
        return None


################################################################################
def test():
    log = AnlageVLogic( 2022 )
    tm:AnlageVTableModel = log.getAnlageVTableModel( "NK_Kleist" )
    print( tm )