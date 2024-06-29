from typing import List

import datehelper
from v2.icc.icclogic import IccLogic
from v2.icc.interfaces import XMietverhaeltnis, XMieterwechsel, XMietverhaeltnisKurz, XSollMiete
from v2.mietverhaeltnis.mietverhaeltnisdata import MietverhaeltnisData
from v2.mtleinaus.mtleinauslogic import MtlEinAusLogic
from v2.sollmiete.sollmietelogic import SollmieteLogic


class MietverhaeltnisLogic( IccLogic ):
    """
    Stellt die Funktionen zur Selektion, Neuanlage, Änderung und Kündigung von Mietverhältnissen bereit.
    Außerdem eine Methode zur Ermittlung der Daten für einen Mieterwechsel.
    **BEACHTE***
    Die Methoden dieser Klasse machen keine Commits!!
    Diese müssen in den übergeordneten UCC-Klassen gemacht werden.
    ***
    Exceptions aus der Datenbank werden von den Methoden dieser Klasse aufgefangen und
    in Exceptions mit user-lesbaren Meldungen umgewandelt. (Work in progress ;-))
    ************
    """
    def __init__( self ):
        self._db:MietverhaeltnisData = MietverhaeltnisData()

    def getAktuellesMietverhaeltnis( self, mv_id:str ) -> XMietverhaeltnis:
        xmv:XMietverhaeltnis = self._db.getAktuellesMietverhaeltnis( mv_id )
        if xmv:
            xmv.name_vorname = self.getNachnameVornameFromMv_id( xmv.mv_id )
            return xmv
        else:
            return None

    def getAktuellesMietverhaeltnisByMietobjekt( self, mobj_id:str ) -> XMietverhaeltnis:
        mv_id = self._db.getAktuelleMV_IDzuMietobjekt( mobj_id )
        xmv = self._db.getAktuellesMietverhaeltnis( mv_id )
        if xmv:
            xmv.name_vorname = self.getNachnameVornameFromMv_id( xmv.mv_id )
        else:
            xmv = XMietverhaeltnis()
            xmv.name_vorname = "derzeit nicht vermietet"
        return xmv

    def getMietverhaeltnisListe( self, mobj_id:str ) -> List[XMietverhaeltnis]:
        xmvlist:List[XMietverhaeltnis] = self._db.getMietverhaeltnisse( mobj_id )
        smlogic = SollmieteLogic()
        for xmv in xmvlist:
            xsm = smlogic.getLetzteSollmiete( xmv.mv_id )
            if xsm:
                xmv.name_vorname = self.getNachnameVornameFromMv_id( xmv.mv_id )
                xmv.nettomiete = xsm.netto
                xmv.nkv = xsm.nkv
                xmv.bruttomiete = xsm.brutto
                xmv.sollmiete_bemerkung = xsm.bemerkung
        return xmvlist

    # def getMietverhaeltnisById( self, mv_id:str ) -> XMietverhaeltnis:
    #     """
    #     Liefert das Mietverhältnis mit der Mietverhältnis-ID <mv_id>
    #     :param id:
    #     :return:
    #     """
    #     return self._db.getMietverhaeltnisById( mv_id )

    def getKuendigungsdatumParts( self, mv_id:str ) -> (int, int, int) or None :
        dic = self._db.getAktuellesMietverhaeltnisVonBis( mv_id )
        bis = dic["bis"]
        if bis:
            return datehelper.getDateParts( bis )
        else:
            return None

    def getMieterwechseldaten( self, mobj_id:str ) -> XMieterwechsel:
        """
        Liefert die Daten, die für einen Mieterwechsel notwendig sind:
        Das aktuelle Mietverhältnis und ENTWEDER das schon für die Zukunft angelegte oder, wenn es
        kein solches gibt, ein leeres XMietverhaeltnis-Objekt.
        :param mobj_id:
        :return:
        """
        mv_id = self._db.getAktuelleMV_IDzuMietobjekt( mobj_id )
        xmv_akt: XMietverhaeltnis = self.getAktuellesMietverhaeltnis( mv_id )
        xmv_next: XMietverhaeltnis = self._db.getFutureMietverhaeltnis( mobj_id )
        if not xmv_next:
            xmv_next = XMietverhaeltnis()
            xmv_next.mobj_id = mobj_id
        return XMieterwechsel( xmv_akt, xmv_next )

    def getAktiveMietverhaeltnisseKurz( self, jahr:int ) -> List[XMietverhaeltnisKurz]:
        """
        Liefert alle Mietverhältnisse, die im Jahr <jahr> aktiv sind.
        Das sind auch die, die in <jahr> enden oder anfangen.
        :param jahr:
        :return:
        """
        return self._db.getAktiveMietverhaeltnisseKurz( jahr, orderby="mv_id" )

    @staticmethod
    def _create_mv_id( name:str, vorname:str ) -> str:
        def replaceUmlauteAndBlanks( s:str ) -> str:
            s = s.lower()
            s = s.replace( "ä", "ae" )
            s = s.replace( "ö", "oe" )
            s = s.replace( "ü", "ue" )
            s = s.replace( "ß", "ss" )
            s = s.replace( " ", "" )
            return s
        name = replaceUmlauteAndBlanks( name )
        vorname = replaceUmlauteAndBlanks( vorname )
        return name + "_" + vorname

    def createMietverhaeltnis( self, xmv:XMietverhaeltnis ):
        """
        Prüft die für die Neuanlage notwendigen Daten für das Mietverhältnis.
        (Die für die Anlage des Sollmieten-Satzes notwendigen Daten werden in sollmietelogic geprüft.)
        Macht einen Insert in Tabelle mietverhaeltnis und ruft sollmietelogic.createSollmiete() auf.
        :param xmv: die Daten des neuen MV
        :return:
        """
        msg = self.validateMietverhaeltnisDaten( xmv )
        if msg:
            raise Exception( "Daten des neuen Mietverhältnisses fehlerhaft:\n%s" % msg )
        xmv.mv_id = self._create_mv_id( xmv.name, xmv.vorname )

        #prüfen, ob schon ein Mietverhältnis mit dieser mv_id existiert:
        try:
            if self._db.existsAktivesOderZukuenftigesMietverhaeltnis( xmv.mv_id ):
                raise Exception( "Anlage Mietverhältnis fehlgeschlagen:\nEs existiert ein aktives Mietverhälntis für "
                                 "mv_id '%s'." % xmv.mv_id )
        except Exception as ex:
            raise Exception( "Fehler bei der Dublettenprüfung bei Anlage Mietverhältnis für '%s':\n'%s'"
                             % (xmv.mv_id, str(ex) ) )

        # MV-Satz anlegen:
        try:
            self._db.insertMietverhaeltnis( xmv )
            xmv.id = self._db.getMaxId( "mietverhaeltnis", "id" )
        except Exception as ex:
            raise Exception( "Bei der Anlage des Mietverhältnisses für '%s' ist der DB-Insert "
                             "in die Tabelle 'mietverhaeltnis' fehlgeschlagen:\n'%s'"
                             % (xmv.mv_id, str(ex) ) )

        # Sollmiete-Satz anlegen:
        xsm = XSollMiete()
        xsm.mv_id = xmv.mv_id
        xsm.von = xmv.von
        xsm.bis = xmv.bis
        xsm.netto = xmv.nettomiete
        xsm.nkv = xmv.nkv
        sml = SollmieteLogic()
        try:
            sml.createSollmiete( xsm )
            xsm.sm_id = self._db.getMaxId( "sollmiete", "sm_id" )
        except Exception as ex:
            raise Exception( "Bei der Anlage des Mietverhältnisses für '%s' ist der DB-Insert "
                             "in die Tabelle 'sollmiete' fehlgeschlagen:\n'%s'"
                             % (xsm.mv_id, str( ex )) )
        self._db.commit()

    def kuendigeMietverhaeltnis( self, xmv:XMietverhaeltnis, commit=True ):
        """
        Kündigung in Tabelle mietverhaeltnis eintragen -
        aber nur, wenn sich das Kündigungsdatum geändert hat.
        Der Update auf sollmiete muss hier erfolgen, da es fachlich falsch ist,
        ein MV ohne den zugehörigen Sollmietensatz zu kündigen.
        """
        xmvCheck = self._db.getAktuellesMietverhaeltnis( xmv.mv_id )
        if xmvCheck.bis == xmv.bis: return
        msg = self.validateKuendigungDaten( xmv )
        if msg:
            raise Exception( "MietverhaeltnisLogic.kuendigeMietverhaeltnis:\nValidierungsfehler:\n" + msg )
        # Mietverhältnis beenden
        self._db.updateMietverhaeltnis2( xmv.id, "bis", xmv.bis )
        # Sollmietensatz beenden
        smlogic = SollmieteLogic()
        smlogic.handleSollmieteBeiMvKuendigung( xmv.mv_id, xmv.bis )
        if commit:
            self._db.commit()

    def updateMietverhaeltnis( self, xmv:XMietverhaeltnis ):
        """
        Ändert ein Mietverhältnis.
        Macht einen Update in die <mietverhaeltnis>.
        Die Sollmiete ist zwar Bestandteil dieses Models, aber wird über diese Methode nicht geändert.
        Die mv_id kann über diese Funktion nicht geändert werden.
        :param xmv: das Mietverhältnis-Objekt mit den geänderten Daten.
        :return:
        """
        xmv_akt = self._db.getMietverhaeltnisById( xmv.id )
        if xmv_akt.equals( xmv ):
            return
        if xmv_akt.bis != xmv.bis:
            self.kuendigeMietverhaeltnis( xmv, commit=False )
        self._db.updateMietverhaeltnis( xmv )
        self._db.commit()

    def updateMietverhaeltnis3( self, id:int, telefon:str, mailto:str, bemerkung1:str, bemerkung2:str,
                                commit=False):
        self._db.updateMietverhaeltnis3( id, telefon, mailto, bemerkung1, bemerkung2 )
        if commit:
            self._db.commit()

    @staticmethod
    def validateMietverhaeltnisDaten( xmv:XMietverhaeltnis ) -> str:
        if not xmv.von:
            return "Mietbeginn fehlt"
        if not datehelper.isValidIsoDatestring( xmv.von ):
            return "Mietbeginn: kein gültiges Datumsformat. Muss 'yyyy-mm-dd' sein."
        if xmv.bis and not datehelper.isValidIsoDatestring( xmv.bis ):
            return "Mietende: kein gültiges Datumsformat. Muss 'yyyy-mm-dd' sein."
        if xmv.bis and xmv.bis < xmv.von:
            return "Das Mietende darf nicht vor dem Mietbeginn liegen."
        if not xmv.name:
            return "Name des Mieters fehlt"
        if not xmv.vorname:
            return "Vorame des Mieters fehlt"
        if not xmv.mobj_id:
            return "Objekt fehlt"
        return ""

    @staticmethod
    def validateKuendigungDaten( xmv:XMietverhaeltnis ) -> str:
        if not xmv.bis:
            # Rücknahme Kündigung
            return ""
        if not datehelper.isValidIsoDatestring( xmv.bis ):
            return "Datum nicht im vorgeschriebenen ISO-Format: '%s'" % xmv.bis
        # prüfen, ob das MV zum ENDE des Monats gekündigt wird - nur das ist zulässig
        monthNumber = int(xmv.bis[5:7])
        letzter = datehelper.getNumberOfDays( monthNumber )
        if int(xmv.bis[8:]) != letzter:
            return "Die Kündigung darf nur zum Letzten eines Monats erfolgen."
        if xmv.von > xmv.bis:
            return "Das Ende des Mietverhältnisses ('%s') darf nicht vor dessen Beginn ('%s') liegen." \
                   % ( xmv.bis, xmv.von )
        return ""


#############################################################################
#################  tests TETS TESTS TESTS  #################################
#############################################################################
def testUpdateMietverhaeltnis3():
    l = MietverhaeltnisLogic()
    l.updateMietverhaeltnis3( 1, "00000/12345", "mailto@mir.de", bemerkung1="BEEMERRKUNGG 1",
                              bemerkung2="beemerrkungg 2", commit=True )


def testNeuanlage():
    xmv = XMietverhaeltnis()
    xmv.mobj_id = "bueb"
    xmv.name = "Hotzenplotz"
    xmv.vorname = "Herbert"
    xmv.von = "2024-03-01"
    xmv.nettomiete = 300
    xmv.nkv = 100
    mvlogic = MietverhaeltnisLogic()
    mvlogic.createMietverhaeltnis( xmv )


if __name__ == "__main__":
    testUpdateMietverhaeltnis3()