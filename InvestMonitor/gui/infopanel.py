from typing import List, Callable

import matplotlib
from PySide2.QtCore import QSize, Signal, Qt
from PySide2.QtGui import QFont

from base.baseqtderivates import BaseGridLayout, BaseLabel, BaseEdit, IntEdit, FloatEdit, HLine, \
    BaseButton, BaseComboBox, HistoryButton, BaseDialogWithButtons, BaseButtonDefinition, ButtonIdent
from base.enumhelper import getEnumFromValue
from data.finance.tickerhistory import TickerHistory, Period, Interval
from utfsymbols import symDELTA, symREFRESH, symZOOM, symBORDER, symINFO, symBINOC, symSUM, symAVG
from interface.interfaces import XDepotPosition

matplotlib.use('Qt5Agg')
from PySide2.QtWidgets import QApplication, QHBoxLayout, QFrame, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT #as NavigationToolbar
from matplotlib.figure import Figure
#import pandas as pd

class AbgeltungssteuerDlg( BaseDialogWithButtons ):
    compute_steuer = Signal( int ) # arg: Anzahl zu verkaufender Stücke
    @staticmethod
    def getButtonDefinitions( compute_callback:Callable, close_callback:Callable ) -> List[BaseButtonDefinition]:
        computeButtonDef = BaseButtonDefinition( text="Berechnen", tooltip="Abgeltungssteuer berechnen",
                                                 callback=compute_callback, ident=ButtonIdent.IDENT_OK )
        closeButtonDef = BaseButtonDefinition( text="Schließen", tooltip="Dialog schließen",
                                               callback=close_callback, ident=ButtonIdent.IDENT_CLOSE )
        return [computeButtonDef, closeButtonDef]

    def __init__( self, wkn:str, kurs:float, max_stck:int ):
        BaseDialogWithButtons.__init__( self, "Berechnung der Abgeltungssteuer für '%s'" % wkn,
                                        AbgeltungssteuerDlg.getButtonDefinitions( self.onComputeBtnClicked,
                                                                                  self.onCloseBtnClicked ) )
        self._wkn = wkn
        self._kurs = kurs
        self._max_stck = max_stck # maximal zur Verfügung stehende Anteile
        self._mainWidget = QWidget()
        self._lblKurs = FloatEdit( isReadOnly=True )
        self._lblKurs.setFixedWidth( 70 )
        self._ieStueck = IntEdit()
        self._ieStueck.setFixedWidth( 70 )
        self._ieSteuer = IntEdit( isReadOnly=True )
        self._ieSteuer.setFixedWidth( 70 )
        self._createMainWidget()
        self._dataToGui()
        self.setMainWidget( self._mainWidget )
        #self.setFixedWidth( 500 )

    def _createMainWidget( self ):
        l = BaseGridLayout()
        self._mainWidget.setLayout( l )
        r = c = 0
        l.addWidget( BaseLabel( "Aktueller Kurs " ), r, c )
        c = 1
        l.addWidget( self._lblKurs, r, c )
        c = 2
        l.addWidget( BaseLabel( "€" ), r, c )

        r += 1
        c = 0
        l.addWidget( BaseLabel( "Zu verkaufende Anteile "), r, c )
        c = 1
        l.addWidget( self._ieStueck, r, c )

        r += 1
        c = 0
        l.addWidget( BaseLabel( "Errechnete Abgeltungssteuer " ), r, c )
        c = 1
        l.addWidget( self._ieSteuer, r, c )
        c = 2
        l.addWidget( BaseLabel( "€" ), r, c )

    def _dataToGui( self ):
        self._lblKurs.setValue( self._kurs )
        self._ieStueck.setValue( self._max_stck )
        self._ieSteuer.setValue( 0 )

    def setAbgeltungssteuer( self, steuer:int ):
        self._ieSteuer.setIntValue( steuer )

    def onComputeBtnClicked( self ):
        self.compute_steuer.emit( self._ieStueck.getIntValue() )

    def onCloseBtnClicked( self ):
        self.close()

