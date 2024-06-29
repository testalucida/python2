from typing import List

from PySide2.QtCore import Qt, QSize, Slot, Signal
from PySide2.QtWidgets import QAction, QMenu, QMessageBox

from base.baseqtderivates import BaseAction, Separator, YearComboBox, BaseIconButton
from base.basetablefunctions import BaseTableFunctions
from base.basetablemodel import BaseTableModel
from base.directories import BASE_IMAGES_DIR
from base.filtertablewidget import FilterTableWidget, FilterTableWidgetFrame, TableTool
from base.messagebox import InfoBox, QuestionBox, ErrorBox
from iconfactory import IconFactoryS
from v2.einaus.einausdialogcontroller import EinAusDialogController
from v2.einaus.einauslogic import EinAusLogic, EinAusTableModel
from v2.einaus.einauswritedispatcher import EinAusWriteDispatcher
from v2.icc.constants import EinAusArt, Action
from v2.icc.icccontroller import IccController
from v2.icc.interfaces import XEinAus
from v2.sammelabgabe.sammelabgabecontroller import SammelabgabeController

# ##############  EinAusController  ####################
class EinAusController( IccController ):
    year_changed = Signal( int ) # arg = new year
    def __init__( self ):
        IccController.__init__( self )
        self._tv: FilterTableWidget = FilterTableWidget()
        self._tvframe: FilterTableWidgetFrame = FilterTableWidgetFrame( self._tv, withEditButtons=True )
        self._logic = EinAusLogic()
        self._jahr:int = self.getYearToStartWith()
        self._btnSortHausObjektEinAusArt:BaseIconButton = None
        EinAusWriteDispatcher.inst().ea_inserted.connect( self.onEinAusInserted )
        EinAusWriteDispatcher.inst().ea_updated.connect( self.onEinAusUpdated )
        EinAusWriteDispatcher.inst().ea_deleted.connect( self.onEinAusDeleted )

    def createGui( self ) -> FilterTableWidgetFrame:
        jahr = self._jahr
        tv = self._tv
        tm = self._logic.getZahlungenModel( jahr )
        tv.setModel( tm, selectRows=True, singleSelection=False )
        tv.sortByColumn( tm.getWriteTimeColumnIdx(), Qt.SortOrder.AscendingOrder )
        jahre = self.getJahre()
        if len(jahre) == 0:
            jahre.append( jahr )
        ycbo = YearComboBox( jahre )
        ycbo.setYear( jahr )
        ycbo.year_changed.connect( self.onYearChanged )
        tv.addToolWidget( ycbo )
        self._btnSortHausObjektEinAusArt = self._createHausObjektEinAusArtSortButton()
        # todo: create and connect with MultiSortHandler2
        tv.addToolWidget( self._btnSortHausObjektEinAusArt )
        tv.addStandardTableTools( (TableTool.SEARCH, TableTool.PRINT, TableTool.EXPORT) )
        tv.setContextMenuCallbacks( self.provideActions, self.onSelected )
        ### neue Zahlung, Zahlung ändern, löschen:
        self._tvframe.newItem.connect( self.onNewEinAus )
        self._tvframe.editItem.connect( self.onEditEinAus )
        self._tvframe.deleteItems.connect( self.onDeleteEinAus )
        return self._tvframe

    def _createHausObjektEinAusArtSortButton( self ) -> BaseIconButton:
        icon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "sort2.png" )
        btn = BaseIconButton( icon )
        btn.setToolTip( "Sortieren nach den Kriterien Haus-Whg-Art-Debitor-eingetragen am" )
        btn.clicked.connect( self.onSortHausWhgArtDebitorClicked )
        return btn

    def onSortHausWhgArtDebitorClicked( self ):
        tm = self._tv.model()
        tm.sortMultipleColumns( ("master_name", "mobj_id", "ea_art", "debi_kredi", "write_time") )

    def getMenu( self ) -> QMenu:
        menu = QMenu( "Sammelabgabe" )
        # Menü "Sammelabgabe"
        action = BaseAction( "Sammelabgabe erfassen und aufsplitten...", parent=menu )
        action.triggered.connect( self.onSammelabgabe )
        menu.addAction( action )
        return menu

    def onSammelabgabe( self ):
        c = SammelabgabeController()
        einauslist:List[XEinAus] = c.processSammelabgabe( self._jahr )
        if einauslist and len( einauslist ) > 0:
            tm:EinAusTableModel = self._tv.model()
            for ea in einauslist:
                tm.addObject( ea )

    def onNewEinAus( self ):
        """
        Im TableView "Alle Zahlungen" wurde der "+"-Button gedrückt.
        Neue Zahlungen werden über den EinAusDialog erfasst, wozu der EinAusDialogController instanziert wird.
        :return:
        """
        ctrl = EinAusDialogController()
        #ctrl.ea_inserted.connect( self.onEinAusInserted )
        ctrl.processNewEinAus()

    @Slot( XEinAus )
    def onEinAusInserted( self, x:XEinAus ):
        # Ist mit dem Signal EinAusWriteDispatcher.ea_inserted connected.
        # Dieses wird gesendet, nachdem ein neuer Satz in Tabelle <einaus> eingefügt wurde.
        # Der Datenbank-Insert ist bereits erfolgt.
        # Jetzt muss der tableView "Alle Zahlungen" der neue Satz hinzugefügt werden -
        # aber nur, wenn das steuerliche Jahr <x.jahr> zu dem in der Combobox selektierten Jahr passt.
        if self._jahr == x.jahr:
            model:EinAusTableModel = self._tv.model()
            model.addObject( x )
        else:
            box = InfoBox( "Buchung für fremdes Jahr", "Die eingegebene Buchung bezieht sich auf das Jahr %d.\n"
                                                       "Eingestellt ist Jahr %d.\n"
                                                       "Deshalb kann die neue Buchung nicht angezeigt werden.\n"
                                                       "Sie wurde jedoch gespeichert." % (x.jahr, self._jahr), "", "OK" )
            box.exec_()

    def onEditEinAus( self, row:int ):
        """
        Im TableView "Alle Zahlungen" wurde der Edit-Button gedrückt.
        Änderungen von Zahlungen werden über den EinAusDialog erfasst, wozu der EinAusDialogController instanziert wird.
        :return:
        """
        x:XEinAus = self._tv.model().getElement( row )
        ea_art_options = EinAusArt.getEinAusDialogOptions()
        if x.ea_art not in ea_art_options:
            msg = "Zahlungen der Art '%s' können hier nicht geändert werden. " \
                  "\nBitte die Änderungsfunktion in der jeweiligen Tabelle verwenden." % x.ea_art
            box = ErrorBox( "Änderung nicht möglich", msg, "" )
            box.exec_()
            return
        if x.sab_id and x.sab_id > 0:
            box = ErrorBox( "Änderung nicht möglich", "Regelmäßige Abschläge können hier nicht geändert werden. "
                            "\nBitte die Änderung im Tab 'Regelmäßige Zahlungen' in Tabelle 'Abschläge' vornehmen.", "" )
            box.exec_()
            return
        if x.reise_id and x.reise_id > 0:
            box = ErrorBox( "Änderung nicht möglich", "Reisekosten können hier nicht geändert werden.",
                            "Bitte die Änderung im Geschäftsreisen-Dialog vornehmen." )
            box.exec_()
            return

        ctrl = EinAusDialogController()
        #ctrl.ea_updated.connect( self.onEinAusUpdated )
        ctrl.processEinAusModification( x )

    @Slot( XEinAus, int or float )
    def onEinAusUpdated( self, x: XEinAus, delta:int or float ):
        """
        # Ist mit dem Signal EinAusWriteDispatcher.ea_updated connected.
        # Dieses wird gesendet, nachdem der Update durchgeführt und in der Datenbank
        gespeichert wurde.
        :param x: das geänderte XEInAus-Objekt
        :param delta: wird hier nicht benötigt.
        :return:
        """
        if self._jahr == x.jahr:
            tm:EinAusTableModel = self._tv.model()
            x2 = tm.getElementByUniqueKeyValue( "ea_id", x.ea_id )
            if x != x2:
                x2.updateFromOther( x )

    def onDeleteEinAus( self, rows:List[int] ):
        """
        Wird aufgerufen, wenn im tvframe "Alle Zahlungen" der delete-Button gedrückt wird.
        :param rows: die markierten Zeilen, Zahlungen repräsentierend, die gelöscht werden sollen
        :return:
        """
        if len( rows ) < 1: return
        model = self._tv.model()
        xealist = model.getElements( rows )
        for xea in xealist:
            if xea.reise_id and xea.reise_id > 0:
                box = ErrorBox( "Löschen nicht zuläassig",
                                "Reisekosten können hier nicht gelöscht werden.",
                                "Bitte den Geschäftsreise-Dialog verwenden." )
                box.exec_()
                return
        box = QuestionBox( "Ausgewählte Element löschen", "Ausgewählte Elemente wirklich löschen?", "Ja", "Nein" )
        if box.exec_() == QMessageBox.Yes:
            ea_id_list = [x.ea_id for x in xealist]
            ea_art = xealist[0].ea_art
            delta = sum([x.betrag for x in xealist])
            self._logic.deleteZahlungen( xealist )
            EinAusWriteDispatcher.inst().einaus_deleted( ea_id_list, ea_art, delta )

    @Slot( list, str, int or float )
    def onEinAusDeleted( self, ea_id_list:List[int], ea_art:str, delta:int or float ):
        """
        Ist mit dem Signal ea_deleted des EinAusWriteDispatchers connected.
        :param ea_id_list: Liste der zu löschenden ea_id
        :param ea_art: die EinAusArt der gelöschten Sätze (alle haben die gleiche EinAusArt)
        :param delta: interessiert hier nicht
        :return:
        """
        model:BaseTableModel = self._tv.model()
        for ea_id in ea_id_list:
            model.removeObjectsByKeyValue( "ea_id", ea_id )

    def onYearChanged( self, newYear:int ):
        self._jahr = newYear
        tm = self._logic.getZahlungenModel( self._jahr )
        tv = self._tv
        tv.setModel( tm, selectRows=True, singleSelection=False )
        self.year_changed.emit( newYear )
        #tv.resizeRowsAndColumns()

    def provideActions( self, index, point, selectedIndexes ) -> List[QAction]:
        #print( "context menu for column ", index.column(), ", row ", index.row() )
        col = index.column() # angeklickte Spalte
        model: EinAusTableModel = self._tv.model()
        key = model.getKey( col ) # Key der angeklickten Spalte
        val = model.getValue( index.row(), col ) # Wert der angeklickten Spalte
        x:XEinAus = model.getElement( index.row() ) # dieses Element wurde angeklickt
        cnt_sel_rows = len( self._tv.getSelectedRows() )
        l = list()
        if cnt_sel_rows == 1:
            l.append( BaseAction( "EinAus-ID: " + str( x.ea_id ) ) )
            l.append( Separator() )
            if x.sab_id and x.sab_id > 0:  # ein regelmäßiger Abschlag
                l.append( BaseAction( "Vertrag...", ident=Action.SHOW_LEISTUNGSVERTRAG, userdata=x ) )
                l.append( Separator() )
            elif x.ea_art in ( EinAusArt.HAUSGELD_VORAUS.display, EinAusArt.HAUSGELD_ABRECHNG.display ):
                l.append( BaseAction( "Verwaltungsdaten...", ident=Action.SHOW_WEG_UND_VERWALTER, userdata=x ) )
                l.append( Separator() )
            if key in ( "master_name", "mobj_id" ):
                l.append( BaseAction( "Hausdaten...", ident=Action.SHOW_MASTEROBJEKT, userdata=x ) )
                if key == "mobj_id" and val and val > "":
                    l.append( BaseAction( "Wohnungsdaten...", ident=Action.SHOW_MIETOBJEKT, userdata=x ) )
                l.append( Separator() )
            elif key == "debi_kredi" and x.ea_art == EinAusArt.BRUTTOMIETE.display:
                l.append( BaseAction( "Mietverhältnis...", ident=Action.SHOW_MIETVERHAELTNIS, userdata=x ) )
                l.append( Separator() )
        l.append( BaseAction( "Markierte Zeile(n) kopieren", ident=Action.COPY ) )
        l.append( BaseAction( "Beträge der markierten Zeile(n) kopieren", ident=Action.COPY_BETRAEGE ) )
        # l.append( Separator() )
        # l.append( BaseAction( "Zahlung duplizieren und mit aktuellem Datum speichern", ident=Action.DUPLICATE_AND_SAVE ) )
        # l.append( BaseAction( "Zahlung duplizieren und im Editor öffnen...", ident=Action.DUPLICATE_AND_EDIT ) )
        #
        if cnt_sel_rows > 1:
            l.append( Separator() )
            l.append( BaseAction( "Summe der markierten Beträge berechnen...", ident=Action.COMPUTE_SUMME ) )
        return l

    def onSelected( self, action: BaseAction ):
        """callback function nach Auswahl eines Kontext-MenüItems"""
        x: XEinAus = action.data()
        ident = action.ident
        if ident == Action.COMPUTE_SUMME:
            model:BaseTableModel = self._tv.model()
            col = model.getColumnIndexByKey( "betrag" )
            btf = BaseTableFunctions()
            btf.computeSumme( self._tv, col, col )
        elif ident == Action.COPY:
            btf = BaseTableFunctions()
            btf.copySelectionToClipboard( tv=self._tv )
        elif ident == Action.COPY_BETRAEGE:
            btf = BaseTableFunctions()
            tm:BaseTableModel = self._tv.model()
            colIdx = tm.getColumnIndexByKey( "betrag" )
            btf.copyColumnCellsToClipboard( tv=self._tv, col=colIdx, convertPointToComma=True )



# #####################   TEST   TEST   TEST   ##################
#
def testMatch():
    i = 10
    # match i:
    #     case 1: print( i )
    #     case 2: print( i )
    #     case _: print( "----" )

def test2():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    c = EinAusController()
    frame = c.createGui()
    w = frame.getTableView().getPreferredWidth()
    h = frame.getTableView().getPreferredHeight()
    frame.show()
    frame.resize( QSize(w, h) )
    app.exec_()
#
# def test():
#     from PySide2.QtWidgets import QApplication
#     app = QApplication()
#     tv = EinAusTableView()
#     vf = EinAusTableViewFrame( tv, withEditButtons=True )
#     vf.show()
#     app.exec_()