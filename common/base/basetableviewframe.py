from typing import List, Callable

from PySide2 import QtCore
from PySide2.QtCore import Signal, Qt
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QWidget, QGridLayout, QToolBar, QComboBox, QApplication, QAction, QLabel, QHBoxLayout, \
    QDialog, QDesktopWidget

from base.dynamicattributeui import DynamicAttributeDialog
from base.filterhandler import FilterHandler
from base.interfaces import TestItem, XBaseUI, VisibleAttribute
from base.baseqtderivates import BaseEdit, BaseWidget, SearchWidget, NewIconButton, EditIconButton, DeleteIconButton, \
    IntEdit, FloatEdit
from base.basetablemodel import BaseTableModel
from base.basetableview import BaseTableView

from base.constants import monthLongNames
from base.directories import BASE_IMAGES_DIR
from base.printhandler import PrintHandler
from base.searchhandler import SearchHandler
from base.multisorthandler import MultiSortHandler
from iconfactory import IconFactoryS

####################  SortKeyValue  #########################
class SortKeyValue:
    def __init__(self):
        self.key = ""
        self.value = ""

####################  BaseTableViewToolBar  ###################
class BaseTableViewToolBar( QToolBar ):
    def __init__( self ):
        QToolBar.__init__( self )
        self._yearCombo:QComboBox = None
        self._monthCombo:QComboBox = None
        self._saveEnabledIcon = None
        self._saveDisabledIcon = None
        self._saveActionId = "save"
        self._printIcon = None
        self._printActionId = "print"
        self._searchActionId = "search"
        self._sortActionId = "sort"
        self._filterActionId = "filter"
        self._resetFilterActionId = "reset_filter"
        self._exportActionId = "export"
        self._actions:List[QAction] = list()
        self._searchWidget = None

    def addYearCombo( self, years:List[int], callback:Callable ) -> None:
        """
        Fügt der ToolBar eine Combobox mit den übergebenen Jahreswerten hinzu.
        :param years: Jahre, die in der Combobox angezeigt werden sollen
        :param callback: Funktion, die gerufen wird, wenn der User das in der Combobox eingestellte Jahr ändert.
                         Die Funktion muss das neu eingestellte Jahr entgegen nehmen.
        """
        combo = QComboBox()
        for y in years:
            combo.addItem( str( y ) )
        combo.currentIndexChanged.connect( lambda: callback(int( self._yearCombo.currentText() ) ) )
        self.addWidget( combo )
        self._yearCombo = combo

    def setYear( self, year:int ) -> None:
        self._yearCombo.setCurrentText( str(year) )

    def addMonthCombo( self, callback:Callable ) -> None:
        """
        Fügt der ToolBar eine Combobox mit 12 Monatswerten hinzu.
        :param callback: Funktion, die gerufen wird, wenn der User den in der Combobox eingestellten Monat ändert.
                         Die Funktion muss den Index des Monats entgegen nehmen (bei 0 beginnend) sowie den Langnamen
                         ("September").
        :return:
        """
        combo = QComboBox()
        combo.addItems( monthLongNames )
        combo.currentIndexChanged.connect( lambda: callback( self._monthCombo.currentIndex(),
                                                             self._monthCombo.currentText() ) )
        self.addWidget( combo )
        self._monthCombo = combo

    def setMonthIdx( self, monthIdx:int ):
        """
        :param monthIdx: 0 = Januar etc.
        :return:
        """
        self._monthCombo.setCurrentIndex( monthIdx )

    def addSaveAction( self, tooltip:str, callback:Callable, enabled:bool=False, separatorBefore:bool=True ):
        if separatorBefore:
            self.addSeparator()
        self._saveEnabledIcon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "save.png" )
        self._saveDisabledIcon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "save_disabled.png" )
        icon = self._saveEnabledIcon if enabled else self._saveDisabledIcon
        action = self.addAction( icon, tooltip, callback )
        action.setData( self._saveActionId )
        action.setEnabled( enabled )
        self._actions.append( action )

    def addPrintAction( self, tooltip:str, callback:Callable, enabled:bool=True, separatorBefore:bool=True ):
        if separatorBefore:
            self.addSeparator()
        self._printIcon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "print.png" )
        action = self.addAction( self._printIcon, tooltip, callback )
        action.setData( self._printActionId )
        action.setEnabled( enabled )
        self._actions.append( action )

    def findAction( self, id:str ) -> QAction:
        for a in self._actions:
            if a.data() == id:
                return a
        raise Exception( "Action with id ", id, " not found." )

    def getSearchWidget( self ) -> SearchWidget:
        return self._searchWidget

    def setSaveActionEnabled( self, enable:bool=True ) -> None:
        action = self.findAction( self._saveActionId )
        if not action:
            raise Exception( "Save Action not found. Did you call BaseTableViewToolBar.addSaveAction before?" )
        if enable and not action.isEnabled():
            action.setIcon( self._saveEnabledIcon )
        elif not enable and action.isEnabled():
            action.setIcon( self._saveDisabledIcon )
        action.setEnabled( enable )

    def addSortAction( self, tooltip:str, callback:Callable, enabled:bool = True, separatorBefore:bool=True ) -> None:
        if separatorBefore:
            self.addSeparator()
        icon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "sort.png" )
        action = self.addAction( icon, tooltip, callback )
        action.setData( self._sortActionId )
        action.setEnabled( enabled )
        self._actions.append( action )

    def addFilterAction( self, tooltip:str, filter:Callable, resetFilter:Callable,
                         enabled:bool=True, separatorBefore:bool=True ) -> None:
        """

        :param tooltip:
        :param filter: callback, wenn auf den Filter-Button gedrückt wird. Funktion ohne Parameter
        :param resetFilter: callback, wenn auf den Reset-Filter-Button gedrückt wird. Funktion ohne Parameter
        :param enabled:
        :param separatorBefore:
        :return:
        """
        if separatorBefore:
            self.addSeparator()
        icon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "filter.png" )
        action = self.addAction( icon, tooltip, filter )
        action.setData( self._filterActionId )
        action.setEnabled( enabled )
        self._actions.append( action )
        # reset filter
        icon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "reset_filter.png" )
        action = self.addAction( icon, "Alle Filter aufheben", resetFilter )
        action.setData( self._resetFilterActionId )
        action.setEnabled( enabled )
        self._actions.append( action )

    def addSearchWidget( self, separatorBefore:bool=True ) -> SearchWidget:
        if separatorBefore:
                self.addSeparator()
        self._searchWidget = SearchWidget()
        self.addWidget( self._searchWidget )
        return self._searchWidget

    def addExportAction( self, tooltip:str, callback:Callable, separatorBefore:bool=True ) -> None:
        if separatorBefore:
            self.addSeparator()
        icon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "calc.png" )
        action = self.addAction( icon, tooltip, callback )
        action.setData( self._exportActionId )
        action.setEnabled( True )
        self._actions.append( action )

    def setFocusToSearchfield( self ):
        self._searchWidget.setFocusToSearchField()

