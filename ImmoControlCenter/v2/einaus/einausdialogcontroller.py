import copy
from typing import List, Callable, Iterable

from PySide2.QtCore import QObject, Signal
from PySide2.QtWidgets import QAction, QDialog, QApplication

import datehelper
from base.baseqtderivates import BaseComboBox, BaseEdit, FloatEdit, IntEdit, BaseCheckBox, SmartDateEdit, MultiLineEdit, \
    EditableComboBox, ButtonIdent, SignedNumEdit
from base.interfaces import VisibleAttribute
from base.messagebox import ErrorBox
from v2.einaus.einauslogic import EinAusLogic
from v2.einaus.einausview import EinAusTableView, EinAusTableViewFrame, XEinAusUI, EinAusDialog
from v2.einaus.einauswritedispatcher import EinAusWriteDispatcher
from v2.icc.constants import EinAusArt, Umlegbar, Modus, iccMonthShortNames

# ##############  EinAusController  ####################
from v2.icc.interfaces import XEinAus, XMasterobjekt, XMietobjekt, XKreditorLeistung, XLeistung

VERTEILT_AUF_DEFAULT = 1
# EINAUSART_DEFAULT = EinAusArt.ALLGEMEINE_KOSTEN
UMLEGBAR_DEFAULT = Umlegbar.JA.value

