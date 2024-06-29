from typing import Callable

from PySide2 import QtWidgets
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QDoubleValidator
from PySide2.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QPushButton

from base.baseqtderivates import BaseEdit, FloatEdit, BaseComboBox, BaseDialogWithButtons, getCloseButtonDefinition, \
    SmartDateEdit, SignedNumEdit
from base.dynamicattributeui import DynamicAttributeDialog
from base.interfaces import XBaseUI, VisibleAttribute
from base.messagebox import ErrorBox
from v2.icc.iccwidgets import IccTableView, IccTableViewFrame

##################   EinAusTableView   ###############
from v2.icc.interfaces import XEinAus


class EinAusTableView( IccTableView ):
    def __init__( self ):
        IccTableView.__init__( self )
        self.setAlternatingRowColors( True )

##################   EinAusTableViewFrame   ##############
class EinAusTableViewFrame( IccTableViewFrame ):
    def __init__( self, tableView:IccTableView, withEditButtons=False ):
        IccTableViewFrame.__init__( self, tableView, withEditButtons )


##################  XEinAusUI  #########################
class XEinAusUI( XBaseUI ):
    def __init__( self, x:XEinAus ):
        XBaseUI.__init__( self, x )

##################  EinAusDialog  ######################
class EinAusDialog( DynamicAttributeDialog ):
    def __init__( self, xui:XEinAusUI, title:str="Neue Zahlung anlegen" ):
        DynamicAttributeDialog.__init__( self, xui, title )

################   TeilahlungDialog   ###########
class TeilzahlungDialog( BaseDialogWithButtons ):
    def __init__( self, tv:EinAusTableView, title="Ändern/Ergänzen von Zahlungen" ):
        BaseDialogWithButtons.__init__( self, title,
                                        getCloseButtonDefinition( self.onClose ) )
        self._tv:EinAusTableView = tv
        self._tvframe:EinAusTableViewFrame = EinAusTableViewFrame( self._tv, withEditButtons=True )
        self.setMainWidget( self._tvframe )

    def getTableViewFrame( self ) -> EinAusTableViewFrame:
        return self._tvframe

    def onClose( self ):
            self.accept()


################ ValueDialog ########################
class ValueDialog( QDialog ):
    def __init__( self, parent=None, mitBuchungsdatum=False ):
        """
        :param parent:
        :param mitBuchungsdatum: Der Dialog wird dreizeilig gezeigt: Value, Buchungsdatum, Bemerkung
        """
        QDialog.__init__( self, parent )
        self._callback: Callable = None
        self.setModal( True )
        self.setWindowTitle( "Neue Zahlung erfassen" )
        layout = QGridLayout( self )
        row = 0

        self._numEntry = SignedNumEdit() # QtWidgets.QLineEdit( self )
        self._numEntry.setPlaceholderText( "Betrag" )
        layout.addWidget( self._numEntry, row, 0 )
        self._numEntry.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        doubleValidator = QDoubleValidator( -9999, 9999, 2, self )
        self._numEntry.setValidator( doubleValidator )
        self._numEntry.setFocus()

        self._sdBuchungsdatum:SmartDateEdit = None
        if mitBuchungsdatum:
            row += 1
            self._sdBuchungsdatum = SmartDateEdit()
            self._sdBuchungsdatum.setPlaceholderText( "Buchungsdatum" )
            layout.addWidget( self._sdBuchungsdatum, row, 0 )
        row += 1
        self._txtEntry = BaseEdit()
        self._txtEntry.setPlaceholderText( "Bemerkung" )
        layout.addWidget( self._txtEntry, row, 0 )

        row += 1
        self._hboxLayout = QHBoxLayout()
        self.btnOk = QPushButton( self, text="OK" )
        self.btnOk.clicked.connect( self._ok )
        self._hboxLayout.addWidget( self.btnOk )

        self.btnCancel = QPushButton( self, text="Cancel" )
        self.btnCancel.clicked.connect( self._cancel )
        self._hboxLayout.addWidget( self.btnCancel )

        layout.addLayout( self._hboxLayout, row, 0 )
        self.setLayout( layout )

    def setSignPlus( self ):
        self._numEntry.setPlus()

    def setSignMinus( self ):
        self._numEntry.setMinus()

    def setCallback( self, fnc ):
        """
        Callback nach Button-Click "+", "-", "-"
        Die Callback-Function muss folgende Signatur haben: value:float, text:str (, buchungsdatum:str)
        :param fnc:
        :return:
        """
        self._callback = fnc

    def setValue( self, numval:float or int ):
        #self._numEntry.setText( str(numval ) )
        self._numEntry.setValue( numval )

    def setLabelText( self, text: str ) -> None:
        self.label.setText( text )

    def setBemerkung( self, bemerkung:str ):
        self._txtEntry.setText( bemerkung )

    def setBuchungsdatum( self, datum:str ):
        """
        :param datum: YYYY-MM-DD
        :return:
        """
        self._sdBuchungsdatum.setDateFromIsoString( datum )

    def _doCallback( self ):
        msg = ""
        if self._callback:
            #num = self._numEntry.text()
            #
            num = self._numEntry.getValue()
            if not self._sdBuchungsdatum:
                msg = self._callback( float( num ), self._txtEntry.text() )
            else:
                #datum = self._sdBuchungsdatum.getDate()
                datum = self._sdBuchungsdatum.text()  # getDate() liefert '' zurück,
                                                      # wenn das eingegebene Datum fehlerhaft ist.
                                                      # Deshalb muss hier text() verwendet werden.
                msg = self._callback( float( num ), self._txtEntry.text(), datum )
        if not msg:
            #self.close()
            self.accept()
        else:
            box = ErrorBox( "Validierung fehlgeschlagen", msg, "" )
            box.exec_()

    def _cancel( self ):
        self.close()

    def _ok( self ):
        if self._numEntry.getValue() != 0:
            self._doCallback()
        else:
            box = ErrorBox( "Ungültiger Wert", "Es muss ein Wert ungleich 0 eingegeben werden." )
            box.exec_()

