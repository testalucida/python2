from abc import abstractmethod
from typing import List, Any, Iterable

from PySide2.QtGui import QBrush, Qt

from v2.icc import constants
from v2.icc.icclogic import IccSumTableModel
from v2.icc.interfaces import XMtlZahlung, XMtlMiete, XMtlHausgeld, XMtlAbschlag

###############  MtlEinAusTableModel  #############
class MtlEinAusTableModel( IccSumTableModel ):
    """
    TableModel, das für die monatlichen Mieteinzahlungen und monatlichen Hausgeldauszahlungen verwendet wird.
    """
    def __init__( self, rowList:List[XMtlZahlung], jahr:int, editablemonthIdx:int, colsToSum:Iterable[str] ):
        """
        :param rowList: Liste mit XBase-Objekten. Jedes XBase-Objekt wird in der TableView durch eine Row repräsentiert.
        :param jahr:
        :param editablemonthIdx: Repräsentiert den Index des Monats, dessen Monatswert nach dem Klicken auf die OK-Spalte
                                 geändert wird. 0=Januar, 11=Dezember
        :param colsToSum: Zu summierende Spalten
        """
        IccSumTableModel.__init__( self, rowList, jahr, colsToSum )
        self._okBrush = QBrush( Qt.green )
        self._nokBrush = QBrush( Qt.red )
        self._editBrush = QBrush( Qt.yellow )
        self._inactiveBrush = QBrush( Qt.black )
        self._inactiveBrush.setStyle( Qt.BDiagPattern )
        self.idxOkColumn = 3
        self.idxNokColumn = 4
        self.idxSollColumn = 2
        self.idxJanuarColumn = 5
        self._editablemonthIdx = editablemonthIdx
        self._idxEditableColumn = self.idxJanuarColumn + editablemonthIdx
        self.setKeyHeaderMappings2(
            ("mobj_id", self.getDebiKrediKey(), "soll", "ok", "nok", "jan", "feb", "mrz", "apr", "mai", "jun", "jul", "aug",
             "sep", "okt", "nov", "dez", "summe"),
            ("Objekt", self.getDebiKrediHeader(), "Soll", "ok", "nok", "Jan", "Feb", "Mrz", "Apr", "Mai", "Jun", "Jul", "Aug",
             "Sep", "Okt", "Nov", "Dez", "Summe") )
        self.idxSumColumn = self.getColumnIndexByKey( "summe" )

    def getMtlZahlung( self, mobj_id:str, debi_kredi:str ) -> XMtlZahlung:
        debi_kredi_key = self.getDebiKrediKey()
        for xmz in self.rowList:
            if xmz.mobj_id == mobj_id and xmz.__dict__[debi_kredi_key] == debi_kredi:
                return xmz

    @abstractmethod
    def getDebiKrediKey( self ) -> str:
        pass

    @abstractmethod
    def getDebiKrediHeader( self ) -> str:
        pass

    def setOkColumnIdx( self, idx:int ):
        self.idxOkColumn = idx

    def setNokColumnIdx( self, idx:int ):
        self.idxNokColumn = idx

    def setSollColumnIdx( self, idx:int ):
        self.idxSollColumn = idx

    def setJanuarColumnIdx( self, idx:int ):
        self.idxJanuarColumn = idx
        self._idxEditableColumn = idx + self._editablemonthIdx

    def getMietobjekt( self, row:int ) -> str:
        objIdx = self.keys.index( "mobj_id" )
        return self.getValue( row, objIdx )

    # def getMieter( self, row:int ) -> str:
    #     objIdx = self.keys.index( "mv_id" )
    #     return self.getValue( row, objIdx )

    def getDebiKredi( self, row ) -> str:
        colIdx = self.keys.index( self.getDebiKrediKey() )
        return self.getValue( row, colIdx )

    def getSab_id( self, row ) -> int:
        return 0

    def setValue( self, row:int, col:int, value:float ) -> None:
        """
        Setzt einen Monatswert und korrigiert die Summe entsprechend.
        Annahme hierbei: vom User können in dieser Tabelle ausschließlich Monatswerte geändert werden.
        Überschreibt die Methode der Basisklasse, weil nach einer Änderung eines Monatswerts
        auch der Summenwert angepasst werden muss. Es finden hier also 2 Aufrufe von BaseTableModel.setValue() statt.
        :param row: Row-Index der zu ändernden Zelle
        :param col: Column-Index der zu ändernden Zelle
        :param value: Neuer Wert
        :return: None
        """
        oldval = self.getValue( row, col )
        delta = value - oldval
        super().setValue( row, col, value )
        oldSum = self.getValue( row, self.idxSumColumn )
        newSum = oldSum + delta
        super().setValue( row, self.idxSumColumn, newSum )

    def getSummeValue( self, row:int ) -> float:
        return self.getValue( row, self.idxSumColumn )

    def addValueToSumme( self, row:int, value:int or float ):
        summe = self.getSummeValue( row )
        summe += value
        self.setValue( row, self.idxSumColumn, summe )

    def subtractValueFromSumme( self, row:int, value:int or float ):
        val = value * (-1)
        self.addValueToSumme( self, row, val )

    def getSollValue( self, row: int ) -> float:
        return self.getValue( row, self.idxSollColumn )

    def internalGetValue( self, indexrow: int, indexcolumn: int ) -> Any:
        if indexcolumn in (self.idxOkColumn, self.idxNokColumn):
            return None
        else:
            return super().internalGetValue( indexrow, indexcolumn )

    def getSollColumnIdx( self ) -> int:
        return self.idxSollColumn

    def getOkColumnIdx( self ) -> int:
        return self.idxOkColumn

    def getNokColumnIdx( self ) -> int:
        return self.idxNokColumn

    def setEditableMonth( self, monthIdx:int ):
        oldEditIdx = self._idxEditableColumn
        self._idxEditableColumn = self.idxJanuarColumn + monthIdx
        idxA = self.createIndex( 0, oldEditIdx )
        idxE = self.createIndex( self.rowCount()-1, oldEditIdx )
        self.dataChanged.emit( idxA, idxE, [Qt.BackgroundColorRole] )
        idxA = self.createIndex( 0, self._idxEditableColumn )
        idxE = self.createIndex( self.rowCount()-1, self._idxEditableColumn )
        self.dataChanged.emit( idxA, idxE, [Qt.BackgroundColorRole] )

    def getSelectedMonthIdx( self ) -> int:
        """
        Liefert den Index des Monats, der zur Bearbeitung ausgewählt ist (0=Januar,...)
        :return:
        """
        return self._idxEditableColumn - self.idxJanuarColumn

    def getSelectedYear( self ) -> int:
        """
        Liefert das Jahr, das zur Bearbeitung ausgewählt ist
        :return:
        """
        return self.getJahr()

    def getEditableColumnIdx( self ) -> int:
        """
        liefert den Index der Spalte, die den bearbeitbaren Monat repräsentiert
        :return:
        """
        return self._idxEditableColumn

    def getEditableMonthIdx( self ) -> int:
        return self._idxEditableColumn - self.idxJanuarColumn

    def getBackgroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        if indexrow == self.rowCount() - 1: return None
        if indexcolumn == self.idxOkColumn:
            return self._okBrush
        elif indexcolumn == self.idxNokColumn:
            return self._nokBrush

        if self.idxJanuarColumn <= indexcolumn < self.idxSumColumn:
            # Ein Monatswert wird abgefragt.
            # Den Diagonal-Brush anzeigen, wenn das XMtlZahlung-Objekt im betreff. Monat nicht aktiv war
            mon = self.getKey( indexcolumn )
            idxmon = constants.iccMonthShortNames.index( mon )
            e:XMtlZahlung = self.getElement( indexrow )
            if not e.vonMonat or not e.bisMonat:
                return self._inactiveBrush
            idxaktivvon = constants.iccMonthShortNames.index( e.vonMonat )
            idxaktivbis = constants.iccMonthShortNames.index( e.bisMonat )
            if not (idxaktivvon <= idxmon <= idxaktivbis):
                return self._inactiveBrush
            #print( "abgefragter Monat: '%s', e.von: '%s', e.bis: '%s' " % (mon, e.vonMonat, e.bisMonat ) )
        if indexcolumn == self._idxEditableColumn:
            return self._editBrush
        return None

