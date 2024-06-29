import copy

import Xlib.X
from PySide2.QtCore import Signal, QSize
from PySide2.QtGui import QFont, Qt
from PySide2.QtWidgets import QWidget, QApplication

from base.baseqtderivates import SmartDateEdit, FloatEdit, BaseLabel, BaseGridLayout, MultiLineEdit, BaseButton, HLine
from generictable_stuff.okcanceldialog import OkCancelDialog
from v2.icc.interfaces import XSollMiete


class SollMieteEditView( QWidget ):
    """
    Eine View, mit der man eine Sollmiete neu anlegen oder ändern kann
    """
    delete_sollmiete = Signal( XSollMiete )
    def __init__( self, x:XSollMiete ):
        QWidget.__init__( self )
        self._x:XSollMiete = x
        self._layout = BaseGridLayout()
        self._sdVon = SmartDateEdit( isReadOnly=False )
        self._feNetto = FloatEdit( isReadOnly=False  )
        self._feNkv = FloatEdit( isReadOnly=False  )
        self._lblBrutto = BaseLabel()
        self._mlBemerkung = MultiLineEdit( isReadOnly=False )
        self._btnDelete = BaseButton( "Diese Sollmiete löschen" )
        self._createGui()
        if x.sm_id == 0:
            title = "Neue Sollmiete für '%s' (%s)" % (x.mv_id, x.mobj_id)
        else:
            title = "Sollmiete für '%s' (%s) ändern" % (x.mv_id, x.mobj_id)
        self.setWindowTitle( title )
        self._setFieldsFromData()

    def _createGui( self ):
        self.setLayout( self._layout )
        W = 90
        r = 0
        lblSmId = BaseLabel( "<neu>" if self._x.sm_id < 1 else str( self._x.sm_id ) )
        lblSmId.setMaximumWidth( W )
        lblSmId.setAlignment( Qt.AlignRight )
        self._layout.addPair( "Sollmiete-ID: ", lblSmId, r, 0 )
        r += 1
        hline = HLine()
        self._layout.addWidget( hline, r, 0, 1, 3 )
        r += 1
        self._sdVon.setMaximumWidth( W )
        self._layout.addPair( "Diese Sollmiete gilt ab: ", self._sdVon, r, 0 )
        self._btnDelete.setEnabled( True if self._x.sm_id > 0 else False )
        self._btnDelete.clicked.connect( lambda x: self.delete_sollmiete.emit( self._x ) )
        self._layout.addWidget( self._btnDelete, r, 2 )
        r += 1
        self._feNetto.setMaximumWidth( W )
        self._feNetto.textChanged.connect( self.nettoOrNkvChanged )
        self._layout.addPair( "Nettomiete: ", self._feNetto, r, 0 )
        r += 1
        self._feNkv.setMaximumWidth( W )
        #self._feNkv.focusOutEvent = self.nettoOrNkvOutEvent
        self._feNkv.textChanged.connect( self.nettoOrNkvChanged )
        self._layout.addPair( "NKV: ", self._feNkv, r, 0 )
        r += 1
        self._lblBrutto.setMaximumWidth( W )
        self._lblBrutto.setAlignment( Qt.AlignRight )
        font = QFont( self._feNkv.font() )
        font.setBold( True )
        font.setPixelSize( 16 )
        self._lblBrutto.setFont( font )
        self._layout.addPair( "Bruttomiete: ", self._lblBrutto, r, 0 )
        r += 1
        self._mlBemerkung.setMaximumHeight( 60 )
        self._layout.addPair( "Bemerkung: ", self._mlBemerkung, r, 0, 1, 2 )

    def getTitle( self ) -> str:
        return self.windowTitle()

    def nettoOrNkvChanged( self, arg ):
        #print( "text changed", arg )
        brutto = self._feNetto.getValue() + self._feNkv.getValue()
        self._lblBrutto.setValue( str(brutto) )

    def getDataCopyWithChanges( self ) -> XSollMiete:
        """
        Übernimmt die Änderungen, die der User gemacht hat, in eine Kopie der Originalschnittstelle und
        liefert diese Kopie zurück.
        :return:
        """
        x = copy.copy( self._x )
        self._setDataFromFields( x )
        return x

    def _setDataFromFields( self, x:XSollMiete ):
        """
        Übertragen der GUI-Felder in <x>
        :param x:
        :return:
        """
        x.von = self._sdVon.getValue()
        x.bemerkung = self._mlBemerkung.getValue()
        x.netto = self._feNetto.getFloatValue()
        x.nkv = self._feNkv.getFloatValue()
        x.bemerkung = self._mlBemerkung.getValue()

    def applyChanges( self ) -> XSollMiete:
        """
        Übernimmt die Änderungen, die der User in der View gemacht hat, in die Original-Schnittstelle.
        :return:
        """
        self._setDataFromFields( self._x )
        return self._x

    def _setFieldsFromData( self ):
        x = self._x
        self._feNetto.setFloatValue( x.netto )
        self._feNkv.setFloatValue( x.nkv )
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
class SollMieteEditDialog( OkCancelDialog ):
    edit_clicked = Signal()
    def __init__( self, v:SollMieteEditView, parent=None ):
        OkCancelDialog.__init__( self, v.getTitle(), parent )
        self.addWidget( v, 0 )


def test():
    def onOk():
        print( "onOk" )
        v.close()
    def onEdit():
        print( "onEdit" )
    app = QApplication()
    x = XSollMiete()
    x.sm_id = 0
    x.mv_id = "amaral_cynthia"
    x.mobj_id = "kleist_31"
    x.von = "2020-03-01"
    x.bis = ""
    x.netto = 234.50
    x.nkv = 60.00
    x.brutto = 294.50
    x.bemerkung = "Bla bla schon so lange keine Erhöhung \nblubb blubb\nund hier noch ne Zeile"
    v = SollMieteEditView( x )
    #v.ok_clicked.connect( onOk )
    #v.edit_clicked.connect( onEdit )
    v.show()
    app.exec_()