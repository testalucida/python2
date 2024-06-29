from abc import abstractmethod
from typing import Dict, List, Any

from PySide2.QtCore import Signal

from base.interfaces import XBase


#################  XDatum  ##############################
from v2.icc.constants import iccMonthIdxToShortName, iccMonthShortNames, Umlegbar


class XDateParts:
    y:int = 0
    m:int = 0
    d:int = 0

#########################################################
class XEinAus( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.ea_id = 0
        self.master_name = ""
        self.mobj_id = ""
        self.debi_kredi = ""
        self.leistung = ""
        self.sab_id = 0
        self.hga_id = 0
        self.nka_id = 0
        self.reise_id = 0
        self.jahr = 0
        self.monat = ""
        self.betrag = 0.0
        self.ea_art = ""
        self.verteilt_auf:int = 1
        self.umlegbar = ""
        self.buchungsdatum = ""
        self.buchungstext = ""
        self.write_time = ""
        if valuedict:
            self.setFromDict( valuedict )

    def getMonthIdx( self ) -> int:
        return iccMonthShortNames.index( self.monat )

class XLetzteBuchung( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.debi_kredi = ""
        self.leistung = ""
        self.betrag = 0.0
        self.ea_art = ""
        if valuedict:
            self.setFromDict( valuedict )


#####################################################################
class XMtlZahlung( XBase ):
    """
    Ein XMtlZahlung-Objekt repräsentiert z.B. eine Zeile in der Tabelle der Mieteingänge
    """
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.master_name = ""
        self.mobj_id = ""
        self.soll = 0.0 # Soll-Betrag des eingestellten Monats. Ändert sich ggf. mit jeder Änderung des "Checkmonats".
        ## vonMonat und bisMonat beziehen sich auf das Jahr, für das dieses Objekt angelegt wird.
        ## Läuft ein MV z.B. von Januar bis Oktober, wird in vonMonat 'jan' und in bisMonat 'okt' eingetragen.
        ## Das dient dazu, dass in der Tabelle die Monate, in denen keine Zahlung erwartet werden kann,
        ## mit einem anderen Hintergrund dargestellt werden können als die anderen Monate.
        self.vonMonat = "" # aktiv ab Monat im betreff. Jahr, Format "jan"
        self.bisMonat = "" # aktiv bis Monat im betreff. Jahr, Format "dez"
        self.jan = 0.0
        self.feb = 0.0
        self.mrz = 0.0
        self.apr = 0.0
        self.mai = 0.0
        self.jun = 0.0
        self.jul = 0.0
        self.aug = 0.0
        self.sep = 0.0
        self.okt = 0.0
        self.nov = 0.0
        self.dez = 0.0
        self.summe = 0.0
        if valuedict:
            self.setFromDict( valuedict )

    def getMonthValue( self, m:int ) -> float:
        """
        :param m: index of month: 0 to 11
        :return: float
        """
        monthname = iccMonthIdxToShortName[m]
        return self.__dict__[monthname]

    def setMonthValue( self, m:int, value:float ):
        """
        Setzt den durch <m> spezifizierten Monatswert auf den Wert <value>.
        Achtung: errechnet KEINE neue Summe!
        Dies muss explizit durch einen Aufruf von computeSum() durchgeführt werden.
        :param m: index of month: 0 to 11
        :param value: float value to set
        :return: None
        """
        monthname = iccMonthIdxToShortName[m]
        self.__dict__[monthname] = value

    def computeSum( self ):
        self.summe = self.jan + self.feb + self.mrz + self.apr + self.mai + self.jun + \
                     self.jul + self.aug + self.sep + self.okt + self.nov + self.dez

###########################   XMtlMiete   ######################
class XMtlMiete( XMtlZahlung ):
    def __init__( self, valuedict:Dict=None ):
        XMtlZahlung.__init__( self, valuedict )
        self.mv_id = ""
        if valuedict:
            self.setFromDict( valuedict )

###########################   XMtlHausgeld   ######################
class XMtlHausgeld( XMtlZahlung ):
    def __init__( self, valuedict:Dict=None ):
        XMtlZahlung.__init__( self, valuedict )
        self.weg_name = "" # Name der WEG - taugt NICHT als Eindeutigkeitskriterium!
        if valuedict:
            self.setFromDict( valuedict )

###########################   XMtlAbschlag   ######################
class XMtlAbschlag( XMtlZahlung ):
    def __init__( self, valuedict:Dict=None ):
        XMtlZahlung.__init__( self, valuedict )
        self.sab_id = 0
        self.kreditor = "" # Name des Kreditors (des Lieferanten)
        self.vnr =  ""
        self.leistung = ""
        self.ea_art = "" # allg oder sonst
        self.master_name = ""
        if valuedict:
            self.setFromDict( valuedict )



##################   XGrundbesitzabgabe   ####################
class XGrundbesitzabgabe( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self, valuedict )#
        self.id = 0
        self.master_name = ""
        self.grundsteuer:float = 0.0
        self.abwasser:float = 0.0
        self.strassenreinigung:float = 0.0
        self.summe:float = 0.0 # der Jahresgesamtbetrag
        self.betrag_vierteljhrl:float = 0.0 # dieser Betrag wird vierteljährlich eingezogen
        self.bemerkung:str = ""
        if valuedict:
            self.setFromDict( valuedict )

    def computeSum( self ):
        self.summe = self.grundsteuer + self.abwasser + self.strassenreinigung
        self.betrag_vierteljhrl = round( self.summe/4, 2 )

class XSammelabgabe( XBase ):
    def __init__( self ):
        XBase.__init__( self )
        self.grundbesitzabgabeList:List[XGrundbesitzabgabe] = list()
        self.betrag = 0.0 # der Betrag, der eff. von der Stadt NK eingezogen wurde für alle Objekte,
                          # die in in der GrundbesitzabgabeListe enthalten sind.

class XSummen( XBase ):
    def __init__( self ):
        XBase.__init__( self )
        self.sumEin = 0
        self.sumHGV = 0
        self.sumSonstAus = 0
        self.saldo = 0

#####################  Mietverhältnis Kurz  ######################
class XMietverhaeltnisKurz( XBase ):
    def __init__( self, valuedict: Dict = None ):
        XBase.__init__( self )
        self.id = 0
        self.mv_id = ""
        self.mobj_id = ""
        self.von = ""
        self.bis = ""
        if valuedict:
            self.setFromDict( valuedict )

#####################  Verwaltung  ######################
class XVerwaltung( XBase ):
    def __init__( self, valuedict: Dict = None ):
        XBase.__init__( self )
        self.vwg_id = 0
        self.master_name = ""
        #self.mobj_id = "" # verwaltet wird ein ganzes Haus, niemals nur eine Wohnung
        self.weg_name = ""
        self.vw_id = ""
        self.von = ""
        self.bis = ""
        if valuedict:
            self.setFromDict( valuedict )

###############  Verwalter  ################################
class XVerwalter( XBase ):
    def __init__( self,  valuedict: Dict = None ):
        self.vw_id = ""
        self.name = ""
        self.strasse = ""
        self.plz_ort = ""
        self.telefon_1 = ""
        self.telefon_2 = ""
        self.mailto = ""
        self.ansprechpartner_1 = "" # Anspr.partner aus Tab. verwalter
        self.ansprechpartner_2 = "" # Anspr.partner aus Tab. verwalter
        self.vw_ap = ""         # Ansprechpartner aus Tab. verwaltung
        self.bemerkung = ""
        if valuedict:
            self.setFromDict( valuedict )

class XVerwalter2( XBase ):
    def __init__( self,  valuedict: Dict = None ):
        self.vw_id = ""
        self.name = ""
        self.strasse = ""
        self.plz_ort = ""
        self.telefon_1 = ""
        self.telefon_2 = ""
        self.mailto = ""
        self.vwg_id = 0
        self.vw_ap = ""         # Ansprechpartner aus Tab. verwaltung
        self.bemerkung = ""
        if valuedict:
            self.setFromDict( valuedict )


#######################################################################
class XHandwerkerKurz( XBase ):
    def __init__(self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.id = 0
        self.name = ""
        self.branche = ""
        self.adresse = ""
        if valuedict:
            self.setFromDict( valuedict )

#################  XSollMiete  ############################
class XSollMiete( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.sm_id = 0
        self.mv_id = ""
        self.mobj_id = ""
        self.von = ""
        self.bis = ""
        self.netto = 0.0
        self.nkv:float = 0.0
        self.brutto:float = 0.0 # Summe von netto + nkv
        self.bemerkung = ""
        if valuedict:
            self.setFromDict( valuedict )

#################  XSollHausgeld  ############################
class XSollHausgeld( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.shg_id = 0
        self.vwg_id = 0
        self.vw_id = ""
        #self.master_name = ""
        self.weg_name = ""
        self.mobj_id = ""
        self.von = ""
        self.bis = ""
        self.netto = 0.0
        self.ruezufue = 0.0
        self.brutto = 0.0 # Summe von netto + nkv
        self.bemerkung = ""
        if valuedict:
            self.setFromDict( valuedict )

#################  XSollAbschlag  ############################
class XSollAbschlag( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.sab_id = 0
        self.kreditor = "" # z.B. KEW, Gaswerk Illingen
        self.vnr = "" # Vertragsnummer des Kreditors
        self.leistung = "" # Gas, Strom, Wasser
        self.ea_art = ""  # allg oder sonst - mit dieser ea_art wird ein gebuchter regelm. Abschlag in Tabelle einaus
                          # geschrieben
        self.master_name = ""
        self.mobj_id = "" # nur erforderlich für eine Leerstehende Wohnung. Dann werden die Verträge auf mich abgeschlossen.
        self.von = ""
        self.bis = ""
        self.betrag = 0.0
        self.umlegbar = 0
        self.bemerkung = ""
        if valuedict:
            self.setFromDict( valuedict )

class XMasterobjekt( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.master_id = 0
        self.master_name = ""
        self.lfdnr = 0
        self.strasse_hnr = ""
        self.plz = ""
        self.ort = ""
        self.gesamt_wfl = 0
        self.anz_whg = 0
        self.afa_wie_vj = "X"
        self.afa = 0
        self.afa_proz = 0.0
        self.vw_id = ""
        self.vwg_id = ""
        self.verwalter = "" # Achtung, dieses Feld wird nur innerhalb der MietobjektView gefüllt, um eine MasterView
                            # zu erzeugen!
        self.verwalter_telefon_1 = ""
        self.verwalter_telefon_2 = ""
        self.verwalter_mailto = ""
        self.verwalter_ap = ""
        self.weg_name = ""
        self.hauswart = ""
        self.hauswart_telefon = ""
        self.hauswart_mailto = ""
        self.heizung = ""
        self.energieeffz = ""
        self.angeschafft_am = ""
        self.veraeussert_am = ""
        self.bemerkung = ""
        if valuedict:
            self.setFromDict( valuedict )

class XMietobjekt( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.mobj_id = ""
        self.whg_bez = ""
        self.qm = 0
        self.container_nr = ""
        self.bemerkung = ""
        self.hgv = XHausgeld()
        if valuedict:
            self.setFromDict( valuedict )

class XHausgeld( XBase ):
    def __init__( self ):
        XBase.__init__( self )
        self.netto = 0.0
        self.ruezufue = 0.0
        self.brutto = 0.0

class XMieter( XBase ):
    def __init__( self ):
        XBase.__init__( self )
        self.id = 0
        self.mieter = ""
        self.telefon = ""
        self.mailto = ""
        self.nettomiete = 0.0
        self.nkv = 0.0
        self.bruttomiete = 0.0
        self.kaution = 0
        self.bemerkung1 = ""
        self.bemerkung2 = ""

class XMasterMietobjektMieter( XBase ):
    def __init__( self ):
        XBase.__init__( self )
        self.xmaster = XMasterobjekt()
        self.xmobj = XMietobjekt()
        self.xmieter = XMieter()

# class XMieterUndMietobjekt( XBase ):
#     def __init__( self ):
#         XBase.__init__( self )
#         self.mietobjekt = XMietobjekt()
#         self.hausgeld = XHausgeld()
#         self.mieter = XMieter()


#################  MietobjektExt  #############################
class XMietobjektExt( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        ### zuerst die Master-Daten ###
        self.master_id:int = 0 # ID des Master-Objekts (Tabelle masterobjekt)
        self.master_name:str = ""
        self.strasse_hnr:str = ""
        self.plz:str = ""
        self.ort:str = ""
        self.gesamt_wfl:int = 0
        self.anz_whg:int = 0
        self.veraeussert_am:str = ""
        self.hauswart:str = ""
        self.hauswart_telefon:str = ""
        self.hauswart_mailto:str = ""
        self.heizung:str = ""
        self.energieeffz:str = ""
        self.bemerkung_masterobjekt:str = "" ### ACHTUNG: Dieses Feld heißt in der Tabelle masterobjekt "bemerkung" --
                                                # Beim Select berücksichtigen!
        ### dann die Daten des Mietobjekts, das ausgesucht wurde
        self.mobj_id:str = "" # ID des Mietobjekts (Tabelle mietobjekt)
        self.whg_bez:str = ""
        self.qm:int = 0  # Größe der Wohnung -- ist identisch mit gesamt_wfl, wenn es sich beim Masterobjekt nicht um ein
                         # ganzes Haus handelt
        self.container_nr:str = "" # Nummer des zur Wohnung gehörenden Abfallcontainers
        self.bemerkung_mietobjekt:str = "" ### ACHTUNG: Dieses Feld heißt in der Tabelle mietobjekt "bemerkung" --
                                            # Beim Select berücksichtigen!
        # Ergänzende Daten zu Mieter, Miete, NKV, Verwaltung und HGV
        self.mieter_id = 0
        self.mv_id = ""
        self.mieter:str = ""
        self.telefon_mieter:str = ""
        self.mailto_mieter:str = ""
        self.nettomiete:float = 0.0
        self.nkv:float = 0.0
        self.kaution:float = 0.0
        self.bemerkung1_mieter = "" # todo: muss noch versorgt werden
        self.bemerkung2_mieter = "" # todo: muss noch versorgt werden
        self.weg_name:str = ""
        self.vw_id = ""
        self.verwalter:str = ""
        self.verwalter_telefon = "" # todo: muss noch versorgt werden
        self.verwalter_mailto = ""   # todo: muss  noch versorgt werden
        self.verwalter_bemerkung = "" # todo: muss  noch versorgt werden
        self.verwalter_ap = "" # Ansprechpartner # todo: muss  noch versorgt werden
        self.hgv_netto:float = 0.0
        self.ruezufue:float = 0.0
        self.hgv_brutto:float = 0.0
        if valuedict:
            self.setFromDict( valuedict )

class XMietobjektAuswahl( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.master_name = ""
        self.mobj_id = ""
        self.mv_id = ""
        self.name = ""
        if valuedict:
            self.setFromDict( valuedict )

###################  Mietverhältnis  #########################
class XMietverhaeltnis( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.id = 0
        self.mv_id = ""
        self.mobj_id = ""
        self.von = ""
        self.bis = ""
        self.name = ""
        self.vorname = ""
        self.name_vorname = ""
        self.name2 = ""
        self.vorname2 = ""
        self.telefon = ""
        self.mobil = ""
        self.mailto = ""
        self.anzahl_pers = 1
        self.IBAN = ""
        self.nettomiete = 0.0
        self.nkv = 0.0
        self.bruttomiete = 0.0
        self.sollmiete_bemerkung = ""
        self.kaution = 0
        self.kaution_bezahlt_am = ""
        self.bemerkung1 = ""
        self.bemerkung2 = ""
        if valuedict:
            self.setFromDict( valuedict )

#####################  Mieterwechsel  ############################
#!!! ACHTUNG: nicht von XBase abgeleitet !!!
class XMieterwechsel:
    def __init__( self, mietverhaeltnis_alt:XMietverhaeltnis=None, mietverhaeltnis_next:XMietverhaeltnis=None ):
        self.mietverhaeltnis_alt = mietverhaeltnis_alt
        self.mietverhaeltnis_next = mietverhaeltnis_next

    def equals( self, other ) -> bool:
        return ( self.mietverhaeltnis_alt.equals( other.mietverhaeltnis_alt ) and
                 self.mietverhaeltnis_next.equals( other.mietverhaeltnis_next ) )

class XLeistung( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.leistung = ""
        self.umlegbar = Umlegbar.NEIN.value
        self.ea_art = ""
        if valuedict:
            self.setFromDict( valuedict )

class XKreditorLeistung( XLeistung ):
    def __init__( self, valuedict:Dict=None ):
        XLeistung.__init__( self )
        self.kredleist_id = 0
        self.master_name = ""
        self.kreditor = ""
        self.bemerkung = ""
        if valuedict:
            self.setFromDict( valuedict )

class XTeilzahlung( XBase ):
    def __init__( self, betrag:float, buchungsdatum:str="", buchungstext:str="", write_time:str="", ea_id=0 ):
        XBase.__init__( self )
        self.ea_id = ea_id
        self.betrag = betrag
        self.buchungsdatum = buchungsdatum
        self.buchungstext = buchungstext
        self.write_time = write_time

class XAbrechnung( XBase ):
    """
    Ein XAbrechnung-Objekt beinhaltet die attribute, die einer HGA und einer NKA gemeinsam sind.
    """
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.abr_id = 0   # dahinter verbirgt sich entweder eine hga_id oder eine nka_id
        self.master_name = ""
        self.mobj_id = ""
        self.ab_jahr = 0
        self.ab_datum = ""
        self.forderung = 0.0
        self.zahlung = 0.0  # Summe der Teil-Zahlungen auf die Forderung gem. Tab. <einaus>
        self.teilzahlungen:List[XTeilzahlung] = list() # Liste der Teilzahlungen. Wenn die Forderung
                                                       # in einer Summe bezahlt wurde, enthält diese Liste
                                                       # genau diesen einen Eintrag.
        #self.buchungsdatum = ""
        self.bemerkung = "" # Bemerkung aus Tabelle hg_abrechnung oder nk_abrechnung
        self.write_time = "" # Eintragung in Tabelle <einaus>
        if valuedict:
            self.setFromDict( valuedict )

    def addZahlung( self, betrag:float, buchungsdatum:str="", buchungstext:str="", write_time:str="", ea_id=0 ):
        tz = XTeilzahlung( betrag, buchungsdatum, buchungstext, write_time, ea_id )
        self.teilzahlungen.append( tz )
        self.zahlung += betrag

class XHGAbrechnung( XAbrechnung ):
    def __init__( self, valuedict:Dict=None ):
        XAbrechnung.__init__( self, valuedict )
        self.weg_name = ""  # Name der WEG
        self.vw_id = ""  # Verwalter-ID, entspricht in etwa dessen Namen
        self.vwg_id = 0  # Prim.key in Tab. <verwaltung>
        self.vwg_von = "" # Beginn der Verwaltung durch diesen Verwalter
        self.vwg_bis = "" # Ende der Verwaltung durch diesen Verwalter
        self.entnahme_rue = 0.0
        if valuedict:
            self.setFromDict( valuedict )

class XNKAbrechnung( XAbrechnung ):
    def __init__( self, valuedict:Dict=None ):
        XAbrechnung.__init__( self, valuedict )
        self.mv_id = "" # entspricht in etwa dem Namen des Mieters
        self.von = "" # Beginn des Mietverhältnisses
        self.bis = "" # Ende des Mietverhältnisses
        if valuedict:
            self.setFromDict( valuedict )

#######################  Geschäftsreise  #######################
class XGeschaeftsreise( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.reise_id = 0
        self.master_name = ""
        #self.master_id = 0
        #self.mobj_id = ""
        self.jahr = 0
        self.von = ""
        self.bis = ""
        #self.ziel = ""
        self.zweck = ""
        self.km = 800
        self.personen = 1
        self.uebernachtung = ""
        self.uebernacht_kosten = 0.0
        if valuedict:
            self.setFromDict( valuedict )

#####################   Pauschale  ##########################
class XPauschale( XBase ):
    def __init__(self, valuedict:Dict=None):
        XBase.__init__( self )
        self.id = 0
        self.jahr_von = 0
        self.jahr_bis = 0
        self.km = 0.0
        self.vpfl_8 = 0.0 #Verpfl.-Pauschale für Hin- u. Rückreise bzw. für 8-24 stündige Dienstreise
        self.vpfl_24 = 0.0 #Verpfl.-Pauschale für ganztägige Abwesenheit
        if valuedict:
            self.setFromDict( valuedict )

##################   XMasterEinAus   ###########################
class XMasterEinAus( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self, valuedict )
        self.master_id = 0
        self.master_name = ""
        self.qm = 0
        self.monate = 0 # Anzahl vermietete Monate
        self.einnahmen = 0 # Bruttomiete plus NKA
        self.netto_je_qm = 0.0
        self.hg = 0 # HGV inkl. RüZuFü plus HGA (Entn. Rü. bleibt unberücksichtigt, da die RüZuFü zu den Rep.-Kosten zählen)
        self.sonder_u = 0 # wird als Ausgabe gewertet
        self.allg_kosten = 0 # Kostenarten a, g, v
        self.rep_kosten = 0 # nicht verteilte und verteilte
        self.sonst_kosten = 0 # Kostenart s
        self.ertrag = 0



#####################################################################################################################

def test():
    d = {"id": 11, "name" : "kendel, martin", "branche" : "Klempner", "adresse" : "Birnenweg 2, Kleinsendelbach"}
    x = XHandwerkerKurz( d )
    x.print()