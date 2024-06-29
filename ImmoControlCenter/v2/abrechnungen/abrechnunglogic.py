import copy
from abc import abstractmethod
from typing import List

import datehelper
from v2.abrechnungen.abrechnungdata import NKAbrechnungData, HGAbrechnungData
from v2.einaus.einausdata import EinAusData
from v2.einaus.einauslogic import EinAusLogic
from v2.einaus.einauswritedispatcher import EinAusWriteDispatcher
from v2.icc import constants
from v2.icc.constants import EinAusArt
from v2.icc.icclogic import IccLogic, IccTableModel
from v2.icc.interfaces import XAbrechnung, XHGAbrechnung, XNKAbrechnung, XVerwaltung, XEinAus, XTeilzahlung

################   AbrechnungTableModel   ####################
class AbrechnungTableModel( IccTableModel ):
    def __init__( self, rowlist:List[XAbrechnung], jahr ):
        IccTableModel.__init__( self, rowlist, jahr )

################   HGAbrechnungTableModel   ####################
class HGAbrechnungTableModel( AbrechnungTableModel ):
    def __init__(self, rowlist:List[XHGAbrechnung], jahr ):
        AbrechnungTableModel.__init__( self, rowlist, jahr )
        self.setKeyHeaderMappings2(
            ("master_name", "mobj_id", "weg_name", "vw_id", "vwg_von", "vwg_bis", "ab_datum", "forderung", "entnahme_rue",
             "bemerkung", "zahlung" ),
            ( "Haus", "Wohnung", "WEG", "Verwalter", "Vwtg. von", "Vwtg. bis", "abgerechnet am", "Forderung", "Entn.Rü.",
              "Bemerkung", "Zahlung" )
        )

################   NKAbrechnungTableModel   ####################
class NKAbrechnungTableModel( AbrechnungTableModel ):
    def __init__(self, rowlist:List[XNKAbrechnung], jahr ):
        AbrechnungTableModel.__init__( self, rowlist, jahr )
        self.setKeyHeaderMappings2(
            ("master_name", "mobj_id", "mv_id", "von", "bis", "ab_datum", "forderung", "bemerkung", "zahlung"),
            ( "Haus", "Wohnung", "Mieter", "MV von", "MV bis", "Abr.Dt.", "Forderung", "Bemerkung", "Zahlung" )
        )

################   TeilzahlungTableModel   ####################
class TeilzahlungTableModel( IccTableModel ):
    def __init__( self, rowlist:List[XTeilzahlung], jahr ):
        IccTableModel.__init__( self, rowlist, jahr )
        self.setKeyHeaderMappings2(
            ("ea_id", "betrag", "buchungsdatum", "buchungstext", "write_time" ),
            ("ea_id", "Betrag", "Buchungsdatum", "Buchungstext", "LWA" )
        )

