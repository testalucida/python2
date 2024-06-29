from PySide2.QtWidgets import QMenu

from base.baseqtderivates import BaseAction
from v2.anlagev.anlagevcontroller import AnlageVController
from v2.extras.ertrag.ertragcontroller import ErtragController
from v2.icc.icccontroller import IccController


class ExtrasController( IccController ):
    def __init__( self ):
        IccController.__init__( self )
        self._ertragCtrl = None
        self._anlageVCtrl = None

    def getMenu( self ) -> QMenu or None:
        """
        Jeder Controller liefert dem MainController ein Menu, das im MainWindow in der Menubar angezeigt wird
        :return:
        """
        menu = QMenu( "Extras" )
        action = BaseAction( "Ertragsübersicht...", parent=menu )
        action.triggered.connect( self.onErtragsuebersicht )
        menu.addAction( action )
        menu.addSeparator()
        action = BaseAction( "Anlagen V...", parent=menu )
        action.triggered.connect( self.onAnlagenV )
        menu.addAction( action )
        return menu

    def onErtragsuebersicht( self ):
        if not self._ertragCtrl:
            self._ertragCtrl = ErtragController()
        self._ertragCtrl.showErtraege()

    def onAnlagenV( self ):
        if not self._anlageVCtrl:
            self._anlageVCtrl = AnlageVController()
        self._anlageVCtrl.showAnlagenV()