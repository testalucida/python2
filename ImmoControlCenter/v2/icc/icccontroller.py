from abc import abstractmethod
from typing import List

from PySide2 import QtWidgets
from PySide2.QtCore import QObject
from PySide2.QtWidgets import QWidget, QMenu

import datehelper
from v2.icc.icclogic import IccLogic
from v2.icc.iccmainwindow import IccMainWindow


class IccController( QObject ):
    def __init__( self ):
        QObject.__init__( self )
        # dic = datehelper.getCurrentYearAndMonth()
        # self._year = dic["year"]
        # self._month = dic["month"] - 1
        self._icclogic = IccLogic()
        self._year = self._icclogic.getYearToStartWith()
        self._month = self._icclogic.getMonthToStartWith()

    @abstractmethod
    def createGui( self ) -> QWidget:
        pass

    @abstractmethod
    def getMenu( self ) -> QMenu or None:
        """
        Jeder Controller liefert ein Menu, das im MainWindow in der Menubar angezeigt wird
        :return:
        """

    def getMainWindow( self ) -> IccMainWindow or None:
        """
        :return:
        """
        for w in QtWidgets.QApplication.topLevelWidgets():
            if w.inherits( 'IccMainWindow' ):
                return w
        return None

    def getYearAndMonthToStartWith( self ):
        """
        Liefert Jahr und Monat, das bei Anwendungsstart zu verwenden ist.
        Geliefert wird der Moants-Index, also Janaur = 0
        :return:
        """
        return self._year, self._month

    def getYearToStartWith( self ):
        """
        Liefert das Jahr das bei Anwendungsstart zu verwenden ist
        :return:
        """
        return self._year

    def getJahre( self ) -> List[int]:
        return self._icclogic.getJahre()
