#from PyQt5.QtWidgets import QWidget
from PySide2.QtCore import Qt, Signal, QModelIndex
from PySide2.QtWidgets import QDialog, QPushButton, QGridLayout, QApplication, QHBoxLayout, QLabel, QMessageBox, QWidget


class OkCancelDialog( QDialog ):
    def __init__( self, title=None, parent=None ):
        QDialog.__init__( self, parent )
        self.title = title
        self._layout = QGridLayout()
        self._okButton = QPushButton( "OK" )
        self._cancelButton = QPushButton( "Abbrechen" )
        self._createGui()
        self._beforeAcceptFnc = None
        self._cancellationFnc = None

    def _createGui( self ):
        self.setLayout( self._layout )

        hbox = QHBoxLayout()
        #hbox.addStretch( 1 )
        hbox.addWidget( self._okButton )
        hbox.addWidget( self._cancelButton )

        self._layout.addLayout( hbox, 3, 0, alignment=Qt.AlignLeft | Qt.AlignBottom )

        self._okButton.setDefault( True )

        if self.title:
            self.setWindowTitle( self.title )
        else:
            self.setWindowTitle( "OkCancelDialog" )

        self._okButton.clicked.connect( self.onAccepted )
        self._cancelButton.clicked.connect( self.onRejected )

    def onAccepted(self):
        rc = True
        if self._beforeAcceptFnc:
            rc = self._beforeAcceptFnc()
        if rc:
            self.accept()

    def onRejected( self ):
        rc = True
        if self._cancellationFnc:
            rc = self._cancellationFnc()
        if rc:
            self.reject()

    def setOkButtonText( self, text:str ):
        self._okButton.setText( text )

    def addWidget( self, w:QWidget, row:int ) -> None:
        if row > 2: raise Exception( "OkCancelDialog.addWidget() -- invalid row index: %d" % ( row ) )
        self._layout.addWidget( w, row, 0 )

    def setBeforeAcceptFunction( self, fnc ):
        self._beforeAcceptFnc = fnc

    def setCancellationFunction( self, fnc ):
        self._cancellationFnc = fnc

    @staticmethod
    def showErrorMessage( title:str, msg:str ):
        mb = QMessageBox( QMessageBox.Critical, title, msg )
        mb.exec_()

    @staticmethod
    def showWarningMessage( title:str, msg:str ):
        mb = QMessageBox( QMessageBox.Warning, title, msg )
        mb.exec_()

###################################################################################
class OkCancelDialog2( QDialog ):
    ok_pressed = Signal()
    cancel_pressed = Signal()
    def __init__( self, title=None, parent=None ):
        QDialog.__init__( self, parent )
        self.title = title
        self._layout = QGridLayout()
        self._widgetsDic = dict()
        self._okButton = QPushButton( "OK" )
        self._cancelButton = QPushButton( "Abbrechen" )
        self._createGui()
        self._validationFnc = None
        self._cancellationFnc = None

    def _createGui( self ):
        self.setLayout( self._layout )

        hbox = QHBoxLayout()
        #hbox.addStretch( 1 )
        hbox.addWidget( self._okButton )
        hbox.addWidget( self._cancelButton )
        margins = hbox.contentsMargins()
        margins.setLeft( 10 )
        hbox.setContentsMargins( margins )
        self._layout.addLayout( hbox, 3, 0, alignment=Qt.AlignLeft | Qt.AlignBottom )

        self._okButton.setDefault( True )

        if self.title:
            self.setWindowTitle( self.title )
        else:
            self.setWindowTitle( "OkCancelDialog" )

        self._okButton.clicked.connect( self.ok_pressed.emit )
        self._cancelButton.clicked.connect( self.cancel_pressed.emit )


    def setOkButtonText( self, text:str ):
        self._okButton.setText( text )

    def addWidget( self, widget:QWidget, row:int ) -> None:
        if row > 2: raise Exception( "OkCancelDialog.addWidget() -- invalid row index: %d" % ( row ) )
        self._layout.addWidget( widget, row, 0 )
        self._widgetsDic[row] = widget

    def getWidget( self, row:int ) -> QWidget:
        return self._widgetsDic[row]

########################   OkDialog   #######################
class OkDialog( QDialog ):
    def __init__( self, title=None, parent=None ):
        QDialog.__init__( self, parent )
        self.title = title
        self._layout = QGridLayout()
        self._okButton = QPushButton( "OK" )
        self._createGui()

    def _createGui( self ):
        self.setLayout( self._layout )
        self._layout.addWidget( self._okButton, 3, 0, alignment=Qt.AlignLeft | Qt.AlignBottom )
        self._okButton.clicked.connect( self.accept )
        self._okButton.setDefault( True )
        if self.title:
            self.setWindowTitle( self.title )
        else:
            self.setWindowTitle( "OkDialog" )

    def setOkButtonText( self, text:str ):
        self._okButton.setText( text )

    def addWidget( self, widget: QWidget, row: int ) -> None:
        if row > 2: raise Exception( "OkDialog.addWidget() -- invalid row index: %d" % (row) )
        self._layout.addWidget( widget, row, 0 )



def testOkCancelDialog():
    def beforeAccept():
        print( "beforeAccept" )

    def onCancel():
        print( "onCancel" )

    app = QApplication()
    dlg = OkCancelDialog()
    dlg.setWindowTitle( "testdialog" )
    dlg.setOkButtonText( "Speichern" )
    lbl = QLabel( "Man beachte diesen erstaunlichen Dialog" )
    dlg.addWidget( lbl, 0 )
    lbl = QLabel( "Did you?" )
    dlg.addWidget( lbl, 2 )
    dlg.setBeforeAcceptFunction( beforeAccept )
    dlg.setCancellationFunction( onCancel )
    dlg.show()
    app.exec_()

def testOkCancelDialog2():
    app = QApplication()
    dlg = OkCancelDialog2()
    dlg.setWindowTitle( "testdialog" )
    dlg.setOkButtonText( "Speichern" )
    lbl = QLabel( "Man beachte diesen erstaunlichen Dialog" )
    dlg.addWidget( lbl, 0 )
    lbl = QLabel( "Did you?" )
    dlg.addWidget( lbl, 2 )
    dlg.show()
    app.exec_()

def testOkDialog():
    app = QApplication()
    dlg = OkDialog()
    dlg.setWindowTitle( "testdialog" )
    dlg.setOkButtonText( "Schließen" )
    lbl = QLabel( "Man beachte diesen erstaunlichen Dialog" )
    dlg.addWidget( lbl, 0 )
    lbl = QLabel( "Did you?" )
    dlg.addWidget( lbl, 2 )
    dlg.exec_()


if __name__ == "__main__":
    testOkCancelDialog()
