from typing import List, Dict

import datehelper
from v2.einaus.einausdata import EinAusData
from v2.icc.constants import iccMonthShortNames, EinAusArt, Umlegbar
from v2.icc.icclogic import IccTableModel, IccLogic
from v2.icc.interfaces import XEinAus, XSummen, XLetzteBuchung


#################   EinAusTableModel   ############################
class EinAusTableModel( IccTableModel):
    def __init__( self, rowlist:List[XEinAus], jahr ):
        IccTableModel.__init__( self, rowlist, jahr )
        self.setKeyHeaderMappings2(
            ("master_name", "mobj_id", "debi_kredi", "leistung", "buchungsdatum", "jahr", "monat", "ea_art", "verteilt_auf",
             "betrag", "buchungstext", "write_time" ),
            ("Haus", "Whg", "Debitor/\nKreditor", "Leistung", "Buch.datum", "steuerl.\nJahr", "Monat", "Art", "vJ",
             "Betrag", "Text", "eingetragen")
        )
        self._colBuchungsdatum = 4
        self._colWriteTime = 11

    def getBuchungsdatumColumnIdx( self ) -> int:
        return self._colBuchungsdatum

    def getWriteTimeColumnIdx( self ) -> int:
        return self._colWriteTime

#################   EinAusLogic   #################################
class EinAusLogic(IccLogic):
    """
    Beinhaltet die Logik, die für Operationen auf die Tabelle einaus notwendig ist.
    Verwendet EinAusData
    Wird verwendet z.B. von MtlEinAusLogic
    """
    def __init__( self ):
        IccLogic.__init__( self )
        self._einausData = EinAusData()

    def getZahlungenModel( self, jahr:int ) -> EinAusTableModel:
        """
        Liefert alle Ein- und Auszahlungen im Jahr <jahr> in Form eines EinAusTableModel.
        :param jahr:
        :return:
        """
        l:List[XEinAus] = self._einausData.getEinAuszahlungenJahr( jahr )
        tm = EinAusTableModel( l, jahr )
        return tm

    def getZahlungenModel2( self, ea_art_display:str, jahr:int, monthIdx:int, mobj_id:str ) -> EinAusTableModel:
        month_sss = iccMonthShortNames[monthIdx]
        l: List[XEinAus] = self._einausData.getEinAuszahlungen2( ea_art_display, jahr, month_sss, mobj_id )
        tm = EinAusTableModel( l, jahr )
        return tm

    def getZahlungenModel3( self, ea_art_display, jahr:int, monthIdx:int, debikredi:str ) -> EinAusTableModel:
        """
        :param ea_art:
        :param jahr:
        :param monthIdx:
        :param debikredi:
        :return:
        """
        month_sss = iccMonthShortNames[monthIdx]
        l: List[XEinAus] = self._einausData.getEinAuszahlungen3( ea_art_display, jahr, month_sss, debikredi )
        tm = EinAusTableModel( l, jahr )
        return tm

    def getZahlungenModel4( self, sab_id:int, jahr:int, monthIdx:int ) -> EinAusTableModel:
        month_sss = iccMonthShortNames[monthIdx]
        l: List[XEinAus] = self._einausData.getEinAuszahlungen4( sab_id, jahr, month_sss )
        tm = EinAusTableModel( l, jahr )
        return tm

    def getZahlungenModel5( self, ea_art_display, jahr: int, monthIdx: int, debikredi:str, mobj_id:str ) -> EinAusTableModel:
        month_sss = iccMonthShortNames[monthIdx]
        l: List[XEinAus] = self._einausData.getEinAuszahlungen5( ea_art_display, jahr, month_sss, debikredi, mobj_id )
        tm = EinAusTableModel( l, jahr )
        return tm

    def getZahlungen( self, ea_art_display:str, jahr:int, additionalWhereClause="" ) -> List[XEinAus]:
        """
        Liefert alle Zahlungen der Art <ea_art> im Jahr <jahr>
        :param ea_art_display:
        :param jahr:
        :return:
        """
        return self._einausData.getEinAusZahlungen( ea_art_display, jahr, additionalWhereClause )

    def getZahlung( self, ea_id:int ) -> XEinAus:
        return self._einausData.getEinAusZahlung( ea_id )

    def getEaIdAndBetragByForeignKey( self, foreignKeyName:str, foreignKeyValue:int ) -> Dict:
        return self._einausData.getEaIdAndBetragByForeignKey( foreignKeyName, foreignKeyValue )

    def getEinnahmenSumme( self, jahr:int ) -> float:
        return self._einausData.getEinnahmenSumme( jahr )

    def getHGVAuszahlungenSumme( self, jahr:int ) -> float :
        return self._einausData.getHGVAuszahlungenSumme( jahr )

    def getAuszahlungenSummeOhneHGV( self, jahr:int ) -> float:
        return self._einausData.getAuszahlungenSummeOhneHGV( jahr )

    # def getEinzahlungen( self, jahr:int ) -> float:
    #     return self._einausData.getEinzahlungenSumme( jahr )

    def trySaveZahlung( self, x:XEinAus ) -> str:
        msg = self.validateZahlung( x )
        if msg:
            # Validierung nicht ok
            return msg
        else:
            # Validierung ok, jetzt speichern
            # ACHTUNG: eine Exception, die von _einausData geworfen wird, wird hier nicht abgefangen
            if x.buchungsdatum and not x.jahr:
                y, m, d = datehelper.getDateParts( x.buchungsdatum )
                x.jahr = y
                if not x.monat:
                    x.monat = iccMonthShortNames[m - 1]
                # if y == x.jahr:
                #     if not x.monat:
                #         x.monat = iccMonthShortNames[m-1]
                # else:
                #     if y > x.jahr:
                #         # Buchung soll für ein vergangenes Jahr gelten,
                #         # fest "Dezember" eingeben
                #         x.monat = iccMonthShortNames[11]
                #     else:
                #         # Buchung soll für ein zukünftiges Jahr gelten,
                #         # fest "Januar" eingeben
                #         x.monat = iccMonthShortNames[0]
                #     x.buchungstext += "\nMonat <%s> - in der Tabelle nicht angezeigt -  wurde algorithmisch ermittelt." % x.monat
            if x.ea_id <= 0:
                self._einausData.insertEinAusZahlung( x )
                self._einausData.commit()
            else:
                self._einausData.updateEinAusZahlung( x )
                self._einausData.commit()
            # todo: Zahlung in das TableModel "AlleZahlungen" eintragen

            return ""

    def validateZahlung( self, x:XEinAus ) -> str:
        """
        validiert die Daten einer Zahlung.
        :param x: XEinAus-Objekt, dessen Daten validiert werden sollen.
        :return: einen Leerstring, wenn alles in Ordnung ist, sonst eine Fehlermeldung.
        """
        if not x.debi_kredi:
            return "Kreditor oder Debitor fehlt."
        if not x.leistung:
            return "Leistung fehlt."
        if x.betrag == 0:
            return "Betrag fehlt."
        if x.ea_art == EinAusArt.REPARATUR.display:
            if not x.verteilt_auf:
                return "Bei Reparaturen muss angegeben werden, auf wieviele Jahre der Betrag verteilt werden soll."
        else:
            if x.verteilt_auf and x.verteilt_auf > 1:
                return "Verteilung auf Jahre darf nur bei Reparaturen angegeben werden."
        if not x.buchungsdatum:
            if not x.jahr:
                return "Wenn schon kein Buchungsdatum angegeben ist, muss wenigstens das Jahr versorgt sein."
            #return "Buchungsdatum fehlt."
        return ""

    def addZahlung( self, ea_art, mobj_id:str, debikredi:str,
                    jahr:int, monthIdx:int, value:float,
                    buchungsdatum:str=None, buchungstext:str=None ) -> XEinAus:
        """
        Methode, die für die monatl. Mietzahlungen und die Hausgeldvorauszahlungen aufgerufen wird
        :param ea_art:
        :param mobj_id:
        :param debikredi:
        :param jahr:
        :param monthIdx:
        :param value:
        :param buchungsdatum:
        :param buchungstext:
        :return:
        """
        if buchungsdatum:
            if not datehelper.isValidIsoDatestring( buchungsdatum ):
                raise ValueError( "EinAusLogic.addZahlung():\nBuchungsdatum '%s' ist nicht im ISO-Format." )
        x = XEinAus()
        x.master_name = self._einausData.getMastername( mobj_id )
        x.mobj_id = mobj_id
        x.ea_art = ea_art
        x.debi_kredi = debikredi
        x.jahr = jahr
        x.monat = iccMonthShortNames[monthIdx]
        x.betrag = value
        x.verteilt_auf = None
        x.buchungstext = buchungstext
        x.buchungsdatum = buchungsdatum
        # todo: Methode trySaveZahlung verwenden
        self._einausData.insertEinAusZahlung( x )
        return x

    def addZahlung2( self, ea_art_display, master_name:str,  mobj_id:str, debikredi:str, sab_id:int, leistung:str,
                    jahr:int, monthIdx:int, value:float, umlegbar:str=Umlegbar.NEIN.value,
                    buchungsdatum:str=None, buchungstext:str=None ) -> XEinAus:
        """
        Methode, die für die Abschlagszahlungen aufgerufen wird.
        :param ea_art_display:
        :param master_name:
        :param mobj_id:
        :param debikredi:
        :param sab_id:
        :param leistung:
        :param jahr:
        :param monthIdx:
        :param value:
        :param umlegbar:
        :param buchungsdatum:
        :param buchungstext:
        :return:
        """
        if buchungsdatum:
            if not datehelper.isValidIsoDatestring( buchungsdatum ):
                raise ValueError( "EinAusLogic.addZahlung():\nBuchungsdatum '%s' ist nicht im ISO-Format." )
        x = XEinAus()
        x.master_name = master_name
        x.mobj_id = mobj_id
        x.ea_art = ea_art_display
        x.debi_kredi = debikredi
        x.sab_id = sab_id
        x.leistung = leistung
        x.jahr = jahr
        x.monat = iccMonthShortNames[monthIdx]
        x.betrag = value
        x.verteilt_auf = None
        x.umlegbar = umlegbar
        x.buchungstext = buchungstext
        x.buchungsdatum = buchungsdatum
        # todo: Methode trySaveZahlung verwenden
        self._einausData.insertEinAusZahlung( x )
        return x

    def updateZahlung( self, x:XEinAus ) -> int:
        # todo: Methode trySaveZahlung verwenden
        rowsAffected = self._einausData.updateEinAusZahlung( x )
        return rowsAffected

    def deleteZahlung( self, ea_id:int ):
        self._einausData.deleteEinAusZahlung( ea_id )

    def deleteZahlungen( self, xlist:List[XEinAus] ):
        for x in xlist:
            self._einausData.deleteEinAusZahlung( x.ea_id )
        self._einausData.commit()

    def commit( self ):
        self._einausData.commit()

    def rollback( self ):
        self._einausData.rollback()