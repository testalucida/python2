import copy
from enum import Enum

from PySide2.QtCore import QSize, Signal
from PySide2.QtGui import Qt, QIcon
from PySide2.QtWidgets import QWidget, QGridLayout, QLabel, QHBoxLayout, QApplication, QPushButton

from base.baseqtderivates import SmartDateEdit, BaseEdit, IntEdit, FloatEdit, MultiLineEdit, HLine, BaseLabel, \
    BaseGridLayout
from base.messagebox import WarningBox, MessageBox
from generictable_stuff.okcanceldialog import OkCancelDialog
from imagefactory import ImageFactory
from modifiyinfo import ModifyInfo


##################  MietverhaeltnisView  ################
from v2.icc.interfaces import XMietverhaeltnis

class MietverhaeltnisView( QWidget ):
    dataChanged = Signal()
    nextMv = Signal()
    prevMv = Signal()
    def __init__( self, mietverhaeltnis:XMietverhaeltnis, enableBrowsing=True, parent=None ):
        QWidget.__init__( self, parent )
        self._mietverhaeltnis:XMietverhaeltnis = mietverhaeltnis
        self._enableBrowsing = enableBrowsing # ob die Browse-Buttons angezeigt werden
        self._layout = QGridLayout()
        self._toolLayout = QHBoxLayout()
        self._btnVor = QPushButton()
        self._btnRueck = QPushButton()
        # self._vormieterName = "" # Nur relevant, wenn die View im Mode.MV_NEW betrieben wird
        self._sdEndeVormieterMietverh = SmartDateEdit()  #  ------------- "" ------------------
        self._sdBeginnMietverh = SmartDateEdit()
        self._sdEndeMietverh = SmartDateEdit()
        self._edMieterName_1 = BaseEdit()
        self._edMieterVorname_1 = BaseEdit()
        self._edMieterName_2 = BaseEdit()
        self._edMieterVorname_2 = BaseEdit()
        self._edMieterTelefon = BaseEdit()
        self._edMieterMobil = BaseEdit()
        self._edMieterMailto = BaseEdit()
        self._edAnzPers = IntEdit()
        self._edNettomiete = FloatEdit()
        self._edNkv = FloatEdit()
        self._edKaution = IntEdit()
        self._sdKautionBezahltAm = SmartDateEdit()
        self._edIban = BaseEdit()
        self._txtBemerkung1 = MultiLineEdit()
        self._txtBemerkung2 = MultiLineEdit()
        self._createGui()
        self._setMietverhaeltnisData( mietverhaeltnis )

    @classmethod
    def createForNewMietverh( cls, mobj_id:str, vormieterName:str, vormieterBis:str="" ):
        xmvNeu = XMietverhaeltnis()
        xmvNeu.mobj_id = mobj_id
        inst = cls( xmvNeu, enableBrowsing=False )
        inst._createVormieterInfo( vormieterName )
        if vormieterBis:
            inst._sdEndeVormieterMietverh.setValue( vormieterBis )
        return inst

    def _createGui( self ):
        hbox = self._toolLayout
        if self._enableBrowsing:
            self._createVorRueckButtons( hbox )
        self._layout.addLayout( hbox, 0, 0, 1, 3, alignment=Qt.AlignLeft )
        self._addHorizontalLine( 1 )
        self._createFelder( r=2 )
        self.setLayout( self._layout )

    def _createVorRueckButtons( self, hbox ):
        self._prepareButton( self._btnRueck, ImageFactory.inst().getPrevIcon(),
                             "Zum vorigen Mietverhältnis blättern", self.prevMv )
        hbox.addWidget( self._btnRueck )
        self._prepareButton( self._btnVor, ImageFactory.inst().getNextIcon(),
                             "Zum nächsten Mietverhältnis blättern", self.nextMv )
        hbox.addWidget( self._btnVor )

    @staticmethod
    def _prepareButton( btn:QPushButton, icon:QIcon, tooltip:str, signal:Signal ):
        btn.setFlat( True )
        btn.setEnabled( True )
        btn.setToolTip( tooltip )
        btn.setIcon( icon )
        size = QSize( 32, 32 )
        btn.setFixedSize( size )
        iconsize = QSize( 30, 30 )
        btn.setIconSize( iconsize )
        btn.clicked.connect( signal.emit )

    def _createVormieterInfo( self, vormieterName:str ):
        hbox = self._toolLayout
        if not hbox.isEmpty():
            spacer = BaseLabel()
            spacer.setFixedWidth( 100 )
            hbox.addWidget( spacer )
        txt = "Ende des Mietverhältnisses mit " + vormieterName + ": "
        hbox.addWidget( BaseLabel( txt ), stretch=1, alignment=Qt.AlignRight )
        hbox.addWidget( self._sdEndeVormieterMietverh )

    def _addHorizontalLine( self, r:int ):
        hline = HLine()
        self._layout.addWidget( hline, r, 0, 1, 2 )
        return r+1

    def _createFelder( self, r ):
        c = 0
        l = self._layout

        lbl = QLabel( "Beginn: " )
        l.addWidget( lbl, r, c )
        c+=1
        self._sdBeginnMietverh.setMaximumWidth( 100 )
        l.addWidget( self._sdBeginnMietverh, r, c )

        c=0
        r += 1
        l.addWidget( BaseLabel( "Ende: " ), r, c )
        c+=1
        self._sdEndeMietverh.setMaximumWidth( 100 )
        l.addWidget( self._sdEndeMietverh, r, c )

        c = 0
        r += 1
        lbl = BaseLabel( "Name / Vorname 1. Mieter: " )
        l.addWidget( lbl, r, c )
        c+=1
        hbox = QHBoxLayout()
        hbox.addWidget( self._edMieterName_1 )
        hbox.addWidget( self._edMieterVorname_1 )
        l.addLayout( hbox, r, c )

        c = 0
        r += 1
        lbl = BaseLabel( "Name / Vorname 2. Mieter: " )
        l.addWidget( lbl, r, c )
        c += 1
        hbox = QHBoxLayout()
        hbox.addWidget( self._edMieterName_2 )
        hbox.addWidget( self._edMieterVorname_2 )
        l.addLayout( hbox, r, c )

        c=0
        r+=1
        l.addWidget( BaseLabel( "Telefon: " ), r, c )
        c+=1
        l.addWidget( self._edMieterTelefon, r, c )

        c = 0
        r += 1
        l.addWidget( BaseLabel( "Mobil: " ), r, c )
        c += 1
        l.addWidget( self._edMieterMobil, r, c )

        c=0
        r+=1
        l.addWidget( BaseLabel( "Mailadresse: " ), r, c )
        c+=1
        l.addWidget( self._edMieterMailto, r, c )

        c=0
        r+=1
        l.addWidget( BaseLabel( "Anzahl Personen i.d. Whg: " ), r, c )
        c += 1
        self._edAnzPers.setMaximumWidth( 20 )
        l.addWidget( self._edAnzPers, r, c )

        c=0
        r+=1
        l.addWidget( BaseLabel( "Nettomiete / NKV: " ), r, c )

        c+=1
        self._edNettomiete.setMaximumWidth( 100 )
        #self._edNettomiete.setEnabled( False )
        self._edNkv.setMaximumWidth( 100 )
        #self._edNkv.setEnabled( False )
        hbox = QHBoxLayout()
        hbox.addWidget( self._edNettomiete )
        hbox.addWidget( self._edNkv )
        hbox.addWidget( BaseLabel( "  Änderungen der Miete und NKV über Dialog 'Sollmiete'") )
        l.addLayout( hbox, r, c, alignment=Qt.AlignLeft )

        c=0
        r+=1
        l.addWidget( BaseLabel( "Kaution: " ), r, c )
        c+=1
        self._edKaution.setMaximumWidth( 100 )
        l.addWidget( self._edKaution, r, c )

        c=0
        r+=1
        l.addWidget( BaseLabel( "Kaution bezahlt am: " ), r, c )
        c+=1
        self._sdKautionBezahltAm.setMaximumWidth( 100 )
        l.addWidget( self._sdKautionBezahltAm, r, c )

        c, r = 0, r+1
        l.addWidget( BaseLabel( "IBAN: " ), r, c )
        c+=1
        l.addWidget( self._edIban, r, c )

        c=0
        r+=1
        l.addWidget( BaseLabel( "" ), r, c )

        r+=1
        l.addWidget( BaseLabel( "Bemerkungen: " ), r, c )
        c+=1
        hbox = QHBoxLayout()
        hbox.addWidget( self._txtBemerkung1 )
        hbox.addWidget( self._txtBemerkung2 )
        l.addLayout( hbox, r, c )

    def getVormieterMvBis( self ) -> str:
        return self._sdEndeVormieterMietverh.getValue()

    def setNettoUndNkvEnabled( self, enabled:bool=True ):
        self._edNettomiete.setEnabled( enabled )
        self._edNkv.setEnabled( enabled )

    def _guiToData( self, x:XMietverhaeltnis ):
        """
        Überträgt die Änderungen, die der User im GUI gemacht hat, in das
        übergebene XMietverhaeltnis-Objekt
        :param x: XMietverhaeltnis-Objekt, in das die geänderten Daten übertragen werden
        :return:
        """
        x.von = self._sdBeginnMietverh.getDate()
        x.bis = self._sdEndeMietverh.getDate()
        x.name = self._edMieterName_1.text()
        x.vorname = self._edMieterVorname_1.text()
        x.name2 = self._edMieterName_2.text()
        x.vorname2 = self._edMieterVorname_2.text()
        x.telefon = self._edMieterTelefon.text()
        x.mobil = self._edMieterMobil.text()
        x.mailto = self._edMieterMailto.text()
        x.anzahl_pers = self._edAnzPers.getIntValue()
        x.nettomiete = self._edNettomiete.getFloatValue()
        x.nkv = self._edNkv.getFloatValue()
        x.kaution = self._edKaution.getIntValue()
        x.kaution_bezahlt_am = self._sdKautionBezahltAm.getDate()
        x.IBAN = self._edIban.text()
        x.bemerkung1 = self._txtBemerkung1.toPlainText()
        x.bemerkung2 = self._txtBemerkung2.toPlainText()

    def getMietverhaeltnisCopyWithChanges( self ) -> XMietverhaeltnis:
        """
        gibt eine Kopie der Mietverhaeltnis-Schnittstellendaten mit Änderungen zurück.
        Diese Kopie kann für Validierungszwecke verwendet werden.
        :return: Kopie von XMietverhaeltnis
        """
        mvcopy = copy.copy( self._mietverhaeltnis )
        self._guiToData( mvcopy )
        return mvcopy

    def getMietverhaeltnis( self ) -> XMietverhaeltnis:
        """
        Liefert das Mietverhältnis in dem Zustand, wie es ist:
            Wenn schon einmal applyChanges aufgerufen wurde, sind die Änderungen, die der User in der GUI gemacht hat,
            eingearbeitet.
            Wenn nicht, ist das Mietverhältnis so, wie zum Zeitpunkt der Instanzierung der GUI.
        :return: XMietverhaeltnis
        """
        return self._mietverhaeltnis

    def applyChanges( self ):
        """
        überträgt die Änderungen, die der User im GUI gemacht hat, in das
        originale XMietverhaeltnis-Objekt.
        """
        if self.isChanged():
            self._guiToData( self._mietverhaeltnis )

    def isChanged( self ):
        xmvcopy = self.getMietverhaeltnisCopyWithChanges()
        if xmvcopy.equals( self._mietverhaeltnis ):
            return False
        else:
            return True

    def _setMietverhaeltnisData( self, mv:XMietverhaeltnis ):
        """
        Daten, die im GUI angezeigt und geändert werden können.
        :param mv:
        :return:
        """
        self._mietverhaeltnis = mv
        if mv.von:
            self._sdBeginnMietverh.setDateFromIsoString( mv.von )
        if mv.bis:
            self._sdEndeMietverh.setDateFromIsoString( mv.bis )
        self._edMieterName_1.setText( mv.name )
        self._edMieterVorname_1.setText( mv.vorname )
        self._edMieterName_2.setText( mv.name2 )
        self._edMieterVorname_2.setText( mv.vorname2 )
        self._edMieterTelefon.setText( mv.telefon )
        self._edMieterMobil.setText( mv.mobil )
        self._edMieterMailto.setText( mv.mailto )
        self._edAnzPers.setIntValue( mv.anzahl_pers )
        self._edNettomiete.setFloatValue( mv.nettomiete )
        self._edNkv.setFloatValue( mv.nkv )
        if mv.kaution:
            self._edKaution.setIntValue( mv.kaution )
        if mv.kaution_bezahlt_am:
            self._sdKautionBezahltAm.setDateFromIsoString( mv.kaution_bezahlt_am )
        if mv.IBAN:
            self._edIban.setText( mv.IBAN )
        self._txtBemerkung1.setText( mv.bemerkung1 )
        self._txtBemerkung2.setText( mv.bemerkung2 )
        #self.resetChangeFlag()

    def clear( self ):
        self._sdBeginnMietverh.clear()
        self._sdEndeMietverh.clear()
        self._sdEndeVormieterMietverh.clear()
        self._edMieterName_1.clear()
        self._edMieterVorname_1.clear()
        self._edMieterName_2.clear()
        self._edMieterVorname_2.clear()
        self._edMieterTelefon.clear()
        self._edMieterMobil.clear()
        self._edMieterMailto.clear()
        self._edAnzPers.clear()
        self._edNettomiete.clear()
        self._edNkv.clear()
        self._edKaution.clear()
        self._sdKautionBezahltAm.clear()
        self._edIban.clear()
        self._txtBemerkung1.clear()
        self._txtBemerkung2.clear()