################   Base class AbrechnungLogic   ##################
class AbrechnungLogic( IccLogic ):
    def __init__(self):
        IccLogic.__init__( self )
        self._eaData = EinAusData()

    @staticmethod
    def _getYearForTeilzahlung( tz: XTeilzahlung ) -> int:
        if tz.buchungsdatum:
            return int( tz.buchungsdatum[0:4] )
        else:
            return datehelper.getCurrentYear()

    @staticmethod
    def _getMonthForTeilzahlung( tz: XTeilzahlung ) -> str:
        if tz.buchungsdatum:
            monthIdx = int( tz.buchungsdatum[5:7] )
            return constants.iccMonthShortNames[monthIdx - 1]
        else:
            dic = datehelper.getCurrentYearAndMonth()
            return constants.iccMonthShortNames[dic["month"] - 1]

    @staticmethod
    def getTeilzahlungTableModel( xabr: XAbrechnung ) -> TeilzahlungTableModel:
        tm = TeilzahlungTableModel( xabr.teilzahlungen, xabr.ab_jahr )
        return tm

    @abstractmethod
    def validateDerived( self, xabr ) -> str:
        """
        Wird von self.validateAbrechnung aufgerufen.
        Damit wird das Abrechnungsobjekt xabr den abgeleiteten Klassen HGAbrechnungLogic und
        NKAbrechnungLogic zur speziellen Prüfung übergeben.
        :return:
        """
        pass

    def validateAbrechnung( self, x:XAbrechnung ) -> str:
        """
        Validiert ein XAbrechnung-Objekt und liefert eine Fehlermeldung zurück, wenn ein Validierungsfehler vorliegt.
        Wenn alles ok ist, wird ein Leerstring zurückgegeben.
        Vor der Validierung wird - sofern es sich nicht um einen Insert handelt - die Abrechnung aus der
        Datenbank geladen, um zu prüfen, ob überhaupt Veränderungen vorliegen.
        Gibt es keine Veränderungen, wird ein Leerstring zurückgegeben.
        :param x: zu prüfende Abrechnung
        :return: Fehlermeldung oder Leerstring
        """
        if not x.master_name: return "Mastername fehlt"
        if not x.mobj_id: return "Objektname fehlt"
        if not x.ab_jahr: return "Abrechnungsjahr fehlt"
        if not x.ab_datum: return "Erstellungsdatum der Abrechnung fehlt"
        if not x.forderung: return "Forderung aus Abrechnung fehlt"
        msg = self.validateDerived( x )
        if msg: return msg
        if len( x.teilzahlungen ) > 0:
            for tz in x.teilzahlungen:
                if not tz.betrag:
                    msg = "Teilzahlungsbetrag '0' unzulässig"
                    if tz.ea_id: return msg + "(ea_id: '%d')" % tz.ea_id
                    return msg
        return ""

    def getAbrechnungTableModel( self, ab_jahr: int ) -> AbrechnungTableModel:
        # Objekte mit Abrechnungen (soweit vorhanden) holen, ohne Zahlungen
        data = self.getData()
        abrlist: List[XAbrechnung] = data.getObjekteUndAbrechnungen( ab_jahr )  # abrlist ist sortiert nach master_name
        # Achtung, die abr_id existiert für ein Objekt erst dann, wenn die Abrechnung gemacht wurde
        # Jetzt die Zahlungen zu den bereits erstellten Abrechnungen holen:
        for abr in abrlist:
            if abr.abr_id:
                ealist: List[XEinAus] = self.getEinAusZahlungen( abr.abr_id )
                for ea in ealist:
                    abr.addZahlung( ea.betrag, ea.buchungsdatum, ea.buchungstext, ea.write_time, ea.ea_id )
        #tm = AbrechnungTableModel( abrlist, ab_jahr )
        tmtype = self.getAbrechnungTableModelType()
        tm = tmtype( abrlist, ab_jahr )
        return tm

    def trySave( self, xabr:XAbrechnung ) -> str:
        """
        An einem Abrechnungsobjekt können Abrechnungsdaten und Zahlungsdaten (x.teilzahlungen) geändert werden.
        Geänderte Abrechnungsdaten werden in Tabelle hg_abrechnung gespeichert, neue/geänderte/gelöschte Teilzahlungen
        in Tabelle einaus.
        Um zu erkennen, ob ein Teilzahlungsobjekt gelöscht werden soll, werden alle Teilzahlungen dieser
        Abrechnung aus <einaus> gelesen. Objekte, die in dieser Liste vorhanden sind, in x.teilzahlungen aber nicht,
        müssen gelöscht werden.
        Insert/Update:
        Vor dem Speichern wird validiert. Das Validierungsergebnis wird zurückgeliefert.
        Gab es keinen Validierungsfehler wird gespeichert und ein Leerstring zurückgegeben.
        Gibt es ein Teilzahlungsobjekt mit ea_id == 0, handelt es sich um eine neue, noch nicht gespeicherte
        Teilzahlung. Es erfolgt ein Insert in einaus.
        Ein Teilzahlungsobjekt mit ea_id > 0 ist bereits gespeichert. Das entsprechende XEinaus-Objekt wird aus
        einaus gelesen und mit dem Teilzahlungsobjekt verglichen. Gibt es Unterschiede, erfolgt ein Update.
        :param xabr: das XAbrechnung-Objekt, dessen Änderungen gespeichert werden sollen.
        :return:
        """
        # Entscheiden, was genau zu tun ist: Ganze Abrechnung neu anlegen, Update auf exist. Abrechnung, Anlage/Änderung
        # einer Teilzahlung
        if xabr.abr_id > 0:
            # prüfen, ob eine Teilzahlung zu löschen ist. Dafür braucht es keine Validierung.
            msg = self._checkDeleteTeilzahlungen( xabr.abr_id, xabr.teilzahlungen )
            if msg: return msg
            # das etwaige Löschen von Teilzahlungen ist erledigt, für alles andere brauchen wir eine Validierung:
            msg = self.validateAbrechnung( xabr )
            if msg: return msg
            msg = self._updateAbrechnung( xabr )
            if msg: return msg
        else:
            # neue Abrechnung
            msg = self.validateAbrechnung( xabr )
            if msg: return msg
            msg = self._insertAbrechnung( xabr )
            if msg: return msg
        # die Abrechnung selbst ist erledigt - jetzt prüfen, ob es neue oder zu ändernde Teilzahlungen gibt:
        msg = self._checkSaveTeilzahlungen( xabr )
        if msg: return msg
        # alles gut gegangen, jetzt commit.
        # Eigtl ist es völlig egal, ob man den commit mit _eaData oder _hgaData macht. Alles läuft
        # in *einer* Transaktion. Sicherheitshalber machen wir zwei commits ;-)
        self._eaData.commit()
        #self._hgaData.commit()
        return ""

    def _checkSaveTeilzahlungen( self, xabr:XAbrechnung ) -> str:
        for tz in xabr.teilzahlungen:
            if tz.ea_id > 0:
                # update Teilzahlung
                xea = self._eaData.getEinAusZahlung( tz.ea_id )
                if tz.betrag != xea.betrag \
                or tz.buchungsdatum != xea.buchungsdatum \
                or tz.buchungstext != xea.buchungstext:
                    delta = 0
                    if tz.betrag != xea.betrag:
                        delta = tz.betrag - xea.betrag
                    xea.betrag = tz.betrag
                    xea.buchungsdatum = tz.buchungsdatum
                    xea.buchungstext = tz.buchungstext
                    self._eaData.updateEinAusZahlung( xea )
                    if delta != 0:
                        EinAusWriteDispatcher.inst().ea_updated.emit( xea, delta )
            else:
                # Neue Teilzahlung
                # Aus dem tz-Objekt ein EinAus-Objekt machen, dann an _eaData übergeben zum Insert
                xea = self._createXeinausFromTeilzahlung( xabr, tz )
                try:
                    self._eaData.insertEinAusZahlung( xea )
                    tz.ea_id = xea.ea_id
                    EinAusWriteDispatcher.inst().ea_inserted.emit( xea )
                except Exception as ex:
                    self._eaData.rollback()
                    msg = "AbrechnungLogic._checkSaveTeilzahlungen():\nFehler beim Insert einer Teilzahlung für " \
                          "Masterobjekt '%s'\n\nFehlermeldung:\n%s " % (xabr.master_name, str( ex ))
                    return msg
        return ""

    def _checkDeleteTeilzahlungen( self, abr_id: int, tzlist: List[XTeilzahlung] ) -> str:
        ealist = self.getEinAusZahlungen( abr_id ) # alle Teilzahlungen, die die Abrechnung <abr_id> betreffen
        tz_ea_id_list = [tz.ea_id for tz in tzlist]
        for ea in ealist:
            if not ea.ea_id in tz_ea_id_list:
                # es gibt in der Datenbank eine ea_id, die in der tz_ea_id_list nicht mehr enthalten ist,
                # also eine Teilzahlung, die vom User gelöscht wurde.
                # Diese muss aus der DB gelöscht werden.
                try:
                    self._eaData.deleteEinAusZahlung( ea.ea_id )
                    EinAusWriteDispatcher.inst().ea_deleted.emit( (ea.ea_id,), ea.ea_art, ea.betrag*(-1) )
                except Exception as ex:
                    self._eaData.rollback()
                    msg = "AbrechnungLogic._checkDeleteTeilzahlungen():\nFehler beim Löschen der Zahlung " \
                          "mit ea_id '%d'\n\nFehlermeldung:\n%s " % (ea.ea_id, str( ex ))
                    return msg
        return ""

    def _createXeinausFromTeilzahlung( self, xabr:XAbrechnung, tz:XTeilzahlung ) -> XEinAus:
        xea = XEinAus()
        xea.master_name = xabr.master_name
        xea.mobj_id = xabr.mobj_id
        xea.debi_kredi = self.getDebiKredi( xabr )
        xea.leistung = self.getLeistungKuerzel() + (" %d" % xabr.ab_jahr)
        self.provideForeignKey( xea, xabr )
        xea.jahr = self._getYearForTeilzahlung( tz )
        xea.monat = self._getMonthForTeilzahlung( tz )
        xea.betrag = tz.betrag
        xea.ea_art = self.getEinAusArt_display()
        xea.buchungsdatum = tz.buchungsdatum
        xea.buchungstext = tz.buchungstext
        xea.write_time = datehelper.getCurrentTimestampIso()
        return xea

    @abstractmethod
    def deleteAbrechnung( self, xabr:XAbrechnung ):
        pass

    def deleteAbrechnungen( self, xabrechnungen:List[XAbrechnung] ):
        """
        Löscht die übergebenen NK- bzw. HG-Abrechnungen.
        Für jede Abrechnung gilt:
        Es ist der Satz in der jeweiligen Tabelle  nk_abrechnung bzw. hg_abrechnung zu löschen sowie alle
        Teilzahlungen in der Tabelle einaus, die sich auf die gelöschte Abrechnung beziehen.
        :param xabrechnungen: Liste zu löschender Abrechnungen
        :return:
        """
        for xabr in xabrechnungen:
            # erst die Teilzahlungen auf diese Abrechnung in Tabelle einaus löschen:
            for tz in xabr.teilzahlungen:
                try:
                    self._eaData.deleteEinAusZahlung( tz.ea_id )
                except Exception as ex:
                    self._eaData.rollback()
                    raise Exception( str(ex) +
                                     "\nBetroffene Teilzahlung: \n'%s'" % tz.toString( printWithClassname=True ) )
            # jetzt die Abrechnung in nk_abrechnung bzw. hg_abrechnung löschen: (Methode hat eigenen try-catch-Block)
            self.deleteAbrechnung( xabr )
        self._commit()
        # jetzt die Anzeige aktualisieren:
        for xabr in xabrechnungen:
            xabr.abr_id = 0
            xabr.forderung = 0
            xabr.ab_datum = None
            xabr.teilzahlungen.clear()
            xabr.zahlung = 0.0

    @abstractmethod
    def getAbrechnungTableModelType( self ) -> type:
        pass

    @abstractmethod
    def getDebiKredi( self, xabr:XAbrechnung ) -> str:
        pass

    @abstractmethod
    def provideForeignKey( self, xea:XEinAus, xabr:XAbrechnung ):
        """
        Versorgt je nach Abrechnungsart einen der beiden Fremdschlüssel hga_id bzw. nka_id im XEinAus-Objekt
        :param xea:
        :param xabr:
        :return:
        """
        pass

    @abstractmethod
    def getLeistungKuerzel( self ) -> str:
        """
        Das Kürzel, das in die Tabelle <einaus> in die Spalte <leistung> eingetragen wird.
        :return:
        """
        pass

    @abstractmethod
    def getEinAusArt_display( self ):
        """
        Liefert die EinAusArt
        :return:
        """
        pass

    @abstractmethod
    def getData( self ) -> HGAbrechnungData:
        pass

    @abstractmethod
    def getEinAusZahlungen( self, abr_id:int ) -> List[XEinAus]:
        pass

    @abstractmethod
    def _updateAbrechnung( self, xabr:XAbrechnung ):
        pass

    @abstractmethod
    def _insertAbrechnung( self, xabr: XAbrechnung ):
        pass

    @abstractmethod
    def _commit( self ):
        pass

