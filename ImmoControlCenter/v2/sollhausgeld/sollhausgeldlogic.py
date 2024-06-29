import copy
from typing import List

import datehelper
from base.basetablemodel import BaseTableModel
from v2.icc.constants import iccMonthShortNames
from v2.icc.icclogic import IccLogic
from v2.icc.interfaces import XSollHausgeld
from v2.sollhausgeld.sollhausgelddata import SollHausgeldData


class SollHausgeldTableModel( BaseTableModel ):
    def __init__( self, sollHausgeldList:List[XSollHausgeld] ):
        BaseTableModel.__init__( self, sollHausgeldList )
        self.setKeyHeaderMappings2(
            ("mobj_id", "vw_id", "weg_name", "von", "bis", "netto", "ruezufue", "brutto", "bemerkung" ),
            ("Wohnung", "Verwalter", "WEG", "von", "bis", "Netto", "RüZuFü", "Brutto", "Bemerkung" )
        )

##################################################################################
class SollHausgeldLogic( IccLogic ):
    def __init__( self ):
        IccLogic.__init__( self )
        self._data = SollHausgeldData()

    def getAllSollHausgelder( self ) -> SollHausgeldTableModel:
        sollhglist = self._data.getAllSollHausgelder()
        tm = SollHausgeldTableModel( sollhglist )
        return tm

    def getCurrentSollHausgeld( self, mobj_id:str ) -> XSollHausgeld:
        x:XSollHausgeld = self._data.getCurrentSollHausgeld( mobj_id )
        return x

    def getSollHausgeldAm( self, mobj_id:str, jahr: int, monthNumber: int ) -> XSollHausgeld or None:
        """
        :param mobj_id:
        :param jahr:
        :param monthNumber: 1 -> Januar,..., 12 -> Dezember
        :return:
        """
        return self._data.getSollHausgeldAm( mobj_id, jahr, monthNumber )

    def getFolgeSollHausgeld( self, currentX: XSollHausgeld ) -> XSollHausgeld:
        """
        Liefert zum aktuellen Soll-Hausgeld currentX einen Nachfolger.
        Ist dieser Nachfolger bereits in der DB angelegt (max. 1 Nachfolger darf vorhanden sein), wird dieser geliefert.
        Gibt es noch keinen Nachfolger, wird ein neues XSollHausgeld-Objekt instanziert und geliefert.
        :param currentX: aktuelles Soll-Hausgeld
        :return:
        """
        x: XSollHausgeld = self.getLetztesSollHausgeld( currentX.mobj_id )
        if x.shg_id == currentX.shg_id:
            # es gibt noch kein Folge-Intervall, deshalb erzeugen wir eines (ohne zu speichern)
            folgeX = copy.copy( currentX )
            folgeX.shg_id = 0
            folgeX.von = datehelper.getFirstOfNextMonth() if not currentX.bis \
                else datehelper.getFirstOfFollowingMonth( currentX.bis )
            folgeX.bis = ""
            return folgeX
        else:
            return x

    def getLetztesSollHausgeld( self, mobj_id: str ) -> XSollHausgeld or None:
        """
        Liefert das letzte eingetragene Soll-Hausgeld, das auch in der Zukunft liegen kann.
        :param mobj_id:
        :return:
        """
        return self._data.getLetztesSollHausgeld( mobj_id )

    def getSollHausgeldzahlungVonBis( self, mobj_id:str, jahr:int ) -> (str, str):
        """
        Liefert den ersten und den letzten Monat, in denen im Jahr <jahr> Hausgeld zu entrichten war.
        :param mobj_id: zu beauskunftendes Mietobjekt
        :param jahr: zu beauskunftendes Jahr
        :return: Monate von und bis im Format "jan", ... "dez"
        """
        li = self._data.getSollHausgeldHistorie( mobj_id, "asc", jahr )
        # in l befinden sich nur XHausgeld-Objekte, die irgendwann in 2022 gültig waren
        firstDayOfYear = "%d-01-01" % jahr
        lastDayOfYear = "%d-12-31" % jahr
        vonMon = "99"
        bisMon = "00"
        for s in li:
            if s.von < firstDayOfYear:  # <von> LT 1.1.<jahr>, also muss <bis> in <jahr> gültig (gewesen) sein, sonst hätten
                # wir diesen Satz gar nicht selektiert. Also ist dieser Satz ab Januar gültig.
                vonMon = "01"
            else:  # s.von beginnt in <jahr>, sonst hätten wir diesen Satz nicht selektiert
                von = s.von[5:7]
                if von < vonMon:
                    vonMon = von
            if not s.bis or s.bis > lastDayOfYear:  # <bis> GT 31.12.<jahr>, also muss <von> in <jahr> (oder früher) liegen,
                # sonst hätten wir diesen Satz nicht selektiert.
                # Also ist dieser Satz im Dezember gültig.
                bisMon = "12"
            else:
                bis = s.bis[5:7]
                if bis > bisMon:
                    bisMon = bis
        if vonMon == "99" and bisMon == "00":
            # Hausgeld geht im Jahr <jahr> schon komplett an den Käufer von <mobj_id>
            return "", ""
        vonMonShort = iccMonthShortNames[int(vonMon)-1]
        bisMonShort = iccMonthShortNames[int(bisMon)-1]
        return vonMonShort, bisMonShort

    def validate( self, x:XSollHausgeld ) -> str:
        if not x.mobj_id:
            return "Mietobjekt-ID fehlt."
        if not x.von:
            return "Beginn des Sollhausgeldzeitraums fehlt."
        if not datehelper.isValidIsoDatestring( x.von ):
            return "Beginn des Sollhausgeldzeitraums hat kein gültiges Datumsformat. Muss 'yyyy-mm-dd' sein."
        if x.von[8:] != "01":
            return "Der Sollhausgeldzeitraum muss am Ersten eines Monats beginnen."
        if x.bis:
            if not datehelper.isValidIsoDatestring( x.bis ):
                return "Ende des Sollhausgeldzeitraums nicht im Format 'yyyy-mm-dd' angegeben."
            monat = x.bis[5:7]
            monatsletzter = datehelper.getNumberOfDays( int(monat) ) # z.B. 31
            if not x.bis[8:] == str( monatsletzter ):
                return "Das Ende eines Sollhausgeldzeitraums muss der Monatsletzte sein."
        if not x.netto:
            return "Netto-Hausgeld fehlt."

    def saveFolgeHausgeld( self, folgeX:XSollHausgeld ) -> str:
        """
        Prüft, ob ein Insert oder Update erfolgen muss und führt ihn entsprechend aus.
        Führt eine Validierung durch.
        Wirft eine Exception, wenn es einen Fehler beim Validieren oder Speichern gibt.
        :param folgeX:
        :return: das Ende-Datum, das in das aktuelle Soll-Hausgeld-Intervall eingetragen wurde.
        """
        msg = self.validate( folgeX )
        if msg:
            raise Exception( "SollHausgeldLogic.saveFolgeHausgeld():\nFehler bei der Validierung:\n" + msg )
        # Das Vorgänger-Soll holen und das bis-Datum anpassen
        sollHistorie:List[XSollHausgeld] = self._data.getSollHausgeldHistorie( folgeX.mobj_id )
        if len( sollHistorie ) < 1:
            raise Exception( "SollHausgeldLogic.saveFolgeHausgeld():\n"
                             "Für '%s' kein Soll-Hausgeld in der DB gefunden." % folgeX.mobj_id )
        if len( sollHistorie ) < 2 and folgeX.shg_id > 0:
            if sollHistorie[0].shg_id == folgeX.shg_id:
                raise Exception( "SollHausgeldLogic.saveFolgeHausgeld():\n"
                                 "Die Historie enthält für '%s' nur 1 Satz, und das ist der Folgesatz.\n"
                                 ">>> shg_id = %d <<<\n"
                                 "Wurde diese Methode fälschlicherweise aufgerufen?" % (folgeX.mobj_id, folgeX.shg_id ) )
            else:
                raise  Exception( "SollHausgeldLogic.saveFolgeHausgeld():\n"
                                 "Die Historie enthält für '%s' nur 1 Satz, das ist aber nicht der Folgesatz.\n"
                                 ">>> sm_id = %d <<<\n"
                                 "Fehlerursache ist unklar." )
        # currentX bestimmen
        if folgeX.shg_id <= 0:
            # der Folgesatz ist noch nicht in der DB gespeichert
            currentX = sollHistorie[0]
        else:
            # der Folgesatz war schon gespeichert
            currentX = sollHistorie[1]

        #prüfen, ob folgeX.von GT currentX.von
        if not folgeX.von > currentX.von:
            raise Exception( "SollHausgeldLogic.saveFolgeHausgeld():\n"
                             "Der Beginn des aktuellen Zeitraums muss kleiner sein als der des Folgezeitraums." )
        # prüfen, ob das bis-Datum des aktuellen Satzes leer ist. Wenn ja, muss es zum von-Datum des Folgesatzes passen.
        if currentX.bis:
            if not folgeX.von > currentX.bis:
                raise Exception( "SollHausgeldLogic.saveFolgeHausgeld():\n"
                                 "Das Ende des aktuellen SollHausgelds ('%s') darf nicht größer sein "
                                 "als der Beginn des Folge-SollHausgelds ('%s').\n"
                                 ">>> shg_id aktuell = %d -- shg_id folge = %d <<<"
                                 % ( currentX.bis, folgeX.von, currentX.shg_id, folgeX.shg_id ) )
        # jetzt ist alles okay, den Folgesatz einfügen bzw. ändern, dann das Bis-Datum des aktuellen Satzes ändern.
        if folgeX.shg_id < 1:
            self._data.insertSollHausgeld( folgeX )
        else:
            self._data.updateSollHausgeld( folgeX )
        # das bis-Datum auf 1 Tag weniger als das von-Datum des Folge-satzes setzen
        currentX.bis = datehelper.addDaysToIsoString( folgeX.von, -1 )
        self._data.updateSollHausgeld( currentX )
        self._data.commit()
        return currentX.bis

    def updateSollHausgeldBemerkung( self, shg_id:int, modBemerkung:str ):
        x:XSollHausgeld = self._data.getSollHausgeld( shg_id )
        if x.bemerkung != modBemerkung:
            x.bemerkung = modBemerkung
            self._data.updateSollHausgeld( x )

    def deleteFolgeSollHausgeld( self, x:XSollHausgeld ) -> str:
        """
        Löscht (pyhsisch) ein Soll-Hausgeld-Intervall, das in der Zukunft beginnt.
        (Davon darf es nur eines geben.)
        Passt danach das Ende-Datum <bis> des aktuellen Intervalls an das Verwaltung-Bis-Datum an.
        :param x: das zu löschende Soll-Hausgeld-Folge-Intervall
        :return: das Datum, auf das das Bis-Datum des aktuellen Soll-Hausgeld-Intervalls zurückgesetzt wurde.
        (Bis-Datum der Verwaltung)
        """
        if x.von < datehelper.getTodayAsIsoString():
            raise Exception( "Das Soll-Hausgeld-Intervall mit shg_id %d hat bereits am %s begonnen\n"
                             "und kann daher nicht gelöscht werden." % (x.shg_id, x.von) )
        self._data.deleteSollHausgeld( x.shg_id )
        # das Vorgänger-Intervall holen:
        shg:XSollHausgeld = self._data.getLetztesSollHausgeld( x.mobj_id )
        if not shg:
            raise Exception( "SollHausgeldLogic.deleteFolgeSollHausgeld:\n"
                             "Es gibt kein aktuelles Soll-Hausgeld-Intervall für Wohnung '%s'." % x.mobj_id )

        vwg = self._data.getVerwaltung( shg.vwg_id )
        if not vwg:
            raise Exception( "SollmieteLogic.deleteFolgeSollHausgeld:\n"
                             "Es gibt keine aktuelle Verwaltung für Wohnung '%s'." % x.mobj_id )
        shg.bis = vwg.bis
        self._data.updateSollHausgeld( shg )
        self._data.commit()
        return shg.bis

###################  TEST   TEST   TEST   ##################
def test():
    logic = SollHausgeldLogic()
    x = logic.getCurrentSollHausgeld( "charlotte" )
    x.print()