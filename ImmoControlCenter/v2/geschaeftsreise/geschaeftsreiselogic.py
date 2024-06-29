from typing import List, Dict, Iterable

import datehelper
from base.transaction import BEGIN_TRANSACTION, COMMIT_TRANSACTION, ROLLBACK_TRANSACTION
from v2.einaus.einauslogic import EinAusLogic
from v2.geschaeftsreise.geschaeftsreisedata import GeschaeftsreiseData
from v2.geschaeftsreise.geschaeftsreisetablemodel import GeschaeftsreiseTableModel
from v2.icc.constants import iccMonthShortNames, EinAusArt, Umlegbar
from v2.icc.interfaces import XGeschaeftsreise, XPauschale, XEinAus

####################   GeschaeftsreiseLogic   ################################
class GeschaeftsreiseLogic:
    """
    Methoden rund ums Thema Geschäftsreisen.
    ACHTUNG: Einige Methoden dazu sind noch in der alten BusinessLogic!! #todo
    """
    def __init__( self ):
        self._data = GeschaeftsreiseData()
        self._pauschalen:Dict = dict() # key: Jahr; value: XPauschale

    def getDistinctJahre( self ) -> List[int]:
        """
        Liefert die Jahre, zu denen in der DB Reisen erfasst sind.
        Wenn zum lfd. Jahr noch keine Reise erfasst ist, wird das lfd. Jahr
        trotzdem zur Rückgabe-Liste hinzugefügt.
        :return: Liste der Jahre
        """
        jahre = self._data.getDistinctJahre()
        current = datehelper.getCurrentYear()
        if not current in jahre:
            jahre.insert( 0, current )
        return jahre

    def getGeschaeftsreisenTableModel( self, jahr: int ) -> GeschaeftsreiseTableModel:
        xlist = self.getAllGeschaeftsreisen( jahr )
        model = GeschaeftsreiseTableModel( xlist )
        return model

    def getPauschale( self, jahr:int ) -> XPauschale:
        try:
            return self._pauschalen[jahr]
        except:
            pausch = self._data.getPauschalen( jahr )
            self._pauschalen[jahr] = pausch
            return pausch

    def getGeschaeftsreise( self, reise_id:int ) -> XGeschaeftsreise:
        return self._data.getGeschaeftsreise( reise_id )

    def getGeschaeftsreisen( self, master_name: str, jahr: int ) -> List[XGeschaeftsreise]:
        xlist = self._data.getGeschaeftsreisen( master_name, jahr )
        return xlist

    def getAllGeschaeftsreisen( self, jahr:int ) -> List[XGeschaeftsreise]:
        return self._data.getAllGeschaeftsreisen( jahr )

    def getSummeGeschaeftsreisekosten( self, jahr:int ) -> float:
        """
        Ermittelt anhand der Tabellen geschaeftsreise und pauschale die Gesamtkosten für das Jahr <jahr>.
        Wir gehen davon aus, dass nur Kosten für mich, nicht für Gudi ansetzbar sind. Die Spalte <personen> in Tabelle
        geschaeftsreise wird also ignoriert.
        :param jahr: das Jahr, das beauskunftet werden soll
        :return: Die Gesamtkosten aller Dienstreisen im Jahr <jahr>
        """
        geschaeftsreisen = self.getAllGeschaeftsreisen( jahr )
        return self._getGeschaeftsreisekosten( geschaeftsreisen )

    def getGeschaeftsreisekosten( self, master_name:str, jahr:int ) -> float:
        """
        Ermittelt die Geschäftsreisekosten für <master_name> im Jahr <jahr>.
        :param master_name:
        :param jahr:
        :return:
        """
        geschaeftsreisen = self.getGeschaeftsreisen( master_name, jahr )
        return self._getGeschaeftsreisekosten( geschaeftsreisen )

    def getGeschaeftsreisekostenParts( self, reise:XGeschaeftsreise ) -> Dict:
        """
        Ermittelt die Kosten für eine Geschäftsreise.
        :param reise:
        :return: Die Bestandteile der Reisekosten in Form eines Dictionary mit den Keys vpfl, uebn, km
        """
        jahr = datehelper.getDateParts( reise.von )[0]
        pausch: XPauschale = self.getPauschale( jahr )
        dauer = datehelper.getNumberOfDays2( reise.von, reise.bis, jahr )
        if dauer == 1:
            f = 1
        else:
            f = 2
        vpflkosten = pausch.vpfl_8 * f  # Hin- u. Rückfahrt
        if dauer > 2:
            ganzetage = dauer - 2
            vpflkosten += (ganzetage * pausch.vpfl_24)
        dic = dict()
        dic["vpfl"] = vpflkosten * -1
        dic["uebn"] = reise.uebernacht_kosten
        dic["km"] = reise.km * pausch.km * -1
        return dic

    def getGeschaeftsreisekosten2( self, reise:XGeschaeftsreise ) -> float:
        """
        Ermittelt die Kosten für eine Geschäftsreise.
        ACHTUNG: Hotelkosten sind echte Abflüsse (im Ggs zum km-Geld und der Vpfl.-Pauschale).
                 Der in die Tabelle einaus eingetragene Betrag setzt sich also zusammen aus den (tatsächlichen)
                 Hotelkosten und den kalkulatorischen Fahrt- und Verpflegungskosten.
        Methode wird auch von der AnlageV_Base_Logic und der AnlageV_Preview_Logic verwendet.
        (Betrifft die alte Version des ICC. Ob das mit v2 auch noch so sein wird, ist derzeit (März 2023) offen.)
        :param reise:
        :return:
        """
        dic = self.getGeschaeftsreisekostenParts( reise )
        summe = dic["vpfl"] + dic["uebn"] + dic["km"]
        return summe

    def _getGeschaeftsreisekosten( self, geschaeftsreisen: List[XGeschaeftsreise] ) -> float:
        """
        Berechnet die Summe der Geschäftsreisekosten für die in <geschaeftsreisen> übergebenen Geschäftsreisen.
        Reisekosten setzen sich zusammen aus km-Geld, Übernachtungskosten, Verpfl.pauschale
        :param geschaeftsreisen:
        :return:
        """
        summe = 0.0
        for g in geschaeftsreisen:
            summe += self.getGeschaeftsreisekosten2( g )
        return summe

    def getMasterNamen( self ) -> Iterable[str]:
        masterlist = self._data.getMasterobjekte()
        masternameslist = [x.master_name for x in masterlist]
        return masternameslist

    def _createXeinausFromXgeschaeftsreise( self, x:XGeschaeftsreise ) -> XEinAus:
        y, m, d = datehelper.getDateParts( x.von )
        monat = iccMonthShortNames[m-1]
        xea = XEinAus()
        xea.reise_id = x.reise_id
        xea.master_name = x.master_name
        xea.debi_kredi = x.uebernachtung if x.uebernachtung else "ohne"
        xea.leistung = "Geschaeftsreise"
        xea.jahr = x.jahr
        xea.monat = monat
        dic = self.getGeschaeftsreisekostenParts( x )
        xea.betrag = dic["vpfl"] + dic["uebn"] + dic["km"]
        #xea.betrag = self.getGeschaeftsreisekosten2( x )
        xea.ea_art = EinAusArt.SONSTIGE_KOSTEN.display
        xea.verteilt_auf = None
        xea.umlegbar = Umlegbar.NEIN.value
        xea.buchungstext = "Geschäftsreisekosten bestehen aus\n" \
                           "tatsächlich abgeflossenen Hotelkosten (%.2f €) und\n" \
                           "kalkulatorischen Fahrt- (%.2f €) und Verpflegungskosten (%.2f €)." % \
                           (dic["uebn"], dic["km"], dic["vpfl"])
        return xea

    def insertGeschaeftsreise( self, x:XGeschaeftsreise ) -> XEinAus:
        self._data.insertGeschaeftsreise( x )
        x.reise_id = self._data.getMaxId( "geschaeftsreise", "reise_id" )
        # in die Tabelle einaus einfügen lassen:
        xea:XEinAus = self._createXeinausFromXgeschaeftsreise( x )
        ea_logic = EinAusLogic()
        msg = ea_logic.trySaveZahlung( xea )
        if msg:
            raise Exception( "GeschaeftsreiseLogic.insertGeschaeftsreise().\n"
                             "Unerwartete Fehlermeldung aus EinAusLogic.trySaveZahlung() erhalten:\n'%s'\n"
                             "\nZu speicherndes XEinAus-Objekt:\n%s" % (msg, xea.toString()) )
        self._data.commit()
        return xea

    def updateGeschaeftsreise( self, x:XGeschaeftsreise ) -> (XEinAus, float):
        """
        Macht mit den Daten in <x> einen Update auf den entsprechenden Satz in Tabelle <geschaeftsreise>.
        Wandelt die Daten in <x> um in eine XEinAus-Objekt und macht einen Update auf den entsprechenden Satz
        in Tabelle <einaus>
        :param x:
        :return: Den aktualisierten Satz der Tabelle <einaus> in einem XEinAus-Objekt sowie das Delta des alten
        und neuen Betrags in Tabelle <einaus>. Dieses Delta kann 0 sein.
        """
        self._data.updateGeschaeftsreise( x )
        ea_logic = EinAusLogic()
        xea_alt = ea_logic.getZahlungen( EinAusArt.SONSTIGE_KOSTEN.display, x.jahr, "and reise_id=%d" % x.reise_id )[0]
        ea_id = xea_alt.ea_id
        xea_neu = self._createXeinausFromXgeschaeftsreise( x )
        xea_neu.ea_id = ea_id
        if xea_neu.master_name != xea_alt.master_name \
        or xea_neu.jahr != xea_alt.jahr \
        or xea_neu.monat != xea_alt.monat \
        or xea_neu.debi_kredi != xea_alt.debi_kredi \
        or xea_neu.betrag != xea_alt.betrag:
            msg = ea_logic.trySaveZahlung( xea_neu )
            if msg:
                raise Exception( "GeschaeftsreiseLogic.updateGeschaeftsreise().\n"
                                 "Unerwartete Fehlermeldung aus EinAusLogic.trySaveZahlung() erhalten:\n'%s'\n"
                                 "\nZu speicherndes XEinAus-Objekt:\n%s" % (msg, xea_neu.toString()) )
        self._data.commit()
        delta = round( xea_neu.betrag - xea_alt.betrag, 2)
        return xea_neu, delta

    def deleteGeschaeftsreise( self, reise_id:int ) -> Dict:
        """
        Löscht die Geschäftsreise mit id <reise_id> aus den Tabellen <geschaeftsreise> und <einaus>
        :param reise_id:
        :return: ein Dictionary mit den Keys ea_id und betrag (aus <einaus> gelöschter Betrag)
        """
        self._data.deleteGeschaeftsreise( reise_id )
        ea_logic = EinAusLogic()
        dic = ea_logic.getEaIdAndBetragByForeignKey( "reise_id", reise_id )
        ea_logic.deleteZahlung( dic["ea_id"] )
        self._data.commit()
        return dic

########################################################################################

def test():
    logic = GeschaeftsreiseLogic()
    reisekosten = logic.getSummeGeschaeftsreisekosten( 2021 )
    print( reisekosten )