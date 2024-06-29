from business import DataProvider, DataError, ServiceException
from anlagevdata import AnlageVData
from anlagevwriter import AnlageVWriter
from typing import List, Dict

class AnlageVCreator:
    def __init__(self, vj, dataprovider: DataProvider, savepath: str = None):
        self._vj = vj
        self._savepath = savepath
        self._dataProvider = dataprovider
        self._anlagevwriter = None

    def getAnlageVData(self, whg_id, anlage_nr) -> List:
        anlagevdata = AnlageVData(whg_id,
                                  anlage_nr,
                                  self._vj,
                                  None,
                                  self._dataProvider)
        return anlagevdata.getAnlageVData()

    def createAnlage(self, whg_id, anlage_nr):
        if not self._savepath:
            self._savepath = self._getAnlageVSavepath()
            if not self._savepath:
                return

        anlagevdata = AnlageVData(whg_id,
                                  anlage_nr,
                                  self._vj,
                                  self._savepath,
                                  self._dataProvider)
        jsonfile = anlagevdata.startWork()
        if not self._anlagevwriter:
            self._anlagevwriter = AnlageVWriter(self._savepath)
        self._anlagevwriter.writePdf(jsonfile)

    def endCreate(self):
        self._anlagevwriter.endPdf()

    def getSavePath(self) -> str:
        return self._savepath

    def _getAnlageVSavepath(self) -> str or None:
        from tkinter import filedialog
        import os
        initdir = os.getcwd()
        wvdir = '/wohnungsverwaltung'
        if os.path.isdir(initdir + wvdir):
            initdir += wvdir
            anlagedir = '/anlagen_v'
            if os.path.isdir(initdir + anlagedir):
                initdir += anlagedir

        options = {}
        options['initialdir'] = initdir
        options['title'] = 'Verzeichnis auswählen, ggf. neues dazuschreiben'
        options['mustexist'] = False
        dir = filedialog.askdirectory(**options)
        if type(dir) is str:
            if not os.path.isdir(dir):
                parts = dir.split('/')
                dirpath = '/'
                for part in parts:
                    if len(part) > 0:
                        dirpath += part
                        if not os.path.isdir(dirpath):
                            os.mkdir(dirpath)
                        dirpath += '/'
            return dir
        return None