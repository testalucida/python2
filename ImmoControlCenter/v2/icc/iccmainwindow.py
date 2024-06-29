from functools import partial
from typing import Dict, Any, List, Callable

from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import Qt, Signal, QSize
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QMenuBar, QToolBar, QAction, QMessageBox, QLineEdit, \
    QLabel, \
    QMenu, QTabWidget
from PySide2.QtGui import QKeySequence, QFont, QCursor
from enum import Enum

import datehelper
from base.baseqtderivates import SmartDateEdit, IntDisplay, BaseTabWidget, BaseGridLayout, BaseLabel
from base.messagebox import InfoBox
from datehelper import getDateParts
from v2.einaus.einausview import EinAusTableViewFrame
from v2.icc.interfaces import XSummen
from v2.mtleinaus.mtleinauslogic import MieteTableModel, HausgeldTableModel, AbschlagTableModel
from v2.mtleinaus.mtleinausview import MieteTableView, MieteTableViewFrame, HausgeldTableView, HausgeldTableViewFrame, \
    AbschlagTableViewFrame
from v2.uebrigeregelm.uebrigeregelmaessview import UebrigeRegelmaessTableViewFrame


class MainWindowAction( Enum ):
    OPEN_OBJEKT_STAMMDATEN_VIEW = 1,
    OPEN_MIETVERH_VIEW = 2,
    SAVE_ACTIVE_VIEW=3,
    SAVE_ALL=4,
    PRINT_ACTIVE_VIEW=5,
    OPEN_MIETE_VIEW=6,
    OPEN_HGV_VIEW=7,
    FOLGEJAHR=8,
    OPEN_SOLL_MIETE_VIEW = 9,
    OPEN_SOLL_HG_VIEW = 10,
    OPEN_NKA_VIEW = 11,
    OPEN_HGA_VIEW = 12,
    EXPORT_CSV = 14,
    OPEN_ANLAGEV_VIEW = 15,
    OPEN_OFFENE_POSTEN_VIEW = 16,
    OPEN_SONST_EIN_AUS_VIEW = 17,
    NOTIZEN = 18,
    RENDITE_VIEW = 19,
    MIETERWECHSEL = 20,
    SHOW_VIEWS = 21,
    BRING_DIALOG_TO_FRONT = 22,
    SHOW_TABLE_CONTENT = 23,
    OPEN_GESCHAEFTSREISE_VIEW = 24,
    SAMMELABGABE_DETAIL = 25,
    EXPORT_DB_TO_SERVER = 26,
    IMPORT_DB_FROM_SERVER = 27,
    OPEN_ERTRAG_VIEW = 28,
    EXIT=99


###################   MtlZahlungenTabWidget   #################
class MtlZahlungenTabWidget( BaseTabWidget ):
    def __init__( self, parent=None ):
        BaseTabWidget.__init__( self, parent )

###################   UebrigeRegelmZahlungenTabWidget   #################
class UebrigeRegelmZahlungenTabWidget( BaseTabWidget ):
    def __init__( self, parent=None ):
        BaseTabWidget.__init__( self, parent )

###################   AbrechnungenTabWidget   #################
class AbrechnungenTabWidget( BaseTabWidget ):
    def __init__( self, parent=None ):
        BaseTabWidget.__init__( self, parent )

########################   AlleZahlungenTabWidget   ############
class AlleZahlungenTabWidget( BaseTabWidget ):
    def __init__( self, parent=None ):
        BaseTabWidget.__init__( self, parent )

########################   MainTabWidget   ##################
class MainTabWidget( BaseTabWidget ):
    def __init__( self, parent=None ):
        BaseTabWidget.__init__( self, parent )
        self._mtlZahlungenTab = MtlZahlungenTabWidget()
        self.addTab( self._mtlZahlungenTab, "Regelmäßige Zahlungen" )
        # self._uebrigeRegelmZahlungenTab = UebrigeRegelmZahlungenTabWidget()
        # self.addTab( self._uebrigeRegelmZahlungenTab, "Übrige regelmäßige Zahlungen" )
        self._abrechnungenTab = AbrechnungenTabWidget()
        self.addTab( self._abrechnungenTab, "Jahresabrechnungen" )
        # self._alleZahlungenTab = AlleZahlungenTabWidget()
        # self.addTab( self._alleZahlungenTab, "fdslkjfdsklj Zahlungen" )

    def getMtlZahlungenTab( self ) -> MtlZahlungenTabWidget:
        return self._mtlZahlungenTab

    # def getUebrigeRegelmZahlungenTab( self ) -> UebrigeRegelmZahlungenTabWidget:
    #     return self._uebrigeRegelmZahlungenTab
    #
    def getAbrechnungenTab( self ) -> AbrechnungenTabWidget:
        return self._abrechnungenTab

    # def getAlleZahlungenTab( self ) -> AlleZahlungenTabWidget:
    #     return self._alleZahlungenTab

