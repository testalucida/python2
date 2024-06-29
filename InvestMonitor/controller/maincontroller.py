import sys
import traceback
from functools import cmp_to_key
from typing import List, Any, Dict

from PySide2.QtCore import QSize, QObject, Signal, QRunnable, Slot, QThreadPool, Qt
# from PySide2.QtGui import QScreen
from PySide2.QtWidgets import QDesktopWidget, QAction

from base.basetablefunctions import BaseTableFunctions
from base.basetablemodel import SumTableModel, BaseTableModel
from base.basetableview import BaseTableView
from base.messagebox import InfoBox
from controller.infopanelcontroller import InfoPanelController
from generictable_stuff.okcanceldialog import OkDialog, OkCancelDialog
from gui.infopanel import InfoPanel
from gui.mainwindow import MainWindow
from imon.definitions import DEFAULT_PERIOD, DEFAULT_INTERVAL, DEFAULT_INFOPANEL_ORDER
from imon.enums import InfoPanelOrder, Period, Interval, SortDirection
from interface.interfaces import XDepotPosition, XDelta
from logic.investmonitorlogic import InvestMonitorLogic
from utfsymbols import symDELTA, symAVG


class WorkerSignals( QObject ):
    finished = Signal()
    error = Signal( tuple )
    result = Signal( object )

##############################################################
class Worker( QRunnable ):
    def __init__( self, fn, wkn_ticker_list:List[Dict], allOrders:List[XDelta] ):
        super( Worker, self ).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self._wkn_ticker_list = wkn_ticker_list
        self._allOrders = allOrders
        self.signals = WorkerSignals()

    @Slot()
    def run( self ):
        try:
            result = self.fn( self._wkn_ticker_list, self._allOrders )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit( (exctype, value, traceback.format_exc()) )
        else:
            self.signals.result.emit( result )  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

##############################################################

class GenericDetailsDialog( OkDialog ):
    """
    Dialog, der im IMON dazu dient, z.B. alle Orders oder Dividenden in verschiedenen Zeiträumen anzuschauen.
    Das zur Instanzierung übergebene TableModel muss die Spalten WKN und Ticker enthalten, und der
    Kontextmenü-Eintrag "Aktuellen Kurs zeigen..." muss sinnhaft sein.
    """
    def __init__( self, title:str, tm:BaseTableModel, summableColumnIdx=-1 ):
        """
        :param title:
        :param tm:
        :param summableColumnIdx: Index der Spalte, deren Wert summiert werden können sollen.
                                  Wenn der Index == -1 (default) gibt es keine solche Spalte.
        """
        OkDialog.__init__( self, title )
        self._tm = tm
        self._summableColumnIdx = summableColumnIdx
        self._tv = BaseTableView()
        self._tv.setAlternatingRowColors( True )
        self._tv.setModel( tm, selectRows=True, singleSelection=False )
        self._tv.setContextMenuCallbacks( self.provideMenuItems, self.onContextMenuSelected )
        w = self._tv.getPreferredWidth()
        h = self._tv.getPreferredHeight()
        self.addWidget( self._tv, 0 )
        self.resize( QSize( w + 25, h + 35 ) )

    def provideMenuItems( self, index, point, selectedIndexes ) -> List[QAction]:
        l = list()
        action = QAction( "WKN kopieren" )
        l.append( action )
        action = QAction( "Ticker kopieren" )
        l.append( action )
        sep = QAction()
        sep.setSeparator( True )
        l.append( sep )
        action = QAction( "Aktuellen Kurs zeigen..." )
        l.append( action )
        if self._summableColumnIdx > -1:
            sep = QAction()
            sep.setSeparator( True )
            l.append( sep )
            colName = self._tm.getHeader( self._summableColumnIdx )
            action = QAction( "Summe der markierten Werte in Spalte '%s' anzeigen..." % colName )
            l.append( action )
        return l

    def onContextMenuSelected( self, action: QAction ):
        selRow = self._tv.getFirstSelectedRow()
        txt = action.text()
        if txt.startswith( "WKN" ):
            key = "wkn"
        elif txt.startswith( "Ticker" ):
            key = "ticker"
        elif txt.startswith( "Summe" ):
            key = "sum"
        elif txt.startswith( "Aktuell" ):
            # Aktuellen Kurs von der Logik holen
            key = ""
        else:
            return
        if key in ("wkn", "ticker"):
            colIdx = self._tm.getColumnIndexByKey( key )
            BaseTableFunctions.copyCellValueToClipboard( self._tv, selRow, colIdx )
        elif key == "sum":
            colName = self._tm.getHeader( self._summableColumnIdx )
            BaseTableFunctions.computeSumme( self._tv, columnVon=self._summableColumnIdx, columnBis=self._summableColumnIdx,
                                             dlg_title="Summe Spalte '%s'" % colName )
        else:
            # aktuellen Kurs ermitteln, dazu brauchen wir erst den Ticker:
            colIdx = self._tm.getColumnIndexByKey( "ticker" )
            ticker = self._tm.getValue( selRow, colIdx )
            logic = InvestMonitorLogic()
            kurs, currency = logic.getKursAktuellInEuro( ticker )
            box = InfoBox( "Aktueller Kurs", "Der aktuelle Kurs von '" + ticker + "' liegt bei\n",
                           str( round( kurs, 2 ) ) + " EUR" )
            box.exec_()

