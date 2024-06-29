import copy

import Xlib.X
from PySide2.QtCore import Signal, QSize
from PySide2.QtGui import QFont, Qt
from PySide2.QtWidgets import QWidget, QApplication

from base.baseqtderivates import SmartDateEdit, FloatEdit, BaseLabel, BaseGridLayout, MultiLineEdit, BaseButton, HLine, \
    BaseEdit, SignedNumEdit
from generictable_stuff.okcanceldialog import OkCancelDialog
from v2.icc.interfaces import XSollHausgeld


class SollHausgeldEditView( QWidget ):
    """
    Eine View, mit der man eine Sollmiete neu anlegen oder ändern kann
    """
    delete_sollhausgeld = Signal( XSollHausgeld )
    def __init__( self, x:XSollHausgeld ):
        QWidget.__init__( self )
        self._x:XSollHausgeld = x
        self._layout = BaseGridLayout()
        self._beVw_id = BaseEdit( isReadOnly=True )
        self._beWeg_name = BaseEdit( isReadOnly=True )
        self._beMobj_Id = BaseEdit( isReadOnly=True )
        self._sdVon = SmartDateEdit( isReadOnly=False )
        self._sdBis = SmartDateEdit( isReadOnly=True )
        self._feNetto = SignedNumEdit( isReadOnly=False )  # FloatEdit( isReadOnly=True  )
        self._feRueZuFue = SignedNumEdit( isReadOnly=False )
        self._lblBrutto = BaseLabel()
        self._mlBemerkung = MultiLineEdit( isReadOnly=False )
        self._btnDelete = BaseButton( "Dieses Soll-Hausgeld löschen" )
        self._createGui()
        if x.shg_id == 0:
            title = "Neues Soll-Hausgeld für '%s' (%s)" % (x.weg_name, x.mobj_id)
        else:
            title = "Sollmiete für '%s' (%s) ändern" % (x.weg_name, x.mobj_id)
        self.setWindowTitle( title )
        self._setFieldsFromData()

    def _createGui( self ):
        self.setLayout( self._layout )
        W = 90
        r = 0
        lblSmId = BaseLabel( "<neu>" if self._x.shg_id < 1 else str( self._x.shg_id ) )
        lblSmId.setMaximumWidth( W )
        lblSmId.setAlignment( Qt.AlignRight )
        self._layout.addPair( "Soll-Hausgeld-ID: ", lblSmId, r, 0 )
        r += 1
        hline = HLine()
        self._layout.addWidget( hline, r, 0, 1, 3 )
        r += 1
        self._sdVon.setMaximumWidth( W )
        self._layout.addPair( "Dieses Soll-Hausgeld gilt ab: ", self._sdVon, r, 0 )
        self._btnDelete.setEnabled( True if self._x.shg_id > 0 else False )
        self._btnDelete.clicked.connect( lambda x: self.delete_sollhausgeld.emit( self._x ) )
        self._layout.addWidget( self._btnDelete, r, 2 )
        r += 1
        self._feNetto.setMaximumWidth( W )
        self._feNetto.textChanged.connect( self.nettoOrRueZuFueChanged )
        self._layout.addPair( "Netto-Hausgeld: ", self._feNetto, r, 0 )
        r += 1
        self._feRueZuFue.setMaximumWidth( W )
        self._feRueZuFue.textChanged.connect( self.nettoOrRueZuFueChanged )
        self._layout.addPair( "Rücklagenzuführg: ", self._feRueZuFue, r, 0 )
        r += 1
        self._lblBrutto.setMaximumWidth( W )
        self._lblBrutto.setAlignment( Qt.AlignRight )
        font = QFont( self._feRueZuFue.font() )
        font.setBold( True )
        font.setPixelSize( 16 )
        self._lblBrutto.setFont( font )
        self._lblBrutto.setStyleSheet( "color: red;" )

        self._layout.addPair( "Brutto-Hausgeld: ", self._lblBrutto, r, 0 )
        r += 1
        self._mlBemerkung.setMaximumHeight( 60 )
        self._layout.addPair( "Bemerkung: ", self._mlBemerkung, r, 0, 1, 2 )

    def getTitle( self ) -> str:
        return self.windowTitle()

    def nettoOrRueZuFueChanged( self, arg ):
        brutto = self._feNetto.getValue() + self._feRueZuFue.getValue()
        self._lblBrutto.setValue( str(brutto) )

    def getDataCopyWithChanges( self ) -> XSollHausgeld:
        """
        Übernimmt die Änderungen, die der User gemacht hat, in eine Kopie der Originalschnittstelle und
        liefert diese Kopie zurück.
        :return:
        """
        x = copy.copy( self._x )
        self._setDataFromFields( x )
        return x

    def _setDataFromFields( self, x:XSollHausgeld ):
        """
        Übertragen der GUI-Felder in <x>
        :param x:
        :return:
        """
        x.von = self._sdVon.getValue()
        x.bemerkung = self._mlBemerkung.getValue()
        x.netto = self._feNetto.getFloatValue()
        x.ruezufue = self._feRueZuFue.getFloatValue()
        x.bemerkung = self._mlBemerkung.getValue()

    def applyChanges( self ) -> XSollHausgeld:
        """
        Übernimmt die Änderungen, die der User in der View gemacht hat, in die Original-Schnittstelle.
        :return:
        """
        self._setDataFromFields( self._x )
        return self._x

    def _setFieldsFromData( self ):
        x = self._x
        self._feNetto.setFloatValue( x.netto )
        self._feRueZuFue.setFloatValue( x.ruezufue )
        self._lblBrutto.setValue( str(x.brutto) )
        self._sdVon.setValue( x.von )
        self._mlBemerkung.setValue( x.bemerkung )

    def show( self ):
        super().show()
        w = self.width()
        h = self.height()
        self.setFixedSize( QSize( w, h ) )

    def getPreferredSize( self ) -> QSize:
        return QSize( self.width(), self.height() )


##############   SollMieteEditDialog   ######################
class SollHausgeldEditDialog( OkCancelDialog ):
    edit_clicked = Signal()
    def __init__( self, v:SollHausgeldEditView, parent=None ):
        OkCancelDialog.__init__( self, v.getTitle(), parent )
        self.addWidget( v, 0 )


def test():
    def onOk():
        print( "onOk" )
        v.close()
    def onEdit():
        print( "onEdit" )
    app = QApplication()
    x = XSollHausgeld()
    x.shg_id = 0
    x.weg_name = "WEG Wilhelm-Marx-Str. 15"
    x.mobj_id = "wilhelmmarx"
    x.von = "2020-03-01"
    x.bis = ""
    x.netto = -234.50
    x.ruezufue = -60.00
    x.brutto = -294.50
    x.bemerkung = "Bla bla schon so lange keine Erhöhung \nblubb blubb\nund hier noch ne Zeile"
    v = SollHausgeldEditView( x )
    #v.ok_clicked.connect( onOk )
    #v.edit_clicked.connect( onEdit )
    v.show()
    app.exec_()