####################  BaseTableViewFrame  #####################
class BaseTableViewFrame( BaseWidget ):
    """
    Ein Widget, das eine BaseTableView enthält und eine erweiterbare Toolbar (BaseTableViewFrame.getToolBar()).
    Auf Wunsch (withEditButtons = True) wird unterhalb der Tabelle eine Buttonleiste angezeigt,
    die einen "Neu"-, "Ändern"- und "Delete"-Button enthält.
    Wird auf einen dieser Buttons gedrückt, wird ein entsprechendes Signal gesendet.
    """
    newItem = Signal()
    editItem = Signal( int ) # row number (index.row of index)
    deleteItems = Signal( list ) # list of ints, each representing a row number (index.row of index)
    def __init__(self, tableView:BaseTableView, withEditButtons=False ):
        BaseWidget.__init__( self )
        self._tv = tableView
        self._layout = QGridLayout()
        self._toolbar = BaseTableViewToolBar()
        self._editBtn = None
        self._newBtn = None
        self._deleteBtn = None
        self._createGui( withEditButtons )

    def _createGui( self, withEditButtons ):
        l = self._layout
        self.setLayout( l )
        l.addWidget( self._toolbar, 0, 0, alignment=QtCore.Qt.AlignTop )
        # l.setContentsMargins( 0, 0, 0, 0 )
        l.setContentsMargins( 2, 0, 2, 2 )
        l.addWidget( self._tv, 1, 0 )
        if withEditButtons:
            hbox = QHBoxLayout()
            self._newBtn = NewIconButton()
            self._newBtn.clicked.connect( self.newItem.emit )
            self._editBtn = EditIconButton()
            self._editBtn.clicked.connect( self._onEditItem )
            self._deleteBtn = DeleteIconButton()
            # self._deleteBtn.clicked.connect( lambda: self.deleteItems.emit( self._tv.getSelectedRows() ) )
            self._deleteBtn.clicked.connect( self._onDeleteItems )
            hbox.addWidget( self._newBtn, stretch=0, alignment=Qt.AlignLeft )
            hbox.addWidget( self._editBtn, stretch=0, alignment=Qt.AlignLeft )
            hbox.addWidget( self._deleteBtn, stretch=0, alignment=Qt.AlignLeft )
            self._layout.addLayout( hbox, 2, 0, 1, 1, Qt.AlignLeft )

    def setNewButtonEnabled( self, enabled=True ):
        self._newBtn.setEnabled( enabled )

    def setDeleteButtonEnabled( self, enabled=True ):
        self._deleteBtn.setEnabled( enabled )

    def getPreferredWidth( self ) -> int:
        colcount = self._tv.model().columnCount()
        w = 0
        for col in range( 0, colcount ):
            w += self._tv.columnWidth( col )
        return w +25

    def getPreferredHeight( self ) -> int:
        rowcount = self._tv.model().rowCount()
        h = self._toolbar.height()
        for row in range( 0, rowcount ):
            h += self._tv.rowHeight( row )
        return h + 25

    def _onEditItem( self ):
        sel_rows = self._tv.getSelectedRows()
        if len( sel_rows ) > 0:
            self.editItem.emit( sel_rows[0] )

    def _onDeleteItems( self ):
        sel_rows = self._tv.getSelectedRows()
        if len( sel_rows ) > 0:
            self.deleteItems.emit( sel_rows )

    def getToolBar( self ) -> BaseTableViewToolBar:
        return self._toolbar

    def getTableView( self ) -> BaseTableView:
        return self._tv