###############################################################
class MainController( QObject ):
    IS_TEST = False
    def __init__( self ):
        QObject.__init__( self )
        self._logic: InvestMonitorLogic = InvestMonitorLogic()
        self._mainWin:MainWindow = None
        self._infoPanelCtrlList:List[InfoPanelController] = list()
        self._selectedInfoPanel:InfoPanel = None
        self._sortOrder:InfoPanelOrder = DEFAULT_INFOPANEL_ORDER
        self._sortKeys:List[str] = None
        self._sortDirection = SortDirection.ASC
        self._dlgSelected:OkDialog = None
        self._dlgGenericDetails:GenericDetailsDialog = None
        self._summeGesamtwerte = 0
        self._summeKaeufe = 0
        self._summeDividendPaid = 0
        self._sumDividendPaidCurrentYear = 0
        self._threadpool = QThreadPool()
        self._dlgDividenden:OkCancelDialog = None

    def createMainWindow( self ) -> MainWindow:
        self._mainWin = MainWindow()
        self._mainWin.setWindowTitle( "Investment-Monitor" )
        self._mainWin.showing_now.connect( self.onMainWindowShowing )
        self._mainWin.period_interval_changed.connect( self.onPeriodIntervalChanged )
        self._mainWin.getSearchField().doSearch.connect( self.onSearchInfoPanel )
        self._mainWin.getSearchField().searchTextChanged.connect( self.onSearchInfoPanelTextChanged )
        self._mainWin.change_infopanel_order.connect( self.onChangeSortOrder )
        self._mainWin.undock_infopanel.connect( self.onUndock )
        self._mainWin.show_orders.connect( self.onShowOrders )
        self._mainWin.show_dividends_period.connect( lambda: self.onShowDividends( self._mainWin.getToolBar().getPeriod() ) )
        self._mainWin.show_dividends_curr_year.connect( lambda: self.onShowDividends( Period.currentYear ) )
        poslist = self._logic.getDepotPositions( DEFAULT_PERIOD, DEFAULT_INTERVAL, MainController.IS_TEST )
        for xdepotpos in poslist:
            self._summeGesamtwerte += xdepotpos.gesamtwert_aktuell
            self._summeKaeufe += xdepotpos.einstandswert_restbestand
            self._summeDividendPaid += xdepotpos.dividend_paid_period
        if self._summeKaeufe > 0:
            delta = round( (self._summeGesamtwerte - self._summeKaeufe) / self._summeKaeufe * 100, 1 )
        else:
            delta = 0.0
        self._mainWin.getToolBar().setSummen( self._summeKaeufe, self._summeGesamtwerte, delta )
        self._mainWin.getToolBar().setDividendPaid( self._summeDividendPaid )
        for xdepotpos in poslist:
            xdepotpos.anteil_an_summe_gesamtwerte = self._computeAnteilAnSummeGesamtwerte( xdepotpos )
            infopanelctrl = InfoPanelController()
            infopanel = infopanelctrl.createInfoPanel( xdepotpos )
            infopanelctrl.order_inserted.connect( self.onSummeGesamtwerteChanged )
            sortfieldInfo = self._setSortKeyAndDirection( xdepotpos, self._sortOrder )
            infopanel.setSortInfo( sortfieldInfo )
            self._mainWin.addInfoPanel( infopanel )
            self._infoPanelCtrlList.append( infopanelctrl )
        rect = QDesktopWidget().screenGeometry()
        w = rect.right() - rect.left()
        h = rect.bottom() - rect.top()
        self._mainWin.resize( QSize( w, h ) )
        self._mainWin.setInfoPanelOrder( DEFAULT_INFOPANEL_ORDER )
        return self._mainWin

    def onSummeGesamtwerteChanged( self, delta:int ):
        self._summeGesamtwerte += delta
        self._mainWin.getToolBar().setSummen( self._summeGesamtwerte )
        for ipc in self._infoPanelCtrlList:
            deppos = ipc.getModel()
            anteil = self._computeAnteilAnSummeGesamtwerte( deppos )
            ipc.updateAnteilAnSummeGesamtwerte( anteil )

    def _computeAnteilAnSummeGesamtwerte( self, deppos:XDepotPosition ) -> int:
        if self._summeGesamtwerte > 0:
            return int( round( deppos.gesamtwert_aktuell / self._summeGesamtwerte * 100, 0 ) )
        return 0

    def onSearchInfoPanel( self, wknOrIsinOrTicker:str ):
        """
        Sucht anhand wknOrIsinOrTicker das InfoPanel, das diese Depot-Position abbildet,
        bringt es in den sichtbaren Bereich und zeichnet den Namen in fett und rot
        :param wknOrIsinOrTicker:
        :return:
        """
        #print( "MainController.onSearchInfoPanel(). Suche nach ", wknOrIsinOrTicker )
        wknOrIsinOrTicker = wknOrIsinOrTicker.upper()
        if self._selectedInfoPanel:
            self._selectedInfoPanel.setSelected( False )
            self._selectedInfoPanel = None
        for infopanelctrl in self._infoPanelCtrlList:
            infopanel = infopanelctrl.getInfoPanel()
            model = infopanel.getModel()
            if wknOrIsinOrTicker in (model.wkn, model.isin, model.ticker):
                infopanel.setSelected( True )
                self._mainWin.ensureVisible( infopanel )
                self._selectedInfoPanel = infopanel
                break

    def getAllDepotPositions( self ) -> List[XDepotPosition]:
        l = list()
        for infopanelctrl in self._infoPanelCtrlList:
            infopanel = infopanelctrl.getInfoPanel()
            deppos:XDepotPosition = infopanel.getModel()
            l.append( deppos )
        return l

    def onSearchInfoPanelTextChanged( self ):
        if self._selectedInfoPanel:
            self._selectedInfoPanel.setSelected( False )
            self._selectedInfoPanel = None

    def onUndock( self ):
        infopanels: List[InfoPanel] = [ctrl.getInfoPanel() for ctrl in self._infoPanelCtrlList]
        selected:List[InfoPanel] = [ip for ip in infopanels if ip.isSelected() ]
        if len( selected ) > 0:
            win = MainWindow()
            # vom bisherigen Parent lösen:
            for ip in selected:
                ip.setSelected( False )
                self._mainWin.removeInfoPanel( ip )
                win.addInfoPanel( ip )
            self._mainWin.repaint()
            win.show()

    def onShowOrders( self ):
        tmOrders:SumTableModel = self._logic.getAllOrders()
        self._dlgGenericDetails = GenericDetailsDialog( title="Orderhistorie", tm=tmOrders, summableColumnIdx=9 )
        self._dlgGenericDetails.show()

    def onShowDividends( self, period:Period ):
        """
        Wird aufgerufen, wenn einer der Menüpunkte des Menüs "Dividenden" ausgewählt wird.
        :return:
        """
        tm:SumTableModel = self._logic.getPaidDividendsTableModel( period )
        dlgTitel = "Dividendenzahlungen "
        if period.value == "ytd":
            dlgTitel += " im laufenden Jahr"
        elif period.value == "1y":
            dlgTitel += " in den letzten 12 Monaten"
        else:
            dlgTitel += " in der Periode '%s'" % period.value
        self._dlgGenericDetails = GenericDetailsDialog( title=dlgTitel, tm=tm, summableColumnIdx=5 )
        self._dlgGenericDetails.show()

    def _showDividendDialog( self, dialogTitle:str, tm:SumTableModel ):
        tv = BaseTableView()
        tv.setModel( tm )
        tv.setAlternatingRowColors( True )
        self._dlgDividenden = OkCancelDialog( title=dialogTitle )
        self._dlgDividenden.addWidget( tv, 0 )
        w = tv.getPreferredWidth()
        h = tv.getPreferredHeight()
        self._dlgDividenden.resize( QSize(w+50, h+50) )
        self._dlgDividenden.show()

        ###################  Wenn das MainWindow aufgemacht wurde, ermitteln wir in einem separaten Thread
        ###################  die Summe der im laufenden Jahr gezahlten Dividenden  #######################
    def onMainWindowShowing( self ):
        # Wird aufgerufen, sobald das MainWindow gezeigt wird, um in einem separaten Thread die im lfd. Jahr
        # gezahlte Dividendensumme anzuzeigen (Toolbar).
        # Die InvestMonitorLogic kann im Thread keinen Datenbankzugriff machen.
        # Deshalb ermitteln wir die Deltas und die WKN/Ticker hier und übergeben sie
        # der Worker-Methode computeSumDividendsCurrentYear.
        wkn_ticker_list = self._logic.getAllWknTickersForDividendComputation()
        if len( wkn_ticker_list ) < 1:
            return
        allOrders:List[XDelta] = self._logic.getAllOrdersList()
        worker = Worker( self.computeSumDividendsCurrentYear, wkn_ticker_list, allOrders )
        worker.signals.result.connect( self.onWorkerResult )
        worker.signals.finished.connect( self.onWorkerComplete )
        worker.signals.error.connect( self.onWorkerError )
        self._threadpool.start( worker )

    def computeSumDividendsCurrentYear( self, wkn_ticker_list:List[Dict], allOrders:List[XDelta] ):
        #print( "computeSumDividendsCurrentYear - called with %d Orders" % len(allOrders) )
        self._sumDividendPaidCurrentYear = self._logic.getSumDividendsCurrentYear( wkn_ticker_list, allOrders )
        #print( "Summe Dividenden: ", self._sumDividendPaidCurrentYear )

    def onWorkerResult( self, sum_dividends:int ):
        self._mainWin.getToolBar().setDividendPaidLfdJahr( self._sumDividendPaidCurrentYear )

    def onWorkerComplete( self ):
        pass #rint( "Worker completed." )

    def onWorkerError( self, tuple ):
        print( "Something went wrong: ", tuple )

        ###########  Ende der für die Thread-Verarbeitung benötigten Methoden  #################
        ########################################################################################

    def onPeriodIntervalChanged( self, period:Period, interval:Interval ):
        self._mainWin.setCursor( Qt.WaitCursor )
        poslist: List[XDepotPosition] = [ctrl.getModel() for ctrl in self._infoPanelCtrlList]
        self._logic.provideTickerHistories( poslist, period, interval )
        self._summeDividendPaid = 0
        for ctrl in self._infoPanelCtrlList:
            ctrl.refreshAfterPeriodIntervalHasChanged( period, interval )
            deppos = ctrl.getModel()
            self._summeDividendPaid += deppos.dividend_paid_period
        self._mainWin.getToolBar().setDividendPaid( self._summeDividendPaid )
        self._mainWin.setCursor( Qt.ArrowCursor )

    def onChangeSortOrder( self, order:InfoPanelOrder ):
        self._sortOrder = order
        infopanels:List[InfoPanel] = [ctrl.getInfoPanel() for ctrl in self._infoPanelCtrlList]
        ### debug ###
        #testlist = list()
        #############
        for ip in infopanels:
            deppos:XDepotPosition = ip.getModel()
            sortfieldInfo = self._setSortKeyAndDirection( deppos, order )
            ip.setSortInfo( sortfieldInfo )
            ### debug ###
            # sortfield = ip.getModel().__dict__["__sortfield__"]
            # testlist.append( sortfield )
            #############
        ### debug ###
        # testlist = sorted( testlist )
        #############
        try:
            infopanels = sorted( infopanels, key=cmp_to_key( self._compare ) )
        except Exception as ex:
            print( "MainController.onChangeSortOrder(): sorted() throws Exception\n%s" % str(ex) )
            for ip in infopanels:
                model = ip.getModel()
                if not model:
                    print( "found InfoPanel without model." )
                    continue
                try:
                    sortfield = model.__dict__["__sortfield__"]
                    if not sortfield:
                        print( "Sortfield von Model '%s' has no value" % model.wkn )
                        continue
                    print( "Wert Sortfield von Model ", model.wkn, ": ", sortfield )
                except Exception as ex:
                    print( "Model '%s' has no sortfield" % model.wkn )

        self._mainWin.clear()
        for ip in infopanels:
            self._mainWin.addInfoPanel( ip )

    def _setSortKeyAndDirection( self, x:XDepotPosition, order:InfoPanelOrder ) -> str:
        """
        Baut anhand des gewünschten Sortierkriteriums den SortKey auf und
        schiebt ihn <x> als neues Attribut unter.
        :return:
        """
        sortfield = ""
        sortfieldInfo = ""
        if order == InfoPanelOrder.Wkn:
            sortfield = x.wkn.lower()
            sortfieldInfo = "WKN: " + x.wkn
            self._sortDirection = SortDirection.ASC
        elif order == InfoPanelOrder.Name:
            sortfield = x.name.lower()
            sortfieldInfo = "Name: " + x.name
            self._sortDirection = SortDirection.ASC
        elif order == InfoPanelOrder.Index:
            sortfield = "" if not x.basic_index else x.basic_index.lower()
            sortfieldInfo = "Index: " + x.basic_index
            self._sortDirection = SortDirection.ASC
        elif order == InfoPanelOrder.Depot:
            sortfield = x.depot_id + " / " + x.wkn
            sortfieldInfo = "Depot-ID: " + x.depot_id + " / WKN: " + x.wkn
            self._sortDirection = SortDirection.ASC
        elif order == InfoPanelOrder.Wert:
            sortfield = x.gesamtwert_aktuell
            sortfieldInfo = "Wert: " + str( x.gesamtwert_aktuell )
            self._sortDirection = SortDirection.DESC
        elif order == InfoPanelOrder.Anteil:
            sortfield = x.anteil_an_summe_gesamtwerte
            sortfieldInfo = "Anteil: " + str( x.anteil_an_summe_gesamtwerte )
            self._sortDirection = SortDirection.DESC
        elif order == InfoPanelOrder.Anteil_USA:
            sortfield = x.anteil_usa
            sortfieldInfo = "USA-Firmen (%): " + str( x.anteil_usa )
            self._sortDirection = SortDirection.DESC
        elif order == InfoPanelOrder.AccLast:
            val = "0 / " if not x.flag_acc else "1 / "
            sortfield = val + x.wkn.lower()
            sortfieldInfo = "Acc.: " + ("Nein" if val.startswith("0") else "Ja" ) + " / WKN: " + x.wkn
            self._sortDirection = SortDirection.ASC
        elif order == InfoPanelOrder.AccFirst:
            val = "0 / " if x.flag_acc else "1 / "
            sortfield = val + x.wkn.lower()
            sortfieldInfo = "Acc.: " + ("Ja" if x.flag_acc else "Nein" ) + " / WKN: " + x.wkn
            self._sortDirection = SortDirection.ASC
        elif order == InfoPanelOrder.LetzterKauf:
            sortfield = x.letzter_kauf
            sortfieldInfo = "Letzter Kauf: " + x.letzter_kauf
            self._sortDirection = SortDirection.DESC
        elif order == InfoPanelOrder.DeltaWert:
            # sortfield = '%07.3f' % x.delta_proz
            sortfield = x.delta_proz
            sortfieldInfo = "Wertentwicklg.: " + str( x.delta_proz )
            self._sortDirection = SortDirection.DESC
        elif order == InfoPanelOrder.DividendYield:
            val = "1 / " if not x.flag_acc else "0 / "
            sortfield = val + '%07.3f' % x.dividend_yield
            sortfieldInfo = "Dividende: " + str( x.dividend_yield )
            self._sortDirection = SortDirection.DESC
        elif order == InfoPanelOrder.DividendPaid:
            sortfield = x.dividend_paid_period
            sortfieldInfo = "Ausschüttung: " + str( x.dividend_paid_period )
            self._sortDirection = SortDirection.DESC
        elif order == InfoPanelOrder.Buy:
            diff = round( x.dividend_yield - x.delta_proz, 3 )
            sortfield = diff
            sortfieldInfo = "Diff. Div.Rend. und " + symDELTA + " Wert: " + str( diff )
            self._sortDirection = SortDirection.DESC
        elif order == InfoPanelOrder.DeltaKursAsc:
            sortfield = x.delta_kurs_1_percent
            sortfieldInfo = symDELTA + " Kurs seit letztem Close: %.2f" % x.delta_kurs_1_percent
            sortfieldInfo += "%"
            self._sortDirection = SortDirection.ASC
        elif order == InfoPanelOrder.RelKursAvgKp:
            sortfield = ((x.kurs_aktuell - x.preisprostueck) / x.preisprostueck) * 100
            sortfieldInfo = "Vh. Kurs / " + symAVG + (" Kaufpr.: %.2f" % sortfield) + "%"
            self._sortDirection = SortDirection.ASC
        else:
            raise Exception( "MainController._setSortKey(): unknown order:\n%s" % str(order) )
        x.__dict__["__sortfield__"] = sortfield
        return sortfieldInfo

    def _compare( self, ip1:InfoPanel, ip2:InfoPanel ) -> int:
        if self._sortDirection == SortDirection.ASC:
            rc_if_gt = 1
            rc_if_lt = -1
        else:
            rc_if_gt = -1
            rc_if_lt = 1
        v1 = ip1.getModel().__dict__["__sortfield__"]
        v2 = ip2.getModel().__dict__["__sortfield__"]
        if v1 == v2: return 0
        else:
            if v1 > v2:  rc = rc_if_gt # 1
            else: rc = rc_if_lt # -1
            #print( "_compare: v1=", v1, "; v2=", v2, " -> returning rc=", rc )
            return rc


###############################################################################
def test():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    ctrl = MainController()
    win = ctrl.createMainWindow()
    win.show()
    app.exec_()

def testAllOrdersTableView():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    ctrl = MainController()
    ctrl.onShowOrders()

def test2():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    x = XDepotPosition()
    ctrl = MainController()
    ctrl._setSortKeyAndDirection( x, InfoPanelOrder.Name )
    d = x.__dict__
    for key, value in d.items():
        print( key, ": ", value )
    app.exec_()

##############################################################
# creating an outer function
def outerFunc(sample_text):
   text = sample_text
    # creating an inner function
   def innerFunc():
    # Printing the variable of the parent class(outer class)
      print(text)
    # calling inner function
   innerFunc()

def testOuterFunc():
    # Calling the outer Function by passing some random name
    outerFunc('Hello tutorialspoint python')