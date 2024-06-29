import copy

from PySide2 import QtGui
from PySide2.QtCore import Qt, QSize, Signal
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QWidget, QApplication

from base.baseqtderivates import SmartDateEdit, FloatEdit, BaseLabel, BaseGridLayout, MultiLineEdit, BaseButton, \
    BaseEdit, SignedNumEdit
from generictable_stuff.okcanceldialog import OkCancelDialog
from v2.icc.interfaces import XSollMiete, XSollHausgeld

class SollHausgeldView( QWidget ):
    """
    Eine (fast) reine ReadOnly-View, die einen Edit-Button enthält, durch dessen Betätigung man zur
    SollHausgeldEditView gelangt.
    In dieser View kann nur die Bemerkung zur aktuellen Sollmiete geändert werden.
    Es gibt keinen OK-Button, da wir davon ausgehen, dass diese View in einen SollMieteDialog eingebettet wird, der über
    einen OK-Button verfügt.
    """
    # ok_clicked = Signal()
    edit_clicked = Signal()

    def __init__( self, x:XSollHausgeld=None ):
        QWidget.__init__( self )
        self._x:XSollHausgeld = x
        self._layout = BaseGridLayout()
        self._beVw_id = BaseEdit( isReadOnly=True )
        self._beWeg_name = BaseEdit( isReadOnly=True )
        self._beMobj_Id = BaseEdit( isReadOnly=True )
        self._sdVon = SmartDateEdit( isReadOnly=True )
        self._sdBis = SmartDateEdit( isReadOnly=True )
        self._feNetto = SignedNumEdit( isReadOnly=True ) #  FloatEdit( isReadOnly=True  )
        self._feRueZuFue = SignedNumEdit( isReadOnly=True  )
        self._lblBrutto = BaseLabel()
        self._mlBemerkung = MultiLineEdit( isReadOnly=False )
        self._btnEdit = BaseButton( "Folge-Soll erfassen oder ändern..." )
        self._createGui()
        if x:
            self._setFieldsFromData()

    def _createGui( self ):
        self.setLayout( self._layout )
        r = 0
        self._layout.addPair( "WEG: ", self._beWeg_name, r, 0 )
        self._layout.addPair( "Verwalter: ", self._beVw_id, r, 2 )
        W = 90
        r += 1
        self._feNetto.setMaximumWidth( W )
        self._layout.addPair( "Nettohausgeld: ", self._feNetto, r, 0 )
        r += 1
        self._feRueZuFue.setMaximumWidth( W )
        self._layout.addPair( "Rücklagenzuführg.: ", self._feRueZuFue, r, 0 )
        r += 1
        self._lblBrutto.setMaximumWidth( W )
        self._lblBrutto.setAlignment( Qt.AlignRight )
        font = QFont( self._feRueZuFue.font() )
        font.setBold( True )
        font.setPixelSize( 16 )
        self._lblBrutto.setFont( font )
        self._lblBrutto.setStyleSheet( "color: red;" )
        self._layout.addPair( "Hausgeld ges.: ", self._lblBrutto, r, 0 )
        r += 1
        self._sdVon.setMaximumWidth( W )
        self._sdBis.setMaximumWidth( W )
        self._layout.addPair( "von: ", self._sdVon, r, 0 )
        self._layout.addWidget( BaseLabel( "bis: " ), r, 2, Qt.AlignRight )
        self._layout.addWidget( self._sdBis, r, 3 )
        r += 1
        self._mlBemerkung.setMaximumHeight( 60 )
        self._layout.addPair( "Bemerkung: ", self._mlBemerkung, r, 0, 1, 3 )
        r += 1
        dummy = BaseLabel()
        dummy.setMaximumHeight( 20 )
        self._layout.addWidget( dummy, r, 0 )
        r += 1
        # self._btnOk.clicked.connect( self.ok_clicked.emit )
        self._btnEdit.clicked.connect( self.edit_clicked.emit )
        # self._layout.addWidget( self._btnOk, r, 0 )
        self._layout.addWidget( self._btnEdit, r, 3 )

    def setSollHausgeld( self, x:XSollHausgeld ):
        if not x: return
        self._x = x
        self.setWindowTitle( "Soll-Hausgeld für '%s'" % (x.mobj_id) )
        self._setFieldsFromData()

    def getTitle( self ):
        return self.windowTitle()

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
        In dieser View kann nur die Bemerkung geändert werden.
        :param x:
        :return:
        """
        #x.bis = self._sdBis.getValue()
        x.bemerkung = self._mlBemerkung.getValue()

    def applyChanges( self ) -> XSollMiete:
        """
        Übernimmt die Änderungen, die der User in der View gemacht hat, in die Original-Schnittstelle.
        :return:
        """
        self._setDataFromFields( self._x )
        return self._x

    def setBis( self, bis:str ):
        """
        Wird aufgerufen, wenn im SollmieteEditView ein Folge-Intervall gelöscht wurde.
        Dann wird das Ende-Datum des aktuellen Intervalls angepasst und muss hier entsprechend angezeigt werden.
        :param bis: anzuzeigendes Ende-Datum
        :return:
        """
        self._sdBis.setValue( bis )

    def _setFieldsFromData( self ):
        x = self._x
        self._beWeg_name.setTextAndAdjustWidth( x.weg_name )
        self._beVw_id.setValue( x.vw_id )
        self._feNetto.setFloatValue( x.netto )
        self._feRueZuFue.setFloatValue( x.ruezufue )
        self._lblBrutto.setValue( str(x.brutto) )
        self._sdVon.setValue( x.von )
        self._sdBis.setValue( x.bis if x.bis else "" )
        self._mlBemerkung.setValue( x.bemerkung )

    def show( self ):
        super().show()
        w = self.width()
        h = self.height()
        self.setFixedSize( QSize( w, h ) )

    def getPreferredSize( self ) -> QSize:
        return QSize( self.width(), self.height() )

##############   SollMieteDialog   ######################
class SollHausgeldDialog( OkCancelDialog ):
    edit_clicked = Signal()
    def __init__( self, v:SollHausgeldView, parent=None ):
        OkCancelDialog.__init__( self, v.getTitle(), parent )
        self.setWindowTitle( v.getTitle() )
        self.addWidget( v, 0 )
        v.edit_clicked.connect( self.edit_clicked.emit )


###############################   TEST   TEST   TEST   #######################
def test():
    def onOk():
        print( "onOk" )
        v.close()
    def onEdit():
        print( "onEdit" )
    app = QApplication()
    x = XSollHausgeld()
    x.mobj_id = "charlotte"
    x.vw_id = "hansen"
    x.weg_name = "WEG Charlottenstr. 6, Saarbrücken"
    x.von = "2020-03-01"
    x.bis = ""
    x.netto = -234.50
    x.ruezufue = -120.00
    x.brutto = -354.50
    x.bemerkung = "Bla bla schon so lange keine Erhöhung \nblubb blubb\nund hier noch ne Zeile"
    v = SollHausgeldView()
    v.setSollHausgeld( x )
    # v.ok_clicked.connect( onOk )
    v.edit_clicked.connect( onEdit )
    #v.show()
    dlg = SollHausgeldDialog( v )
    dlg.show()
    app.exec_()