def testAbgeltungssteuerDlg():
    app = QApplication()
    dlg = AbgeltungssteuerDlg( wkn="ABCDEF", kurs=30.90, max_stck=30 )
    dlg.exec_()

# ########### TEST TEST TEST TEST TEST
# class InfoPanel_( QFrame ):
#     update_graph = Signal( Period, Interval )
#     enter_bestand_delta = Signal()
#     compute_abgeltungssteuer = Signal()
#     show_kauf_historie = Signal()
#     update_kurs = Signal()
#     show_details = Signal()
#     show_div_payments = Signal()
#     show_simul_yield = Signal()
#     nr = 0
#     labelfont = QFont( "Ubuntu", 16 )
#     def __init__( self ):
#         QFrame.__init__( self )
#         self._nr = str( self.nr )
#         #borderstyle = "#" + self._nr + " {border: 5px solid darkblue; }"
#         borderstyle = "border: 2px solid darkblue;"
#         self.setStyleSheet( borderstyle )
#         self.setFixedSize( QSize(400, 400) )
#         self._lbl = BaseLabel( self._nr )
#         self._lbl.setFont( self.labelfont )
#         self._lbl.setFixedWidth( 50 )
#         self._lbl.setFixedHeight( 50 )
#         self._lbl.setAlignment( Qt.AlignCenter )
#         labelstyle = "border: 1px solid red;"
#         self._lbl.setStyleSheet( labelstyle )
#         self.nr += 1
#         self._layout = BaseGridLayout()
#         self.setLayout( self._layout )
#         self._layout.addWidget( self._lbl, 0, 0, 1, 1, alignment=Qt.AlignVCenter | Qt.AlignHCenter )
#
#     def getLabel( self ) -> str:
#         return self._nr
#
#     def setDepotPosition( self, x: XDepotPosition ):
#         pass
#
#     def setPeriodAndInterval( self, period: Period, interval: Interval ):
#         pass
#
#     def setSortInfo( self, values: str ):
#         pass
####################################


############################################################
class NavigationToolbar(NavigationToolbar2QT):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', None)]

##############################################################
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, width=5, height=4, dpi=100):
        self._width = width
        self._height = height
        self._dpi = dpi
        self._figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self._figure.add_subplot(111)
        super(MplCanvas, self).__init__( self._figure )

        self.toolbar = NavigationToolbar( self, self )

    def clear( self ):
        self._figure.clear()
        self._figure = Figure( figsize=(self._width, self._height), dpi=self._dpi )
        self.figure = self._figure
        self.axes = self._figure.add_subplot( 111 )

    def draw( self ):
        super().draw()
        rend = self.get_renderer()
        self._figure.draw( rend )

    def refresh( self ):
        super().resize( self._width, self._height )