########################  InfoPanel  ########################
class InfoPanel( QWidget ):
    """
    Ein InfoPanel ohne Buttons, das vom Programm aus geschlossen wird, nachdem ein Thread abgearbeitet ist.
    """
    def __init__( self, title:str, text:str ):
        QWidget.__init__( self )
        self.setWindowTitle( title )
        self._text = text
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._label = BaseLabel()
        self._label.setText( self._text )
        self._label.setAlignment( Qt.AlignCenter )
        self._layout.addWidget( self._label, 0, 0 )
        self.resize( QSize( 500, 200 ) )

    def moveToCursor( self ):
        crsr = QCursor.pos()
        self.move( crsr.x(), crsr.y() )


########################   IccMainWindow   ####################
class IccMainWindow( QMainWindow ):
    def __init__( self, environment ):
        QMainWindow.__init__( self )
        self.shutdownCallback:Callable = None
        self.setWindowTitle( "ImmoControlCenter   " + environment )
        self._menubar:QMenuBar = None
        self._mainTab = MainTabWidget()
        self._mieteTableViewFrame:MieteTableViewFrame = None
        self._hausgeldTableViewFrame: HausgeldTableViewFrame = None
        self._abschlagTableViewFrame: AbschlagTableViewFrame = None
        self._alleZahlungenTableViewFrame:EinAusTableViewFrame = None
        self._toolbar: QToolBar = None
        self._sdLetzteBuchung: SmartDateEdit = SmartDateEdit( self )
        self._leLetzteBuchung: QLineEdit = QLineEdit( self )

        # Summen
        self._idSumEin:IntDisplay = self._createSumDisplay( "Summe aller Einnahmen" )
        self._idSummeSonstAus:IntDisplay = self._createSumDisplay( "Summe aller sonstigen Ausgaben" )
        self._idSummeHGV:IntDisplay = self._createSumDisplay( "Summe aller Hausgeld-Vorauszahlungen" )
        self._idSaldo:IntDisplay = self._createSumDisplay( "Einnahmen minus Ausgaben minus HG-Vorauszahlungen.\n"
                                                           "Ohne Berücksichtigung von Sonderumlagen.\n"
                                                           "Verteilte Aufwendungen werden nur für das Jahr der Bezahlung berücksichtigt.\n"
                                                           "AfA wird nicht berücksichtigt." )
        self._summenfont = QFont( "Times New Roman", 16, weight=QFont.Bold )
        self._summenartfont = QFont( "Times New Roman", 9 )

        self._actionCallbackFnc = None #callback function for all action callbacks
        self._shutdownCallback = None  # callback function for shutdown action
        self._createUI()

    def setShutdownCallback( self, cb:Callable ):
        """
        :param cb: Callback-Function, die keine Argumente empfängt und einen bool-Wert zurückgeben muss:
                    True: alles in Ordnung, Anwendung kann geschlossen werden
                    False: Anwendung nicht schließen
        :return: None
        """
        self._shutdownCallback = cb

    def setSummenValues( self, x:XSummen ):
        self._idSumEin.setIntValue( x.sumEin )
        self._idSummeHGV.setIntValue( x.sumHGV )
        self._idSummeSonstAus.setIntValue( x.sumSonstAus )
        self._idSaldo.setIntValue( x.saldo )

    def getSummenValues( self ) -> XSummen:
        """
        Gibt ein Dict zurück mit den keys "ein", "hgv", "sonstaus", "saldo".
        Die values sind allesamt vom Typ int.
        :return:
        """
        x = XSummen()
        x.sumEin = self._idSumEin.getIntValue()
        x.sumHGV = self._idSummeHGV.getIntValue()
        x.sumSonstAus = self._idSummeSonstAus.getIntValue()
        x.saldo = self._idSaldo.getIntValue()
        return x

    def getPreferredWidth( self ) -> int:
        #w = self._abschlagTableViewFrame.getPreferredWidth()
        w = self._alleZahlungenTableViewFrame.getPreferredWidth()
        return w

    def getPreferredHeight( self ) -> int:
        h = self._alleZahlungenTableViewFrame.getPreferredHeight()
        return h

    # die TableViewFrames für die Tab "Monatliche Zahlungen" setzen: (vom MainController.createGui)
    def setMieteTableViewFrame( self, tvf:MieteTableViewFrame ):
        self._mainTab.getMtlZahlungenTab().addTab( tvf, "Mieten (mtl.)" )
        self._mieteTableViewFrame = tvf

    def setHausgeldTableViewFrame( self, tvf:HausgeldTableViewFrame ):
        self._mainTab.getMtlZahlungenTab().addTab( tvf, "Hausgelder (mtl.)" )
        self._hausgeldTableViewFrame = tvf

    def setAbschlagTableViewFrame( self, tvf:AbschlagTableViewFrame ):
        self._mainTab.getMtlZahlungenTab().addTab( tvf, "Abschläge (mtl., vierteljhrl.)" )
        self._abschlagTableViewFrame = tvf

    def setUebrigeRegelmaessZahlungenTableViewFrame( self, tvf:UebrigeRegelmaessTableViewFrame ):
        self._mainTab.addTab( tvf, "Übrige regelmäßige Zahlungen" )

    def setHGAbrechnungenTableViewFrame( self, tvf ):
        self._mainTab.getAbrechnungenTab().addTab( tvf, "HGA" )

    def setNKAbrechnungenTableViewFrame( self, tvf ):
        self._mainTab.getAbrechnungenTab().addTab( tvf, "NKA" )

    # den TableViewFrame als neuen Tab im MainTabWidget setzen:
    def setAlleZahlungenTableViewFrame( self, tvf:EinAusTableViewFrame ):
        #self._mainTab.getAlleZahlungenTab().addTab( tvf, "Alle Zahlungen" )
        self._mainTab.addTab( tvf, "Alle Zahlungen" )
        self._alleZahlungenTableViewFrame = tvf

    def getMieteTableViewFrame( self ) -> MieteTableViewFrame:
        return self._mieteTableViewFrame

    def getHausgeldTableViewFrame( self ) -> HausgeldTableViewFrame:
        return self._hausgeldTableViewFrame

    def getAlleZahlungenTableViewFrame( self ) -> EinAusTableViewFrame:
        return self._alleZahlungenTableViewFrame


    def onSumFieldsProvidingFailed( self, msg:str ):
        self.showException( msg )

    def _createUI( self ):
        self._createMenusAndTools()
        self.setCentralWidget( self._mainTab )

    def _createMenusAndTools( self ):
        self._menubar = QMenuBar( self )
        self._toolBar = QToolBar( self )
        self._toolBar.addSeparator()
        lbl = QLabel( self, text="Letzte verarbeitete Buchung: " )
        self._toolBar.addWidget( lbl )
        self._sdLetzteBuchung.setToolTip( "Freier Eintrag der Kenndaten der letzten Buchung,\n "
                                          "um beim nächsten Anwendungsstart gezielt weiterarbeiten zu können." )
        self._sdLetzteBuchung.setMaximumWidth( 90 )
        self._sdLetzteBuchung.before_show_calendar.connect( self.onBeforeShowCalendar )
        self._toolBar.addWidget( self._sdLetzteBuchung )
        dummy = QWidget()
        dummy.setFixedWidth( 5 )
        self._toolBar.addWidget( dummy )
        self._leLetzteBuchung.setToolTip( "Freier Eintrag der Kenndaten der letzten Buchung,\n "
                                          "um beim nächsten Anwendungsstart gezielt weiterarbeiten zu können." )
        # self._leLetzteBuchung.setMaximumWidth( 300 )
        self._toolBar.addWidget( self._leLetzteBuchung )

        dummy = QWidget()
        dummy.setFixedWidth( 30 )
        #dummy.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred )
        self._toolBar.addWidget( dummy )

        self._addSumFields()

        self.setMenuBar( self._menubar )
        self.addToolBar( QtCore.Qt.TopToolBarArea, self._toolBar )

    def onBeforeShowCalendar( self ):
        self._sdLetzteBuchung.setDefaultDateFromIsoString( datehelper.getCurrentDateIso() )

    def addMenu( self, menu:QMenu ):
        self._menubar.addMenu( menu )
        # for child in menu.children():
        #     print( str(child) )

    def _addSumFields( self ):
        self._toolBar.addWidget( self._createSumLabel() )
        self._toolBar.addWidget( self._createSumArtLabel( "Einnahmen", 55 ) )
        self._toolBar.addWidget( self._idSumEin )

        self._toolBar.addWidget( self._createLabel( "-", 20 ) )

        self._toolBar.addWidget( self._createSumLabel() )
        self._toolBar.addWidget( self._createSumArtLabel( "Ausgaben", 50 ) )
        self._toolBar.addWidget( self._idSummeSonstAus )

        self._toolBar.addWidget( self._createLabel( "-", 20 ) )

        self._toolBar.addWidget( self._createSumLabel() )
        self._toolBar.addWidget( self._createSumArtLabel( "HGV", 40 ) )
        self._toolBar.addWidget( self._idSummeHGV )

        self._toolBar.addWidget( self._createLabel( "=", 20 ) )

        self._toolBar.addWidget( self._idSaldo )

        self._toolBar.addWidget( self._createSpacer( 20 ) )


    def _createSumDisplay( self, tooltip:str ) -> IntDisplay:
        display = IntDisplay( self )
        display.setMaximumWidth( 70 )
        display.setEnabled( False )
        display.setToolTip( tooltip )
        return display

    def _createSumLabel( self ) -> QLabel:
        lbl = QLabel( self, text = "∑" )
        lbl.setFont( self._summenfont )
        lbl.setMaximumWidth( 15 )
        return lbl

    def _createSumArtLabel( self, sumart:str, width:int ) -> QLabel:
        lbl = QLabel( self, text=sumart )
        lbl.setFont( self._summenartfont )
        lbl.setMaximumWidth( width )
        return lbl

    def _createLabel( self, text:str, width:int ) -> QLabel:
        lbl = QLabel( self, text=text )
        lbl.setMinimumWidth( width )
        lbl.setMaximumWidth( width )
        lbl.setAlignment( Qt.AlignCenter )
        return lbl

    def _createSpacer( self, width:int ) -> QWidget:
        spacer = QWidget( self )
        spacer.setMinimumWidth( width )
        spacer.setMaximumWidth( width )
        return spacer

    def canShutdown( self ) -> bool:
        if self._shutdownCallback:
            return self._shutdownCallback()
        else:
            return True

    def setLetzteBuchung( self, datum:str, text:str ) -> None:
        self._sdLetzteBuchung.setDateFromIsoString( datum )
        self._leLetzteBuchung.setText( text )

    def setTabellenAuswahl( self, tables:List[str] ) -> None:
        """
        Fügt dem SubMenu "Ganze Tabelle anzeigen" soviele Tabellen-Namen hinzu wie in <tables> enthalten.
        :param tables:
        :return:
        """
        n = len( tables )
        actions = [QAction( self._submenuShowTableContent ) for i in range(n)]
        for i in range( n ):
            act = actions[i]
            act.setText( tables[i] )
            #act.triggered.connect( lambda action=act: self.onShowTableContent(action) ) --> funktioniert nicht
            act.triggered.connect( partial( self.onShowTableContent, act ) )
            #txt = act.text()
            #act.triggered.connect( lambda table=txt: self.showTableContent.emit( txt ) ) --> funktioniert nicht
            self._submenuShowTableContent.addAction( act )

    def getLetzteBuchung( self ) -> Dict:
        """
        :return: dictionary with keys "date" and "text"
        """
        d = dict()
        d["datum"] = self._sdLetzteBuchung.getDate()
        d["text"] = self._leLetzteBuchung.text()
        return d

    def setShutdownCallback( self, callbackFnc ) -> None:
        self._shutdownCallback = callbackFnc

    def setActionCallback( self, callbackFnc ) -> None:
        self._actionCallbackFnc = callbackFnc

    def addOpenedDialog( self, name:str, data:Any ):
        """
        Fügt dem Views-Menü eine gerade geöffnete View hinzu
        :param name:
        :param data:
        :return:
        """
        action = QAction( self._viewsMenu, text=name )
        action.setData( data )
        self._viewsMenu.addAction( action )
        #action.triggered.connect( lambda name=name, data=data: self.bringDialogToFront.emit( name, data ) )
        action.triggered.connect( partial( self.onShowDialog, action ) )

    def removeClosedDialog( self, name:str, data:Any ):
        """
        Entfernt den Eintrag <name> aus dem Views-Menü.
        :param name:  Name der zu entfernenden  View (entspricht dem Text des Menüpunktes)
        :param data: Wird zur Identifikation der View verwendet.
        :return:
        """
        for a in self._viewsMenu.actions():
            if a.data() == data:
                self._viewsMenu.removeAction( a )
                break
        return

    def doCallback( self, action:MainWindowAction, arg=None ):
        if self._actionCallbackFnc:
            if arg:
                self._actionCallbackFnc( action, arg )
            else:
                self._actionCallbackFnc( action )

    def showException( self, exception: str, moretext: str = None ):
        print( exception )
        msg = QtWidgets.QMessageBox()
        msg.setIcon( QMessageBox.Critical )
        msg.setText( exception )
        if moretext:
            msg.setInformativeText( moretext )
        msg.setWindowTitle( "Error" )
        msg.exec_()

    def showInfo( self, title, msg ):
        box = InfoBox( title, msg, "", "OK" )
        box.exec_()

################################################################################
################################################################################


def testMainTabWidget():
    app = QApplication()
    tab = MainTabWidget()
    tab.show()
    app.exec_()

def testMtlZahlungenTab():
    app = QApplication()
    tab = MtlZahlungenTabWidget()
    tab.show()
    app.exec_()


def test():
    import sys
    app = QApplication()
    win = IccMainWindow( "DEVELOP" )
    win.show()
    sys.exit( app.exec_() )

if __name__ == "__main__":
    test()