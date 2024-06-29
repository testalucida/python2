from abc import abstractmethod
from typing import List, Iterable, Callable

from PySide2.QtCore import QModelIndex, QSize, Signal, Slot
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QAction, QDialog, QMenu, QApplication

from base.baseqtderivates import BaseEdit, FloatEdit, IntEdit, MultiLineEdit, BaseAction, SumDialog, Separator, \
    SmartDateEdit, BaseComboBox, SignedNumEdit
from base.basetablefunctions import BaseTableFunctions
from base.basetableview import BaseTableView
from base.dynamicattributeui import DynamicAttributeDialog
from base.interfaces import XBaseUI, VisibleAttribute
from base.messagebox import ErrorBox, InfoBox
from generictable_stuff.okcanceldialog import OkCancelDialog
from v2.einaus.einauslogic import EinAusTableModel
from v2.einaus.einausview import EinAusTableView, TeilzahlungDialog, ValueDialog
from v2.einaus.einauswritedispatcher import EinAusWriteDispatcher
from v2.icc import constants
from v2.icc.constants import Action, Modus, EinAusArt, Umlegbar
from v2.icc.icccontroller import IccController
from v2.icc.iccwidgets import IccCheckTableViewFrame, IccTableView
from v2.icc.interfaces import XMtlZahlung, XEinAus, XSollAbschlag, XMtlAbschlag
from v2.mietobjekt.mietobjektcontroller import MietobjektController
#from v2.mietverhaeltnis.mietverhaeltniscontroller import MietverhaeltnisController
from v2.mtleinaus.mtleinauslogic import MieteLogic, MtlEinAusTableModel, MtlEinAusLogic, MieteTableModel, HausgeldLogic, \
    HausgeldTableModel, AbschlagLogic, AbschlagTableModel
from v2.mtleinaus.mtleinausview import MieteTableView, MieteTableViewFrame, \
    HausgeldTableView, HausgeldTableViewFrame, AbschlagTableView, AbschlagTableViewFrame


#############  MtlEinAusController  #####################
from v2.sollmiete.sollmietecontroller import SollMieteController


