from numbers import Number
from typing import List

from PySide2.QtCore import QModelIndex
from PySide2.QtGui import QGuiApplication, Qt
from PySide2.QtWidgets import QTableView

from base.baseqtderivates import SumDialog
from base.basetablemodel import BaseTableModel
#from base.basetableview import BaseTableView


class BaseTableFunctions:
    def __init__(self):
        pass

    @staticmethod
    def computeSumme( tv:QTableView, columnVon:int=None, columnBis:int=None, dlg_title="" ):
        """
        Addiert die in der TableView <tv> markierten Werte.
        Sind columnVon und column-Bis angegeben, werden nur Werte zwischen diesen beiden Columns (jeweils inklusive)
        berücksichtigt.
        :param tv: BaseTableView, in dem sich die selektierten Zellen befinden
        :param columnVon: Column-Index, ab dem addiert werden soll
        :param columnBis: Column-Index, bis zu dem addiert werden soll. Ist columnBis nicht angegeben, wird bis zur
        letzten Spalte addiert.
        :return:
        """
        if not columnVon and not columnBis:
            columnVon = 0
            columnBis = 999
        if columnVon and not columnBis:
            columnBis = 999
        if columnBis and columnVon is None: return
        if columnVon > columnBis: return
        model: BaseTableModel = tv.model()
        summe = 0
        idxlist = tv.selectedIndexes()
        for idx in idxlist:
            if columnVon <= idx.column() <= columnBis:
                val = model.getValue( idx.row(), idx.column() )
                if type( val ) in (int, float):
                    summe += val
        summe = "%.2f" % summe
        dlg = SumDialog( title=dlg_title )
        dlg.setSum( summe )
        dlg.exec_()

    @staticmethod
    def copyCellValueToClipboard( tv:QTableView, rowIdx:int, colIdx:int ):
        tm = tv.model()
        idx = tm.createIndex( rowIdx, colIdx )
        val = tm.data( idx, Qt.DisplayRole )
        clipboard = QGuiApplication.clipboard()
        clipboard.setText( val )

    @staticmethod
    def copySelectionToClipboard( tv:QTableView ):
        values: str = ""
        indexes = tv.selectedIndexes()
        row = -1
        for idx in indexes:
            if row == -1: row = idx.row()
            if row != idx.row():
                values += "\n"
                row = idx.row()
            elif len( values ) > 0:
                values += "\t"
            val = tv.model().data( idx, Qt.DisplayRole )
            val = "" if not val else val
            if isinstance( val, Number ):
                values += str( val )
            else:
                values += val
        clipboard = QGuiApplication.clipboard()
        clipboard.setText( values )

    @staticmethod
    def copyColumnCellsToClipboard( tv:QTableView, col:int, convertPointToComma=False ):
        """
        Kopiert die Werte der Spalte, die durch <col> referenziert wird, ins Clipboard.
        Berücksichtigt werden nur die Zellen, die markiert sind.
        :param tv:
        :param col: Index der Spalte
        :param convertPointToComma: Wenn True, werden Punkte, die in den Spaltenwerten gefunden werden,
        in Kommas umgewandelt. "True" sollte also nur für Spalten gesetzt werden, die ausschließlich numerische
        Werte enthalten.
        :return: None
        """
        rows = BaseTableFunctions.getSelectedRows( tv )
        values = ""
        tm = tv.model()
        for row in rows:
            idx = tm.index( row, col )
            val = tm.data( idx, Qt.DisplayRole )
            val = "" if not val else val
            if isinstance( val, Number ):
                val = str( val )
            if convertPointToComma:
                val = val.replace( ".", "," )
            values += ( val + "\n" )
        clipboard = QGuiApplication.clipboard()
        clipboard.setText( values )

    @staticmethod
    def getSelectedRows( tv:QTableView ) -> List[int]:
        sm = tv.selectionModel()
        indexes:List[QModelIndex] = sm.selectedRows()  ## Achtung missverständlicher Methodenname
        l = list( indexes )
        rows = [i.row() for i in l]
        return rows

    @staticmethod
    def getPreferredWidth( tv:QTableView ):
        colcount = tv.model().columnCount()
        w = 0
        for col in range( 0, colcount ):
            w += tv.columnWidth( col )
        if not tv.verticalHeader().isHidden():
            w += tv.verticalHeader().height()
        return w

    @staticmethod
    def getPreferredHeight( tv: QTableView ):
        rowcount = tv.model().rowCount()
        h = 0
        for row in range( 0, rowcount ):
            h += tv.rowHeight( row )
        if not tv.horizontalHeader().isHidden():
            h += tv.horizontalHeader().height()
        return h
