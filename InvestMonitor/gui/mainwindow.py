from typing import List

from PySide2.QtCore import Signal, QSize, QPoint
from PySide2.QtGui import Qt, QScreen
from PySide2.QtWidgets import QMainWindow, QScrollArea, QWidget, QApplication, QDesktopWidget, QHBoxLayout, QMenu, \
    QAction, QMenuBar

from base.baseqtderivates import BaseGridLayout, BaseToolBar, SearchField, BaseComboBox, BaseLabel, Separator, \
    BaseButton, BaseWidget, BaseEdit, IntEdit
from base.dragndrop import DragWidgetsContainer
from base.enumhelper import getEnumValues, getEnumFromValue
from gui.infopanel import InfoPanel
from imon.definitions import DEFAULT_PERIOD, DEFAULT_INTERVAL
from imon.enums import InfoPanelOrder, Period, Interval
from utfsymbols import symSUM, symDELTA

#
# class AllInfoPanel___( QWidget ):
#     def __init__( self ):
#         QWidget.__init__( self )
#         self._layout = BaseGridLayout()
#         self.setLayout( self._layout )
#         self._row = 0
#         self._col = 0
#         self._maxCols = 3
#
#     def addInfoPanel( self, infopanel: InfoPanel ):
#         self._layout.addWidget( infopanel, self._row, self._col )
#         self._col += 1
#         if self._col == self._maxCols:
#             self._row += 1
#             self._col = 0
#
#     def removeInfoPanel( self, ip:InfoPanel ):
#         self._layout.removeWidget( ip )
#
#     def clear( self ) -> None:
#         self.children().clear()
#         self._row = 0
#         self._col = 0

############################################################
class AllInfoPanel( DragWidgetsContainer ):
    def __init__( self ):
        DragWidgetsContainer.__init__( self )
        self._row = 0
        self._col = 0
        self._maxCols = 3

    def addInfoPanel( self, infopanel: InfoPanel ):
        self.addWidget( infopanel, self._row, self._col )
        self._col += 1
        if self._col == self._maxCols:
            self._row += 1
            self._col = 0
        rows, cols = self.getRowAndColumnCount()
        #print( "rows: ", rows, " -- cols: ", cols )

    def removeInfoPanel( self, ip:InfoPanel ):
        self.removeWidget( ip )

    def clear( self ) -> None:
        self.children().clear()
        self._row = 0
        self._col = 0


##############################################################
class AllInfoPanelsScrollArea( QScrollArea ):
    def __init__(self):
        QScrollArea.__init__( self )
        self._allPanels = AllInfoPanel()
        self.setWidget( self._allPanels )
        # self._layout = BaseGridLayout()
        # self.setLayout( self._layout )
        self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )
        self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOn )
        self.setWidgetResizable( True )

    def addInfoPanel( self, infoPanel:InfoPanel ):
        self._allPanels.addInfoPanel( infoPanel )

    def removeWidget( self, widget:QWidget ):
        self._allPanels.removeWidget( widget )

    def clear( self ):
        self._allPanels.clear()

