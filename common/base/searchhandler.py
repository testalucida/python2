import numbers
from typing import Any, List

from PySide2.QtCore import QModelIndex, QItemSelectionModel, Signal, QObject
from PySide2.QtWidgets import QGridLayout, QDialog

from base.baseqtderivates import BaseEdit, SearchWidget, BaseDialog, BaseCheckBox, BaseLabel, BaseButton
from base.basetablemodel import BaseTableModel
from base.basetableview import BaseTableView

class SearchSettings:
    def __init__( self ):
        self.caseSensitive = False
        self.exactMatch = False

class SearchSettingsDialog( BaseDialog ):
    def __init__( self ):
        BaseDialog.__init__( self )
        self._cbCaseSensitive = BaseCheckBox()
        self._cbExactMatch = BaseCheckBox()
        self._layout = QGridLayout()
        self.setLayout( self._layout )
        self.setWindowTitle( "Sucheinstellungen festlegen" )
        self._btnOk = BaseButton( "OK" )
        self._btnCancel = BaseButton( "Abbrechen" )
        self._createGui()

    def _createGui( self ):
        l = self._layout
        r = 0
        l.addWidget( BaseLabel( "Case sensitiv suchen: " ), r, 0 )
        l.addWidget( self._cbCaseSensitive, r, 1 )
        r += 1

        l.addWidget( BaseLabel( "Nur ganze Wörter suchen: " ), r, 0 )
        l.addWidget( self._cbExactMatch, r, 1 )
        r += 1

        self._btnOk.setDefault( True )
        self._btnOk.clicked.connect( self.accept )
        l.addWidget( self._btnOk, r, 0 )
        self._btnCancel.clicked.connect( self.reject )
        l.addWidget( self._btnCancel, r, 1 )

    def getSettings( self ) -> SearchSettings:
        sese = SearchSettings()
        sese.caseSensitive = self._cbCaseSensitive.isChecked()
        sese.exactMatch = self._cbExactMatch.isChecked()
        return sese


class SearchHandler( QObject ):
    def __init__( self, tv: BaseTableView, searchWidget:SearchWidget ):
        QObject.__init__( self )
        self._searchValueOrig = None # so wurde der Suchbegriff vom Anwender ins Suchfeld eingetragen
        self._searchValue = None # enthält den aufbereiteten Suchbegriff (siehe _prepareSearchValue)
        self._searchValueNum = None # der Suchbegriff in numerischer Form
                                    # (not None nur, wenn z.B. nach "123" gesucht werden soll)
        self._tv = tv
        self._searchWidget = searchWidget
        self._searchFieldBackground = None
        self._searchWidget.doSearch.connect( self.onDoSearch )
        self._searchWidget.searchtextChanged.connect( self.onSearchfieldChanged )
        self._searchWidget.openSettings.connect( self.onOpenSettings )
        # self._model:BaseTableModel = tv.model() NEIN! Der Pointer auf das Model muss in _searchNextMatch()
                                                # geholt werden, da sich das Model ändern kann (durch Filterung)
        self._caseSensitive = False
        self._exactMatch = False
        self._row = 0
        self._col = 0
        self._dlg = None

    def onSearchfieldChanged( self ):
        self._searchWidget.setSearchFieldBackgroundColor( "#ffffff" )
        self._tv.clearSelection()

    def _makeComparable( self, val ):
        valNum = None
        if isinstance(val, numbers.Number):
            valNum = val
            val = str( val )
        else:  # string (hopefully)
            try:
                valNum = int( val )
            except ValueError:
                try:
                    valNum = float( val )
                except ValueError:
                    pass
        if not self._caseSensitive:
            val = val.lower()
        return val, valNum

    def onDoSearch( self, searchValue ):
        self.search( searchValue, self._caseSensitive, self._exactMatch )

    def search( self, searchValue, caseSensitive:bool=False, exactMatch:bool=False ):
        if searchValue != self._searchValueOrig or \
                self._caseSensitive != caseSensitive or \
                self._exactMatch != exactMatch:
            # Anwender hat die Suchkriterien geändert, neue Suche beginnen
            self._row = self._col = 0
            self._searchValueOrig = searchValue
            self._caseSensitive = caseSensitive
            self._exactMatch = exactMatch
            self._searchValue, self._searchValueNum = self._makeComparable( searchValue )
        self._searchNextMatch()

    def _searchNextMatch( self ):
        if self._row == 0 and self._col == 0:
            self._searchWidget.setSearchFieldBackgroundColor( "#ffffff" )
        tm = self._tv.model()
        for r in range( self._row, tm.rowCount() ):
            for c in range( self._col, tm.columnCount() ):
                tmval = tm.getValue( r, c )
                if not tmval: continue
                tmval, tmvalNum = self._makeComparable( tmval )
                match = False
                if( self._exactMatch and self._searchValue == tmval) or \
                        (not self._exactMatch and self._searchValue in tmval ):
                    match = True
                if match or (tmvalNum is not None and
                             self._searchValueNum is not None and
                             tmvalNum == self._searchValueNum):
                    self._showMatch( tm.index( r, c ) )
                    self._row, self._col = r, c+1
                    if self._col >= tm.columnCount():
                        self._row += 1
                        self._col = 0
                        if self._row >= tm.rowCount():
                            self._row = 0
                    return
            self._col = 0
        self._row = self._col = 0
        self._searchWidget.setSearchFieldBackgroundColor( "#eb8795" )

    def _showMatch( self, index: QModelIndex ):
        self._tv.selectionModel().select( index, QItemSelectionModel.ClearAndSelect )
        self._tv.scrollTo( index )

    def onOpenSettings( self ):
        if not self._dlg:
            self._dlg = SearchSettingsDialog()
        if self._dlg.exec_() == QDialog.Accepted:
            sese = self._dlg.getSettings()
            self._caseSensitive = sese.caseSensitive
            self._exactMatch = sese.exactMatch