def testScreenSize():
    app = QApplication()
    tv = BaseTableView()
    tvf = BaseTableViewFrame( tv )
    tvf.show()
    #rect = tvf.getScreenSize()
    #print( rect )
    app.exec_()

########################### TEST  TEST  TEST  ############################
### Test siehe auch basetableview.py Funktion testBaseTableViewFrame()

def makeTestModel() -> BaseTableModel:
    nachnamen = ("Kendel", "Knabe", "Verhoeven", "Adler", "Strack-Zimmermann", "Kendel")
    vornamen = ("Martin", "Gudrun", "Paul", "Henriette", "Marie-Agnes", "Friedi")
    plzn = ("91077", "91077", "77654", "88954", "66538", "91077")
    orte = ("Keinsendelbach", "kainsendelbach", "Niederstetten", "Oberhimpflhausen", "Neunkirchen", "Steinbach")
    strn = ("Birnenweg 2", "Birnenweg 2", "Rebenweg 3", "Hubertusweg 22", "Wellesweilerstr. 56", "Ahornweg 2")
    alter = (67, 65, 54, 49, 60, 41)
    groessen = (180, 170, 179, 185, 161.5, 161.5)
    itemlist = list()
    for n in range( 0, len(nachnamen) ):
        i = TestItem()
        i.nachname = nachnamen[n]
        i.vorname = vornamen[n]
        i.plz = plzn[n]
        i.ort = orte[n]
        i.str = strn[n]
        i.alter = alter[n]
        i.groesse = groessen[n]
        itemlist.append( i )
    tm = BaseTableModel( itemlist )
    tm.headers = ("Nachname", "Vorname", "PLZ", "Ort", "Straße", "Alter", "Größe")
    key = tm.getKeyByHeader( "Straße" )
    print( key )
    return tm

def onSave():
    print( "onSave" )

def onYearChanged( newYear ):
    print( "year changed: ", newYear )