#############################################################
class InfoPanel( QFrame ):
    """
    Ein InfoPanel enthält alle Informationen zu einem Wertpapier (Aktie, Fonds- oder ETF-Anteil)
    und einen Graph, der die Kursentwicklung eines Zeitraums anzeigt.
    """
    update_graph = Signal( Period, Interval )
    enter_bestand_delta = Signal()
    compute_abgeltungssteuer = Signal()
    show_kauf_historie = Signal()
    update_kurs = Signal()
    show_details = Signal()
    show_div_payments = Signal()
    show_simul_yield = Signal()

    @staticmethod
    def createCombo( items: List[str], callback ) -> BaseComboBox:
        cbo = BaseComboBox()
        cbo.addItems( items )
        cbo.currentIndexChanged.connect( callback )
        return cbo

    def __init__(self):
        QFrame.__init__( self )
        #borderstyle = "border: 3px solid darkblue;"
        self._borderstyle = "InfoPanel {border: 2px solid darkblue; }"
        self.setStyleSheet( self._borderstyle )
        self._row = -1 # row im MainWindow
        self._col = -1 # col im MainWindow
        maxwnumlabels = 70
        wdate = 70
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._mplCanvas = MplCanvas()
        self._x:XDepotPosition = None
        self._lblName = BaseEdit( isReadOnly=True)
        self._btnDetails = BaseButton( symINFO )
        self._btnDetails.clicked.connect( self.show_details.emit )
        self._btnDetails.setMaximumSize( QSize(23, 23) )
        self._btnSelect = BaseButton( symBORDER )
        self._btnSelect.clicked.connect( lambda x: self.setSelected( not self._isSelected ) )
        self._isSelected = False
        self._btnSelect.setMaximumSize( QSize( 23, 23 ) )
        self._laySort = QHBoxLayout()
        self._lblSortValues = BaseEdit( isReadOnly=True )
        self._lblSortValues.setObjectName( "sortvalues" )
        self._lblSortValues.setStyleSheet( "#sortvalues {background: #e7e3e4}")

        self._layCombos = QHBoxLayout()
        self._cboPeriod = self.createCombo( Period.getPeriods(), self.onPeriodIntervalChanged )
        self._cboInterval = self.createCombo( Interval.getIntervals(), self.onPeriodIntervalChanged )
        self._btnUpdateGraph = BaseButton( "⟳", callback=self.onUpdateGraphClicked )
        self._btnUpdateGraph.setFixedSize( QSize( 23, 23 ) )

        self._lblWkn = BaseEdit( isReadOnly=True )
        #self._lblWkn.setMaximumWidth( maxwtextlabels )
        self._lblTicker = BaseEdit( isReadOnly=True )
        self._lblTicker.setFixedWidth( 90 )
        self._lblIsin = BaseEdit( isReadOnly=True )
        # self._lblIsin.setMaximumWidth( 110 )
        self._lblAnteilUSA = BaseEdit( isReadOnly=True )
        self._lblAnteilUSA.setFixedWidth( 23 )
        self._lblTer = FloatEdit( isReadOnly=True )
        self._lblTer.setFixedWidth( 43 )
        self._lblWaehrung = BaseEdit( isReadOnly=True )
        self._lblWaehrung.setFixedWidth( 90 )
        self._lblAcc = BaseEdit( isReadOnly=True )
        #self._lblAcc.setMaximumWidth( maxwtextlabels )
        self._lblStueck = IntEdit( isReadOnly=True )
        self._lblStueck.setMaximumWidth( maxwnumlabels )
        self._btnStueckDelta = BaseButton( symDELTA )
        self._btnStueckDelta.clicked.connect( self.enter_bestand_delta.emit )
        self._btnStueckDelta.setFixedSize( QSize(23, 23) )
        self._btnAbgeltungssteuer = BaseButton( "§" )
        #self._btnAbgeltungssteuer.clicked.connect( self.onAbgeltungssteuerClicked )
        self._btnAbgeltungssteuer.clicked.connect( self.compute_abgeltungssteuer.emit )
        self._btnAbgeltungssteuer.setFixedSize( QSize(23, 23) )
        self._lblEinstandswertRestbestand = IntEdit( isReadOnly=True )
        self._lblEinstandswertRestbestand.setMaximumWidth( maxwnumlabels )
        self._btnKaufHistorie = HistoryButton( "Zeigt die Historie der Käufe an" )
        self._btnKaufHistorie.clicked.connect( self.show_kauf_historie.emit )
        self._btnKaufHistorie.setFixedSize( QSize(23, 23) )
        self._lblErsterKauf = BaseEdit( isReadOnly=True )
        self._lblErsterKauf.setFixedWidth( wdate )
        self._lblErsterKauf.setContentsMargins( 0, 0, 0,0 )
        self._lblLetzterKauf = BaseEdit( isReadOnly=True )
        self._lblLetzterKauf.setFixedWidth( wdate )
        self._lblLetzterKauf.setContentsMargins(0, 0, 0, 0)
        self._lblPreisProStueck = FloatEdit( isReadOnly=True )
        self._lblPreisProStueck.setMaximumWidth( maxwnumlabels )
        self._lblMaxKaufpreis = FloatEdit( isReadOnly=True )
        self._lblMaxKaufpreis.setMaximumWidth( maxwnumlabels )
        self._lblMinKaufpreis = FloatEdit( isReadOnly=True )
        self._lblMinKaufpreis.setMaximumWidth( maxwnumlabels )
        self._lblGesamtWertAktuell = IntEdit( isReadOnly=True )
        self._lblGesamtWertAktuell.setMaximumWidth( maxwnumlabels )
        self._lblAnteilAnSummeGesamtwerte = IntEdit( isReadOnly=True )
        self._lblAnteilAnSummeGesamtwerte.setMaximumWidth( 23 )
        self._lblKursAktuell = FloatEdit( isReadOnly=True )
        self._lblKursAktuell.setMaximumWidth( maxwnumlabels )
        self._btnKursAktualisieren = BaseButton( symREFRESH )
        self._btnKursAktualisieren.clicked.connect( self.update_kurs.emit )
        self._btnKursAktualisieren.setFixedSize( QSize(23, 23) )
        self._lblDivJeStck = FloatEdit( isReadOnly=True )
        self._lblDivJeStck.setMaximumWidth( maxwnumlabels )
        self._btnDividendPayments = BaseButton( symZOOM )
        self._btnDividendPayments.clicked.connect( self.show_div_payments.emit )
        self._btnDividendPayments.setFixedSize( QSize( 23, 23 ) )
        self._lblDivYield = FloatEdit( isReadOnly=True )
        self._lblDivYield.setMaximumWidth( maxwnumlabels )
        self._btnSimulYield = BaseButton( symBINOC )
        self._btnSimulYield.setFixedSize( QSize(23, 23) )
        self._btnSimulYield.clicked.connect( self.show_simul_yield.emit )
        self._lblPaidDividend = IntEdit( isReadOnly=False )
        self._lblPaidDividend.setMaximumWidth( maxwnumlabels )

        self._lblDeltaProz = FloatEdit( isReadOnly=True )
        self._lblDeltaProz.setMaximumWidth( maxwnumlabels )
        self._createGui()

    def _createGui( self ):
        l = self._layout
        cols = 6
        r, c = 0, 0
        layNameAndWaehrung = QHBoxLayout()
        layNameAndWaehrung.addWidget( self._lblName )
        self._lblAcc.setFixedWidth( 40 )
        layNameAndWaehrung.addWidget( self._lblAcc )
        self._lblWaehrung.setFixedWidth( 40 )
        layNameAndWaehrung.addWidget( self._lblWaehrung )
        l.addLayout( layNameAndWaehrung, r, c, 1, 6 )

        c = 6
        layBtnDetAndMark = QHBoxLayout()
        layBtnDetAndMark.addWidget( self._btnDetails )
        layBtnDetAndMark.addWidget( self._btnSelect )
        self._layout.addLayout( layBtnDetAndMark, r, c )
        self._btnDetails.setToolTip( "Details anzeigen" )
        self._btnSelect.setToolTip( "Diese Depotposition markieren" )

        r += 1
        c = 0
        self._laySort.addWidget( BaseLabel( "Sort" ) )
        self._laySort.addWidget( self._lblSortValues )
        l.addLayout( self._laySort, r, c, 1, 5 )

        self._layCombos.addWidget( BaseLabel( "Period" ) )
        self._layCombos.addWidget( self._cboPeriod )
        self._layCombos.addWidget( BaseLabel( " Interval" ) )
        self._layCombos.addWidget( self._cboInterval )
        self._layCombos.addWidget( self._btnUpdateGraph )
        self._layCombos.addStretch()
        c = 5
        l.addLayout( self._layCombos, r, c )

        r += 1
        c = 0
        self._lblWkn.setFixedWidth( 75 )
        l.addWidget( self._lblWkn, r, c, 1, 1 )
        c = 1
        self._lblTicker.setFixedWidth( 75 )
        l.addWidget( self._lblTicker, r, c, 1, 1 )

        r += 1
        c = 0
        l.addWidget( self._lblIsin, r, c, 1, 2 )

        r += 1
        c = 0
        l.addWidget( BaseLabel( "USA " ), r, c )
        c = 1
        self._lblAnteilUSA.setToolTip( "Anteil von Firmen mit Sitz in den USA" )
        lay = QHBoxLayout()
        lay.setSpacing( 1 )
        lay.setMargin( 0 )
        lay.addWidget( self._lblAnteilUSA )
        lblProz = BaseLabel( "%" )
        lblProz.setFixedWidth( 20 )
        lay.addWidget( lblProz )
        lblTer = BaseLabel( "TER" )
        lblTer.setFixedWidth( 30 )
        lay.addWidget( lblTer )
        l.addLayout( lay, r, c, 1, 1, alignment=Qt.AlignLeft )
        c = 2
        lay = QHBoxLayout()
        lay.setSpacing( 1 )
        lay.addWidget( self._lblTer )
        self._lblTer.setToolTip( "Gesamtkosten dieser Depotposition pro Jahr (Total Expense Ratio)")
        lblProz = BaseLabel( "%" )
        lblProz.setFixedWidth( 20 )
        lay.addWidget( lblProz )
        l.addLayout( lay, r, c, 1, 2 )

        r += 1
        c = 0
        l.addWidget( BaseLabel( "Bestand" ), r, c )
        c = 1
        l.addWidget( self._lblStueck, r, c )
        c = 2
        l.addWidget( BaseLabel("St"), r, c )
        c = 3
        lay = QHBoxLayout()
        lay.setSpacing( 1 )
        lay.setMargin( 0 )
        self._btnStueckDelta.setToolTip( "Bestandsveränderung eintragen (Kauf/Verkauf)" )
        lay.addWidget( self._btnStueckDelta, stretch=0, alignment=Qt.AlignLeft )
        self._btnAbgeltungssteuer.setToolTip( "Abgeltungssteuer auf zu verkaufende Stückzahl errechnen" )
        lay.addWidget( self._btnAbgeltungssteuer, stretch=0, alignment=Qt.AlignLeft )
        l.addLayout( lay, r, c )

        r += 1
        c = 0
        l.addWidget( BaseLabel( "Ø Kp./Stck" ), r, c )
        c = 1
        self._lblPreisProStueck.setToolTip( "Summe aller Einzelkäufe / Stück" )
        l.addWidget( self._lblPreisProStueck, r, c )
        c = 2
        l.addWidget( BaseLabel( "€"), r, c )

        r += 1
        c = 0
        l.addWidget( BaseLabel( symSUM + " Käufe" ), r, c )
        c = 1
        self._lblEinstandswertRestbestand.setToolTip( "Stück mal " + symAVG + " Kp./Stck" )  # ( "Summe aller Einzelkäufe" )
        l.addWidget( self._lblEinstandswertRestbestand, r, c )
        c = 2
        l.addWidget( BaseLabel( "€" ), r, c )
        c = 3
        l.addWidget( self._btnKaufHistorie, r, c, 1, 1, Qt.AlignLeft )

        r += 1
        c = 0
        l.addWidget( BaseLabel( "1./Ltztr. Kauf" ), r, c )
        c = 1
        lay = QHBoxLayout()
        font = QFont( "Ubuntu", 8 )
        self._lblErsterKauf.setFont( font )
        lay.addWidget( self._lblErsterKauf )
        self._lblLetzterKauf.setFont( font )
        lay.addWidget( self._lblLetzterKauf )
        l.addLayout( lay, r, c, 1, 3 )

        r += 1
        c = 0
        l.addWidget( HLine(), r, c, 1, 3 )

        r += 1
        l.addWidget( BaseLabel( "Wert" ), r, c )
        c = 1
        self._lblGesamtWertAktuell.setToolTip( "Wert der Depotposition: Stück * akt. Kurs" )
        l.addWidget( self._lblGesamtWertAktuell, r, c )
        c = 2
        l.addWidget( BaseLabel( "€" ), r, c )
        c = 3
        self._lblAnteilAnSummeGesamtwerte.setToolTip( "Anteil dieser Depotposition an der Summe der Gesamtwerte "
                                                      "aller Depotpositionen im InvestMonitor" )
        lay = QHBoxLayout()
        lay.setSpacing( 0 )
        lay.addWidget( self._lblAnteilAnSummeGesamtwerte )
        lay.addWidget( BaseLabel( "%" ) )
        l.addLayout( lay, r, c )

        r += 1
        c = 0
        l.addWidget( BaseLabel( "Kurs" ), r, c )
        c = 1
        self._lblKursAktuell.setToolTip( "aktueller Kurs in Euro" )
        l.addWidget( self._lblKursAktuell, r, c )
        c = 2
        l.addWidget( BaseLabel( "€" ), r, c )
        c = 3
        self._btnKursAktualisieren.setToolTip( "Kurs aktualisieren")
        l.addWidget( self._btnKursAktualisieren, r, c, 1, 1, Qt.AlignLeft )
        r += 1
        c = 0
        l.addWidget( BaseLabel( "Div./Stck" ), r, c )
        c = 1
        self._lblDivJeStck.setToolTip( "Dividende in Euro im gewählten Zeitraum pro Stück" )
        l.addWidget( self._lblDivJeStck, r, c )
        c = 2
        l.addWidget( BaseLabel( "€" ) )
        c = 3
        self._btnDividendPayments.setToolTip( "Dividendenzahlungen im gewählten Zeitraum in EUR" )
        l.addWidget( self._btnDividendPayments, r, c, 1, 1, Qt.AlignLeft )

        r += 1
        c = 0
        l.addWidget( BaseLabel( "Div.Rend." ), r, c )
        c = 1
        self._lblDivYield.setToolTip( "Dividendenrendite: Summe der Dividenden in der gewählten Periode/"
                                      "Kurs am ersten Tag der Periode" )
        l.addWidget( self._lblDivYield, r, c )
        c = 2
        l.addWidget( BaseLabel( "%" ) )
        c = 3
        self._btnSimulYield.setToolTip( "Simuliere die Dividendenrendite für 1 Jahr anhand der durschnittl. Dividendzahlung der eingestellten Periode "
                                        "\nund des aktuellen Kurses")
        l.addWidget( self._btnSimulYield, r, c )

        r += 1
        c = 0
        l.addWidget( BaseLabel( symSUM + " Div. Periode" ), r, c )
        c = 1
        self._lblPaidDividend.setToolTip( "Summe der Dividendenzahlungen (vor Abgeltungssteuer)\n"
                                   "für diese Depotposition in der eingestellten Periode."
                                   "\nEs wird der zum Zeitpunkt der Ausschüttung vorhandene Bestand berücksichtigt." )
        l.addWidget( self._lblPaidDividend )
        c = 2
        l.addWidget( BaseLabel( "€" ), r, c )

        r += 1
        c = 0
        l.addWidget( HLine(), r, c, 1, 3 )

        r += 1
        c = 0
        l.addWidget( BaseLabel( symDELTA + " Wert" ), r, c )
        c = 1
        self._lblDeltaProz.setToolTip( "Verh. durchschn. Kaufpreis zu akt. Kurs" )
        l.addWidget( self._lblDeltaProz, r, c )
        c = 2
        l.addWidget( BaseLabel( "%" ), r, c )

        #der Graph:
        r, c = 2, 4
        l.addWidget( self._mplCanvas, r, c, l.rowCount()-1, 3 )

        l.setColumnStretch( 0, 0 )
        l.setColumnStretch( 1, 0 )
        l.setColumnStretch( 2, 0 )
        l.setColumnStretch( 3, 0 )
        l.setColumnStretch( 4, 1 )

    def setDepotPosition( self, x:XDepotPosition ):
        self._x = x
        self.setObjectName( x.wkn )
        self._dataToGui()
        self._btnUpdateGraph.setEnabled( False )
        self._plot()

    def setPeriodAndInterval( self, period:Period, interval:Interval ):
        self._cboPeriod.setCurrentText( period.value )
        self._cboInterval.setCurrentText( interval.value )
        self._btnUpdateGraph.setEnabled( False )

    def changeModel( self, x:XDepotPosition ):
        """
        Versieht dieses InfoPanel mit einer geänderten Depot-Position, was zur Änderung es Graphen führt.
        (x- und ggf. y-Achse - nach Änderung von Period oder Interval)
        :return:
        """
        self._x = x
        self._dataToGui()
        self._btnUpdateGraph.setEnabled( False )
        self._mplCanvas.clear()
        self._plot()
        self._mplCanvas.draw()
        self._mplCanvas.refresh()

    def _dataToGui( self ):
        x = self._x
        self._cboPeriod.setCurrentText( x.history_period.value )
        self._cboInterval.setCurrentText( x.history_interval.value )
        self._lblName.setValue( x.name )
        self._lblIsin.setValue( x.isin )
        self._lblAnteilUSA.setValue( str(x.anteil_usa ) )
        self._lblTer.setValue( x.ter )
        self._lblWkn.setValue( x.wkn )
        self._lblTicker.setValue( x.ticker )
        self._lblWaehrung.setValue( x.waehrung )
        self._lblAcc.setValue( "Acc" if x.flag_acc else "Dis" )
        self._lblStueck.setValue( x.stueck )
        #self._lblGesamtPreis.setValue( x.gesamtkaufpreis )
        self._lblEinstandswertRestbestand.setValue( x.einstandswert_restbestand )
        self._lblErsterKauf.setValue( x.erster_kauf )
        self._lblLetzterKauf.setValue( x.letzter_kauf )
        self._lblPreisProStueck.setValue( x.preisprostueck )
        self._lblMaxKaufpreis.setValue( x.maxKaufpreis )
        self._lblMinKaufpreis.setValue( x.minKaufpreis )
        self._lblGesamtWertAktuell.setValue( x.gesamtwert_aktuell )
        self._lblAnteilAnSummeGesamtwerte.setValue( x.anteil_an_summe_gesamtwerte )
        self._lblKursAktuell.setValue( x.kurs_aktuell )
        self._lblDivJeStck.setValue( x.dividend_period )
        self._lblDivYield.setValue( x.dividend_yield )
        self._lblPaidDividend.setValue( x.dividend_paid_period )
        self._lblDeltaProz.setValue( x.delta_proz )

    def updateKursAktuell( self, kurs:float, divYield:float ):
        self._lblKursAktuell.setValue( kurs )
        self._lblDivYield.setValue( divYield )

    def updateOrderRelatedData( self ):
        x = self._x
        self._lblStueck.setValue( x.stueck )
        # self._lblGesamtPreis.setValue( x.gesamtkaufpreis )
        self._lblEinstandswertRestbestand.setValue( x.einstandswert_restbestand )
        self._lblPreisProStueck.setValue( x.preisprostueck )
        self._lblMaxKaufpreis.setValue( x.maxKaufpreis )
        self._lblMinKaufpreis.setValue( x.minKaufpreis )
        self._lblErsterKauf.setValue( x.erster_kauf )
        self._lblLetzterKauf.setValue( x.letzter_kauf )
        self._lblGesamtWertAktuell.setValue( x.gesamtwert_aktuell )
        self._lblAnteilAnSummeGesamtwerte.setValue( x.anteil_an_summe_gesamtwerte )
        self._lblDeltaProz.setValue( x.delta_proz )

    def updateAnteilAnSummeGesamtwerte( self ):
        self._lblAnteilAnSummeGesamtwerte.setValue( self._x.anteil_an_summe_gesamtwerte )

    def getModel( self ) -> XDepotPosition:
        return self._x

    # def setSelected2( self, selected:bool=True ):
    #     self._lblName.setBold( selected )
    #     color = "red" if selected else "black"
    #     self._lblName.setTextColor( color )

    def setSelected( self, selected:bool=True ):
        if selected:
            # borderstyle = "#" + self._x.wkn + " {border: 5px solid darkblue; }"
            borderstyle = "InfoPanel {border: 5px solid darkblue; }"
        else:
            borderstyle = self._borderstyle #"#" + self._x.wkn + " {border: 2px solid darkblue; }"
        self.setStyleSheet(  borderstyle )
        self._isSelected = selected

    def isSelected( self ) -> bool:
        return self._isSelected

    def setSortInfo( self, values:str ):
        #self._lblSortItems.setValue( items )
        self._lblSortValues.setValue( values )

    def _plot( self ):
        try:
            # kann schiefgehen im TEST-Betrieb und kann dann ignoriert werden
            self._x.history.plot( ax=self._mplCanvas.axes, grid=True )
        except:
            pass

    def onPeriodIntervalChanged( self, arg ):
        self._btnUpdateGraph.setEnabled( True )

    def onUpdateGraphClicked( self ):
        period = getEnumFromValue( Period, self._cboPeriod.currentText() )
        interval = getEnumFromValue( Interval, self._cboInterval.currentText() )
        self._btnUpdateGraph.setEnabled( False )
        self.update_graph.emit( period, interval )

    def setPosition( self, row:int, col:int ):
        self._row = row
        self._col = col

    def getPosition( self ) -> (int, int):
        return self._row, self._col

