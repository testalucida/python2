from typing import Iterable, List, Dict

from v2.icc.constants import ValueMapperHelper, Heizung
from v2.icc.iccdata import IccData
from v2.icc.icclogic import IccLogic, IccTableModel
from v2.icc.interfaces import XMietobjektAuswahl, XMietobjektExt, XMietverhaeltnis, XSollHausgeld, XVerwalter, \
    XMasterMietobjektMieter, XMietobjekt, XVerwalter2

##########################   MietobjektTableModel   ###################
from v2.masterobjekt.masterobjektdata import MasterobjektData
from v2.masterobjekt.masterobjektlogic import MasterobjektLogic
from v2.mietobjekt.mietobjektdata import MietobjektData
from v2.mietverhaeltnis.mietverhaeltnislogic import MietverhaeltnisLogic
from v2.sollhausgeld.sollhausgeldlogic import SollHausgeldLogic


class MietobjektTableModel( IccTableModel ):
    def __init__( self, rowlist:Iterable[XMietobjektAuswahl] ):
        IccTableModel.__init__( self, rowlist )
        self.setKeyHeaderMappings2(
            ( "master_name", "mobj_id", "name" ),
            ( "Haus", "Wohnung", "Mieter" ) )

##########################   MietobjektLogic   ###################
class MietobjektLogic( IccLogic ):
    def __init__( self ):
        IccLogic.__init__( self )
        self._data = MietobjektData()

    def getMietobjektTableModel( self ) -> MietobjektTableModel:
        def setName( x:XMietobjektAuswahl ):
            x.name = self.getNachnameVornameFromMv_id( x.mv_id )
            return x
        l:List[XMietobjektAuswahl] = self._data.getMietobjekte()
        l = [setName( x ) for x in l]
        tm = MietobjektTableModel( l )
        return tm

    def getMietobjektExt( self, mobj_id: str ) -> XMietobjektExt:
        xmo: XMietobjektExt = self._data.getMietobjektExt( mobj_id )
        xmo.heizung = ValueMapperHelper.getDisplay( Heizung, xmo.heizung )
        xvw:XVerwalter = self._data.getVerwalterDetails( xmo.vw_id )
        if xvw and xvw.vw_id:
            # es gibt eine Verwaltung
            xmo.verwalter_mailto = xvw.mailto
            xmo.verwalter_telefon = xvw.telefon_1
            if xvw.telefon_2:
                if xmo.verwalter_telefon:
                    xmo.verwalter_telefon += "\n"
                xmo.verwalter_telefon += xvw.telefon_2
            xmo.verwalter_bemerkung = xvw.bemerkung
            xmo.verwalter_ap = xvw.ansprechpartner_1
            if xvw.ansprechpartner_2:
                if xmo.verwalter_ap:
                    xmo.verwalter_ap += "\n"
                xmo.verwalter_ap += xvw.ansprechpartner_2

        xmv: XMietverhaeltnis = MietverhaeltnisLogic().getAktuellesMietverhaeltnisByMietobjekt( xmo.mobj_id )
        if not xmv:
            xmv = XMietverhaeltnis()
        else:
            xmo.mieter_id = xmv.id
            xmo.mv_id = xmv.mv_id
            xmo.mieter = xmv.vorname + " " + xmv.name
            if xmv.telefon:
                xmo.telefon_mieter = xmv.telefon
            if xmv.mobil:
                if xmv.telefon:
                    xmo.telefon_mieter += ", "
                xmo.telefon_mieter += xmv.mobil
            if xmv.mailto:
                xmo.mailto_mieter = xmv.mailto

            xmo.nettomiete = xmv.nettomiete
            xmo.nkv = xmv.nkv
            xmo.kaution = xmv.kaution
            xmo.bemerkung1_mieter = xmv.bemerkung1
            xmo.bemerkung2_mieter = xmv.bemerkung2
        xsh: XSollHausgeld = SollHausgeldLogic().getCurrentSollHausgeld( xmo.mobj_id )
        #xmo.verwalter = xsh.vw_id
        #xmo.weg_name = xsh.weg_name
        if xsh: # Wohnung könnte derzeit nicht vermietet sein, dann ist xsh None
            xmo.hgv_netto = xsh.netto
            xmo.ruezufue = xsh.ruezufue
            xmo.hgv_brutto = xsh.brutto
        return xmo

    def getMasterMietobjektMieterData(self, mobj_id: str) -> XMasterMietobjektMieter:
        xmmm: XMasterMietobjektMieter = XMasterMietobjektMieter()
        xmmm.xmaster = MasterobjektLogic().getMasterData( mobj_id )
        xmaster = xmmm.xmaster
        xvw: XVerwalter2 = self._data.getVerwalterDetails2(xmaster.vw_id, xmaster.master_name)
        if xvw and xvw.vw_id:
            # es gibt eine Verwaltung
            xmaster.verwalter = xvw.name + "\n" + xvw.strasse + "\n" + xvw.plz_ort
            xmaster.verwalter_mailto = xvw.mailto
            xmaster.verwalter_telefon_1 = xvw.telefon_1
            xmaster.verwalter_telefon_2 = xvw.telefon_2
            xmaster.verwalter_bemerkung = xvw.bemerkung
            xmaster.vwg_id = xvw.vwg_id
            xmaster.verwalter_ap = xvw.vw_ap
        xmobj:XMietobjekt = self._data.getMietobjektData(mobj_id)
        xmmm.xmobj.copyByKey( xmobj )

        xmv:XMietverhaeltnis = MietverhaeltnisLogic().getAktuellesMietverhaeltnisByMietobjekt(mobj_id)
        if xmv:
            xmmm.xmieter.copyByKey(xmv)
            xmi = xmmm.xmieter
            xmi.mieter = xmv.vorname + " " + xmv.name
            if xmv.mobil:
                if xmv.telefon:
                    xmi.telefon += ", "
                xmi.telefon += xmv.mobil

        xsh: XSollHausgeld = SollHausgeldLogic().getCurrentSollHausgeld(mobj_id)
        if xsh:  # Wohnung könnte derzeit nicht vermietet sein, dann ist xsh None
            xmmm.xmobj.hgv.copyByKey(xsh)
        return xmmm

    def saveMasterMietobjektMieterChanges( self, xmmmcopy:XMasterMietobjektMieter,
                                           xmmmorig:XMasterMietobjektMieter ) -> str:
        """
        Speichert die Änderungen an einem XMietobjektExt - Objekt.
        Diese Änderungen werden anhand eines Vergleichs von xmmmcopy (nach Änderung) und
        xmmmorig (vor Änderung) gefunden.
        Wenn die Validierung nicht ok ist, wird eine Meldung zurückgegeben.
        Wenn Validierung == OK, wird die Speicher-Methode aufgerufen. Wenn das Speichern schiefgeht, wird
        von der Speicher-Methode eine Exception geworfen, die hier nicht aufgefangen wird (muss im Controller 
        geschehen).
        :param xmmmcopy: Datenschnitttelle mit Änderungen
        :param xmmmorig: Datenschnittstelle vor Änderungen
        :return: eine Nachricht, wenn die Validierung fehlgeschlagen ist bzw. ein Fehler beim
                Speichern aufgetreten ist, sonst "".
        """
        masterChanged = vwChanged = vwApChanged = mobjChanged = mieterChanged = False
        if xmmmcopy.xmaster != xmmmorig.xmaster:
            diffs:Dict = xmmmcopy.xmaster.getDifferences( xmmmorig.xmaster)
            for k in diffs.keys():
                if k in ("verwalter_telefon_1", "verwalter_telefon_2", "verwalter_mailto"):
                    vwChanged = True
                    continue
                if k == "verwalter_ap":
                    vwApChanged = True
                    continue
                else:
                    masterChanged = True
        if xmmmcopy.xmobj != xmmmorig.xmobj:
            mobjChanged = True
        if xmmmcopy.xmieter != xmmmorig.xmieter:
            mieterChanged = True

        if masterChanged:
            masterlogic = MasterobjektLogic()
            masterlogic.updateMasterobjekt( xmmmcopy.xmaster )
        if vwChanged or vwApChanged:
            iccdata = IccData()
            x = xmmmcopy.xmaster
            if vwChanged:
                iccdata.updateVerwalterKontakt(x.vw_id, x.verwalter_telefon_1, x.verwalter_telefon_2,
                                               x.verwalter_mailto)
            if vwApChanged:
                iccdata.updateVerwaltungAnsprechpartner(x.vwg_id, x.verwalter_ap)
        if mobjChanged:
            mobj = xmmmcopy.xmobj
            self._data.updateMietobjekt1(mobj.mobj_id, mobj.whg_bez, mobj.container_nr, mobj.bemerkung)
        if mieterChanged:
            mieter = xmmmcopy.xmieter
            mvlogic = MietverhaeltnisLogic()
            mvlogic.updateMietverhaeltnis3( mieter.id, mieter.telefon,mieter.mailto,
                                            mieter.bemerkung1, mieter.bemerkung2)
        self._data.commit()
        return ""

###################################################################
def test():
    logic = MietobjektLogic()
    xext = logic.getMietobjektExt( "kleist_01" )
    xext.print()