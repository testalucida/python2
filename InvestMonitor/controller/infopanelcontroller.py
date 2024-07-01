from typing import List

from PySide2.QtCore import QSize, QObject, Signal
from PySide2.QtWidgets import QDialog
from pandas import Series

import datehelper
from base.baseqtderivates import BaseEdit, MultiLineEdit, SmartDateEdit, IntEdit, FloatEdit, SignedNumEdit, \
    PositiveSignedFloatEdit, FixedNegativeSignedFloatEdit
from base.basetablemodel import BaseTableModel, SumTableModel
from base.basetableview import BaseTableView
from base.dynamicattributeui import DynamicAttributeView, DynamicAttributeDialog
from base.interfaces import XBaseUI, VisibleAttribute
from base.messagebox import ErrorBox, InfoBox
from data.finance.tickerhistory import Period, Interval, SeriesName
from generictable_stuff.okcanceldialog import OkDialog, OkCancelDialog
from gui.infopanel import InfoPanel, AbgeltungssteuerDlg
from interface.interfaces import XDepotPosition, XDelta, XDetail
from logic.investmonitorlogic import InvestMonitorLogic


class InfoPanelController( QObject ):
    order_inserted = Signal( int ) # parameter: Ordersumme (pos. oder neg.)

    def __init__( self ):
        QObject.__init__( self )
        self._x:XDepotPosition = None
        self._logic:InvestMonitorLogic = InvestMonitorLogic()
        self._infoPanel:InfoPanel = None
        self._detailDlg:DynamicAttributeDialog = None
        self._computeAbgeltSteuerDlg:AbgeltungssteuerDlg = None
        self._dividendPaidDlg:OkCancelDialog = None
        self._orderHistorieDig:OkDialog = None
        self._theoretischeRenditeBox:InfoBox = None

    def createInfoPanel( self, xdepotpos:XDepotPosition ) -> InfoPanel:
        self._x = xdepotpos
        infopanel = InfoPanel()
        infopanel.setDepotPosition( xdepotpos )
        infopanel.show_details.connect( self.onShowDetails )
        infopanel.show_div_payments.connect( self.onShowDividendPayments )
        infopanel.show_simul_yield.connect( self.onShowSimulatedDividendYield )
        infopanel.update_graph.connect( self.onUpdateGraph )
        infopanel.enter_bestand_delta.connect( self.onEnterBestandDelta )
        infopanel.compute_abgeltungssteuer.connect( self.onComputeAbgeltungssteuer )
        infopanel.show_kauf_historie.connect( self.onShowKaufHistorie )
        infopanel.update_kurs.connect( self.onUpdateKurs )
        self._infoPanel = infopanel
        return infopanel

    def getInfoPanel( self ) -> InfoPanel:
        return self._infoPanel

    def getModel( self ) -> XDepotPosition:
        return self._x

    def onShowDetails( self ):
        details:XDetail = self._logic.getDetails( self._x )
        detailsUI = XBaseUI( details )
        vislist = (
            VisibleAttribute( "basic_index", BaseEdit, "Index: ", editable=False, nextRow=True ),
            VisibleAttribute( "beschreibung", MultiLineEdit, "", editable=False, nextRow=True ),
            VisibleAttribute( "toplaender", MultiLineEdit, "Top-Länder: ", widgetHeight=55, editable=False, nextRow=True ),
            VisibleAttribute( "topsektoren", MultiLineEdit, "Top-Sektoren: ", widgetHeight=55, editable=False, nextRow=True ),
            VisibleAttribute( "topfirmen", MultiLineEdit, "Top-Firmen: ", widgetHeight=55, editable=False, nextRow=True ),
            VisibleAttribute( "bank", BaseEdit, "Bank: ", editable=False, nextRow=True ),
            VisibleAttribute( "depot_nr", BaseEdit, "Depot-Nr.: ", editable=False, nextRow=True ),
            VisibleAttribute( "depot_vrrkto", BaseEdit, "Vrr.-Konto: ", editable=False, nextRow=True )
        )
        detailsUI.addVisibleAttributes( vislist )
        self._detailDlg = DynamicAttributeDialog( detailsUI, title="Details zur Depotposition '%s'" % self._x.name,
                                                  okButton=False, applyButton=False )
        self._detailDlg.resize( QSize(500, 500) )
        self._detailDlg.show()

    def onShowDividendPayments( self ):
        divs:Series = self._x.dividends
        tm = SumTableModel.fromSeries( divs, indexLen=10, jahr=0, colsToSum=("value",) )
        tm.setKeyHeaderMappings2( ("index", "value"), ("Datum", "Dividende") )
        tv = BaseTableView()
        tv.setModel( tm )
        tv.setAlternatingRowColors( True )
        self._dividendPaidDlg = OkCancelDialog( title="Dividendenzahlungen " + self._x.wkn )
        self._dividendPaidDlg.addWidget( tv, 0 )
        self._dividendPaidDlg.show()

    def onShowSimulatedDividendYield( self ):
        """
        Öffnet ein Infofenster, in dem die theoretische Dividendenrendite auf Basis des aktuellen Kurses und des Durchschnitts der
        Dividendenzahlungen in der eingestellten Periode angezeigt wird.
        :return: None
        """
        divyield:float = self._logic.getSimulatedDividendYield( self._x.kurs_aktuell, self._x.dividends )
        self._theoretischeRenditeBox = \
              InfoBox( title="Theoretische Rendite " + self._x.wkn,
                       info="Auf Basis in der Vergangenheit (eingestellte Periode) gezahlter Dividenden "
                            "und des aktuellen Kurses\nergibt sich für das kommende Jahr rechnerisch eine Rendite von",
                       more=str(divyield) + "%" )
        self._theoretischeRenditeBox.show()

    def onUpdateGraph( self, period:Period, interval:Interval ):
        self._logic.updateWertpapierData( self._x, period, interval )
        self._infoPanel.changeModel( self._x )

    def refreshAfterPeriodIntervalHasChanged( self, period:Period, interval:Interval ):
        self._infoPanel.changeModel( self._x )
        self._infoPanel.setPeriodAndInterval( period, interval )

    def onEnterBestandDelta( self ):
        def validateDeltaData() -> str or None:
            view:DynamicAttributeView = deltaDlg.getDynamicAttributeView()
            w:SmartDateEdit = view.getWidget( "delta_datum" )
            if not datehelper.isValidIsoDatestring( w.getDate() ):
                return "Orderdatum muss mit gültigem ISO-Datum versorgt sein. "
            w:PositiveSignedFloatEdit = view.getWidget( "delta_stck" )
            if w.getValue() ==0:
                return "Stückzahl darf nicht 0 sein."
            # if view.getWidget( "order_summe" ).getValue() <= 0:
            if view.getWidget( "preis_stck" ).getValue() <= 0:
                return "Der Kurs muss immer positiv sein.\nDie Erkennung Kauf/Verkauf erfolgt über das " \
                       "Vorzeichen der Stückzahl (+ -> Kauf, - -> Verkauf)."
            if view.getWidget( "delta_stck" ).getValue() < 0 and view.getWidget( "verkaufskosten" ).getValue() == 0:
               return "Bei einem Verkauf müssen die Kosten des Verkaufs angegeben werden." \
                      "\nAndernfalls wird ein zu hoher Veräußerungsgewinn berechnet."

        delta = XDelta()
        delta.wkn = self._x.wkn
        delta.delta_datum = datehelper.getCurrentDateIso()
        deltaUI = XBaseUI( delta )
        vislist = (
            VisibleAttribute( "wkn", BaseEdit, "WKN: ", widgetWidth=100, editable=False, nextRow=True ),
            VisibleAttribute( "delta_datum", SmartDateEdit, "Order ausgeführt am: ", widgetWidth=100, editable=True,
                              nextRow=True ),
            VisibleAttribute( "delta_stck", PositiveSignedFloatEdit, "Anzahl Stück: ", widgetWidth=100,
                              tooltip="Bei Kauf Vorzeichen '+' verwenden, bei Verkauf '-'",
                              editable=True, nextRow=True ),
            VisibleAttribute( "preis_stck", FloatEdit, "Kurs (€): ", widgetWidth=100,
                              tooltip="Kurs, zu dem gekauft/verkauft wurde",
                              editable=True, nextRow=True ),
            VisibleAttribute( "verkaufskosten", FixedNegativeSignedFloatEdit, "Orderkosten (€) (nur bei Verkauf)", widgetWidth=100,
                              tooltip="Kosten, die beim Verkauf erhoben wurden.\nKönnen vom Veräuß.gewinn abgezogen werden.",
                              editable=True, nextRow=True ),
            VisibleAttribute( "bemerkung", MultiLineEdit, "Bemerkung: ", editable=True, widgetHeight=50, nextRow=True ),
        )
        deltaUI.addVisibleAttributes( vislist )
        deltaDlg = DynamicAttributeDialog( deltaUI, title="Orderdaten '%s'" % self._x.name,
                                                  okButton=True, applyButton=False )
        deltaDlg.setCallbacks( beforeAcceptCallback=validateDeltaData )
        if deltaDlg.exec_() == QDialog.Accepted:
            deltaDlg.getDynamicAttributeView().updateData()
            try:
                self._logic.insertOrderAndUpdateDepotData( delta, self._x )
                self._infoPanel.updateOrderRelatedData()
                self.order_inserted.emit( delta.order_summe )
            except Exception as ex:
                box = ErrorBox( "Fehler beim Insert in die Datenbank", str( ex ) )
                box.exec_()

    def onComputeAbgeltungssteuer( self ):
        """
        Es wurde auf den Button Abgeltungssteuer geklickt.
        Dialog zur Eingabe der gewünschten zu verkaufenden Stückzahl öffnen.
        Mit OK die InvestmonitorLogic aufrufen, um die Abgeltungssteuer ausrechnen zu lassen.
        Ergebnis im Dialog anzeigen.
        :return:
        """
        def computeSteuer( anz_stck:int ):
            steuer = self._logic.computeAbgeltungssteuer( self._x.wkn, self._x.kurs_aktuell, anz_stck )
            dlg.setAbgeltungssteuer( steuer )
        self._computeAbgeltSteuerDlg = dlg = AbgeltungssteuerDlg( self._x.wkn, self._x.kurs_aktuell, self._x.stueck )
        dlg.compute_steuer.connect( computeSteuer )
        dlg.show()

    def updateAnteilAnSummeGesamtwerte( self, anteil:int ):
        """
        Nach einer eingetragenen Order ändert sich der Anteil dieser DepotPosition an der Gesamtheit.
        Die DepotPosition muss geändert werden, danach die Anzeige aktualisiert werden.
        :return:
        """
        self._x.anteil_an_summe_gesamtwerte = anteil
        self._infoPanel.updateAnteilAnSummeGesamtwerte()

    def onShowKaufHistorie( self ):
        tm:BaseTableModel = self._logic.getOrders( self._x.wkn )
        tv = BaseTableView()
        tv.setModel( tm )
        w = tv.getPreferredWidth()
        h = tv.getPreferredHeight()
        self._orderHistorieDig = OkDialog( title="Orderhistorie für WKN '%s', '%s' " % (self._x.wkn, self._x.name) )
        dlg = self._orderHistorieDig
        dlg.addWidget( tv, 0 )
        dlg.resize( QSize(w+25, h+35) )
        dlg.show()

    def onUpdateKurs( self ):
        self._logic.updateKursAndDivYield( self._x )
        self._infoPanel.updateKursAktuell( self._x.kurs_aktuell, self._x.dividend_yield )

    def isInfoPanelSelected( self ) -> bool:
        return self._infoPanel.isSelected()

def test2():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    ipc = InfoPanelController()
    logic = InvestMonitorLogic()
    ticker = "GLDV.L"
    deppos = logic.getDepotPosition( ticker, Period.oneYear, Interval.fiveDays )
    ipanel = ipc.createInfoPanel( deppos )
    ipanel.show()
    app.exec_()

def test():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    ipc = InfoPanelController()
    ticker = "GDIG.L" # "DBXS.DE" # "IEDY.L" #"H4ZJ.DE" #"XSMI.SW" #"EUNY.DE" # "IEDY.L"  #IEFV.L" #"HMWD.L"
    #hist: Series = InvestMonitorLogic.getHistory( ticker, SeriesName.Close )
    log = InvestMonitorLogic( )
    pos:XDepotPosition = log.getDepotPosition( ticker )
    ip = ipc.createInfoPanel( pos )
    ip.show()
    app.exec_()