##########  TEST ###  TEST  ###################################################
def test():
    app = QApplication()
    ip = InfoPanel()
    #ip.setFrameRect()
    #ip.setContentsMargins( 5, 5, 5, 5 )
    # pal = ip.palette()
    # pal.setColor( QPalette.WindowText, QColor( "red" ) )
    # ip.setPalette( pal )
    # ip.setObjectName( "ip" )
    # ip.setStyleSheet( "#ip {border: 5px solid black; }")
    # ip.setStyleSheet( "#ip {border: 0px solid black; }" )
    # ip.setFrameStyle( QFrame.Box | QFrame.Raised )
    # ip.setLineWidth( 3 )
    #ip.setFrameStyle( QFrame.NoFrame )
    x = XDepotPosition()
    x.name = "WisdomTree Global Quality Dividend Growth"
    x.wkn = "A2AG1E"
    x.isin = "IE00BZ56SW52"
    x.ticker = "WTEM.DE"
    x.basic_index = "WisdomTree Global Developed Quality Dividend Growth index"
    x.gattung = "ETF"
    x.waehrung = "USD"
    x.flag_acc = True
    x.ter = 0.12
    x.beschreibung = "The WisdomTree Global Quality Dividend Growth UCITS ETF USD Acc seeks to track the WisdomTree Global Developed Quality Dividend Growth index. The WisdomTree Global Developed Quality Dividend Growth index tracks dividend-paying developed markets stocks with growth characteristics. The index is a fundamentally weighted index."
    x.history = TickerHistory.getTickerHistoryByPeriod( x.ticker )
    x.stueck = 445
    #x.gesamtkaufpreis = 13461
    x.einstandswert_restbestand = 13461
    x.preisprostueck = round( 13461/445, 2 )
    x.minKaufpreis = 30.00
    x.maxKaufpreis = 31.21
    x.kurs_aktuell = 30.02
    x.gesamtwert_aktuell = round( x.stueck * x.kurs_aktuell, 2 )
    x.anteil_an_summe_gesamtwerte = 25
    #x.delta_proz = round( (x.gesamtwert_aktuell - x.gesamtkaufpreis) * 100 / x.gesamtkaufpreis, 2 )
    x.delta_proz = round( (x.kurs_aktuell - x.preisprostueck) * 100 / x.preisprostueck, 2 )
    x.depot_id = "ING_023"
    x.bank = "Ing DiBa"
    x.depot_nr = 4242424256
    x.depot_vrrkto = "FR55 0098 9907 6676 9912 12"
    # df = pd.DataFrame( [
    #     [0, 10], [5, 15], [2, 20], [15, 25], [4, 10],
    # ], columns=['A', 'B'] )
    ip.setDepotPosition( x )
    #ip.setSelected2()
    ip.show()
    app.exec_()