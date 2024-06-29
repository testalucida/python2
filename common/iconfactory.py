import os

from PySide2.QtGui import QIcon

class UsedIcons:
    __instance = None
    __icons = dict()

    @staticmethod
    def inst():
        if UsedIcons.__instance is None:
            UsedIcons()
        return UsedIcons.__instance

    def __init__( self ):
        if UsedIcons.__instance is not None:
            raise Exception( "UsedIcons is a singleton!" )
        UsedIcons.__instance = self

    def getIcon( self, path ) -> QIcon:
        try:
            return UsedIcons.__icons[path]
        except:
            icon = QIcon( path )
            UsedIcons.__icons[path] = icon
            return icon

#########################  Singleton IconFactory  #######################
class IconFactoryS:
    __instance = None

    @staticmethod
    def inst():
        if IconFactoryS.__instance is None:
            IconFactoryS()
        return IconFactoryS.__instance

    def __init__( self ):
        if IconFactoryS.__instance is not None:
            raise Exception( "IconFactoryS is a singleton!" )
        IconFactoryS.__instance = self

    def getIcon( self, pathToImagefile:str ) -> QIcon:
        return UsedIcons.inst().getIcon( pathToImagefile )

############################  Instanzierbare IconFactory -- DEPRECATED ####################
class IconFactory:
    def __init__( self ):
        self._icons = UsedIcons.inst()

    def getIcon( self, path ) -> QIcon:
        return self._icons.getIcon( path )



