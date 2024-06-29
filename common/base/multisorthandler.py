from functools import cmp_to_key
from typing import List, Iterable

from PySide2.QtCore import QObject, Qt, SIGNAL
from PySide2.QtWidgets import QGridLayout, QDialog, QApplication

from base.baseqtderivates import BaseDialog, BaseLabel, BaseComboBox, FatLabel, HLine, BaseCheckBox, BaseButton
from base.basetablemodel import BaseTableModel
from base.basetableview import BaseTableView
from base.interfaces import XBase, TestItem

##########################   MultiSortDialog   ####################
class MultiSortDialog( BaseDialog ):
    def __init__( self, columnHeaders:List[str] ):
        BaseDialog.__init__( self )
        self._columnHeaders = list()
        self._columnHeaders.append( "" )
        self._columnHeaders += columnHeaders
        self.setWindowTitle( "Sortieren nach mehreren Spalten" )
        self._layout = QGridLayout()
        self.setLayout( self._layout )
        self._combos:List[BaseComboBox] = list()
        self._cbSortOrder = BaseComboBox()
        self._btnOk = BaseButton( "OK" )
        self._btnCancel = BaseButton( "Abbrechen" )
        self._createGui()

    def _createGui( self ):
        l = self._layout
        r = 0
        lbl = FatLabel("Sortieren nach folgenden Spalten" )
        lbl.setAlignment( Qt.AlignCenter )
        l.addWidget( lbl, r, 0, 1, 2, Qt.AlignCenter )
        r += 1
        l.addWidget( HLine(), r, 0, 1, 2 )
        r += 1
        n = 0
        max = len( self._columnHeaders )
        max = 9 if max > 9 else max
        for n in range( 1, max ):
            lbl = BaseLabel()
            lbl.setText( str(n) + ".:  " )
            l.addWidget( lbl, r, 0 )
            allColumnsCombo = BaseComboBox()
            allColumnsCombo.addItems( self._columnHeaders )
            l.addWidget( allColumnsCombo, r, 1 )
            self._combos.append( allColumnsCombo )
            r += 1

        l.addWidget( BaseLabel(""), r, 0 )  #Vertical space dummy
        r += 1
        l.addWidget( BaseLabel( "Richtung: " ), r, 0 )
        self._cbSortOrder.addItems( ("Aufsteigend", "Absteigend") )
        self._cbSortOrder.setCurrentIndex( 0 )
        l.addWidget( self._cbSortOrder, r, 1 )
        r += 1
        l.addWidget( BaseLabel( "" ), r, 0 )  # Vertical space dummy
        r +=1
        self._btnOk.setDefault( True )
        self._btnOk.clicked.connect( self.accept )
        l.addWidget( self._btnOk, r, 0 )
        self._btnCancel.clicked.connect( self.reject )
        l.addWidget( self._btnCancel, r, 1 )

    def getSortColumns( self ) -> List[str]:
        sortCols = list()
        for cb in self._combos:
            if cb.currentText():
                sortCols.append( cb.currentText() )
        return sortCols

    def getSortOrder( self ) -> str:
        return self._cbSortOrder.currentText()

#######################   MultiSortHandler2   ################
# class Tmp:
#     def __init__( self, row:int, x:XBase ):
#         self.row = row
#         self.x = x
# ###############################################################
# class MultiSortHandler2( QObject ):
#     """
#     Behandelt die Sortierung mehrerer vorgegebener Spalten OHNE den Dialog, den der MultiSortHandler verwendet.
#     """
#     def __init__( self ):
#         QObject.__init__( self )
#         self._sort_reverse = False
#         self._keys:List[str] = None
#
#     def sort( self, tm:BaseTableModel, keys:Iterable[str] ) -> List[int]:
#         self._keys = keys
#         rowIndexList = tm.getVisibleRowIndexes()
#         xlist = tm.getElements( rowIndexList )
#         tmplist:List[Tmp] = list() # Hilfsliste, die sowohl den RowIndex wie auch das zugehörige XBase-Objekt enthält
#         for i in range(0, len(rowIndexList) ):
#             t = Tmp( rowIndexList[i], xlist[i])
#             tmplist.append( t )
#         tm.emit( SIGNAL( "layoutAboutToBeChanged()" ) )
#         self._sort_reverse = not self._sort_reverse
#         tmplistSorted = sorted( tmplist, key=cmp_to_key( self._compareMultiple ) )
#         rowIdxListSorted = [t.row for t in tmplistSorted]
#         return rowIdxListSorted
#
#     def _compareMultiple( self, t1:Tmp, t2:Tmp ):
#         for key in self._keys:
#             v1 = t1.x.__dict__[key]
#             v2 = t2.x.__dict__[key]
#             if isinstance( v1, str ):
#                 v1 = v1.lower()
#                 v2 = v2.lower()
#             if v1 < v2: return -1 if self._sort_reverse else 1
#             if v1 > v2: return 1 if self._sort_reverse else -1
#         return 0