###############  MieteTableModel  #############
class MieteTableModel( MtlEinAusTableModel ):
    def __init__( self, rowList:List[XMtlMiete], jahr:int, editableMonthIdx:int ):
        MtlEinAusTableModel.__init__( self, rowList, jahr, editableMonthIdx, ( "soll", "summe" ) )

    def getForegroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        brush = super().getForegroundBrush( indexrow, indexcolumn )
        if not brush:
            col_mobj_id = self.getColumnIndexByKey( "mobj_id" )
            col_soll = self.getColumnIndexByKey( "soll" )
            if indexcolumn in ( col_mobj_id, col_soll ):
                if not self.getValue( indexrow, indexcolumn ) == "SUMME":
                    return self.darkGreyBrush
        return brush

    def getDebiKrediKey( self ) -> str:
        return "mv_id"

    def getDebiKrediHeader( self ) -> str:
        return "Mieter"

###############  HausgeldTableModel  #############
class HausgeldTableModel( MtlEinAusTableModel ):
    def __init__( self, rowList:List[XMtlHausgeld], jahr:int, editableMonthIdx:int ):
        MtlEinAusTableModel.__init__( self, rowList, jahr, editableMonthIdx, ( "soll", "summe" ) )
        self.setKeyHeaderMappings2(
        ("mobj_id", self.getDebiKrediKey(), "soll", "ok", "nok", "jan", "feb", "mrz", "apr", "mai", "jun", "jul",
         "aug", "sep", "okt", "nov", "dez", "summe"),
        ("Objekt", self.getDebiKrediHeader(), "Soll", "ok", "nok", "Jan", "Feb", "Mrz", "Apr", "Mai", "Jun", "Jul",
         "Aug", "Sep", "Okt", "Nov", "Dez", "Summe") )

    def getForegroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        brush = super().getForegroundBrush( indexrow, indexcolumn )
        if indexcolumn == self.getColumnIndexByKey( "mobj_id" ):
            if not self.getValue( indexrow, indexcolumn ) == "SUMME":
                return self.darkGreyBrush
        # if indexcolumn == self.getColumnIndexByKey( "soll" ):
        #     return self.darkRedBrush
        return brush

    def getDebiKrediKey( self ) -> str:
        return "weg_name"

    def getDebiKrediHeader( self ) -> str:
        return "WEG"

