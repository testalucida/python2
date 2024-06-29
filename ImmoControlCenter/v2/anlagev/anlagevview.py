from typing import List, Iterable

from PySide2.QtCore import QSize, Signal, QModelIndex, QPoint
from PySide2.QtWidgets import QWidget, QHBoxLayout, QTabWidget, QMenu

from base.baseqtderivates import BaseGridLayout, BaseLabel, YearComboBox, BaseToolBar, BaseButton, BaseAction
from base.basetableview import BaseTableView
from generictable_stuff.okcanceldialog import OkDialog
from v2.anlagev.anlagevtablemodel import AnlageVTableModel, XAnlageV


class AnlageVTableView( BaseTableView ):
    def __init__( self ):
        BaseTableView.__init__( self )

    def setModel( self, tm:AnlageVTableModel ):
        super().setModel( tm, selectRows=True, singleSelection=False )
        # for r in range( 0, tm.rowCount() ):
        #     self.setRowHeight( r, 25 )

################################################
class AnlageVView( QWidget ):
    year_changed = Signal(str, int)
    def __init__( self ):
        QWidget.__init__( self )
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._vj = 0
        self._yearCombo = YearComboBox()
        self._lblAdresse = BaseLabel()
        self._tv = AnlageVTableView()
        self._createGui()

    def _createGui( self ):
        self._layout.addWidget( self._yearCombo, 0, 0 )
        self._layout.addWidget( self._lblAdresse, 0, 1 )
        self._layout.addWidget( self._tv, 1, 0, 1, 2 )

    def addAndSetVeranlagungsjahre( self, vjList:Iterable[int], currentVj:int ):
        self._yearCombo.addYears( vjList )
        self._yearCombo.setYear( currentVj )

    def getAnlageVTableView( self ) -> AnlageVTableView:
        return self._tv

    def getAnlageVTableModel( self ) -> AnlageVTableModel:
        return self.getAnlageVTableView().model()

    def setModel( self, tm:AnlageVTableModel ):
        try:
            self._yearCombo.year_changed.disconnect( self.onYearChanged )
        except:
            pass
        self._tv.setModel( tm )
        self._lblAdresse.setValue( tm.getMasterName() )
        self._yearCombo.year_changed.connect( self.onYearChanged )

    def getModel( self ) -> AnlageVTableModel:
        return self._tv.model()

    def getMasterName( self ):
        tm = self._tv.model()
        if not tm:
            return "model not set"
        return tm.getMasterName()

    def setPreferredSize( self ):
        w = self.getPreferredWidth()
        h = self.getPreferredHeight()
        self.resize( QSize(w,h) )

    def getPreferredWidth( self ) -> int:
        return self._tv.getPreferredWidth() + 25

    def getPreferredHeight( self ) -> int:
        return self._tv.getPreferredHeight() + 25

    def onYearChanged( self, newYear:int ):
        self.year_changed.emit( self._tv.model().getMasterName(), newYear )

#################################################
class AnlageVTabs( QTabWidget ):
    def __init__( self, vj:int ):
        QTabWidget.__init__( self )
        self._vj = vj  # wird nur benötigt für die Überschrift "Summe der Überschüsse im Vj 2022".
                        # Dieses Jahr hat nichts zu tun mit den aktuell eingestellten Jahren der einzelnen Tabs
        self._summeUeberschuesse = 0
        self.setWindowTitle( "Anlagen V" )

    def addAnlageV( self, view:AnlageVView ):
        self.addTab( view, view.getMasterName() )
        self._summeUeberschuesse += view.getModel().getUeberschuss()

    def setPreferredSize( self ):
        self.resize( self.getPreferredSize() )

    def getPreferredSize( self ):
        w, h = 0, 0
        for i in range( 0, self.count() ):
            tab: AnlageVView = self.widget( i )
            pw = tab.getPreferredWidth()
            w = pw if pw > w else w
            ph = tab.getPreferredHeight()
            h = ph if ph > h else h
        return QSize( w, h+50 )

    def getAnlageVView( self, master_name:str ) -> AnlageVView:
        for i in range( 0, self.count() ):
            anlageV:AnlageVView = self.widget( i )
            if anlageV.getMasterName() == master_name:
                return anlageV
        raise Exception( "AnlageVTabs.getAnlageVView():\nKeine Anlage für '%s' gefunden." % master_name )

    def getVj( self ) -> int:
        return self._vj

    def getCurrentAnlageVView( self ) -> AnlageVView:
        return self.currentWidget()

    def getSummeUeberschuesse( self ):
        return self._summeUeberschuesse

#################################################
class AnlageVDialog( OkDialog ):
    def __init__( self, anlageVTabs:AnlageVTabs ):
        OkDialog.__init__( self, "Anlagen V" )
        self._avTabs = anlageVTabs
        self._toolBar = BaseToolBar()
        self._lblUeberschuss = BaseLabel()
        self._toolBar.addWidget( self._lblUeberschuss )
        self._createGui2()

    def setPreferredSize( self ):
        sz = self._avTabs.getPreferredSize()
        w = sz.width() + 25
        h = sz.height() + 70
        self.resize( QSize( w, h ) )

    def _createGui2( self ):
        info = "Summe der Überschüsse im Vj %d: >>>>  %d €  <<<<" % (self._avTabs.getVj(), self._avTabs.getSummeUeberschuesse() )
        self._lblUeberschuss.setValue( info )
        self.addWidget( self._toolBar, 0 )
        self.addWidget( self._avTabs, 1 )
