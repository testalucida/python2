import copy
from typing import Iterable, List

from PySide2.QtCore import QSize, QObject, Signal

import datehelper
from base.baseqtderivates import BaseEdit, SmartDateEdit, FloatEdit, MultiLineEdit, ButtonIdent, IntEdit, \
    BaseDialogWithButtons, getOkCancelButtonDefinitions, SignedNumEdit
from base.basetableview import BaseTableView
from base.basetableviewframe import BaseTableViewFrame
from base.dynamicattributeui import DynamicAttributeDialog
from base.interfaces import VisibleAttribute, ButtonDefinition
from v2.abrechnungen.abrechnungenview import XAbrechnungUI
from v2.abrechnungen.abrechnunglogic import HGAbrechnungLogic, TeilzahlungTableModel, AbrechnungLogic
from v2.einaus.einausview import ValueDialog, TeilzahlungDialog
from v2.icc.interfaces import XHGAbrechnung, XAbrechnung, XTeilzahlung, XNKAbrechnung


class AbrechnungDialogController:
    """
    Controller für den dynamisch zu erzeugenden AbrechnungDialog, mit dem
    genau 1 Abrechnung geändert wird.
    Geändert wird entweder die Abrechnung selbst (Abrechnungsdatum, Forderung, Entnahme aus Rücklagen, Bemerkung)
    ODER
    eine (Teil-)Zahlung, die auf die erhobene Forderung geleistet wird.
    """
    def __init__( self, xabr:XAbrechnung, logic:AbrechnungLogic ):
        self._xabr_orig = xabr
        self._xabr = copy.deepcopy( xabr )
        self._isNka = ( type( xabr ) == XNKAbrechnung )
        self._logic = logic
        self._xui = XAbrechnungUI( self._xabr )
        self._dlg:DynamicAttributeDialog = None

    def processAbrechnung( self ):
        if self._isNka:
            vislist = self._createVisibleAttributeListNKA()
        else:
            vislist = self._createVisibleAttributeListHGA()
        self._xui.addVisibleAttributes( vislist )
        title = "Hausgeldabrechnung eintragen/ändern für Objekt '%s'" % self._xabr.master_name
        self._dlg = dlg = DynamicAttributeDialog( self._xui, title )
        btnApply = dlg.getButton( ButtonIdent.IDENT_APPLY )
        btnApply.setEnabled( False )
        dlg.setCallbacks( self.onOk, None, self.onCancel )
        dlg.setMinimumWidth( 500 )
        v = dlg.getDynamicAttributeView()
        w = v.getWidget( "forderung" )
        w.setFocus()
        dlg.exec_()

    def onOk( self ) -> str:
        """
        Im Dialog "Hausgeldabrechnung eintragen/ändern für Objekt..." wurde OK gedrückt.
        Die neuen oder geänderten Werte validieren und - wenn Validierung ok - speichern.
        Dialog schließen.
        :return:
        """
        dlg = self._dlg
        v = dlg.getDynamicAttributeView()
        xcopy: XAbrechnung = v.getModifiedXBaseCopy()
        # der logic übergeben zum Validieren
        msg = self._logic.validateAbrechnung( xcopy )
        if not msg:
            # Validierung war ok, jetzt die geänderten Daten von der View ins Model übernehmen, dann
            # das Model speichern
            dlg.getDynamicAttributeView().updateData()
            xabr = dlg.getDynamicAttributeView().getXBase()
            msg = self._logic.trySave( xabr )
            if not msg:
                self._xabr_orig.updateFromOther( xabr )
                self._updateZahlung( xabr.teilzahlungen )
        return msg

    def onCancel( self ) -> str:
        """
        Dialog "Hausgeldabrechnung eintragen/ändern für Objekt..." wurde Abbrechen gedrückt.
        Dialog schließen.
        :return:
        """
        return ""

    def onEditZahlungen( self ):
        """
        Im Dialog "Hausgeldabrechnung eintragen/ändern für Objekt ..." wurde der Button "(Teil-)Zahlung erfassen/ändern"
        neben dem Zahlungsfeld gedrückt.
        Die Verarbeitung wird an den TeilzahlungController übergeben.
        :return:
        """
        #feZahlung = self._dlg.getDynamicAttributeView().getWidget( "zahlung" )
        tzctrl = TeilzahlungController( self._xabr, self._logic )
        # tzctrl.teilzahlung_added.connect( self.onTeilzahlungAdded )
        # tzctrl.teilzahlung_modified.connect( self.onTeilzahlungModified )
        # tzctrl.teilzahlung_deleted.connect( self.onTeilzahlungDeleted )
        tzctrl.teilzahlung_processing_finished.connect( self.onTeilzahlungProcessingFinished )
        tzctrl.processTeilzahlung()

    def onTeilzahlungProcessingFinished( self, tm:TeilzahlungTableModel ):
        # die Arbeiten an den Teilzahlungen im Teilzahlungsdialog oder ValueDialog sind beendet.
        # Wir übernehmen die aktualisierten Zahlungen in das Abrechnungsobjekt self._xabr (welches nur eine
        # Kopie des bei der Instanzierung übergebenen Originals ist).
        teilzahlungen = tm.getAllElements()
        self._xabr.teilzahlungen = teilzahlungen
        self._updateZahlung( teilzahlungen )

    def _updateZahlung( self, teilzahlungen: List[XTeilzahlung] ):
        tzsum = sum( [tz.betrag for tz in teilzahlungen] )
        v = self._dlg.getDynamicAttributeView()
        feZahlung = v.getWidget( "zahlung" )
        feZahlung.setFloatValue( tzsum )

    def _createVisibleAttributeListNKA( self ) -> Iterable[VisibleAttribute]:
        smallW = 90
        vislist = (
            VisibleAttribute( "master_name", BaseEdit, "Haus: ", editable=False ),
            VisibleAttribute( "mobj_id", BaseEdit, "Wohnung: ", editable=False ),
            VisibleAttribute( "mv_id", BaseEdit, "Mieter: ", editable=False ),
            VisibleAttribute( "ab_jahr", IntEdit, "Abrechnung für: ", editable=False, widgetWidth=smallW ),
            VisibleAttribute( "ab_datum", SmartDateEdit, "abgerechnet am: ", widgetWidth=smallW ),
            VisibleAttribute( "forderung", SignedNumEdit, "Forderung (€): ", widgetWidth=smallW ),
            VisibleAttribute( "bemerkung", MultiLineEdit, "Bemerkung: ", widgetHeight=55 ),
            VisibleAttribute( "zahlung", FloatEdit, "Zahlung (€): ", widgetWidth=smallW, editable=False,
                              trailingButton=ButtonDefinition(
                                  "...", callback=self.onEditZahlungen, tooltip="(Teil-)Zahlung erfassen / ändern",
                                  ident="tz", maxW=30, maxH=30
                              ) )
        )
        return vislist

    def _createVisibleAttributeListHGA( self ) -> Iterable[VisibleAttribute]:
        smallW = 90
        vislist = (
            VisibleAttribute( "master_name", BaseEdit, "Haus: ", editable=False ),
            VisibleAttribute( "weg_name", BaseEdit, "WEG: ", editable=False ),
            VisibleAttribute( "mobj_id", BaseEdit, "Wohnung: ", editable=False ),
            VisibleAttribute( "vw_id", BaseEdit, "Verwalter: ", editable=False ),
            VisibleAttribute( "ab_jahr", IntEdit, "Abrechnung für: ", editable=False, widgetWidth=smallW ),
            VisibleAttribute( "ab_datum", SmartDateEdit, "abgerechnet am: ", widgetWidth=smallW ),
            VisibleAttribute( "forderung", SignedNumEdit, "Forderung (€): ", widgetWidth=smallW ),
            VisibleAttribute( "entnahme_rue", SignedNumEdit, "Entnahme aus Rückl. (€): ", widgetWidth=smallW ),
            VisibleAttribute( "bemerkung", MultiLineEdit, "Bemerkung: ", widgetHeight=55 ),
            VisibleAttribute( "zahlung", FloatEdit, "Zahlung (€): ", widgetWidth=smallW, editable=False,
                              trailingButton=ButtonDefinition(
                                  "...", callback=self.onEditZahlungen, tooltip="(Teil-)Zahlung erfassen / ändern",
                                  ident="tz", maxW=30, maxH=30
                              ) )
        )
        return vislist