class MtlEinAusController( IccController ):
    show_objekt = Signal( str )
    def __init__( self ):
        IccController.__init__( self )
        self._tableViewFrame:IccCheckTableViewFrame = None
        self._tv:IccTableView = None
        self._newEinAus:XEinAus = None # hier werden ggf. neu angelegte Zahlungen geparkt

    def createGui( self ) -> IccCheckTableViewFrame:
        jahr, monthIdx = self.getYearAndMonthToStartWith()
        tvf:IccCheckTableViewFrame = self.createTableViewFrame( jahr, monthIdx )
        tb = tvf.getToolBar()
        jahre = self.getJahre()
        if len( jahre ) == 0:
            jahre.append( jahr )
        tb.addYearCombo( jahre, self.onYearChanged )
        tb.setYear( jahr )
        tb.addMonthCombo( self.onMonthChanged )
        tb.setMonthIdx( monthIdx )
        tv = tvf.getTableView()
        tv.setContextMenuCallbacks( self.provideActions, None ) #self.onSelected )
        tv.okClicked.connect( self.onBetragOk )
        tv.nokClicked.connect( self.onBetragEdit )
        self._tableViewFrame = tvf
        self._tv = tv
        return tvf

    def getMenu( self ) -> QMenu:
       return None

    @abstractmethod
    def getSollActions( self ) -> List[BaseAction]:
        pass

    @abstractmethod
    def createTableViewFrame( self, jahr:int, monat:int ) -> IccCheckTableViewFrame:
        pass

    @abstractmethod
    def createModel( self, jahr: int, monat: int ) -> MtlEinAusTableModel:
        pass

    @abstractmethod
    def getModel( self ) -> MtlEinAusTableModel:
        pass

    @abstractmethod
    def getLogic( self ) -> MtlEinAusLogic:
        pass

    @abstractmethod
    def getEinzelzahlungenModelMonat( self, debikredi:str, sab_id:int, jahr:int, monthIdx:int, mobj_id:str=None ) -> EinAusTableModel:
        pass

    @abstractmethod
    def provideContextMenuActions( self, model:MtlEinAusTableModel, row:int, key:str ) -> List[BaseAction]:
        pass

    @abstractmethod
    def getShowDebiKrediActions( self ) -> List[BaseAction]:
        pass

    @abstractmethod
    def getSollAction( self ) -> BaseAction:
        pass

    @abstractmethod
    def onSpecificAction( self, action:Action ):
        pass

    @abstractmethod
    def onYearChanged( self, newYear: int ):
        pass

    @abstractmethod
    def getDefaultSign( self ) -> str:
        return "minus"

    def onMonthChanged( self, newMonthIdx:int, newMonthLongName:str = "" ) :
        model: MtlEinAusTableModel = self.getModel()
        model.setEditableMonth( newMonthIdx )
        self.getLogic().selectedMonthChanged( model, newMonthIdx )

    def provideActions( self, index, point, selectedIndexes ) -> List[QAction]:
        """
        Callback-Function, die zur Verfügung stehende Aktionen liefert, wenn der User durch Rechtsklick
        in eine Tabellenzelle das Kontextmenü öffnen möchte
        :param index:
        :param point:
        :param selectedIndexes:
        :return:
        """
        model: MieteTableModel = self._tv.model()
        col = index.column()
        key = model.keys[col]
        actions = self.provideContextMenuActions( model, index.row(), key )
        if actions:
            actions.append( Separator() )
        else:
            actions = list()
        if col >= model.idxJanuarColumn:
            idxlist = self._tv.selectedIndexes()
            if len( idxlist ) > 1:
                action = BaseAction( "Berechne Summe..." )
                action.triggered.connect(  self._computeSumme )
                if not actions:
                    actions = list()
                actions.append( action )
                actions.append( Separator() )
            else:
                if key != 'summe':
                    a = BaseAction( "Zahlungsdetails anzeigen..." )
                    a.triggered.connect( self.onShowZahlungsdetails )
                    actions.append( a )
                    actions.append( Separator() )
        a = BaseAction( "Kopiere" )
        a.triggered.connect( self.copySelectionToClipboard )
        actions.append( a )
        return actions

    def onShowZahlungsdetails( self, dummy ):
        indexes = self._tv.selectedIndexes()
        model: MtlEinAusTableModel = self.getModel()
        mieter = model.getDebiKredi( indexes[0].row() )
        monat = model.getHeader( indexes[0].column() )
        monatkey = model.getKeyByHeader( monat )
        monatidx = constants.iccMonthShortNames.index( monatkey )
        eamodel = self.getEinzelzahlungenModelMonat( mieter, None, model.getSelectedYear(), monatidx )
        tv = BaseTableView()
        tv.setModel( eamodel )
        dlg = OkCancelDialog()
        dlg.setWindowTitle( "Zahlungsdetails " + mieter + " im Monat " + monat + " " + str(model.getSelectedYear() ) )
        dlg.addWidget( tv, 0 )
        h = tv.getPreferredHeight()
        w = tv.getPreferredWidth()
        dlg.resize( QSize( w+50, h+100 ) )
        dlg.exec_()

    def onBetragOk( self, index:QModelIndex ):
        model:MtlEinAusTableModel = self.getModel()
        row = index.row()
        col = model.getEditableColumnIdx()
        val = model.getValue( row, col )
        if val != 0:
            box = ErrorBox( "Übernahme des Soll-Werts nicht möglich.", "Der Monatswert ist bereits versorgt.",
                            "Vor Übernehmen des Soll-Werts muss der eingetragene Wert gelöscht werden." )
            box.exec_()
            return
        sollVal = model.getSollValue( row )
        if sollVal == 0:
            box = ErrorBox( "Übernahme des Soll-Werts nicht möglich.",
                            "Ein Sollwert von '0' kann nicht übernommen werden.", "" )
            box.exec_()
            return
        self._addZahlung( row, sollVal )

    def onBetragEdit( self, index: QModelIndex ):
        def showValueDialog():
            vdlg = ValueDialog()
            defaultSign = self.getDefaultSign()
            if defaultSign == "plus":
                vdlg.setSignPlus()
            else:
                vdlg.setSignMinus()
            crsr = QCursor.pos()
            vdlg.setCallback( editing_done )
            vdlg.move( crsr.x(), crsr.y() )
            rc = vdlg.exec_()
            return rc

        def editing_done( val:float, bemerkung:str ):
            # callback für den ValueDialog, der dann zum Einsatz kommt, wenn es für einen Monat keine oder nur eine
            # Zahlung gibt.
            self._addZahlung( index.row(), val, bemerkung )
            eatm.addObject( self._newEinAus )

        def onNewItem():
            showValueDialog()

        def onEditItem( row:int ):
            """
            Callback vom MtlZahlungEditDialog.
            Ausgewählte Zahlung im DynamicAttributeDialog ändern lassen.
            TeilzahlungDialog aktualisieren.
            MtlEinAusTableView aktualisieren (Geänderte Zahlung anzeigen).
            :param row: Zeile des zu ändernden XEinAus-Objekts
            :return:
            """
            debikrediLabel = self.getModel().getDebiKrediHeader() + ": "
            x:XEinAus = eatm.getElement( row )
            xui = XBaseUI( x )
            vislist = ( VisibleAttribute( "master_name", BaseEdit, "Haus: ", editable=False, nextRow=False ),
                        VisibleAttribute( "mobj_id", BaseEdit, "Wohnung: ", editable=False, nextRow=False ),
                        VisibleAttribute( "debi_kredi", BaseEdit, debikrediLabel, editable=False ),
                        VisibleAttribute( "jahr", IntEdit, "Jahr: ", editable=False, widgetWidth=50 ),
                        VisibleAttribute( "monat", BaseEdit, "Monat: ", widgetWidth=50, editable=False ),
                        VisibleAttribute( "betrag", FloatEdit, "Betrag: ", widgetWidth=60, nextRow=False ),
                        VisibleAttribute( "buchungstext", MultiLineEdit, "Bemerkung: ", widgetHeight=60 ),
                        VisibleAttribute( "write_time", BaseEdit, "gebucht am: ", editable=False, columnspan=2 ) )
            xui.addVisibleAttributes( vislist )
            dyndlg = DynamicAttributeDialog( xui, "Ändern einer Monatszahlung" )
            if dyndlg.exec_() == QDialog.Accepted:
                v = dyndlg.getDynamicAttributeView()
                xcopy = v.getModifiedXBaseCopy()
                msg = self.getLogic().validateMonatsZahlung( xcopy )
                if msg:
                    box = ErrorBox( "Validierungsfehler", msg, xcopy.toString( printWithClassname=True ) )
                    box.exec_()
                    return
                v.updateData() # Validierung war ok, also Übernahme der Änderungen ins XBase-Objekt
                try:
                    # aus dem MtlZahlungenEditDialog die Liste der Einzelzahlungen holen,
                    # die in Summe die Monatszahlung ergeben:
                    xlist:List[XEinAus] = eatm.getAllElements()
                    self._updateZahlung( x, xlist, row )
                except Exception as ex:
                    box = ErrorBox( "Fehler beim Ändern einer Monatszahlung", str( ex ), x.toString( True ) )
                    box.exec_()
                    return
            else:
                # cancelled
                return

        def onDeleteItems( rowlist:List[int] ):
            """
            Callback vom MtlZahlungEditDialog.
            Ausgewählte Zahlungen in <rowlist> löschen, MtlZahlungEditDialog aktualisieren (Row entfernen),
            MtlEinAusTableView aktualisieren (den Betrag der gelöschten Zahlung vom Monatswert abziehen).
            :param rowlist:
            :return:
            """
            try:
                self._deleteZahlungen( eatm, rowlist )
            except Exception as ex:
                box = ErrorBox( "Fehler beim Delete", str( ex ),
                                "\nException aufgetreten in MtlEinAusController.onBetragEdit.onDeleteItems" )
                box.moveToCursor()
                box.exec_()

        monatstm:MtlEinAusTableModel = self.getModel()
        monthIdx = monatstm.getSelectedMonthIdx()
        eatm = self.getEinzelzahlungenModelMonat( monatstm.getDebiKredi( index.row() ),
                                                  monatstm.getSab_id( index.row() ),
                                                  self._year, monthIdx,
                                                  monatstm.getMietobjekt( index.row() ) )
        if eatm.rowCount() > 0:
            # Es gibt schon eine Zahlung für den betreff. Monat.
            # Deshalb den TeilzahlungDialog zeigen, damit der User die Zahlung auswählen kann, die er ändern oder
            # löschen will. Er kann auch eine neue Zahlung anlegen.
            eatv = EinAusTableView()
            eatv.setModel( eatm )
            dlg = TeilzahlungDialog( eatv )
            tvframe = dlg.getTableViewFrame()
            tvframe.newItem.connect( onNewItem )
            tvframe.editItem.connect( onEditItem )
            tvframe.deleteItems.connect( onDeleteItems )
            w = tvframe.getPreferredWidth()
            h = tvframe.getPreferredHeight()
            dlg.resize( QSize( w, h ) )
            dlg.exec_()
        else:
            # Es gibt noch keine Zahlung für den betreff. Monat,
            # deshalb können wir den "kleinen" Dialog zeigen
            showValueDialog()



    def _addZahlung( self, row:int, value:float, bemerkung="" ) -> XEinAus or None:
        model: MtlEinAusTableModel = self.getModel()
        selectedMonthIdx = model.getSelectedMonthIdx()
        selectedYear = model.getJahr()
        try:
            # Datenbank-Insert
            x:XMtlZahlung = model.getElement( row ) # das OBjekt, in das die neue Monatszahlung eingetragen werden soll
            self._newEinAus = self.getLogic().addMonatsZahlung( x, selectedYear, selectedMonthIdx, value, bemerkung )
            # EinAusWriteDispatcher informieren, damit die tableview "Alle Zahlungen" und die Summenfelder
            # aktualisiert werden
            EinAusWriteDispatcher.inst().einaus_inserted( self._newEinAus )
        except Exception as ex:
            box = ErrorBox( "Fehler beim Aufruf von MieteLogic.addZahlung(...) ",
                            "Exception in MtlEinAusController._addZahlung():\n" +
                            str( ex ), "" )
            box.exec_()
            return None
        # Update von Model und View
        editColIdx = model.getEditableColumnIdx()
        oldval = model.getValue( row, editColIdx )
        model.setValue( row, editColIdx, oldval + value )
        return self._newEinAus

    def _updateZahlung( self, x:XEinAus, xlist:List[XEinAus], row ):
        """
        Die Zahlung <x>, die Teil einer Monatszahlung ist, wurde geändert.
        (Der angezeigte Monatswert kann aus 0 bis n einzelnen Zahlungen bestehen.)
        Der angezeigte Monatswert muss deshalb aktualisiert werden.
        Alle relevanten Einzelzahlungen sind in xlist vorhanden.
        Zunächst erfolgt der Datenbank-Update mit der geänderten Zahlung <x>.
        Danach werden alle Einzelzahlungen in xlist addiert, was den neuen Monatswert ergibt.
        Mit diesem wird das MtlEinAusTableModel aktualisiert.
        :param x: die geänderte Zahlung
        :param xlist: Liste aller Zahlungen des betreff. Monats
        :param row: Die Zeile im MtlEinAusTableModel, in der sich das zu ändernde XMtlZahlung-Objekt befindet
        :return: 
        """
        try:
            # Datenbank-Update:
            delta = self.getLogic().updateMonatsZahlung( x, self.getModel() )
            # EinAusWriteDispatcher informieren, damit die tableview "Alle Zahlungen" und die Summenfelder
            # aktualisiert werden
            EinAusWriteDispatcher.inst().einaus_updated( x, delta )
        except Exception as ex:
            box = ErrorBox( "Fehler beim Aufruf von MtlEinAusLogic.updateMonatsZahlung(...) ",
                            "Exception in MtlEinAusController._updateZahlung():\n" +
                            str( ex ), "" )
            box.exec_()
            return None

    def _deleteZahlungen( self, eatm:EinAusTableModel, rowlist:List[int] ):
        """
        Ein oder mehrere Einzelzahlungen, die zu einem Monatswert gehören, sollen gelöscht werden.
        :param eatm: EinAusTableModel, das die Einzelzahlungen enthält, die in Summe einen Monatswert ausmachen.
        :param rowlist: Liste der zu löschenden Zeilennummern.
                        Es handelt sich um das Model der Einzelzahlungen, die die Monatszahlung ergeben.
        :return:
        """
        if len( rowlist ) < 1: return
        xlist: List[XEinAus] = eatm.getElements( rowlist )
        ea_id_list = [x.ea_id for x in xlist]
        ea_art = xlist[0].ea_art # Annahme, dass alle ea_art'en gleich sind. Überprüft wird das im Logik-Modul.
        # wir übergeben der Logik die Einzelzahlungen in xlist zum Löschen aus der <einaus>.
        # Außerdem übergeben wir das Model mit den XMtlZahlung-Objekten. (Ein XMtlZahlung-Objekt ist aus
        # der Saldierung mehrerer XEinAus-Objekte entstanden.
        delta = self.getLogic().deleteZahlungen( xlist, self.getModel() )
        # hat geklappt - jetzt die gelöschten Zahlungen aus dem MtlZahlungEditDialog
        # ("Ändern/Ergänzen von Zahlungen") entfernen:
        eatm.removeObjects( xlist )
        # EinAusWriteDispatcher informieren, damit die tableview "Alle Zahlungen" und die Summenfelder
        # aktualisiert werden
        EinAusWriteDispatcher.inst().einaus_deleted( ea_id_list, ea_art, delta )

    def _computeSumme( self ):
        btf = BaseTableFunctions()
        btf.computeSumme( self._tv, 5 )

    def copySelectionToClipboard( self ):
        btf = BaseTableFunctions()
        btf.copySelectionToClipboard( self._tv )