def onMonthChanged( newMonthIdx, newMonth ):
    print( "month changed: ", newMonthIdx, ": ", newMonth )

def onSearch( search ):
    print( "search for: ", search )

def onSort():
    print( "sort" )
#
# def onFilter():
#     print( "filter" )
#
# def onResetFilter():
#     print( "reset filter" )




def onEditItem( ix ):
    print( ix )

def onDeleteItems( intlist ):
    print( intlist )

def onPrint():
    print( "print..." )

def testFrame():
    def onNewItem():
        #print( "onNewItem" )
        x = TestItem()
        xui = XBaseUI( x )
        vislist = (VisibleAttribute( "nachname", BaseEdit, "Nachname: " ),
                   VisibleAttribute( "vorname", BaseEdit, "Vorname" ),
                   VisibleAttribute( "plz", BaseEdit, "PLZ: ", nextRow=False ),
                   VisibleAttribute( "ort", BaseEdit, "Ort: ", widgetWidth=150 ),
                   VisibleAttribute( "str", BaseEdit, "Straße: ", widgetWidth=160 ),
                   VisibleAttribute( "alter", IntEdit, "Aler: " ),
                   VisibleAttribute( "groesse", FloatEdit, "Größe: " ))
        xui.addVisibleAttributes( vislist )
        dlg = DynamicAttributeDialog( xui, "Ändern einer Monatszahlung" )
        if dlg.exec_() == QDialog.Accepted:
            v = dlg.getDynamicAttributeView()
            xcopy = v.getModifiedXBaseCopy()
            xcopy.print()
            x = v.getXBase()
            x.print()
            v.updateData()
            x = v.getXBase()
            x.print()
            tm.addObject( x )

    app = QApplication()
    tm = makeTestModel()
    tv = BaseTableView()
    tv.setModel( tm )
    f = BaseTableViewFrame( tv, withEditButtons=True )
    f.newItem.connect( onNewItem )
    f.editItem.connect( onEditItem )
    f.deleteItems.connect( onDeleteItems )
    tb = f.getToolBar()
    # save
    tb.addSaveAction( "Änderungen speichern", onSave, separatorBefore=False )
    tb.addSeparator()
    tb.addYearCombo( (2022, 2021, 2020), onYearChanged )
    tb.addMonthCombo( onMonthChanged )
    # sort
    sortHandler = MultiSortHandler( tv )
    tb.addSortAction( "Öffnet den Dialog zur Definition mehrfacher Sortierkriterien", sortHandler.onMultiSort )
    # filter
    fh = FilterHandler( tv )
    tb.addFilterAction( "Öffnet den Filterdialog zur Eingabe der Filterkriterien", fh.onFilter, fh.onResetFilter )
    #search
    searchwidget = tb.addSearchWidget( True )
    sh = SearchHandler( tv, searchwidget )
    ph = PrintHandler( tv )
    tb.addPrintAction( "Öffne Druckvorschau für diese Tabelle...", ph.handlePreview )
    f.show()
    #tb.setSaveActionEnabled( True )
    tb.setFocusToSearchfield()
    app.exec_()

def testToolBar():
    def onYearChanged( newIndex ):
        print( "year changed: ", newIndex )

    def onMonthChanged( newIndex ):
        print( "month changed: ", newIndex )
        tb.setSaveActionEnabled( True )

    def onSave():
        print( "onSave" )
        tb.setSaveActionEnabled( False )

    def onSearch():
        pass

    def onExport():
        print( "onExport" )

    app = QApplication()
    w = QWidget()
    w.setWindowTitle( "TestContainter für BaseTableViewToolBar" )
    l = QGridLayout()
    w.setLayout( l )
    tb = BaseTableViewToolBar()
    l.addWidget( tb, 0, 0 )
    tb.addYearCombo( (2022, 2021, 2020), onYearChanged )
    tb.addMonthCombo( onMonthChanged )
    tb.addSaveAction( "Änderungen speichern", onSave, enabled=True )
    tb.addSearchWidget( onSearch )
    tb.addExportAction( "Exportiere diese Tabelle in Calc", onExport )
    w.show()
    app.exec_()