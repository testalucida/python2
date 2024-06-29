from PySide2.QtGui import QTextDocument, QTextCursor
from PySide2.QtPrintSupport import QPrintDialog, QPrintPreviewDialog
from PySide2.QtWidgets import QDialog, QApplication

from base.basetablemodel import BaseTableModel
#from base.basetableview import BaseTableView
from base.basetableview import BaseTableView


class PrintHandler:
    def __init__( self, tv:BaseTableView ):
        self._tv = tv

    def handlePrint(self):
        """
        connect your print button with this method.
        :return:
        """
        dialog = QPrintDialog()
        if dialog.exec_() == QDialog.Accepted:
            self._handlePaintRequest( dialog.printer() )

    def handlePreview(self):
        """
        connect your print preview button with this method
        :return:
        """
        dialog = QPrintPreviewDialog()
        dialog.paintRequested.connect( self._handlePaintRequest )
        dialog.exec_()

    def _handlePaintRequest( self, printer ):
        document = QTextDocument()
        cursor = QTextCursor(document)
        model:BaseTableModel = self._tv.model()
        table = cursor.insertTable(
            model.rowCount()+1, model.columnCount())
        for column in range( table.columns() ):
            cursor.insertText( model.getHeader( column ) )
            cursor.movePosition( QTextCursor.NextCell )
        rowcount = model.rowCount()
        colcount = model.columnCount()
        for row in range( rowcount ):
            for column in range( colcount ):
                cursor.insertText( model.getText( row, column ) )
                cursor.movePosition( QTextCursor.NextCell )
        document.print_(printer)
