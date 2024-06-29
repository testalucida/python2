import copy
from typing import List, Iterable

from PySide2.QtWidgets import QWidget, QFormLayout, QComboBox, QApplication, QPushButton, QHBoxLayout, QDialog

from base.baseqtderivates import SmartDateEdit, BaseEdit, MultiLineEdit, IntEdit, FloatEdit, SignedNumEdit
from generictable_stuff.okcanceldialog import OkCancelDialog
from v2.icc.interfaces import XGeschaeftsreise


class GeschaeftsreiseEditView( QWidget ):
    def __init__( self, masterlist:Iterable[str], x:XGeschaeftsreise, parent=None ):
        QWidget.__init__( self, parent )
        self._xgeschaeftsreise = x
        self._layout = QFormLayout()
        self.setLayout( self._layout )
        self._cboMasterNames = QComboBox()
        self._sdVon = SmartDateEdit()
        self._sdBis = SmartDateEdit()
        #self._beZiel = BaseEdit()
        self._meZweck = MultiLineEdit()
        self._ieKm = IntEdit( showNegativNumbersRed=False )
        self._iePersonen = IntEdit( showNegativNumbersRed=False )
        self._beUebernachtung = BaseEdit()
        self._feUebernachtKosten = SignedNumEdit()
        self._createGui()
        self.setMasterobjekte( masterlist )
        self.setData( x )
        self._xOrig = x

    def _createGui( self ):
        """
        :return:
        """
        l = self._layout
        self._cboMasterNames.setMaximumWidth( 100 )
        l.addRow( "Haus: ", self._cboMasterNames )
        self._sdVon.setMaximumWidth( 100 )
        l.addRow( "Beginn: ", self._sdVon )
        self._sdBis.setMaximumWidth( 100 )
        l.addRow( "Ende: ", self._sdBis )
        # l.addRow( "Ziel: ", self._beZiel )
        self._meZweck.setMaximumHeight( 80 )
        l.addRow( "Zweck: ", self._meZweck )
        l.addRow( "Hotel o.ä.: ", self._beUebernachtung )
        self._feUebernachtKosten.setMaximumWidth( 90 )
        l.addRow( "Übernacht.-Kosten: ", self._feUebernachtKosten )
        self._ieKm.setMaximumWidth( 55 )
        l.addRow( "Gefahrene Kilometer: ", self._ieKm )
        self._iePersonen.setMaximumWidth( 55 )
        l.addRow( "Anzahl Personen: ", self._iePersonen )
        dummy = QWidget()
        dummy.setFixedHeight( 20 )
        l.addRow( "", dummy )

    def _setFieldsFromData( self ):
        """
        :return:
        """
        x = self._xgeschaeftsreise
        self._cboMasterNames.setCurrentText( x.master_name )
        self._sdVon.setDateFromIsoString( x.von )
        self._sdBis.setDateFromIsoString( x.bis )
        # self._beZiel.setText( x.ziel )
        self._meZweck.setText( x.zweck )
        self._ieKm.setIntValue( x.km )
        self._iePersonen.setIntValue( x.personen )
        self._beUebernachtung.setText( x.uebernachtung )
        self._feUebernachtKosten.setFloatValue( x.uebernacht_kosten )

    def _setDataFromFields( self, x:XGeschaeftsreise ):
        x.master_name = self._cboMasterNames.currentText()
        x.von = self._sdVon.getDate()
        x.bis = self._sdBis.getDate()
        #x.ziel = self._beZiel.text()
        x.zweck = self._meZweck.toPlainText()
        x.km = self._ieKm.getIntValue()
        x.personen = self._iePersonen.getIntValue()
        x.uebernachtung = self._beUebernachtung.text()
        x.uebernacht_kosten = self._feUebernachtKosten.getFloatValue()

    def setMasterobjekte( self, masternameList:Iterable[str] ):
        """
        Versorgt die ComboBox mit den möglichen Werten (Mietobjekten)
        Diese Methode muss VOR setData() aufgerufen werden.
        :param masternameList:
        :return:
        """
        self._cboMasterNames.addItems( masternameList )

    def getDataCopyWithChanges( self ) -> XGeschaeftsreise:
        x = copy.copy( self._xgeschaeftsreise )
        self._setDataFromFields( x )
        return x

    def applyChanges( self ) -> XGeschaeftsreise:
        self._setDataFromFields( self._xgeschaeftsreise )
        return self._xgeschaeftsreise

    def setData( self, x:XGeschaeftsreise ) -> None:
        self._xgeschaeftsreise = x
        self._setFieldsFromData()

########################  GeschaeftsreiseEditDialog  ####################
class GeschaeftsreiseEditDialog( OkCancelDialog ):
    def __init__( self, masterlist, x:XGeschaeftsreise, parent=None ):
        OkCancelDialog.__init__( self, parent )
        self.view = GeschaeftsreiseEditView( masterlist, x )
        self.addWidget( self.view, 0 )


#########################################################################
#########################################################################
#########################################################################
def testEditDialog():
    app = QApplication()
    masterlist = ("Ill_Eich", "NK_Kleist", "SB_Charlotte", "SB_Kaiser")
    x = XGeschaeftsreise()
    dlg = GeschaeftsreiseEditDialog( masterlist, x )
    dlg.setOkButtonText( "Speichern" )
    if dlg.exec_() == QDialog.Accepted:
        x.print()
    else:
        print( "Cancelled" )


def testEditView():
    app = QApplication()
    masterlist = ("Ill_Eich", "NK_Kleist", "SB_Charlotte", "SB_Kaiser")
    x = XGeschaeftsreise()
    v = GeschaeftsreiseEditView( masterlist, x )
    v.show()
    app.exec_()
