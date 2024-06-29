import sys
import os
from dbaccess import DbAccess
from typing import List, Dict
from mywidgets import CheckableItemList
from fpdf import FPDF

offset = {
    1: (18, 8),
    2: (18, 16),
    3: ((47, 25), (140, 25)),
    4: ((18, 52), (168, 52)),
    5: ((18, 62), (47, 62)),
    6: (28, 72),
}

class BusinessLogic:
    def __init__(self):
        self._db:DbAccess
        self._stpflDictList:List[Dict]

    def prepare(self):
        self._db = DbAccess()
        self._db.open()

    def terminate(self):
        self._db.close()

    def getAllSteuerpflichtige(self) -> List[str]:
        self._stpflDictList = self._db.getAllSteuerpflichtige()
        itemlist: List[str] = []
        for dic in self._stpflDictList:
            item: str = dic["name"] + ", " + dic["vorname"]
            itemlist.append(item)
        return itemlist

    def getObjekteById( self, stpfl_id:int ) -> List[Dict]:
        return self._db.getObjekte( stpfl_id )

    def getObjekteByName( self, stpfl:str ) -> CheckableItemList:
        namevorname:List[str] = stpfl.split( ", " )
        name = namevorname[0]
        vorname = namevorname[1]
        for d in self._stpflDictList:
            if d["name"] == name and d["vorname"] == vorname:
                dictlist:List[Dict] = self.getObjekteById( d["id"] )
                checkitemlist:CheckableItemList = self._createObjektList( dictlist )
                return checkitemlist

    def createPdf(self, idList:List[int] ) -> None:
        dictlist:List[Dict] = self._db.getSomeObjekte( idList )
        stpfl_id:int = dictlist[0]["stpfl_id"]
        stpfl:Dict = self._db.getSteuerpflichtigen( stpfl_id )
        topdf:AnlageVToPdf = AnlageVToPdf()
        for i in range( len(idList) ):
            zeilen:Dict = self._createZeilenDict( i+1, stpfl, dictlist[i] )
            #zeilen_json = json.dumps( zeilen )
            topdf.write( zeilen )
        topdf.endPdf()

    def _createZeilenDict(self, nr:int, stpfl:Dict, objekt:Dict) -> Dict:
        zeilen = {}
        zeilen["1"] = [{"name":"Name", "value":stpfl["name"]}]
        zeilen["2"] = [{"name":"Vorname", "value":stpfl["vorname"]}]
        zeilen["3"] = [{"name": "Steuernummer", "value":stpfl["steuernummer"]},
                        {"name": "lfd.Nr.", "value":str( nr )}]
        zeilen["4"] = [{"name": "Strasse, Hausnummer", "value": objekt["strasse_hnr"]},
                        {"name": "Angeschafft am", "value": objekt["angeschafft_am"]}]
        zeilen["5"] = [{"name": "Postleitzahl", "value": objekt["plz"]},
                        {"name": "Ort", "value": objekt["ort"]}]
        zeilen["6"] = [{"name": "Einheitswert-Aktenzeichen", "value": objekt["einh_wert_az"]}]
        return zeilen

    def _createObjektList(self, dictlist:List[Dict]) -> CheckableItemList:
        cil:CheckableItemList = CheckableItemList()
        for d in dictlist:
            whg:str = d["ort"] + ", " + d["strasse_hnr"]
            cil.appendItem( whg, d["id"], check=False)
        return cil

class AnlageVToPdf:
    def __init__(self):
        self._pdf = FPDF()
        self._pdf.set_font('helvetica', '', 14.0)

    def write(self, zeilen:Dict ):
        self._pdf.add_page()
        x = 0
        y = 1
        a = 'L'
        for z, coords in offset.items():
            try:
                fieldlist = zeilen[str(z)]  # get data for line z
                i = 0
                for field in fieldlist:
                    posX = posY = 0
                    if type(coords[i]) == tuple:
                        args = list(coords[i])
                        posX = coords[i][x]
                        posY = coords[i][y]
                        i += 1
                    else:
                        args = list(coords)
                        posX = coords[x]
                        posY = coords[y]

                    if len(args) == 2:  # align not specified
                        align = a  # default
                    else:
                        align = args[2]

                    self.writeZeile( posX, posY, " " if not field['value'] else field['value'], align )
            except:
                print('field_name %s, field_value %s: unexpected error: ' % (field['name'], field['value']), sys.exc_info()[0])

    def writeZeile(self, x:int, y:int, text:str, align:str="L" ) -> None:
        self._pdf.set_xy(x, y)
        self._pdf.cell(ln=0, h=5.0, align=align, w=18.0, txt=text, border=0)

    def endPdf(self):
        pdfFile = "./anlagev.pdf"
        self._pdf.output(pdfFile, 'F')

        if sys.platform.startswith("linux"):
            #os.system("xdg-open ./anlagev.pdf")
            os.system("xdg-open " + pdfFile)
        else:
            os.system(pdfFile)