###############  AbschlagTableModel  #############
class AbschlagTableModel( MtlEinAusTableModel ):
    def __init__( self, rowList:List[XMtlAbschlag], jahr:int, editableMonthIdx:int ):
        MtlEinAusTableModel.__init__( self, rowList, jahr, editableMonthIdx, ( "soll", "summe" ) )
        self.setOkColumnIdx( 6 )
        self.setNokColumnIdx( 7 )
        self.setSollColumnIdx( 5 )
        self.setJanuarColumnIdx( 8 )
        self.setKeyHeaderMappings2(
            ("master_name", "mobj_id", self.getDebiKrediKey(), "leistung", "vnr", "soll", "ok", "nok",
             "jan", "feb", "mrz", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "dez", "summe"),
            ("Haus", "Wohnung", self.getDebiKrediHeader(), "Leistg.", "Vertrag", "Soll", "ok", "nok",
             "Jan", "Feb", "Mrz", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez", "Summe") )
        self.idxSumColumn = self.getColumnIndexByKey( "summe" )

    def getDebiKrediKey( self ) -> str:
        return "kreditor"

    def getDebiKrediHeader( self ) -> str:
        return "Kreditor"

    def getSab_id( self, row ) -> int:
        x = self.getElement( row )
        return x.sab_id