#######################   MultiSortHandler   ################
class MultiSortHandler( QObject ):
    def __init__( self, tv:BaseTableView ):
        QObject.__init__( self )
        self._tv = tv
        #self._tv.horizontalHeader().setMouseTracking( True )
        self._tv.horizontalHeader().sectionClicked.connect( self.onSectionClicked )
        self._tm = tv.model()
        self._sortKeys:List[str] = list()
        self._sort_reverse = False
        self._dlg = None

    def onSectionClicked( self, logicalIndex ):
        if self._tv.isSortingEnabled():
            self._tv.horizontalHeader().setSortIndicatorShown( True )

    def onMultiSort( self ):
        self._tm = self._tv.model()
        self._sortKeys.clear()
        headers:List[str] = self._tm.getHeaders()
        if not self._dlg:
            self._dlg = MultiSortDialog( headers )
        if self._dlg.exec_() == QDialog.Accepted:
            self._sort_reverse = False if self._dlg.getSortOrder() == "Aufsteigend" else True
            sortColumns = self._dlg.getSortColumns()
            self._provideKeysFromColumns( sortColumns )
            self._doSort()
            self._sortKeys = list()
            self._tv.horizontalHeader().setSortIndicatorShown( False )

    def _provideKeysFromColumns( self, sortColumns:List[str] ) -> List[str]:
        for header in sortColumns:
            self._sortKeys.append( self._tm.getKeyByHeader( header ) )

    def _doSort( self ):
        rowlist:List[XBase] = self._tm.getRowList()
        self._tm.emit( SIGNAL( "layoutAboutToBeChanged()" ) )
        self._sort_reverse = not self._sort_reverse
        rowlist = sorted( rowlist, key=cmp_to_key( self._compareMultiple ) )
        self._tm.rowList = rowlist
        self.emit( SIGNAL( "layoutChanged()" ) )

    def _compareMultiple( self, x1:XBase, x2:XBase ):
        for key in self._sortKeys:
            v1 = x1.__dict__[key]
            v2 = x2.__dict__[key]
            if isinstance( v1, str ):
                v1 = v1.lower()
                v2 = v2.lower()
            if v1 < v2: return -1 if self._sort_reverse else 1
            if v1 > v2: return 1 if self._sort_reverse else -1
        return 0


########################   TEST  TEST  TEST  TEST   ####################################
def makeTestModel2() -> BaseTableModel:
    nachnamen = ("Kendel", "Knabe", "Verhoeven", "Adler", "Strack-Zimmermann", "Kendel")
    vornamen = ("Martin", "Gudrun", "Paul", "Henriette", "Marie-Agnes", "Friedi" )
    plzn = ("91077", "91077", "77654", "88954", "66538", "91077" )
    orte = ("Kleinsendelbach", "Kleinsendelbach", "Niederstetten", "Oberhimpflhausen", "Neunkirchen", "Steinbach")
    strn = ("Birnenweg 2", "Birnenweg 2", "Rebenweg 3", "Hubertusweg 22", "Wellesweilerstr. 56", "Ahornweg 2" )
    alter = ( 67, 65, 54, 49, 60, 41)
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
    tm.headers = ("Nachname", "Vorname", "PLZ", "Ort", "Straße", "Alter", "Größe" )
    return tm

def testMultiSortHandler2():
    app = QApplication()
    msh = MultiSortHandler2()
    tm = makeTestModel2()
    #msh.sort( tm)
    msh.onMultiSort()

def test():
    app = QApplication()
    msh = MultiSortHandler( makeTestModel2() )
    msh.onMultiSort()
    #app.exec_()