###############  MietverhaeltnisDialog  ##########################
class MietverhaeltnisDialog( OkCancelDialog ):
    def __init__(self, view:MietverhaeltnisView, title:str=None, parent=None ):
        OkCancelDialog.__init__( self, parent )
        if not title:
            xmv = view.getMietverhaeltnis()
            if xmv.mv_id:
                title = "Mietverhältnis '" + xmv.mv_id + "' in Wohnung '" + xmv.mobj_id  + "'"
            else:
                title = "Neues Mietverhältnis in Wohnung '" + xmv.mobj_id + "'"
        self.setWindowTitle( title )
        self._view = view
        self.addWidget( self._view, 0 )
        self.setOkButtonText( "Speichern" )
        self.setCancellationFunction( self.onCancellation )

    def getView( self ) -> MietverhaeltnisView:
        return self._view

    def onCancellation( self ) -> int:
        if self._view.isChanged():
            box = WarningBox( "Änderungen im Dialog", "Es gibt Änderungen am Mietverhältnis.", "Wirklich abbrechen?",
                              "Ja, abbrechen", "Nein")
            if box.exec_() == MessageBox.Yes:
                return 1 # Ja, abbrechen
            return 0 # nein, nicht abbrechen
        else:
            # RC 1: ja, abbrechen
            return 1

    @classmethod
    def fromMietverhaeltnis( cls, xmv:XMietverhaeltnis ):
        view = MietverhaeltnisView( xmv )
        return cls( view )