#################   HGAbrechnungTableModel   ######################
class HGAbrechnungLogic( AbrechnungLogic ):
    def __init__(self):
        AbrechnungLogic.__init__( self )
        self._hgaData = HGAbrechnungData()

    def getAbrechnungTableModelType( self ) -> type:
        return HGAbrechnungTableModel

    def getDebiKredi( self, xabr: XHGAbrechnung ) -> str:
        return xabr.weg_name

    def provideForeignKey( self, xea: XEinAus, xabr: XAbrechnung ):
        xea.hga_id = xabr.abr_id

    def getLeistungKuerzel( self ) -> str:
        """
        Das Kürzel, das in die Tabelle <einaus> in die Spalte <leistung> eingetragen wird.
        :return:
        """
        return "HGA"

    def getEinAusArt_display( self ):
        """
        Liefert die EinAusArt
        :return:
        """
        return EinAusArt.HAUSGELD_ABRECHNG.display

    def getData( self ) -> HGAbrechnungData:
        return self._hgaData

    def getEinAusZahlungen( self, abr_id ) -> List[XEinAus]:
        return  self._eaData.getEinAuszahlungenByHgaId( abr_id )

    def validateDerived( self, xabr:XHGAbrechnung ) -> str:
        # der allgemeine Teil der Abrechnung (s. XAbrechnung) wurde schon geprüft.
        # Hier wird der spezielle Teil geprüft
        if not xabr.weg_name: return "WEG-Bezeichnung fehlt."
        if not xabr.vw_id: return "Verwalter fehlt."
        if not xabr.vwg_id: return "Verwaltungs-ID fehlt."
        return ""

    def _insertAbrechnung( self, xhga:XHGAbrechnung ) -> str:
        try:
            self._hgaData.insertAbrechnung( xhga )
            return ""
        except Exception as ex:
            self._hgaData.rollback()
            msg = "AbrechnungLogic._insertAbrechnung():\nFehler beim Insert der Abrechnung %d für " \
                  "Masterobjekt '%s'\n\nFehlermeldung:\n%s " % (xhga.ab_jahr, xhga.master_name, str( ex ))
            return msg

    def _updateAbrechnung( self, xhga:XHGAbrechnung ) -> str:
        try:
            self._hgaData.updateAbrechnung( xhga )
            return ""
        except Exception as ex:
            self._hgaData.rollback()
            msg = "AbrechnungLogic._updateAbrechnung():\nFehler beim Update der Abrechnung %d für " \
                  "Masterobjekt '%s'\n\nFehlermeldung:\n%s " % (xhga.ab_jahr, xhga.master_name, str( ex ))
            return msg

    def deleteAbrechnung( self, xabr:XAbrechnung ):
        try:
            self._hgaData.deleteAbrechnung( xabr )
        except Exception as ex:
            self._hgaData.rollback()
            raise Exception( str(ex) + "\nBetroffene HG-Abrechnung: %d" % xabr.abr_id )

    def _commit( self ):
        self._hgaData.commit()



