from tkinter import messagebox
from typing import List, Dict
from anlagevframe import AnlageVFrame
from business import BusinessLogic
from mywidgets import CheckableItemList, CheckableItemView

class Controller:
    def __init__(self, view:AnlageVFrame, businessLogic:BusinessLogic):
        self._view:AnlageVFrame = view
        self._busilogic:BusinessLogic = businessLogic
        self._stpflDictList:List[Dict]
        self._view.setStpflSelectionCallback( self.onStpflSelectionChanged )
        self._view.setCreatePdfCallback( self.onCreatePdf )

    def startWork(self):
        self._busilogic.prepare()
        itemlist:List[str] = self._busilogic.getAllSteuerpflichtige()
        itemlist.insert( 0, "-- Steuerpflichtigen auswählen --" )
        self._view.setSteuerpflichtige( itemlist )
        return

    def onStpflSelectionChanged(self, newStpfl:str ) -> None:
        if newStpfl.startswith( "--" ): return
        else:
            checkItemList:CheckableItemList = self._busilogic.getObjekteByName( newStpfl )
            self._view.setObjektList( checkItemList )

    def onCreatePdf(self, cil:CheckableItemList ) -> None:
        idList = []
        for item in cil.getItems():
            if item.check:
                idList.append( item.id )
        self._busilogic.createPdf( idList )