######################   TeilzahlungController   #####################
class TeilzahlungController( QObject ):
    """
    Controller, der die Erfassung, Änderung und Löschung von Teilzahlungen einer Abrechnung übernimmt.
    Dazu kommt wahlweise der ValueDialog oder der TeilzahlungDialog zum Einsatz.
    Er führt keine Speicheraktionen durch, sondern sendet ein Signal für jede neu anzulegende, zu ändernde
    und zu löschende Teilzahlung.
    """
    # teilzahlung_added = Signal( XTeilzahlung )
    # teilzahlung_modified = Signal( XTeilzahlung )
    # teilzahlung_deleted = Signal( XTeilzahlung )
    # teilzahlung_processing_finished = Signal( list, list, list )
    teilzahlung_processing_finished = Signal( TeilzahlungTableModel )

    def __init__( self, xabr:XAbrechnung, logic:AbrechnungLogic ):
        """
        Achtung: der TeilzahlungController verändert xabr NICHT.
        Es wird eine Kopie von xabr erzeugt, die bearbeitet wird.
        :param logic:
        """
        QObject.__init__( self )
        self._xabr = copy.deepcopy( xabr )
        self._logic = logic
        self._tm:TeilzahlungTableModel = self._logic.getTeilzahlungTableModel( self._xabr )
        self._dlg:TeilzahlungDialog = None
        #self._tzAdd:List[XTeilzahlung] = list()
        self._tzMod: List[XTeilzahlung] = list()
        # self._tzDel: List[XTeilzahlung] = list()

    def processTeilzahlung( self ):
        # erstmal entscheiden, ob der ValueDialog oder der Teilzahlungsdialog geöffnet wird.
        # Wenn es noch keine Teilzahlung gibt, kann der ValueDialog verwendet werden.
        if len( self._xabr.teilzahlungen ) == 0:
            # es gibt noch keine (gespeicherte) Zahlung zur ausgewählten Abrechnung.
            # Deshalb erfassen oder ändern wir (eine evtl. vorhd. *nicht gespeicherte* Zahlung)
            # mit dem kleinen ValueDialog.
            self._processViaValueDialog( parentIsTzDialog=False )
        else:
            self._processViaTeilzahlungDialog()

    def _processViaValueDialog( self, parentIsTzDialog=True ):
        def validate( value: float, text: str, buchungsdatum: str ) -> str:
            # wird aufgerufen, wenn im ValueDialog OK gedrückt wurde
            if not value:
                return "Es ist kein Wert angegeben."
            if buchungsdatum and not datehelper.isValidIsoDatestring( buchungsdatum ):
                return "Datum im falschen Format. Muss YYYY-MM-DD sein."
            tz = XTeilzahlung( value, buchungsdatum, text )
            self._tm.addObject( tz )
            #self._tzAdd.append( tz )
            if not parentIsTzDialog:
                # der ValueDialog wurde direkt vom Abrechnungsdialog aufgerufen, nicht vom Teilzahlungsdialog.
                # Nach Schließen des ValueDialogs befindet sich der User wieder im Abrechnungsdialog.
                # self.teilzahlung_processing_finished.emit( self._tzAdd, list(), list() )
                self.teilzahlung_processing_finished.emit( self._tm )
            return ""
        valuedlg = ValueDialog( mitBuchungsdatum=True)
        valuedlg.setCallback( validate )
        if not parentIsTzDialog:
            valuedlg.setValue( self._xabr.forderung )
            valuedlg.setBuchungsdatum( datehelper.getCurrentDateIso() )
        valuedlg.exec_()

    def _processViaTeilzahlungDialog( self ):
        ########### callbacks für Tz-Dialog
        def onNewTeilzahlung():
            # es soll eine neue Teilzahlung angelegt werden.
            # Dazu wird der ValueDialog geöffnet
            self._processViaValueDialog( parentIsTzDialog=True )

        def onEditTeilzahlung( row: int ):
            def validate( value: float, text: str, buchungsdatum: str ) -> str:
                # wird aufgerufen, wenn im ValueDialog OK gedrückt wurde
                if not value:
                    return "Es ist kein Wert angegeben."
                if buchungsdatum and not datehelper.isValidIsoDatestring( buchungsdatum ):
                    return "Datum im falschen Format. Muss YYYY-MM-DD sein."
                tz.betrag = value
                tz.buchungstext = text
                tz.buchungsdatum = buchungsdatum
                return ""
            tz: XTeilzahlung = self._tm.getElement( row )
            valuedlg = ValueDialog( mitBuchungsdatum=True )
            valuedlg.setValue( tz.betrag )
            valuedlg.setBuchungsdatum( tz.buchungsdatum )
            valuedlg.setBemerkung( tz.buchungstext )
            valuedlg.setCallback( validate )
            valuedlg.exec_()

        def onDeleteTeilzahlung( rows: Iterable[int] ):
            for row in rows:
                tz:XTeilzahlung = self._tm.getElement( row )
                self._tm.removeObject( tz )
                # self._tzDel.append( tz )
                # zahlung = self._feZahlung.getFloatValue()
                # zahlung -= x.betrag
                # self._feZahlung.setValue( zahlung )
        ###########  end callbacks

        # Öffnet den Teilzahlungsdialog (mit der Übersicht über die bisher geleisteten Zahlungen):
        self._dlg = self._createTeilzahlungDialog( self._xabr, onNewTeilzahlung, onEditTeilzahlung, onDeleteTeilzahlung,
                                                   self.onTzDialogOk, self.onTzDialogCancel )
        self._dlg.exec_()

    def _createTeilzahlungDialog( self, xabr:XAbrechnung, newTzCallback, editTzCallback, deleteTzCallback,
                                  okCallback, cancelCallback ) -> BaseDialogWithButtons:
        # self._tm = self._logic.getTeilzahlungTableModel( xabr )
        tv = BaseTableView()
        tv.setModel( self._tm )
        tvf = BaseTableViewFrame( tv, withEditButtons=True )
        tvf.newItem.connect( newTzCallback )
        tvf.editItem.connect( editTzCallback )
        tvf.deleteItems.connect( deleteTzCallback )
        w = tvf.getPreferredWidth()
        title = "Teilzahlungen für Objekt %s, Abrechnung %d, Forderung: %.2f Euro" % \
                (xabr.master_name, xabr.ab_jahr, xabr.forderung)
        dlg = BaseDialogWithButtons( title, getOkCancelButtonDefinitions( okCallback, cancelCallback ) )
        dlg.setMainWidget( tvf )
        dlg.resize( QSize( w, dlg.height() ) )
        return dlg

    def onTzDialogOk( self ):
        self._dlg.close()
        # self.teilzahlung_processing_finished.emit( self._tzAdd, self._tzMod, self._tzDel )
        self.teilzahlung_processing_finished.emit( self._tm )

    def onTzDialogCancel( self ):
        self._dlg.close()
        # self.teilzahlung_processing_finished.emit( list(), list(), list() )
        self.teilzahlung_processing_finished.emit( self._tm )



#####################    TEST  TEST  TEST  TEST   #######################

def test():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    xhga = XHGAbrechnung()
    xhga.abr_id = 0
    xhga.master_name = "NK_Volkerstal"
    xhga.weg_name = "WEG Volkerstal"
    xhga.vw_id = "grunge"
    xhga.vwg_id = 33
    xhga.vwg_von = "2019-01-01"
    xhga.ab_jahr = 2022
    xhga.ab_datum = datehelper.getCurrentDateIso()
    xhga.forderung = 123.40
    logic = HGAbrechnungLogic()
    c = AbrechnungDialogController( xhga, logic )
    c.processAbrechnung()
    #app.exec_()


