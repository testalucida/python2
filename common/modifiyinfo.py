from typing import Callable

from PySide2.QtWidgets import QWidget, QLineEdit, QComboBox, QTextEdit


class ModifyInfo:
    """
    Basisklasse für Widgets (siehe z.B. MietverhaeltnisView).
    Stellt die isChanged()-Methode zur Verfügung, mit der abgefragt werden kann, ob irgend ein Element
    der GUI verändert wurde.
    Mit resetChangeFlag() stellt man das isChanged-Flag wieder auf False.
    Aktivierung: Nachdem im Widget alle GUI-Elemente instanziert sind, muss das Widget ModifyInfo.connectWidgetsToChangeSlot()
    aufgerufen werden.
    """
    def __init__( self ):
        self._isChanged = False
        self._changeCallback:Callable = None
        self._resetCallback = None

    def connectWidgetsToChangeSlot( self, changeCallback:Callable=None, resetCallback:Callable=None ):
        """
        Verbindet alle GUI-Elemente mit dem internen _onChange-Slot, der das Change-Flag steuert.
        :param changeCallback: wenn angegeben, wird diese callback-Funktion bei jeder Änderung aufgerufen.
               resetCallback: wenn angegeben, wird diese Funktion bei jedem reset des Change-Flags aufgerufen.
        aufgerufen (ohne Argumente!)
        :return:
        """
        self._changeCallback = changeCallback
        self._resetCallback = resetCallback
        children = self.findChildren( QWidget, "" )
        for child in children:
            if isinstance( child, QLineEdit ):
                child.textChanged.connect( self._onChange )
            if isinstance( child, QComboBox ):
                child.currentIndexChanged.connect( self._onChange )
                child.currentTextChanged.connect( self._onChange )
            if isinstance( child, QTextEdit ):
                child.textChanged.connect( self._onChange )

    def _onChange( self ):
        """
        interner Slot für Change-Signale.
        Setzt das Change-Flag auf True.
        :return:
        """
        self._isChanged = True
        if self._changeCallback:
            self._changeCallback()

    def isChanged( self ) -> bool:
        return self._isChanged

    def resetChangeFlag( self ):
        """
        Setzt das Change-Flag wieder auf False
        :return:
        """
        self._isChanged = False
        if self._resetCallback:
            self._resetCallback()