##################   MietverhaeltnisKuendigenView   #################
class MietverhaeltnisKuendigenView( QWidget ):
    def __init__( self, xmv:XMietverhaeltnis, parent=None ):
        QWidget.__init__( self, parent )
        self._xmv = xmv
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._createGui()

    def _createGui( self ):
        pass

##################   MietverhaeltnisKuendigenDialog   ##################
class MietverhaeltnisKuendigenDialog( OkCancelDialog ):
    def __init__( self, view:MietverhaeltnisKuendigenView ):
        OkCancelDialog.__init__( self )
        pass

##############  TEST TEST TEST   #######################
def onPrevMv():
    print( "prev mv" )

def onNextMv():
    print( "next mv" )

def test():
    app = QApplication()
    xmv = XMietverhaeltnis()
    xmv.name = "Hinterhuber"
    xmv.vorname = "Konstantin-Wilhelm"
    xmv.bis = "2023-12-31"
    v = MietverhaeltnisView( xmv, enableBrowsing=True )
    v.prevMv.connect( onPrevMv )
    v.nextMv.connect( onNextMv )
    dlg = MietverhaeltnisDialog( v )
    dlg.exec_()
    #v.show()
    #app.exec_()

def testNewMietverh():
    app = QApplication()
    v = MietverhaeltnisView.createForNewMietverh( mobj_id="bueb", vormieterName="Atatürk, Atze", vormieterBis="2024-02-29" )
    v.prevMv.connect( onPrevMv )
    v.nextMv.connect( onNextMv )
    dlg = MietverhaeltnisDialog( v )
    dlg.exec_()