##############  MieteController  ####################
class MieteController( MtlEinAusController ):
    show_mietverhaeltnis = Signal( str )
    kuendige_mietverhaeltnis = Signal( str )
    show_NettomieteAndNkv = Signal( str, int, int ) # (mv_id, jahr, monthNumber)

    def __init__( self ):
        MtlEinAusController.__init__( self )
        self._logic = MieteLogic()
        self._tv: MieteTableView = None #MieteTableView()
        self._tvframe: MieteTableViewFrame = None #MieteTableViewFrame( self._tv )

    def getTableView( self ) -> MieteTableView:
        return self._tv

    def getDefaultSign( self ) -> str:
        return "plus"

    def createTableViewFrame( self, jahr:int, monat:int ) -> IccCheckTableViewFrame:
        self._tv = MieteTableView()
        tm = self.createModel( jahr, monat )
        self._tv.setModel( tm )
        self._tvframe = MieteTableViewFrame( self._tv )
        return self._tvframe

    def createModel( self, jahr:int, monat:int ) -> MieteTableModel:
        return self._logic.createMietzahlungenModel( jahr, monat )

    def getModel( self ) -> MtlEinAusTableModel:
        return self._tv.model()

    def getLogic( self ) -> MieteLogic:
        return self._logic

    # def getMenu( self ) -> QMenu:
    #     return None

    def getEinzelzahlungenModelMonat( self, debikredi: str, sab_id:int, jahr: int, monthIdx: int, mobj_id:str=None ) -> EinAusTableModel:
        """
        :param debikredi: Mieter
        :param sab_id: wird hier nicht benötigt
        :param jahr:
        :param monthIdx:
        :param mobj_id: optional, wird im MieteController nicht benötigt
        :return:
        """
        eatm = self._logic.getZahlungenModelDebiKrediMonat( debikredi, jahr, monthIdx )
        keys = ("mobj_id", "debi_kredi", "jahr", "monat", "betrag", "buchungsdatum", "buchungstext", "write_time")
        headers = ("Wohnung", "Mieter", "Jahr", "Monat", "Betrag", "Buchg. am", "Buchungstext", "gebucht am")
        eatm.setKeyHeaderMappings2( keys, headers )
        return eatm

    @Slot()
    def onShowNettomieteAndNkv( self ):
        mv_id, year, monthIdx = self._getSelection()
        self.show_NettomieteAndNkv.emit( mv_id, year, monthIdx+1 )

    def _getSelection( self ) -> [str, int, int]:
        """
        Liefert folgende Daten der aktuellen Selektion:
        - mv_id
        - jahr
        - selektierte Monatsspalte ( 0 -> jan, ..., 11 -> dez )
        :return: mv_id, jahr, monatsIndex
        """
        model: MieteTableModel = self.getModel()
        idx = self._tv.selectedIndexes()[0]
        mv_id = model.getElement( idx.row() ).getValue( "mv_id" )
        year = model.getSelectedYear()
        monthIdx = model.getSelectedMonthIdx()  # 0 -> jan, ..., 11 -> dez
        return mv_id, year, monthIdx

    def onYearChanged( self, newYear:int ):
        self._year = newYear
        tm = self._logic.createMietzahlungenModel( newYear, self.getModel().getEditableMonthIdx() )
        self._tv.setModel( tm )

    def provideContextMenuActions( self, model:MieteTableModel, row:int, key:str ) -> List[BaseAction] or None:
        """
        Liefert die Actions für diese TableView in Abhängigkeit von der geklickten Spalte (key)
        :param model: MieteTableModel
        :param row: selektierte Zeile
        :param key: Key der selektierten Spalte
        :return:
        """
        if key in ( "mv_id", "mobj_id", "soll" ):
            val = model.getValueByName( row, key )
            actions = list()
            if key == "mv_id":
                a = BaseAction( "Mietverhältnis anschauen und bearbeiten..." )
                a.triggered.connect( lambda: self.show_mietverhaeltnis.emit( val ) )
                actions.append( a )
                a = BaseAction( "Mietverhältnis kündigen..." )
                a.triggered.connect( lambda: self.kuendige_mietverhaeltnis.emit( val ) )
                actions.append( a )
            elif key == "mobj_id":
                a = BaseAction( "Objektstammdaten..." )
                a.triggered.connect( lambda: self.show_objekt.emit( val ) )
                actions.append( a )
            elif key == "soll":
                a = BaseAction( "Nettomiete und NKV anzeigen..." )
                a.triggered.connect( self.onShowNettomieteAndNkv )
                actions.append( a )
            return actions
        return None