#################   NKAbrechnungTableModel   ######################
class NKAbrechnungLogic( AbrechnungLogic ):
    def __init__(self):
        AbrechnungLogic.__init__( self )
        self._nkaData = NKAbrechnungData()

    def getAbrechnungTableModelType( self ) -> type:
        return NKAbrechnungTableModel

    def getDebiKredi( self, xabr: XNKAbrechnung ) -> str:
        return xabr.mv_id

    def provideForeignKey( self, xea: XEinAus, xabr: XAbrechnung ):
        xea.nka_id = xabr.abr_id

    def getLeistungKuerzel( self ) -> str:
        """
        Das Kürzel, das in die Tabelle <einaus> in die Spalte <leistung> eingetragen wird.
        :return:
        """
        return "NKA"

    def getEinAusArt_display( self ):
        """
        Liefert die EinAusArt
        :return:
        """
        return EinAusArt.NEBENKOSTEN_ABRECHNG.display

    def getData( self ) -> NKAbrechnungData:
        return self._nkaData

    def getEinAusZahlungen( self, abr_id ) -> List[XEinAus]:
        return  self._eaData.getEinAuszahlungenByNkaId( abr_id )

    def validateDerived( self, xabr: XNKAbrechnung ) -> str:
        # der allgemeine Teil der Abrechnung (s. XAbrechnung) wurde schon geprüft.
        # Hier wird der spezielle Teil geprüft
        if not xabr.mv_id: return "Name des Mieters fehlt."
        return ""

    def _insertAbrechnung( self, xnka: XNKAbrechnung ) -> str:
        try:
            self._nkaData.insertAbrechnung( xnka )
            return ""
        except Exception as ex:
            self._nkaData.rollback()
            msg = "AbrechnungLogic._insertAbrechnung():\nFehler beim Insert der Abrechnung %d für " \
                  "Masterobjekt '%s'\n\nFehlermeldung:\n%s " % (xnka.ab_jahr, xnka.master_name, str( ex ))
            return msg

    def _updateAbrechnung( self, xnka: XNKAbrechnung ) -> str:
        try:
            self._nkaData.updateAbrechnung( xnka )
            return ""
        except Exception as ex:
            self._nkaData.rollback()
            msg = "NKAbrechnungLogic._updateAbrechnung():\nFehler beim Update der Abrechnung %d für " \
                  "Masterobjekt '%s'\n\nFehlermeldung:\n%s " % (xnka.ab_jahr, xnka.master_name, str( ex ))
            return msg

    def deleteAbrechnung( self, xabr:XAbrechnung ):
        try:
            self._nkaData.deleteAbrechnung( xabr )
        except Exception as ex:
            self._nkaData.rollback()
            raise Exception( str(ex) + "\nBetroffene NK-Abrechnung: %d" % xabr.abr_id )

    def _commit( self ):
        self._nkaData.commit()
