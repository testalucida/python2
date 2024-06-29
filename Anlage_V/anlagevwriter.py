import os
import sys
from fpdf import FPDF
import json
from anlagevlayout import zeilen

class AnlageVWriter:
    def __init__(self, savepath: str):
        self._data = None
        self._pdf = FPDF()
        self._savepath = savepath

    def writePdf(self, data_filename: str):
        """
        call this method for each anlageV json-struct that is to
        be converted into a single pdf file.
        After having written the last json struct call endPdf to
        create and open the desired pdf file.
        :param data_filename: like anlagevdata_2018.json.
        contains line numbers of the Anlage V form and the values
        to be written in each line, e.g.:
                "zeilen": {
                "1": [
                    {
                        "name": "Name",
                        "value": "Kendel"
                    }
                ],
                "2": [
                    {
                        "name": "Vorname",
                        "value": "Martin"
                    }
                ],
                "3": [
                    {
                        "name": "Steuernummer",
                        "value": "217/235/50499"
                    },
                    {
                        "name": "lfd. Nr.",
                        "value": "1"
                    }
                ], ...
        :return: None
        """

        # open interface written by AnlageVData:
        anlv_zeilen = self._openAnlageData(data_filename)['zeilen']

        self._pdf.add_page()
        self._pdf.set_font('helvetica', '', 12.0)

        x = 0
        y = 1
        a = 'L'
        page_2 = False
        for z, coords in zeilen.items():
            # zeilen: dictionary defined in anlagevlayout.py
            # key (z): line number
            # value (coords): list containing x, y or list of lists -
            # depending on the number of fields to print

            if z > 29 and not page_2:
                self._pdf.add_page()
                page_2 = True

            try:
                fieldlist = anlv_zeilen[str(z)] # get data for line z
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

                    if len(args) == 2: #align not specified
                        align = a #default
                    else:
                        align = args[2]

                    self.write(posX, posY, field['value'], align)
            except:
                print('unexpected error: ', sys.exc_info()[0])

    def endPdf(self):
        pdfFile = self._savepath + '/anlagev.pdf'
        self._pdf.output(pdfFile, 'F')

        if sys.platform.startswith("linux"):
            #os.system("xdg-open ./anlagev.pdf")
            os.system("xdg-open " + pdfFile)
        else:
            os.system(pdfFile)

    def write(self, x: int, y: int, text: str, align: str = 'L') -> None:
        self._pdf.set_xy(x, y)
        self._pdf.cell(ln=0, h=5.0, align=align, w=18.0, txt=text, border=0)

    def _openAnlageData(self, filename: str) -> None:
        """
        open interface written by AnlageVData
        :param filename: name of json file containing interface data
        :return:
        """
        f = open(filename)
        json_struc = json.load(f)
        f.close()
        return json_struc

def test():
    writer = AnlageVWriter('.')
    writer.createPdf("/home/martin/Projects/python/Wohnungsverwaltung/anlagevdata_2018.json")

if __name__ == '__main__':
    test()