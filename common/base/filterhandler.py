import numbers
from functools import cmp_to_key
from typing import List, Dict, Any

from PySide2.QtCore import QObject, Qt, SIGNAL, QSize
from PySide2.QtWidgets import QGridLayout, QDialog, QApplication

from base.baseqtderivates import BaseDialog, BaseLabel, BaseComboBox, FatLabel, HLine, BaseCheckBox, BaseButton, \
    BaseEdit
from base.basetablemodel import BaseTableModel, FilterCondition
from base.basetableview import BaseTableView
from base.interfaces import XBase, TestItem

# class FilterCondition:
#     def __init__( self ):
#         self.header = ""  # Name der Spalte
#         self.value = ""   # Vergleichswert
#         self.op = "=" # Vergleichsopeartor {'startsWith', 'contains', '=', '>=', '<=', '>', '<'}
#         self.caseSensitive = False
#
#     def toString( self ):
#         return "Column: " + self.header + " - op: '" + self.op + "' - comp.value: " + self.value + \
#                " - exactMatch: " + str( self.exactMatch ) + " - caseSensitive: " + str( self.caseSensitive )
from numberhelper import NumberHelper


class DefinitionRow:
    """
    Enthält alle Widgets, die benötigt werden, um EINE FilterCondition zu definieren.
    """
    def __init__( self ):
        self.cboHeader:BaseComboBox = None
        self.cboOp:BaseComboBox = None
        self.edValue:BaseEdit = None
        self.btnCaseSensitive:BaseButton = None
        #self.btnExactMatch:BaseButton = None

##########################   MultiSortDialog   ####################
class FilterDialog( BaseDialog ):
    def __init__( self, columnHeaders:List[str] ):
        BaseDialog.__init__( self )
        self._columnHeaders = list()
        self._columnHeaders.append( "" )
        self._columnHeaders += columnHeaders
        self.setWindowTitle( "Filterkriterien festlegen" )
        self._layout = QGridLayout()
        self.setLayout( self._layout )
        self._dicList:List[Dict] = list # jeder Dict. hat die Keys "header", "op", "value"
        self._btnOk = BaseButton( "OK" )
        self._btnCancel = BaseButton( "Abbrechen" )
        #self._filterConditionList:List[FilterCondition] = list()
        self._definitionsList:List[DefinitionRow] = list()
        self._createGui()

    def _createGui( self ):
        l = self._layout
        r = 0
        lbl = FatLabel("Filtern nach folgenden Bedingungen: "  )
        lbl.setAlignment( Qt.AlignCenter )
        l.addWidget( lbl, r, 0, 1, 5, Qt.AlignCenter )
        r += 1
        l.addWidget( HLine(), r, 0, 1, 5 )
        r += 1
        lbl = BaseLabel( "Spalte" )
        l.addWidget( lbl, r, 0, 1, 1, alignment=Qt.AlignCenter )
        lbl = BaseLabel( "Vgl.Op" )
        l.addWidget( lbl, r, 1, 1, 1, alignment=Qt.AlignCenter )
        lbl = BaseLabel( "Vergleichswert" )
        l.addWidget( lbl, r, 2, 1, 1, alignment=Qt.AlignCenter )
        r += 1
        n = 0
        max = len( self._columnHeaders )
        max = 9 if max > 9 else max
        btnSize = QSize( 26, 26 )
        for n in range( 1, max ):
            allColumnsCombo = BaseComboBox()
            allColumnsCombo.addItems( self._columnHeaders )
            l.addWidget( allColumnsCombo, r, 0 )
            #self._combos.append( allColumnsCombo )
            op = BaseComboBox()
            op.addItems( ("startsWith", "contains", "=", "<>", "<=", ">=", ">", "<" ) )
            op.setFixedWidth( 100 )
            # op.currentIndexChanged.connect( self._onOpChanged )
            l.addWidget( op, r, 1, 1, 1, alignment=Qt.AlignCenter )
            val = BaseEdit()
            l.addWidget( val, r, 2 )
            casesensitve = BaseButton( "Aa" )
            casesensitve.setCheckable( True )
            casesensitve.setFixedSize( btnSize )
            casesensitve.setToolTip( "Case-sensitves Filtern" )
            l.addWidget( casesensitve, r, 3 )
            # exactMatch = BaseButton( "|a|" )
            # exactMatch.setCheckable( True )
            # exactMatch.setFixedSize( btnSize )
            # exactMatch.setToolTip( "Exact Match" )
            # exactMatch.setEnabled( False )
            # l.addWidget( exactMatch, r, 4 )
            gui = DefinitionRow()
            gui.cboHeader = allColumnsCombo
            gui.cboOp = op
            gui.edValue = val
            gui.btnCaseSensitive = casesensitve
            # gui.btnExactMatch = exactMatch
            self._definitionsList.append( gui )
            op.setUserData( gui )
            r += 1

        l.addWidget( BaseLabel(""), r, 0 )  #Vertical space dummy
        r += 1
        l.addWidget( BaseLabel( "" ), r, 0 )  # Vertical space dummy
        r +=1
        self._btnOk.setDefault( True )
        self._btnOk.clicked.connect( self.accept )
        l.addWidget( self._btnOk, r, 0, 1, 2 )
        self._btnCancel.clicked.connect( self.reject )
        l.addWidget( self._btnCancel, r, 2 )

    # def _onOpChanged( self, idx ):
    #     op:BaseComboBox = self.sender()
    #     enabled = False if op.currentText() == "=" else True
    #     defRow:DefinitionRow = op.getUserData()
    #     defRow.btnExactMatch.setEnabled( enabled )

    def getFilterConditions( self ) -> List[FilterCondition]:
        l = list()
        for defi in self._definitionsList:
            header = defi.cboHeader.currentText()
            if header:
                filter = FilterCondition()
                filter.header = header
                filter.op = defi.cboOp.currentText()
                filter.value = defi.edValue.text()
                filter.value_num = NumberHelper.getFloatOrIntOrNone( filter.value )
                filter.caseSensitive = True if defi.btnCaseSensitive.isChecked() else False
                # filter.exactMatch = True if defi.btnExactMatch.isChecked() else False
                l.append( filter )
        return l

