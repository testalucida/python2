import copy
from typing import Iterable, List

import datehelper
from base.basetablemodel import BaseTableModel
from v2.icc.interfaces import XSollMiete, XMietverhaeltnis
from v2.sollmiete.sollmietedata import SollmieteData


class SollMieteTableModel( BaseTableModel ):
    def __init__( self, sollHausgeldList:List[XSollMiete] ):
        BaseTableModel.__init__( self, sollHausgeldList )
        self.setKeyHeaderMappings2(
            ("mv_id", "mobj_id", "von", "bis", "netto", "nkv", "brutto", "bemerkung" ),
            ("Mieter", "Wohnung", "von", "bis", "Netto", "NKV", "Brutto", "Bemerkung" )
        )

#############################################################################
class SollmieteLogic:
    """
    Stellt die Funktionen zur Selektion, Neuanlage, Änderung und Beendigung von Sollmiete-Intervallen bereit.
    (Jeder Satz in der Tabelle sollmiete stellt ein Gültigkeits-Intervall dar.)
    **BEACHTE***
    Die Methoden dieser Klasse machen keine Commits und keine Exception-Behandlung!!
    Dies muss in den übergeordneten UCC-Klassen geschehen.
    ************
    """
    def __init__( self ):
        self._db:SollmieteData = SollmieteData()

    def getAlleSollMieten( self ) -> SollMieteTableModel:
        sollmieten:List[XSollMiete] = self._db.getAlleSollMieten()
        tm = SollMieteTableModel( sollmieten )
        return tm

    def getFolgeSollmiete( self, currentX:XSollMiete ) -> XSollMiete:
        """
        Liefert zur aktuellen Sollmiete currentX einen Nachfolger.
        Ist dieser Nachfolger bereits in der DB angelegt (max. 1 Nachfolger darf vorhanden sein), wird dieser geliefert.
        Gibt es noch keinen Nachfolger, wird ein neues XSollMiete-Objekt instanziert und geliefert.
        :param currentX: aktuelle Sollmiete
        :return:
        """
        x:XSollMiete = self.getLetzteSollmiete( currentX.mv_id )
        if x.sm_id == currentX.sm_id:
            # es gibt noch kein Folge-Intervall, deshalb erzeugen wir eines (ohne zu speichern)
            folgeX = copy.copy( currentX )
            folgeX.sm_id = 0
            folgeX.von = datehelper.getFirstOfNextMonth() if not currentX.bis \
                         else datehelper.getFirstOfFollowingMonth( currentX.bis )
            folgeX.bis = ""
            return folgeX
        else:
            return x


    # def getLetzteSollmiete2( self, mv_id:str, mobj_id:str ) -> XSollMiete or None:
    #     """
    #     Liefert die letzte eingetragene Sollmiete, die auch in der Zukunft liegen kann.
    #     Diese Methode ist der Methode getLetzteSollmiete() vorzuziehen, da durch die zusätzliche <mobj_id>
    #     Eindeutigkeit gewährleistet ist.
    #     :param mv_id:  Mieter
    #     :param mobj_id:  Mietobjekt
    #     :return:
    #     """
    #     return self._db.getLetzteSollmiete2( mv_id, mobj_id )

    def getLetzteSollmiete( self, mv_id: str ) -> XSollMiete or None:
        """
        Liefert die letzte eingetragene Sollmiete, die auch in der Zukunft liegen kann.
        **ACHTUNG** Diese Methode kann falsche Ergebnisse liefern, wenn ein Mieter von einer Wohnung
                    in eine andere gezogen ist.
                    Es fehlt hier meines Erachtens der Aufrufparameter <mobj_id>, um Eindeutigkeit zu erzielen.
                    In der Tabelle sollmiete gibt es aber leider keine mobj_id. Das ist ein Modellierungsfehler,
                    der erst behoben werden muss.
        :param mv_id:
        :return:
        """
        return self._db.getLetzteSollmiete( mv_id )

    def getAktuelleSollmiete( self, mv_id: str ) -> XSollMiete or None:
        """
        Liefert die aktuelle Sollmiete, die auch inaktiv sein kann.
        Sie kann NICHT in der Zukunft liegen.
        :param mv_id:
        :return:
        """
        return self._db.getAktuelleSollmiete( mv_id )

    def getSollmieteAm( self, mv_id:str, jahr:int, monthNumber:int ) -> XSollMiete or None:
        """
        :param mv_id:
        :param jahr:
        :param monthNumber: 1 -> Januar,..., 12 -> Dezember
        :return:
        """
        return self._db.getSollmieteAm( mv_id, jahr, monthNumber )

    def validate( self, xsm:XSollMiete ) -> str:
        if not xsm.mv_id:
            return "mv_id fehlt."
        if not xsm.von:
            return "Beginn des Sollmietenzeitraums fehlt."
        if not datehelper.isValidIsoDatestring( xsm.von ):
            return "Beginn des Sollmietenzeitraums hat kein gültiges Datumsformat. Muss 'yyyy-mm-dd' sein."
        if xsm.von[8:] != "01":
            return "Der Sollmietenzeitraums muss am Ersten eines Monats beginnen."
        if xsm.bis:
            if not datehelper.isValidIsoDatestring( xsm.bis ):
                return "Ende des Sollmietenzeitraums nicht im Format 'yyyy-mm-dd' angegeben."
            monat = xsm.bis[5:7]
            monatsletzter = datehelper.getNumberOfDays( int(monat) ) # z.B. 31
            if not xsm.bis[8:] == str(monatsletzter):
                return "Das Ende eines Sollmietenzeitraums muss der Monatsletzte sein."
        # prüfen, ob das MV bereits gekündigt ist. Wenn ja, darf das xsm.bis nicht größer sein als das Künd.datum
        xmv = self._getAktuellesMietverhaeltnis( xsm.mv_id )
        if xmv:
            if xmv.bis and ( not xsm.bis or xsm.bis > xmv.bis ):
                return "Das Ende-Datum des Sollmiete-Intervalls ('%s') darf nicht weiter in der Zukunft liegen " \
                       "als das Kündigungsdatum ('%s') " % ( xsm.bis, xmv.bis )
        if not xsm.netto:
            return "Nettomiete fehlt."
        if not xsm.nkv:
            return "Nebenkostenvorauszahlung fehlt."

    def updateSollmieteBemerkung( self, sm_id:int, bemerkung:str ):
        """
        Macht einen Update auf das Bemerkungsfeld der Sollmiete <sm_id>
        :param sm_id: ID der Sollmiete
        :param bemerkung: ggf. geänderte Bemerkung
        :return:
        """
        xsm = self._db.getSollmiete( sm_id )
        if xsm.bemerkung != bemerkung:
            xsm.bemerkung = bemerkung
            self._db.updateSollmiete( xsm )
            self._db.commit()

    def saveFolgeSollmiete( self, folgeX:XSollMiete ) -> str:
        """
        Prüft, ob ein Insert oder Update erfolgen muss und führt ihn entsprechend aus.
        Führt eine Validierung durch.
        Wirft eine Exception, wenn es einen Fehler beim Validieren oder Speichern gibt.
        :param folgeX:
        :return: das Ende-Datum, das in das aktuelle Sollmiete-Intervall eingetragen wurde.
        """
        msg = self.validate( folgeX )
        if msg:
            raise Exception( "SollmieteLogic.saveFolgemiete():\nFehler bei der Validierung:\n" + msg )
        # Das Vorgänger-Soll holen und das bis-Datum anpassen
        sollHistorie:List[XSollMiete] = self._db.getSollmieteHistorie( folgeX.mv_id )
        if len( sollHistorie ) < 1:
            raise Exception( "SollmieteLogic.saveFolgeMiete():\n"
                             "Für '%s' keine Sollmiete in der DB gefunden." % folgeX.mv_id )
        if len( sollHistorie ) < 2 and folgeX.sm_id > 0:
            if sollHistorie[0].sm_id == folgeX.sm_id:
                raise Exception( "SollmieteLogic.saveFolgeMiete():\n"
                                 "Die Historie enthält für '%s' nur 1 Satz, und das ist der Folgesatz.\n"
                                 ">>> sm_id = %d <<<\n"
                                 "Wurde diese Methode fälschlicherweise aufgerufen?" % (folgeX.mv_id, folgeX.sm_id ) )
            else:
                raise  Exception( "SollmieteLogic.saveFolgeMiete():\n"
                                 "Die Historie enthält für '%s' nur 1 Satz, das ist aber nicht der Folgesatz.\n"
                                 ">>> sm_id = %d <<<\n"
                                 "Fehlerursache ist unklar." )
        # currentX bestimmen
        if folgeX.sm_id <= 0:
            # der Folgesatz ist noch nicht in der DB gespeichert
            currentX = sollHistorie[0]
        else:
            # der Folgesatz war schon gespeichert
            currentX = sollHistorie[1]

        #prüfen, ob folgeX.von GT currentX.von
        if not folgeX.von > currentX.von:
            raise Exception( "SollmieteLogic.saveFolgeMiete():\n"
                             "Der Beginn des aktuellen Zeitraums muss kleiner sein als der des Folgezeitraums." )
        # prüfen, ob das bis-Datum des aktuellen Satzes leer ist. Wenn ja, muss es zum von-Datum des Folgesatzes passen.
        if currentX.bis:
            if not folgeX.von > currentX.bis:
                raise Exception( "SollmieteLogic.saveFolgeMiete():\n"
                                 "Das Ende der aktuellen Sollmiete ('%s') darf nicht größer sein "
                                 "als der Beginn der Folge-Sollmiete ('%s').\n"
                                 ">>> sm_id aktuell = %d -- sm_id folge = %d <<<"
                                 % ( currentX.bis, folgeX.von, currentX.sm_id, folgeX.sm_id ) )
        # jetzt ist alles okay, den Folgesatz einfügen bzw. ändern, dann das Bis-Datum des aktuellen Satzes ändern.
        if folgeX.sm_id < 1:
            self._db.insertSollmiete( folgeX )
        else:
            self._db.updateSollmiete( folgeX )
        # das bis-Datum auf 1 Tag weniger als das von-Datum des Folge-satzes setzen
        currentX.bis = datehelper.addDaysToIsoString( folgeX.von, -1 )
        self._db.updateSollmiete( currentX )
        self._db.commit()
        return currentX.bis

    def createSollmiete( self, xsm:XSollMiete ):
        """
        Legt eine Sollmiete an.
        Wird im Zuge der Neuanlage eines Mietverhältnisses aufgerufen (MietverhaeltnisLogic.createMietverhaeltnis())
        :param xsm:
        :return:
        """
        msg = self.validate( xsm )
        if msg:
            raise Exception( "Anlage Sollmiete fehlgeschlagen:\n%s" % msg )
        self._db.insertSollmiete( xsm )
        sm_id = self._db.getMaxId( "sollmiete", "sm_id" )
        xsm.sm_id = sm_id

    def deleteFolgeSollmiete( self, x:XSollMiete ) -> str:
        """
        Löscht (pyhsisch) ein Sollmiete-Intervall, das in der Zukunft beginnt.
        (Davon darf es nur eines geben.)
        Passt danach das Ende-Datum <bis> des aktuellen Intervalls an das Mietverhaeltnis-Bis-Datum an.
        :param x: das zu löschende Sollmiete-Folge-Intervall
        :return: das Datum, auf das das Bis-Datum des aktuellen Sollmiete-Intervalls zurückgesetzt wurde. (=Bis-Datum
        des Mietverhältnisses)
        """
        if x.von < datehelper.getTodayAsIsoString():
            raise Exception( "Das Sollmiete-Intervall mit sm_id %d hat bereits am %s begonnen\n"
                             "und kann daher nicht gelöscht werden." % (x.sm_id, x.von) )
        self._db.deleteSollmiete( x.sm_id )
        # das Vorgänger-Intervall holen:
        xsm:XSollMiete = self._db.getLetzteSollmiete( x.mv_id )
        if not xsm:
            raise Exception( "SollmieteLogic.deleteFolgeSollmiete:\n"
                             "Es gibt kein aktuelles Sollmiete-Intervall für Mieter '%s'." % x.mv_id )

        xmv = self._getAktuellesMietverhaeltnis( x.mv_id )
        if not xmv:
            raise Exception( "SollmieteLogic.deleteFolgeSollmiete:\n"
                             "Es gibt kein aktuelles Mietverhältnis für Mieter '%s'." % x.mv_id )
        xsm.bis = xmv.bis
        self._db.updateSollmiete( xsm )
        self._db.commit()
        return xsm.bis

    @staticmethod
    def _getAktuellesMietverhaeltnis( mv_id:str ) -> XMietverhaeltnis or None:
        from v2.mietverhaeltnis.mietverhaeltnislogic import MietverhaeltnisLogic  # muss hier importiert werden
        # wegen Gefahr des Zirkelbezugs
        mvlogic = MietverhaeltnisLogic()
        xmv:XMietverhaeltnis = mvlogic.getAktuellesMietverhaeltnis( mv_id )
        # xmv kann None sein!
        return xmv

    def handleSollmieteBeiMvKuendigung( self, mv_id:str, kuenddatum:str ):
        """
        Wird aufgerufen von MietverhaeltnisLogic.kuendigeMietverhaeltnis().
        Beendet das aktuelle Sollmiete-Intervall von Mieter mv_id zu <kuenddatum>
        und löscht (physisch) ein ggf. vorhandenes  Folge-Sollmiete-Intervall aus der Tabelle <sollmiete>.
        :param mv_id: Mieter
        :param kuenddatum: KÜndigungsdatum des Mietvertrags; ACHTUNG: kann bei Rücknahme Kündigung auch LEER sein!!
        :return:
        """
        xsmlist:List[XSollMiete] = self._db.getSollmieteHistorie( mv_id )
        if len( xsmlist ) < 1:
            raise Exception( "SollmieteLogic.handleSollmieteBeiMvKuendigung():\n"
                             "Für Mieter '%s' kein aktuelles Sollmieten-Intervall gefunden." % mv_id )
        for xsm in xsmlist:
            if kuenddatum and xsm.von > kuenddatum:
                # Folge-Intervall:löschen
                self._db.deleteSollmiete( xsm.sm_id )
            else:
                self._db.terminateSollmiete( xsm.sm_id, kuenddatum )
                break # wir wollen nur das aktuelle Intervall beenden, nicht die historischen


def test():
    x = XSollMiete()
    x.mv_id = "lukas_franz"
    x.von = "2023-05-01"
    x.netto = 990.50
    x.nkv = 300
    logic = SollmieteLogic()
    msg = logic.validate( x )
    logic.saveFolgeSollmiete( x )
    print( msg )