#############  HausgeldController  ####################
class HausgeldController( MtlEinAusController ):
    show_hgaAndRueZuFue = Signal( str, int, int )
    show_verwaltung = Signal( str, int, int )

    def __init__( self ):
        MtlEinAusController.__init__( self )
        self._logic = HausgeldLogic()
        self._tv: HausgeldTableView = None
        self._tvframe: HausgeldTableViewFrame = None

    def getTableView( self ) -> HausgeldTableView:
        return self._tv

    def getDefaultSign( self ) -> str:
        return "minus"

    def createTableViewFrame( self, jahr:int, monat:int ) -> IccCheckTableViewFrame:
        self._tv = HausgeldTableView()
        tm = self.createModel( jahr, monat )
        self._tv.setModel( tm )
        self._tvframe = HausgeldTableViewFrame( self._tv )
        return self._tvframe

    def createModel( self, jahr:int, monat:int ) -> HausgeldTableModel:
        return self._logic.createHausgeldzahlungenModel( jahr, monat )

    def getModel( self ) -> MtlEinAusTableModel:
        return self._tv.model()

    def getLogic( self ) -> HausgeldLogic:
        return self._logic

    def getEinzelzahlungenModelMonat( self, debikredi: str, sab_id:int, jahr: int, monthIdx: int, mobj_id:str=None ) -> EinAusTableModel:
        eatm = self._logic.getHausgeldvorauszahlungen( mobj_id, debikredi, jahr, monthIdx )
        keys = ("master_name", "mobj_id", "debi_kredi", "jahr", "monat", "betrag", "buchungsdatum", "buchungstext", "write_time")
        headers = ("Haus",     "Wohnung", "WEG",        "Jahr", "Monat", "Betrag", "Buch.datum", "Buch.text", "gebucht am")
        eatm.setKeyHeaderMappings2( keys, headers )
        return eatm

    def onYearChanged( self, newYear:int ):
        self._year = newYear
        tm = self._logic.createHausgeldzahlungenModel( newYear, self.getModel().getEditableMonthIdx() )
        self._tv.setModel( tm )

    def provideContextMenuActions( self, model: HausgeldTableModel, row: int, key: str ) -> List[BaseAction] or None:
        """
        Liefert die Actions für diese TableView in Abhängigkeit von der geklickten Spalte (key)
        :param model: HausgeldTableModel
        :param row: selektierte Zeile
        :param key: Key der selektierten Spalte
        :return:
        """
        if key in ("weg_name", "soll"):
            weg_name, year, monthIdx = self._getSelection()
            actions = list()
            if key == "weg_name":
                if not weg_name: return None
                a = BaseAction( "Verwaltung..." )
                a.triggered.connect( lambda: self.show_verwaltung.emit( weg_name, year, monthIdx+1 ) )
                actions.append( a )
            elif key == "soll":
                x = model.getElement( row )
                mobj_id = x.mobj_id
                a = BaseAction( "Hausgeld und RüZuFü anzeigen..." )
                a.triggered.connect( lambda: self.show_hgaAndRueZuFue.emit( mobj_id, year, monthIdx+1 ) )
                actions.append( a )
            return actions
        return None

    def _getSelection( self ) -> [str, int, int]:
        """
        Liefert folgende Daten der aktuellen Selektion:
        - weg_name
        - jahr
        - selektierte Monatsspalte ( 0 -> jan, ..., 11 -> dez )
        :return: mv_id, jahr, monatsIndex
        """
        model: HausgeldTableModel = self.getModel()
        idx = self._tv.selectedIndexes()[0]
        weg_name = model.getElement( idx.row() ).getValue( "weg_name" )
        year = model.getSelectedYear()
        monthIdx = model.getSelectedMonthIdx()  # 0 -> jan, ..., 11 -> dez
        return weg_name, year, monthIdx