#######################   MultiSortHandler   ################
class FilterHandler( QObject ):
    def __init__( self, tv:BaseTableView ):
        QObject.__init__( self )
        self._tv = tv
        #self._tm:BaseTableModel = None
        self._dlg = None

    def onFilter( self ):
        """
        callback Funktion, die den Filterdialog öffnet.
        Wenn im Filterdialog eine gültige Auswahl getroffen und auf OK geklickt wurde,
        wird dem Model bescheidgesagt, alle Zeilen auszublenden, die nicht den Filterkriterien entsprechen.
        :return:
        """
        tm:BaseTableModel = self._tv.model()
        if not self._dlg:
            self._dlg = FilterDialog( tm.getHeaders() )
        if self._dlg.exec_() == QDialog.Accepted:
            condlist:List[FilterCondition] = self._dlg.getFilterConditions()
            tm.applyFilter( condlist )

    def onResetFilter( self ):
        self._tv.model().resetFilter()
        if self._dlg:
            del self._dlg
            self._dlg = None


########################   TEST  TEST  TEST  TEST   ####################################
def testDialog():
    app = QApplication()
    dlg = FilterDialog( ["Name", "Vorname", "PLZ", "Ort", "Straße"] )
    if dlg.exec_() == QDialog.Accepted:
        print( "OK" )
        filters = dlg.getFilterConditions()
        for f in filters:
            print( "Filter: ", f.header, " ", f.op, " ", f.value,
                   " caseSensitive: ", f.caseSensitive )
    else: print( "Cancelled" )

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

def test():
    app = QApplication()
    tv = BaseTableView()
    tm = makeTestModel2()
    tv.setModel( tm )
    fh = FilterHandler( tv )
    tv.show()
    #fh.onFilter()
    app.exec_()