##############################################################
class IMonToolBar( BaseToolBar ):
    period_interval_changed = Signal( Period, Interval )
    def __init__(self):
        BaseToolBar.__init__( self )
        self._wertInfo = BaseWidget()
        self.addWidget( BaseLabel( symSUM + " Käufe: ") )
        self._summeKaeufe = IntEdit( isReadOnly=True )
        self._summeKaeufe.setFixedWidth( 70 )
        self.addWidget( self._summeKaeufe )
        self.addWidget( BaseLabel( "€   " ) )
        self.addWidget( BaseLabel( symSUM + " akt. Wert: " ) )
        self._summeAktuelleWerte = IntEdit( isReadOnly=True )
        self._summeAktuelleWerte.setFixedWidth( 70 )
        self.addWidget( self._summeAktuelleWerte )
        self.addWidget( BaseLabel( "€   " ) )
        self.addWidget( BaseLabel( symDELTA + ": ") )
        self._delta = IntEdit( isReadOnly=True )
        self._delta.setFixedWidth( 35 )
        self.addWidget( self._delta )
        self.addWidget( BaseLabel( "%  " ) )
        self.addSeparator()

        self._searchField = SearchField()
        self._searchField.setPlaceholderText( "Suche nach WKN oder ISIN oder Ticker" )
        self._searchField.setFixedWidth( 300 )
        self.addWidget( self._searchField )
        self._cboOrder = BaseComboBox()
        self._cboOrder.addItems( getEnumValues( InfoPanelOrder ) )
        self.addSeparator()

        self.addWidget( BaseLabel( " InfoPanels anordnen:  " ) )
        self.addWidget( self._cboOrder )
        self.addSeparator()

        self._periodAndIntervalWidget = BaseWidget()
        self._cboPeriod = BaseComboBox()
        self._cboInterval = BaseComboBox()
        self._btnUpdateAllInfoPanels = BaseButton( "⟳", callback=self.onUpdateAllInfoPanels )
        self._addPeriodAndIntervalWidget()
        self.addSeparator()
        # Dividendenzahlungen
        # a) in der eingestellten Period
        self._lblDividendPaid = IntEdit( isReadOnly=True )
        self._lblDividendPaid.setFixedWidth( 70 )
        self._lblDividendPaid.setToolTip( "Summe der tatsächlich erhaltenen Dividenden in der eingestellten Periode" )
        self.addWidget( BaseLabel( symSUM + " Div. Periode: " ) )
        self.addWidget( self._lblDividendPaid )
        self.addWidget( BaseLabel( "€" ) )
        spacer = BaseLabel()
        spacer.setFixedWidth( 10 )
        self.addWidget( spacer )
        # b) im laufenden Jahr
        self._lblDividendPaidLfdJahr = IntEdit( isReadOnly=True )
        self._lblDividendPaidLfdJahr.setFixedWidth( 70 )
        self._lblDividendPaidLfdJahr.setToolTip( "Summe der tatsächlich erhaltenen Dividenden im laufenden Jahr" )
        self.addWidget( BaseLabel( symSUM + " Div. lfd. Jahr: " ) )
        self.addWidget( self._lblDividendPaidLfdJahr )
        self.addWidget( BaseLabel( "€" ) )
        self.addSeparator()

    def _addPeriodAndIntervalWidget( self ):
        self._cboPeriod.addItems( Period.getPeriods() )
        self._cboPeriod.setCurrentText( DEFAULT_PERIOD.value )
        self._cboInterval.addItems( Interval.getIntervals() )
        self._cboInterval.setCurrentText( DEFAULT_INTERVAL.value )
        self._cboPeriod.currentIndexChanged.connect( self.onPeriodIntervalChanged )
        self._cboInterval.currentIndexChanged.connect( self.onPeriodIntervalChanged )
        lay = QHBoxLayout()
        lay.addWidget( BaseLabel( "Period" ) )
        lay.addWidget( self._cboPeriod )
        lay.addWidget( BaseLabel( "Interval" ) )
        lay.addWidget( self._cboInterval )
        self._btnUpdateAllInfoPanels.setFixedSize( QSize(25, 25) )
        self._btnUpdateAllInfoPanels.setEnabled( False )
        lay.addWidget( self._btnUpdateAllInfoPanels )
        self._periodAndIntervalWidget.setLayout( lay )
        self.addWidget( self._periodAndIntervalWidget )

    def setSummen( self, sumEinstand:int, sumWert:int, delta:float ):
        self._summeKaeufe.setValue( sumEinstand )
        self._summeAktuelleWerte.setValue( sumWert )
        self._delta.setValue( delta )

    def getSearchField( self ) -> SearchField:
        return self._searchField

    def getOrderComboBox( self ) -> BaseComboBox:
        return self._cboOrder

    def getUndockButton( self ) -> BaseButton:
        return self._btnUndock

    def getAllDeltasButton( self ) -> BaseButton:
        return self._btnAllDeltas

    def getPeriod( self ) -> Period:
        """
        Liefert die in der Combobox "period" eingestellte Periode.
        :return:
        """
        return getEnumFromValue( Period, self._cboPeriod.currentText() )

    def onPeriodIntervalChanged( self, arg ):
        self._btnUpdateAllInfoPanels.setEnabled( True )

    def onUpdateAllInfoPanels( self ):
        period = getEnumFromValue( Period, self._cboPeriod.currentText() )
        interval = getEnumFromValue( Interval, self._cboInterval.currentText() )
        self._btnUpdateAllInfoPanels.setEnabled( False )
        self.period_interval_changed.emit( period, interval )

    def setDividendPaid( self, val:int ):
        self._lblDividendPaid.setValue( val )

    def setDividendPaidLfdJahr( self, val:int ):
        self._lblDividendPaidLfdJahr.setValue( val )

