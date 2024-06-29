from typing import Any

from PySide2.QtCore import QSize
from PySide2.QtWidgets import QWidget, QApplication, QMenu

from base.baseqtderivates import BaseAction
from base.messagebox import ErrorBox
from generictable_stuff.okcanceldialog import OkDialog
from v2.einaus.einauswritedispatcher import EinAusWriteDispatcher
from v2.geschaeftsreise.geschaeftsreiseeditcontroller import GeschaeftsreiseEditController
from v2.geschaeftsreise.geschaeftsreiselogic import GeschaeftsreiseLogic
from v2.geschaeftsreise.geschaeftsreisetablemodel import GeschaeftsreiseTableModel
from v2.geschaeftsreise.geschaeftsreisenview import GeschaeftsreisenView
from v2.icc.constants import EinAusArt
from v2.icc.icccontroller import IccController
from v2.icc.interfaces import XGeschaeftsreise, XEinAus
from v2.icc.screen import getScreenWidth, setScreenSize


class GeschaeftsreiseController( IccController ):
    def __init__( self ):
        IccController.__init__( self )
        self._logic = GeschaeftsreiseLogic()
        self._view:GeschaeftsreisenView = None
        self._editCtrl = GeschaeftsreiseEditController()

    def getMenu( self ) -> QMenu or None:
        """
        Jeder Controller liefert ein Menu, das im MainWindow in der Menubar angezeigt wird
        :return:
        """
        menu = QMenu( "Geschäftsreisen" )
        action = BaseAction( "Geschäftsreisen anzeigen und bearbeiten...", parent=menu )
        action.triggered.connect( self.onGeschaeftsreise )
        menu.addAction( action )
        return menu

    def onGeschaeftsreise( self ):
        view = self.createGui()
        dlg = OkDialog( "Geschäftsreisen bearbeiten" )
        dlg.setOkButtonText( "Schließen" )
        dlg.addWidget( view, 0 )
        dlg.resize( QSize( 1350, 800 ) )
        dlg.exec_()

    def createGui( self ) -> QWidget:
        try:
            jahre = self.getJahre()
            jahr = self.getYearToStartWith()
            tm:GeschaeftsreiseTableModel = self._logic.getGeschaeftsreisenTableModel( jahr )
        except Exception as ex:
            box = ErrorBox( "Fehler beim Erzeugen des GeschaeftsreiseView", str( ex ), "" )
            box.exec_()
            return None
        self._view = GeschaeftsreisenView( tm )
        self._view.setJahre( jahre )
        self._view.setJahr( jahr )
        #self._view.save.connect( self.onSave )
        self._view.yearChanged.connect( self.onYearChanged )
        self._view.createItem.connect( self.onCreate )
        self._view.editItem.connect( self.onEdit )
        self._view.deleteItem.connect( self.onDelete )

        w = self._view.getPreferredWidth()
        screenwidth = getScreenWidth()
        if w > screenwidth:
            w = screenwidth
        sz = self._view.size()
        self._view.resize( w, sz.height() )
        return self._view

    def onYearChanged( self, newyear:int ):
        self._setNewModel( newyear )

    def _setNewModel( self, jahr:int ):
        tm: GeschaeftsreiseTableModel = self._logic.getGeschaeftsreisenTableModel( jahr )
        self._view.setModel( tm )
        tm.setSortable( True )

    @staticmethod
    def getViewTitle() -> str:
        return "Geschäftsreisen"

    # def isChanged( self ) -> bool:
    #     model:GeschaeftsreiseTableModel = self._view.getModel()
    #     return model.isChanged()

    def onCreate( self ):
        editCtrl = GeschaeftsreiseEditController()
        x:XGeschaeftsreise = editCtrl.createGeschaeftsreise( self._view.getJahr() )
        if x:
            try:
                xea:XEinAus = self._logic.insertGeschaeftsreise( x )
                EinAusWriteDispatcher.inst().einaus_inserted( xea )
            except Exception as ex:
                box = ErrorBox( "Speichern fehlgeschlagen", str( ex ),
                                "\nAufgefangen in GeschaeftsreiseController.onCreate()")
                box.exec_()
                return
            model:GeschaeftsreiseTableModel = self._view.getModel()
            model.addObject( x )

    def onEdit( self, x: XGeschaeftsreise ):
        editCtrl = GeschaeftsreiseEditController( x )
        if editCtrl.editGeschaeftsreise():
            try:
                xea, delta = self._logic.updateGeschaeftsreise( x )
                EinAusWriteDispatcher.inst().einaus_updated( xea, delta )
            except Exception as ex:
                box = ErrorBox( "Speichern fehlgeschlagen", str( ex ),
                                "\nAufgefangen in GeschaeftsreiseController.onEdit()")
                box.exec_()
                return
            model: GeschaeftsreiseTableModel = self._view.getModel()
            model.objectUpdatedExternally( x )

    def onDelete( self, x: XGeschaeftsreise ):
        try:
            dic = self._logic.deleteGeschaeftsreise( x.reise_id )
            EinAusWriteDispatcher.inst().einaus_deleted( (dic["ea_id"],),
                                                         EinAusArt.SONSTIGE_KOSTEN.display, dic["betrag"]*(-1) )
        except Exception as ex:
            box = ErrorBox( "Löschen fehlgeschlagen", str( ex ),
                            "\nAufgefangen in GeschaeftsreiseController.onDelete()" )
            box.exec_()
            return
        model: GeschaeftsreiseTableModel = self._view.getModel()
        model.removeObject( x )


##############################  T E S T  ############################
def jahrChanged( arg ):
    print( "Jahr geändert: ", arg )

def save():
    print( "Speichern" )

def test():
    app = QApplication()
    setScreenSize( app )
    c = GeschaeftsreiseController()
    v = c.createGui()
    v.yearChanged.connect( jahrChanged )
    dlg = OkDialog( "Geschäftsreisen bearbeiten" )
    dlg.setOkButtonText( "Schließen" )
    dlg.addWidget( v, 0 )
    dlg.exec_()
    #v.show()
    #app.exec_()

if __name__ == "__main__":
    test()