######################   ValueDialog2  #################################
class ValueDialog2__probably_not_used( QDialog ):
    """
    Vereinfachte Variante des ValueDialog.
    Er enthält außer dem Value-Feld und der Bemerkung immer ein Buchungsdatum.
    Es wird auf jeglichen callback-Mechanismus verzichtet.
    Wenn ok gedrückt wird, ohne dass ein Betrag eingegeben ist, wird eine Fehlermeldung ausgegeben und
    es gibt keinen accept()-Aufruf.
    Wenn cancel gedrückt wird, wird der Dialog ohne Sicherheitsabfrage geschlossen.
    """
    def __init__( self, parent=None ):
        """
        :param parent:
        :param mitBuchungsdatum: Der Dialog wird dreizeilig gezeigt: Value, Buchungsdatum, Bemerkung
        """
        QDialog.__init__( self, parent )
        # self._callback: Callable = None
        self.setModal( True )
        self.setWindowTitle( "Neue Zahlung erfassen" )
        layout = QGridLayout( self )
        row = 0

        self._numEntry = QtWidgets.QLineEdit( self )
        self._numEntry.setPlaceholderText( "Betrag" )
        layout.addWidget( self._numEntry, row, 0 )
        self._numEntry.setAlignment( Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter )
        self._numEntry.setValidator( QDoubleValidator( -9999, 9999, 2, self ) )
        self._numEntry.setFocus()

        self._sdBuchungsdatum:SmartDateEdit = None
        row += 1
        self._sdBuchungsdatum = SmartDateEdit()
        self._sdBuchungsdatum.setPlaceholderText( "Buchungsdatum" )
        layout.addWidget( self._sdBuchungsdatum, row, 0 )
        row += 1
        self._txtEntry = BaseEdit()
        self._txtEntry.setPlaceholderText( "Bemerkung" )
        layout.addWidget( self._txtEntry, row, 0 )

        row += 1
        self._hboxLayout = QHBoxLayout()
        self.btnOk = QPushButton( self, text="OK" )
        self.btnOk.clicked.connect( self._ok )
        self._hboxLayout.addWidget( self.btnOk )

        self.btnCancel = QPushButton( self, text="Cancel" )
        self.btnCancel.clicked.connect( self._cancel )
        self._hboxLayout.addWidget( self.btnCancel )

        layout.addLayout( self._hboxLayout, row, 0 )
        self.setLayout( layout )

    def setValue( self, numval:float or int ):
        self._numEntry.setText( str(numval ) )

    def getValue( self ) -> float:
        num = self._numEntry.text()
        if num is None or num == '': num = "0"
        num = num.replace( ",", "." )
        return float( num )

    def getBuchungsdatum( self ) -> str:
        return self._sdBuchungsdatum.text()

    def getBemerkung( self ) -> str:
        return self._txtEntry.text()

    def setLabelText( self, text: str ) -> None:
        self.label.setText( text )

    def showError( self, title:str, msg:str ):
        box = ErrorBox( title, msg, "" )
        box.exec_()

    def _cancel( self ):
        self.reject()

    def _ok( self ):
        num = self._numEntry.text()
        if num is None or num == '' or num == "0":
            self.showError( "Fehlende Eingabe", "Betrag darf nicht '0' sein." )
        else:
            self.accept()


#################   TEST   TEST   TEST   TEST   #########################
def test():
    from PySide2.QtWidgets import QApplication
    def onMasterChanged( newMaster:str ):
        print( "onComboChanged ", newMaster )
        combo:BaseComboBox = dlg.getDynamicAttributeView().getWidget( "mobj_id" )
        combo.clear()
        combo.addItems( ["", "def1", "def2"] )

    app = QApplication()
    x = XEinAus()
    x.master_name = "ABC"
    x.mobj_id = "meine mobj_id"
    x.debi_kredi = "Debikredi"
    x.betrag = 111.11
    xui = XEinAusUI( x )
    vislist = (
                VisibleAttribute( "master_name", BaseComboBox, "Master: ",  nextRow=False,
                                  comboValues=["ABC", "DEF"], comboCallback=onMasterChanged),
                VisibleAttribute( "mobj_id", BaseComboBox, "Wohnung: ", comboValues=["abc1", "abc2"] ),
                VisibleAttribute( "debi_kredi", BaseEdit, "Debi/Kredi: "),
                VisibleAttribute( "betrag", FloatEdit, "Betrag: " )
              )
    xui.addVisibleAttributes( vislist )
    dlg = EinAusDialog( xui )
    if dlg.exec_() == QDialog.Accepted:
        print( "accepted" )
        dynattrview = dlg.getDynamicAttributeView()
        x = dynattrview.getXBase()
        x.print()
        xcopy = dynattrview.getModifiedXBaseCopy()
        xcopy.print()
        dynattrview.updateData()
        x = dynattrview.getXBase()
        x.print()
    else:
        print( "cancelled" )