############################################################
class IMonMenuBar( QMenuBar ):
    undock_infopanel = Signal()
    show_orders = Signal()
    show_dividends_period = Signal()
    show_dividends_curr_year = Signal()
    def __init__(self):
        QMenuBar.__init__( self )
        self._menuIMon = QMenu( "InvestMonitor" )
        self._actionBeenden = self._menuIMon.addAction( "Beenden" )
        self.addMenu( self._menuIMon )
        #----
        self._menuDividends = QMenu( "Dividenden" )
        self._actionDividendsPeriod = self._menuDividends.addAction(
                                        "Dividendenzahlungen in der eingestellten Periode..." )
        self._actionDividendsPeriod.triggered.connect( self.show_dividends_period.emit )
        self._actionDividendsCurrYear = self._menuDividends.addAction(
                                        "Dividendenzahlungen im lfd. Jahr..." )
        self._actionDividendsCurrYear.triggered.connect( self.show_dividends_curr_year.emit )
        self.addMenu( self._menuDividends )
        #----
        self._menuExtras = QMenu( "Extras" )
        self._actionUndock = self._menuExtras.addAction( "Markierte InfoPanels in separatem Dialog anzeigen..." )
        self._actionUndock.triggered.connect( self.undock_infopanel.emit )
        self._menuExtras.addSeparator()
        self._actionShowOrders = self._menuExtras.addAction( "Alle Orders anzeigen..." )
        self._actionShowOrders.triggered.connect( self.show_orders.emit )
        self.addMenu( self._menuExtras )
        #---

############################################################
class MainWindow( QMainWindow ):
    showing_now = Signal()
    change_infopanel_order = Signal( InfoPanelOrder )
    undock_infopanel = Signal()
    period_interval_changed = Signal( Period, Interval )
    show_orders = Signal()
    show_dividends_period = Signal()
    show_dividends_curr_year = Signal()
    def __init__( self ):
        QMainWindow.__init__( self )
        self._menuBar = IMonMenuBar()
        self._menuBar.undock_infopanel.connect( self.undock_infopanel.emit )
        self._menuBar.show_orders.connect( self.show_orders.emit )
        self._menuBar.show_dividends_period.connect( self.show_dividends_period.emit )
        self._menuBar.show_dividends_curr_year.connect( self.show_dividends_curr_year.emit )
        self.setMenuBar( self._menuBar )
        self._toolBar = IMonToolBar()
        self.addToolBar( self._toolBar )
        self._toolBar.period_interval_changed.connect( self.period_interval_changed.emit )
        ##########self._allInfoPanel = AllInfoPanel()
        self._panelsScroll = AllInfoPanelsScrollArea()
        ##########self._panelsScroll.setWidget( self._allInfoPanel )
        self.setCentralWidget( self._panelsScroll )
        cbo = self._toolBar.getOrderComboBox()
        cbo.currentTextChanged.connect(
            lambda txt: self.change_infopanel_order.emit( getEnumFromValue( InfoPanelOrder, txt ) ) )
        # btn = self._toolBar.getUndockButton()
        # btn.clicked.connect( self.undock_infopanel.emit )
        # btn = self._toolBar.getAllDeltasButton()
        # btn.clicked.connect( self.show_orders.emit )

    def addInfoPanel( self, infopanel:InfoPanel ):
        self._panelsScroll.addInfoPanel( infopanel )

    def getToolBar( self ) -> IMonToolBar:
        return self._toolBar

    def getSearchField( self ) -> SearchField:
        return self._toolBar.getSearchField()

    def setInfoPanelOrder( self, order:InfoPanelOrder ):
        self._toolBar.getOrderComboBox().setValue( order.value )

    def clear( self ) -> None:
        self._panelsScroll.clear()

    def ensureVisible( self, infopanel:InfoPanel ):
        if infopanel.visibleRegion().isEmpty():
            self._panelsScroll.ensureWidgetVisible( infopanel )

    def removeInfoPanel( self, ip:InfoPanel ):
        self._panelsScroll.removeInfoPanel( ip )

    def show( self ):
        super().show()
        self.showing_now.emit()

#####################################################################################################
def test():
    def changeOrder( newOrder:InfoPanelOrder ):
        print( "new Order: ", newOrder.value )
    app = QApplication()
    win = MainWindow()
    win.show()
    win.change_infopanel_order.connect( changeOrder )
    rect = QDesktopWidget().screenGeometry()
    #r:QPoint = rect.topRight()
    w = rect.right() - rect.left()
    #w = rect.topRight().x() - rect.topLeft().x() - 100
    h = rect.bottom() - rect.top()
    win.resize( QSize( w, h ) )
    app.exec_()