class EinAusDialogController( QObject ):
    def __init__( self ):
        QObject.__init__( self )
        self._x:XEinAus = None # das XEinAus-Objekt, das neu angelegt wurde oder geändert wird
        self._modus:str = Modus.UNK
        self._dlg: EinAusDialog = None
        self._logic = EinAusLogic()
        self._cboMasternames: BaseComboBox = None
        self._cboMietobjekte: BaseComboBox = None
        self._cboKreditoren: BaseComboBox = None
        self._cboLeistungen: BaseComboBox = None
        self._cboEinAus: BaseComboBox = None
        self._cboUmlegbar: BaseComboBox = None
        self._sneBetrag: SignedNumEdit = None
        self._ieJahr:IntEdit = None
        self._cboMonate:BaseComboBox = None

    def _createGui( self ) -> EinAusDialog:
        x = self._x
        masternames = self._logic.getMasterNamen()
        if self._modus == Modus.NEW:
            x.master_name = masternames[0]
        mietobjektenames = self._logic.getMietobjektNamen( x.master_name )
        kreditoren = self._logic.getKreditoren( x.master_name )
        if self._modus == Modus.NEW:
            x.buchungsdatum = datehelper.getCurrentDateIso()
        xui = XEinAusUI( x )
        vislist = self._createVisibleAttributeList( masternames, mietobjektenames, kreditoren,
                                                    self.onMasterChanged, self.onKreditorChanged,
                                                    self.onLeistungChanged, self.onEinAusArtChanged )
        xui.addVisibleAttributes( vislist )
        title = "Neue Zahlung anlegen" if x.ea_id <= 0 else "Zahlung ändern"
        dlg = EinAusDialog( xui, title )
        btnApply = dlg.getButton( ButtonIdent.IDENT_APPLY )
        btnApply.setText( "Speichern und Neu" )
        btnApply.setToolTip( "Mit jedem Drücken dieses Buttons wird eine neue Zahlung angelegt." )
        if self._modus == Modus.MODIFY:
            # bei einer Zahlungsänderung hat der Übernehmen-Button keinen Sinn,
            # nur bei Neuanlagen (hintereinander mehrfache Anlagen)
            btnApply.setEnabled( False )
        dlg.setCallbacks( self.onOk, self.onApply, self.onCancel )
        v = dlg.getDynamicAttributeView()
        # zum späteren schnellen Zugriff halten wir die Widgets als Membervariable:
        self._cboMasternames: BaseComboBox = v.getWidget( "master_name" )
        self._cboMietobjekte: BaseComboBox = v.getWidget( "mobj_id" )
        self._cboKreditoren: BaseComboBox = v.getWidget( "debi_kredi" )
        self._cboLeistungen: BaseComboBox = v.getWidget( "leistung" )
        self._cboEinAus: BaseComboBox = v.getWidget( "ea_art" )
        self._cboUmlegbar: BaseComboBox = v.getWidget( "umlegbar" )
        # self._feBetrag:FloatEdit = v.getWidget( "betrag" )
        self._sneBetrag: SignedNumEdit = v.getWidget( "betrag" )
        self._ieVerteiltAuf:IntEdit = v.getWidget( "verteilt_auf" )
        self._sdeBuchungsdatum:SmartDateEdit = v.getWidget( "buchungsdatum" )
        self._sdeBuchungsdatum.textChanged.connect( self.onBuchungsdatumChanged )
        self._ieJahr:IntEdit = v.getWidget( "jahr" )
        # Jahr übertragen in _ieJahr:
        self.onBuchungsdatumChanged( self._sdeBuchungsdatum.getDate() )
        # self._cboMonate:BaseComboBox = v.getWidget( "monat" )
        self._beBuchungstext:BaseEdit = v.getWidget( "buchungstext" )
        #self._mleMehrtext:MultiLineEdit = v.getWidget( "mehrtext" )
        self._dlg = dlg
        return dlg

    @staticmethod
    def _createVisibleAttributeList( masterobjekte:List[str], mietobjekte:List[str], kreditoren:List[str],
                                     onMasterChangedCallback:Callable, onKreditorChangedCallback:Callable,
                                     onLeistungChangedCallback:Callable,
                                     onEinAusArtChangedCallback:Callable ) \
            -> Iterable[VisibleAttribute]:
        smallW = 90
        vislist = (
            VisibleAttribute( "master_name", BaseComboBox, "Haus: ", nextRow=False,
                              comboValues=masterobjekte, comboCallback=onMasterChangedCallback ),
            VisibleAttribute( "mobj_id", BaseComboBox, "Wohnung: ", widgetWidth=150, comboValues=mietobjekte ),
            VisibleAttribute( "debi_kredi", EditableComboBox, "Zahlung an/von: ",
                              comboValues=kreditoren, comboCallback=onKreditorChangedCallback ),
            VisibleAttribute( "leistung", EditableComboBox, "Art d. Leistung: ",
                              comboCallback=onLeistungChangedCallback ),
            # VisibleAttribute( "betrag", FloatEdit, "Betrag: ", widgetWidth=smallW ),
            VisibleAttribute( "betrag", SignedNumEdit, "Betrag: ", widgetWidth=smallW+20 ),
            VisibleAttribute( "ea_art", BaseComboBox, "Art d. Zahlung: ", comboValues=EinAusArt.getEinAusDialogOptions(),
                              comboCallback=onEinAusArtChangedCallback ),
            VisibleAttribute( "verteilt_auf", IntEdit, "vert. auf Jahre: ", widgetWidth=smallW ),
            VisibleAttribute( "umlegbar", BaseComboBox, "umlegbar: ", widgetWidth=smallW,
                              comboValues=[Umlegbar.JA.value, Umlegbar.NEIN.value] ),
            VisibleAttribute( "buchungsdatum", SmartDateEdit, "Buchungsdatum: ", widgetWidth=smallW ),
            VisibleAttribute( "jahr", IntEdit, "Jahr (steuerl.): ", widgetWidth=smallW ),
            # VisibleAttribute( "monat", BaseComboBox, "Monat: ", comboValues=iccMonthShortNames, widgetWidth=smallW ),
            VisibleAttribute( "buchungstext", BaseEdit, "Text: ", columnspan=3 )
            #VisibleAttribute( "mehrtext", MultiLineEdit, "Bemerkung: ", widgetHeight=55, columnspan=3 )
        )
        return vislist


    def _resetDialog( self ):
        self._sneBetrag.setValue( 0.0 )
        self._ieVerteiltAuf.setValue( VERTEILT_AUF_DEFAULT )
        self._beBuchungstext.setValue( "" )
        self._x.ea_id = 0
        self._x.betrag = 0.0
        self._x.verteilt_auf = VERTEILT_AUF_DEFAULT
        self._x.buchungstext = ""

    def processNewEinAus( self ):
        """
        behandelt die Neuanlage einer (Ein-/Aus-)Zahlung
        :return: None
        """
        self._modus = Modus.NEW
        self._x = XEinAus()
        self._x.verteilt_auf = VERTEILT_AUF_DEFAULT
        self._x.umlegbar = UMLEGBAR_DEFAULT
        dlg = self._createGui()
        rc = dlg.exec_()
        if rc == QDialog.Accepted:
            EinAusWriteDispatcher.inst().einaus_inserted( self._x )

    def processEinAusModification( self, x:XEinAus ):
        self._modus = Modus.MODIFY
        oldx = copy.deepcopy( x )
        self._x = x
        dlg = self._createGui()
        if dlg.exec_() == QDialog.Accepted:
            delta = self._x.betrag - oldx.betrag
            EinAusWriteDispatcher.inst().einaus_updated( self._x, delta )

    def onMasterChanged( self, newMaster:str ):
        # Mietobjektnamen für geänderten Master ermitteln:
        mietobjektnamen = self._logic.getMietobjektNamen( newMaster )
        self._cboMietobjekte.clear()
        self._cboMietobjekte.addItems( mietobjektnamen )
        # Kreditoren für geänderten Master ermitteln:
        kreditoren = self._logic.getKreditoren( newMaster )
        self._cboKreditoren.clear()
        self._cboKreditoren.addItems( kreditoren )
        self._cboLeistungen.clear()

    def onKreditorChanged( self, newKreditor:str ):
        # Leistungen für den geänderten Kreditor ermitteln:
        master_name = self._cboMasternames.currentText()
        try:
            leistungen:List[str] = self._logic.getLeistungen( master_name, newKreditor )
        except Exception as ex:
            box = ErrorBox( "Datenbankfehler", str(ex), "Aufgetreten in EinAusDialogController.onKreditorChanged" )
            box.exec_()
            return
        self._cboLeistungen.clear()
        self._cboLeistungen.addItems( leistungen )

    def onLeistungChanged( self, newLeistung:str ):
        umlegbar = UMLEGBAR_DEFAULT
        ea_art_display = EinAusArt.ALLGEMEINE_KOSTEN.display
        if newLeistung:
            master_name = self._cboMasternames.currentText()
            kreditor = self._cboKreditoren.currentText()
            leist:XLeistung = self._logic.getLeistungskennzeichen( master_name, kreditor, newLeistung)
            if leist:
                umlegbar = Umlegbar.JA.value if leist.umlegbar else Umlegbar.NEIN.value
                ea_art_display = leist.ea_art
        self._cboUmlegbar.setCurrentText( umlegbar )
        self._cboEinAus.setCurrentText( ea_art_display )

    def onEinAusArtChanged( self, newEinAusArt ):
        if newEinAusArt == EinAusArt.REPARATUR.display:
            # Reparatur
            self._ieVerteiltAuf.setEnabled( True )
            self._cboUmlegbar.setCurrentText( Umlegbar.NEIN.value )
        else:
            # keine Reparatur
            self._ieVerteiltAuf.setValue( VERTEILT_AUF_DEFAULT )
            self._ieVerteiltAuf.setEnabled( True )
            if newEinAusArt == EinAusArt.ALLGEMEINE_KOSTEN.display:
                # Allgemeine Hauskosten
                self._cboUmlegbar.setCurrentText( Umlegbar.JA.value )
            else:
                self._cboUmlegbar.setCurrentText( Umlegbar.NEIN.value )

    def onBuchungsdatumChanged( self, buchungsdatum:str ):
        """
        Mit jeder Eintragung des Buchungsdatums müssen die Attribute <jahr> und <monat> versorgt werden.
        Das soll automatisch passieren, aber muss durch den Anwender änderbar sein (Dezember-/Januar-Thematik)
        :param buchungsdatum:
        :return:
        """
        #print( "onBuchungsdatumChanged")
        if buchungsdatum:
            year, mon, day = datehelper.getDateParts( buchungsdatum )
            self._ieJahr.setIntValue( year )

    def onOk( self ) -> str:
        """
        callback-fnc die vom EinAusDialog nach "OK" aufgerufen wird
        :return: None, wenn Validierung und Speichern geklappt hat, sonst eine Fehlermeldung
        """
        return self.trySave()

    def onApply( self ) -> str:
        """
        callback-fnc die vom EinAusDialog nach "Übernehmen" aufgerufen wird
        :return: :return: None, wenn Validierung und Speichern geklappt hat, sonst eine Fehlermeldung
        """
        msg = self.trySave()
        if msg:
            return msg
        else:
            self._resetDialog()
            return  ""

    def onCancel( self ) -> str:
        return "Wirklich abbrechen?"

    def trySave( self ) -> str:
        v = self._dlg.getDynamicAttributeView()
        xcopy:XEinAus = v.getModifiedXBaseCopy()
        try:
            msg = self._logic.trySaveZahlung( xcopy )
        except Exception as ex:
            msg = "EinAusDialogController.trySave():\nException beim Speichern der Zahlung.\n" + str( ex )
        if not msg:
            v.updateData()
            self._x.write_time = xcopy.write_time
            if self._modus == Modus.NEW:
                self._x.ea_id = xcopy.ea_id
            self._checkForNewItems()
        return msg

    def _checkForNewItems( self ):
        """
        Prüft, ob in einer der Comboboxen Zahlung an/von und Art der Leistung ein neues
        Item eingegeben wurde.
        Wenn ja, speichern.
        :return:
        """
        kredleist_new:XKreditorLeistung = \
            self._logic.checkKreditorLeistung( self._x.master_name, self._x.debi_kredi, self._x.leistung,
                                               self._x.umlegbar, self._x.ea_art )
        if kredleist_new:
            # currentKreditor = self._cboKreditoren.currentText()
            # currentLeistung = self._cboLeistungen.currentText()
            try:
                kreditoren = self._logic.getKreditoren( self._cboMasternames.currentText() )
            except Exception as ex:
                box = ErrorBox( "Datenbankfehler", str( ex ), "Aufgetreten in EinAusDialogController._checkForNewItems" )
                box.exec_()
                return
            self._cboKreditoren.clear()
            self._cboKreditoren.addItems( kreditoren )
            # self._cboKreditoren.setCurrentText( currentKreditor )
            # self._cboLeistungen.setCurrentText( currentLeistung )


# #####################   TEST   TEST   TEST   ##################

def test3():
    app = QApplication()
    x = XEinAus()
    x.ea_id = 124
    x.master_name = "NK_Kleist"
    x.mobj_id = "kleist_12"
    x.debi_kredi = "Fuchs"
    x.leistung = "nix Genaues"
    x.jahr = 2022
    x.monat = "nov"
    x.betrag = 111.0
    x.ea_art = "a"
    x.umlegbar = Umlegbar.JA.value
    x.buchungsdatum = "2022-11-28"
    x.write_time = "2022-11-28:14.18.09.358989"
    c = EinAusDialogController()
    c.processEinAusModification( x )
    print( "...und feddich." )
    x.print()

def test():
    app = QApplication()
    c = EinAusDialogController()
    c.processNewEinAus()