#############  AbschlagController  ####################
class AbschlagController( MtlEinAusController ):
    def __init__( self ):
        MtlEinAusController.__init__( self )
        self._logic = AbschlagLogic()
        # self._tv: AbschlagTableView = None
        # self._tvframe: AbschlagTableViewFrame = None
        self._cboMasternames: BaseComboBox = None
        self._cboMietobjekte: BaseComboBox = None
        self._cboEinAusArt: BaseComboBox = None

    def getTableView( self ) -> AbschlagTableView:
        return self._tv

    def getDefaultSign( self ) -> str:
        return "minus"

    def createTableViewFrame( self, jahr:int, monat:int ) -> IccCheckTableViewFrame:
        self._tv = AbschlagTableView()
        tm = self.createModel( jahr, monat )
        self._tv.setModel( tm )
        self._tvframe = AbschlagTableViewFrame( self._tv )
        return self._tvframe

    def createModel( self, jahr:int, monat:int ) -> AbschlagTableModel:
        return self._logic.createAbschlagzahlungenModel( jahr, monat )

    def getModel( self ) -> MtlEinAusTableModel:
        return self._tv.model()

    def getLogic( self ) -> AbschlagLogic:
        return self._logic

    def getMenu( self ) -> QMenu:
        return None

    def getEinzelzahlungenModelMonat( self, debikredi: str, sab_id:int, jahr: int, monthIdx: int, mobj_id:str=None ) -> EinAusTableModel:
        # für die Anzeige, aus welchen Einzelzahlungen sich der ausgewiesene Monatswert zusammensetzt
        if not sab_id:
            sab_id = self._getSelection()[0]
        eatm = self._logic.getEinzelzahlungenModel( sab_id, jahr, monthIdx )
        keys = ("master_name", "mobj_id", "debi_kredi", "buchungstext", "leistung", "jahr", "monat", "betrag", "write_time")
        headers = ("Haus", "Wohnung", "Kreditor", "Buchungstext(Vnr)", "Leistung", "Jahr", "Monat", "Betrag", "write_time")
        eatm.setKeyHeaderMappings2( keys, headers )
        return eatm

    def onShowLeistungsvertrag( self, sab_id:int ):
        xsa = self._logic.getSollAbschlag( sab_id )
        self.showVertragDialog( xsa, Modus.MODIFY )

    def showVertragDialog( self, xsa: XSollAbschlag, modus:Modus ):
        """
        Zeigt die Details des Leistungsvertrags <xsa>
        :param xsa: XSollAbschlag-Objekt
        :param modus: NEW oder MODIFY
        :return:
        """
        def validate():
            v = dlg.getDynamicAttributeView()
            xcopy:XSollAbschlag = v.getModifiedXBaseCopy()
            return self._mvlogic.validateKuendigungDaten( xcopy )
        xui = XBaseUI( xsa )
        masternames = self._logic.getMasterNamen()
        if modus == Modus.NEW:
            xsa.master_name = masternames[0]
        mietobjektenames = self._logic.getMietobjektNamen( xsa.master_name )
        ea_art_list = (EinAusArt.ALLGEMEINE_KOSTEN.display, EinAusArt.SONSTIGE_KOSTEN.display,
                       EinAusArt.VERSICHERUNG.display)
        vislist = self._createVisibleAttributesList( masternames, mietobjektenames, ea_art_list, self.onMasterChanged )
        xui.addVisibleAttributes( vislist )
        dlg = DynamicAttributeDialog( xui, "Anzeige Leistungsvertrag" )
        dlg.getApplyButton().setEnabled( False )
        dlg.setCallbacks( beforeAcceptCallback=validate )
        v = dlg.getDynamicAttributeView()
        self._cboMasternames: BaseComboBox = v.getWidget( "master_name" )
        self._cboMietobjekte: BaseComboBox = v.getWidget( "mobj_id" )
        self._cboEinAusArt: BaseComboBox = v.getWidget( "ea_art" )
        if dlg.exec_() == QDialog.Accepted:
            v = dlg.getDynamicAttributeView()
            v.updateData()  # Validierung war ok, also Übernahme der Änderungen ins XBase-Objekt
            try:
                # Logik-Aufruf zum Speichern
                pass
            except Exception as ex:
                box = ErrorBox( "AbschlagController.onShowLeistungsvertrag():\n"
                                "Fehler beim Speichern des Vertrags", str( ex ), xsa.toString( True ) )
                box.exec_()
                return
        else:
            # cancelled
            return

    @staticmethod
    def _createVisibleAttributesList( masternames:List[str], mietobjekte:List[str], ea_art_list:Iterable[str],
                                      onMasterChangedCallback:Callable ) \
            -> Iterable[VisibleAttribute]:
        smallW = 85
        vislist = (VisibleAttribute( "sab_id", IntEdit, "sab_id: ", widgetWidth=smallW, editable=False, nextRow=True ),
                   VisibleAttribute( "master_name", BaseComboBox, "Haus: ", nextRow=False,
                                     comboValues=masternames, comboCallback=onMasterChangedCallback ),
                   VisibleAttribute( "mobj_id", BaseComboBox, "Wohnung: ", widgetWidth=150, comboValues=mietobjekte ),
                   VisibleAttribute( "kreditor", BaseEdit, "Kreditor: ", editable=True, nextRow=True ),
                   VisibleAttribute( "vnr", BaseEdit, "Vertragsnummer o.ä.: ", editable=True, columnspan=4 ),
                   VisibleAttribute( "leistung", BaseEdit, "Leistung: ", editable=True, columnspan=4 ),
                   VisibleAttribute( "betrag", SignedNumEdit, "Abschlag (€): ", widgetWidth=smallW, editable=True ),
                   VisibleAttribute( "ea_art", BaseComboBox, "EinAus-Art: ", editable=True,
                                     comboValues=ea_art_list ),
                   VisibleAttribute( "umlegbar", BaseComboBox, "umlegbar: ", widgetWidth=smallW,
                                     comboValues=[Umlegbar.JA.value, Umlegbar.NEIN.value], editable=True ),
                   VisibleAttribute( "von", SmartDateEdit, "beginnt: ", widgetWidth=smallW ),
                   VisibleAttribute( "bis", SmartDateEdit, "endet: ", widgetWidth=smallW ),
                   VisibleAttribute( "bemerkung", BaseEdit, "Bemerkung: ", columnspan=4, editable=True ))
        return vislist

    def onMasterChanged( self, newMaster:str ):
        # Mietobjektnamen für geänderten Master ermitteln:
        mietobjektnamen = self._logic.getMietobjektNamen( newMaster )
        self._cboMietobjekte.clear()
        self._cboMietobjekte.addItems( mietobjektnamen )

    def onYearChanged( self, newYear:int ):
        self._year = newYear
        tm = self.createModel( newYear, self.getModel().getEditableMonthIdx() )
        self._tv.setModel( tm )

    def provideContextMenuActions( self, model:AbschlagTableModel, row:int, key:str ) -> List[BaseAction]:
        """
        Liefert die Actions für diese TableView in Abhängigkeit von der geklickten Spalte (key)
        :param model:
        :param row: die selektierte Zeile
        :param key: Key der selektierten Spalte
        :return:
        """
        if key in ( "kreditor", "leistung", "vnr", "soll" ):
            sab_id, year, monthIdx = self._getSelection()
            actions = list()
            a = BaseAction( "Leistungsvertrag..." )
            a.triggered.connect( lambda: self.onShowLeistungsvertrag( sab_id ) )
            actions.append( a )
            return actions
        return None

    def _getSelection( self ) -> [int, int, int]:
        """
        Liefert folgende Daten der aktuellen Selektion:
        - sab_id
        - jahr
        - selektierte Monatsspalte ( 0 -> jan, ..., 11 -> dez )
        :return: weg_name, jahr, monatsIndex
        """
        model: MieteTableModel = self.getModel()
        idx = self._tv.selectedIndexes()[0]
        sab_id = model.getElement( idx.row() ).getValue( "sab_id" )
        year = model.getSelectedYear()
        monthIdx = model.getSelectedMonthIdx()  # 0 -> jan, ..., 11 -> dez
        return sab_id, year, monthIdx


def test():
    app = QApplication()
    # xsa = XSollAbschlag()
    # xsa.sab_id = 1234
    # xsa.master_name = "SB_Kaiser"
    # xsa.mobj_id = ""
    # xsa.kreditor = "energis"
    # xsa.vnr = "GGPP 12345/54321 Kd.Nr. 3345"
    # xsa.leistung = "Hausratversichterung"
    # xsa.ea_art = EinAusArt.VERSICHERUNG.display
    # xsa.umlegbar = "nein"
    # xsa.von = "2022-05-01"
    # xsa.bis = ""
    # xsa.betrag = -65.78
    # xsa.bemerkung = "Strom vom Stromlieferanten"
    ctrl = AbschlagController()
    ctrl.onShowLeistungsvertrag( 3 )

