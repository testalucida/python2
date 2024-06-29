import sys, traceback
from typing import Dict, List
from anlagevcreator import AnlageVCreator
from business import DataProvider, WvException

class AnlageVCreatorBatch:
    def __init__(self, vj, dataprovider: DataProvider, whgList: List[Dict[str, str]]):
        self._vj = vj
        self._dataProvider = dataprovider
        self._whgList: List[Dict[str, str]] = whgList
        """
        {
            'whg_id': '3',
            'plz': '90429',
            'ort': 'Nürnberg',
            'strasse': 'Austr. 22',
            'whg_bez': '2. OG'
        }
        """
        self._savePath = None
        self._infoCallback = None

    def registerInfoCallback(self, cbFnc):
        self._infoCallback = cbFnc

    def startWork(self):
        anlcreator = AnlageVCreator(self._vj, self._dataProvider)
        anl_nr = 0
        for whg in self._whgList:
            anl_nr += 1
            whg_id = int(whg['whg_id'])
            try:
                anlcreator.createAnlage(whg_id, anl_nr)
                self._doCallback('Anlage V für Wohnung ' + str(whg_id) +
                                 ' (' + whg['ort'] + ', ' + whg['strasse'] + ' ' +
                                 whg['whg_bez'] + ') erstellt.')
            except WvException as e:
                msg = 'Wohnung ' + str(whg_id) + ':\n' + e.message()
                raise WvException(e.rc(), msg)

        anlcreator.endCreate()
        self._savePath = anlcreator.getSavePath()
        self._doCallback('Alle Anlagen V im Verzeichnis ' +
                         anlcreator.getSavePath() + ' erstellt.')

    def getSavePath(self):
        return self._savePath

    def _doCallback(self, msg: str):
        if self._infoCallback:
            self._infoCallback(msg)

def info(msg: str) -> None:
    print('Batch says: ', msg)

if __name__ == '__main__':
    prov = DataProvider()
    prov.connect('d02bacec')
    whglist = prov.getWohnungsUebersicht()
    partlist = whglist[0:2]
    batch = AnlageVCreatorBatch(2018, prov, partlist)
    batch.registerInfoCallback(info)
    batch.startWork()
