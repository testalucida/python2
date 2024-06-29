from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from typing import List, Tuple, Dict
#from xanlagevdata import XAnlageVKopfdaten
from mywidgets import MyCombobox2, CheckableItemTableView, CheckableItemList

class AnlageVFrame( ttk.Frame ):
    def __init__( self, parent ):
        ttk.Frame.__init__( self, parent )
        self.columnconfigure( 0, weight=1 )
        self._stpflCombo:MyCombobox2
        self._objektView:CheckableItemTableView
        self._objektList:CheckableItemList
        self._stpflSelectionChangedCallback = None
        self._createPdfCallback = None
        self._btnCreatePdf: ttk.Button = None
        self._createGui()

    def _createGui(self):
        f = ttk.Frame(self)
        f.grid( row=0, column=0, sticky="nsew", padx=5, pady=5)
        f.columnconfigure( 0, weight=1 )
        c = MyCombobox2( f )
        c.grid( row=0, column=0, sticky="nswe", padx=3, pady=3 )
        c.setCallback( self._onBesitzerChosen )
        self._stpflCombo = c

        objView = CheckableItemTableView( f )
        objView.grid( row=1, column=0, sticky="nswe", padx=3, pady=3 )
        self._objektView = objView

        btn = ttk.Button( f, text="pdf-Datei mit ausgewählten Objekten erzeugen" )
        btn.grid( row=2, column=0, sticky="nw", padx=3, pady=3 )
        btn["state"] = "disabled"
        btn["command"] = self._onCreatePdfCallback
        self._btnCreatePdf = btn

    def _onBesitzerChosen(self, newValue ):
        #print( "Besitzer gewählt: newValue = %s " % ( newValue ) )
        self._btnCreatePdf["state"] = "disabled"
        self._objektView.clear()
        if self._stpflSelectionChangedCallback:
            self._stpflSelectionChangedCallback( newValue )

    def _onCreatePdfCallback(self):
        if self._createPdfCallback:
            cil:CheckableItemList = self._objektView.getCheckableItemList()
            self._createPdfCallback( cil )

    def setStpflSelectionCallback(self, cb_func ):
        self._stpflSelectionChangedCallback = cb_func

    def setCreatePdfCallback(self, cb_func ):
        self._createPdfCallback = cb_func

    def setSteuerpflichtige(self, data:List[str]) -> None:
        self._data = data
        self._stpflCombo.setItems(data)
        self._stpflCombo.current(0)
        #self._provideStpflCombo()

    def setObjektList(self, objList:CheckableItemList ) -> None:
        self._objektList = objList
        self._objektView.setCheckableItemList( objList )
        self._btnCreatePdf["state"] = "normal"

    def getSelectedStpfl(self) -> str:
        return self._stpflCombo.get()

    def _provideStpflCombo(self):
        besitzerlist = []
        for item in self._data:
            besitzerlist.append( item )
        self._stpflCombo.setItems(besitzerlist)
        self._stpflCombo.current(0)

    def _guiToData(self):
        pass

def test():
    root = Tk()
    root.title( "Anlage V -- Dateneingabe und Erstellung")
    root.columnconfigure( 0, weight=1 )
    root.rowconfigure( 0, weight=1 )
    root.option_add('*Dialog.msg.font', 'Helvetica 11')

    f = AnlageVFrame(root)
    f.grid( row=0, column=0, sticky='nswe', padx=5, pady=5 )
    stpfllist = []
    stpfllist.append( "Kendel, Martin" )
    stpfllist.append( "Schirber, Albert" )
    f.setSteuerpflichtige(stpfllist)

    root.mainloop()

if __name__ == '__main__':
    test()