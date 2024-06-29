from tkinter import *
from tkinter import ttk
from typing import Dict, List
from mywidgets import ScrollableView

testdict = \
{
    "vj": 2018,
    "zeilen": {
        1: [
            {
                "name": "Name",
                "value": "Kendel"
            }
        ],
        2: [
            {
                "name": "Vorname",
                "value": "Martin"
            }
        ],
        3: [
            {
                "name": "Steuernummer",
                "value": "217/235/50499"
            },
            {
                "name": "lfd. Nr.",
                "value": "1"
            }
        ],
        4: [
            {
                "name": "Stra\u00dfe, Hausnummer",
                "value": "Mendelstr. 24 / 3. OG rechts (Whg 8 - S\u00fcd)"
            },
            {
                "name": "Angeschafft am",
                "value": "13.05.1997"
            }
        ],
        5: [
            {
                "name": "Postleitzahl",
                "value": "90429"
            },
            {
                "name": "Ort",
                "value": "N\u00fcrnberg"
            }
        ],
        6: [
            {
                "name": "Einheitswert-Aktenzeichen",
                "value": "24101153470240083"
            }
        ],
        7: [
            {
                "name": "Als Ferienwohnung genutzt",
                "value": "2"
            },
            {
                "name": "An Angeh\u00f6rige vermietet",
                "value": "2"
            }
        ],
        8: [
            {
                "name": "Gesamtwohnfl\u00e4che",
                "value": "52"
            }
        ],
        9: [
            {
                "name": "Mieteinnahmen ohne Umlagen",
                "value": "4920"
            }
        ],
        13: [
            {
                "name": "Umlagen, verrechnet mit Erstattungen",
                "value": "1200"
            }
        ],
        21: [
            {
                "name": "Summe der Einnahmen",
                "value": "6120"
            }
        ],
        33: [
            {
                "name": "linear",
                "value": "X"
            },
            {
                "name": "degressiv",
                "value": " "
            },
            {
                "name": "prozent",
                "value": ""
            },
            {
                "name": "wie_vorjahr",
                "value": "X"
            },
            {
                "name": "betrag",
                "value": "1126"
            }
        ],
        39: [
            {
                "name": "voll_abzuziehende",
                "value": "0"
            }
        ],
        41: [
            {
                "name": "gesamtaufwand_vj",
                "value": "0"
            },
            {
                "name": "anteil_vj",
                "value": "0"
            }
        ],
        42: [
            {
                "name": "vj_minus_4",
                "value": "0"
            }
        ],
        43: [
            {
                "name": "vj_minus_3",
                "value": "0"
            }
        ],
        44: [
            {
                "name": "vj_minus_2",
                "value": "0"
            }
        ],
        45: [
            {
                "name": "vj_minus_1",
                "value": "860"
            }
        ],
        46: [
            {
                "name": "grundsteuer_txt",
                "value": "Grundsteuer"
            },
            {
                "name": "grundsteuer",
                "value": "44"
            }
        ],
        47: [
            {
                "name": "hausgeld",
                "value": "Hausgeld OHNE Zuf\u00fchrg. R\u00fccklagen"
            },
            {
                "name": "verwaltungskosten",
                "value": "991"
            }
        ],
        49: [
            {
                "name": "sonst_kost",
                "value": "Porto, Fahrtkosten, H&G etc."
            },
            {
                "name": "sonstige",
                "value": "68"
            }
        ],
        22: [
            {
                "name": "summe_werbungskosten",
                "value": "3089"
            }
        ],
        50: [
            {
                "name": "summe_werbungskosten",
                "value": "3089"
            }
        ],
        23: [
            {
                "name": "ueberschuss",
                "value": "3031"
            }
        ],
        24: [
            {
                "name": "zurechng_mann",
                "value": "3031"
            },
            {
                "name": "zurechng_frau",
                "value": "0"
            }
        ]
    }
}

class AnlageVDataModel:
    def __init__(self, datadict):
        #self._keys = "zeilen"
        self.vj = datadict['vj']
        self._datadict = datadict['zeilen']
        self._rowdict = dict()
        self._makeTable(datadict['zeilen'])

    def _makeTable(self, datadict:Dict):
        r = 0
        for key, val in datadict.items():
            #print(key, ": ")
            if self._isIterable(val):
                for v in val:
                    name = v['name']
                    value = v['value']
                    self._rowdict[r] = [key, name, value,
                                        self._getComment(key, name, value)]
                    r += 1
                    #print( "\t", v)
            else: raise KeyError("Key " + key + " is not iterable")

        # for k, v in self._rowdict.items():
        #     print(k, v)

    def _getComment(self, z:int, name:str, value:any) -> str:
        """
        :param z:  Zeilennummer des Formulars
        :param name: Name des Formularfelds
        :param value: Wert, der im Formularfeld eingetragen wird
        :return: Erläuterung, wie der ausgewiesene Wert zustande kam
        """
        try:
            numval = float(value)
        except Exception:
            try:
                numval = int(value)
            except:
                return ""

        lf = "\n"
        tab = "\t"
        text = ""

        if z == 9: #Mieteinnahmen
            #AnlageVData._getZeile_9_to_14_mtlEinn() ->
            #   DataProvider.getAnlageVData_9_to_14_mtlEinn(whg_id, vj)
            #       returns XMtlEinnahmenList (gueltig_ab, gueltig_bis, netto_miete,
            #                                   nk_abschlag)
            comment = "Addition des Feldes netto_miete über alle Datensätze\n" \
                      "im passenden Zeitraum"
            sql = "select ..., netto_miete, ..." + lf + \
                  "from mtl_ein_aus " + lf + \
                  "where whg_id = <id>" + lf + \
                  "and (gueltig_bis is null or year(gueltig_bis) >= <vj>)" + lf + \
                  "and year(gueltig_ab) <= <vj>" + lf + \
                  "order by gueltig_ab asc"
            text = comment + lf + "SQL:" + lf + sql
        elif z == 13: #Nebenkostenabschlag saldiert mit Nach- u. Rückzahlg.
            #NK-Abschläge werden im gleichen Serviceaufruf wie bei Zeile 9 ermittelt
            #(nur 1 call)
            #danach Berechnung der NK-Korrekturen über den Service
            #DataProider.getAnlageVData_13_nkKorr(whg_id, vj)
            #   returns nkAdjustList: vj, betrag, art=NK-Nachzahlung, NK-Rückzahlung
            comment = "Addition des Feldes nk_abschlag über alle Datensätze\n" \
                      "im passenden Zeitraum.\n" \
                      "Dann Saldierung aller Nach- u.Rückzahlungen im VJ und \n" \
                      "Verrechnung mit der Summe der NK-Abschläge."
            sql = "select ..., betrag, art.art, art.ein_aus\n"\
                  "from sonstige_ein_aus sea\n"\
                  "inner join sea_art art on art.art_id = sea.art_id\n"\
                  "where sea.whg_id = $whg_id\n"\
                  "and art.art_kurz in ('nk_nachz', 'nk_rueck')\n"\
                  "and vj = $vj"
            text = comment + lf + "SQL:" + lf + sql
        elif z == 21:
            text = "Summe der Werte aus den Zeilen 9 u. 13"
        elif z == 33:
            text = "AfA: Alle Zeilenwerte aus Tabelle afa"
        elif z == 39:
            comment = "Voll abzuziehender Erhaltungsaufwand:\n" \
                      "Addition aller Rechnungsbeträge, die im VJ bezahlt wurden (rg_bezahlt_am) UND\n\t" \
                      "die nicht auf mehrere Jahre zu verteilen sind." \
                      "Ist eine Rechnung auf mehrere Jahre zu verteilen,\n" \
                      "wird nur der anteilige Betrag ausgegeben.\n" \
                      "Beachte: Entnahmen aus den Rücklagen werden als (Dummy-)Rechnung gespeichert\n" \
                      "\tund hier berücksichtigt."
            sql = "select ..., rg_datum, betrag, verteilung_jahre, rg_bezahlt_am, ...\n"\
                  "from rechnung\n"\
                  "where whg_id = $whg_id\n"\
                  "order by rg_datum desc"
            text = comment + lf + "SQL:" + lf + sql
        elif z == 41:
            if name == "gesamtaufwand_vj":
                text = "Auf bis zu 5 Jahre zu verteilender Gesamtaufwand,\n" \
                       "der *im VJ* entstanden ist (Formularfeld 57)."

            else:
                text = "Anteiliger Betrag für das VJ (Formularfeld 38)."
        elif z == 42 or z == 43 or z == 44 or z == 45:
            text = "Anteilige Beträge aus Rechnungen vergangener VJ."
        elif z == 47: #Formularzeile "Verwaltungskosten".
            comment = "Summe der monatlichen Hausgeldzahlungen OHNE Rücklagenanteil, \n" \
                      "bereinigt um Nach- und Rückzahlungen,\n" \
                      "eingetragen in der Zeile Verwaltungskosten.";
            sql = "select ..., gueltig_ab, gueltig_bis, hg_netto_abschlag\n" \
                  "from mtl_ein_aus\n"\
                  "where whg_id = $whg_id\n"\
                  "and (gueltig_bis is null or year(gueltig_bis) >= $vj)\n"\
                  "and year(gueltig_ab) <= $vj\n"\
                  "order by gueltig_ab asc\n" \
                  "...und\n" \
                  "select ..., vj, betrag, art.art, art.ein_aus\n"\
                  "from sonstige_ein_aus sea\n"\
                  "inner join sea_art art on art.art_id = sea.art_id\n"\
                  "where sea.whg_id = $whg_id\n"\
                  "and art.art_kurz in ('hg_nachz', 'hg_rueck')\n"\
                  "and vj = $vj"
            text = comment + lf + "SQL:" + lf + sql
        elif z == 49:
            comment = "Addiert werden die Beträge aller Datensätze des VJ\n" \
                      "mit der Art 'Sonstige Kosten'."
            sql = "select ..., vj, betrag\n"\
                  "from sonstige_ein_aus sea\n"\
                  "inner join sea_art art on art.art_id = sea.art_id\n"\
                  "where sea.whg_id = $whg_id\n"\
                  "and art.art_kurz = 'sonst_kost'\n"\
                  "and vj = $vj"
            text = comment + lf + "SQL:" + lf + sql
        elif z == 22:
            text = "Summe der Werbungskosten:\n" \
                  "AfA + \n" \
                  "voll abzuziehende Aufwände + \n" \
                  "anteilige Aufwände aus Vorjahren + \n" \
                  "Grundsteuer + \n" \
                  "Verwaltungskosten (Hausgeld ohne Zuf. Rücklagen) + \n" \
                  "Sonstige Kosten"
        elif z == 50:
            text = "Übertrag aus Zeile 22"
        elif z == 23:
            text = "Überschuss:\n" \
                   "Summe der Einnahmen - Summe der Werbungskosten (Zeile 22)\n" \
                   "Summe der Einnahmen errechnet sich zu\n\t" \
                   "Netto-Miete des VJ saldiert mit den NK-Nach- u. Rückzahlungen."

        return text

    def _isIterable(self, val: any) -> bool:
        try:
            iter(val)
        except Exception:
            return False
        else:
            return True

    def getValue(self, row:int, col:int) -> any:
        li:List = self._rowdict[row]
        return li[col]

    def getValues(self, row:int) -> List:
        return self._rowdict[row]

    def getRows(self) -> int:
        return len(self._rowdict)

    def getColumns(self) -> int:
        return len(self._rowdict[0])

#########################################################################

class AnlageVTableView(ScrollableView):
    def __init__(self, parent):
        ScrollableView.__init__(self, parent)
        self._headers = ("Z#", "Feldbezeichnung", "Eingetragener Wert", "Erläuterung")
        self._colW = (5, 35, 35, 100)
        self._data = None
        self._rowlist = [] #list of ttk.Frames representing a row each

    def setData(self, data:AnlageVDataModel) -> None:
        cols = data.getColumns()
        self._provideHeaders(cols)
        rows = data.getRows()
        for r in range(rows):
            f = ttk.Frame(self.clientarea)
            f.grid(row=r+1, column=0, columnspan=cols, sticky='nswe', padx=1, pady=1)
            #self._rowlist.append(f)
            self._provideColumnValues(f, data.getValues(r))

    def _provideHeaders(self, cols:int):
        f = ttk.Frame(self.clientarea)
        f.grid(row=0, column=0, columnspan=cols, sticky='nswe', padx=1, pady=1)
        s = ttk.Style()
        s.configure("header.Label", ipady=5, background="#000000")
        for c in range(cols):
            #lbl = ttk.Label(f, text=self._headers[c], width=self._colW[c], style="header.Label")
            lbl = Label(f, text=self._headers[c], width=self._colW[c], height=2)
            lbl.grid(row=0, column=c, sticky='nswe', padx=1, pady=1)

    def _provideColumnValues(self, parent:ttk.Frame, values:List) -> None:
        c = 0
        s = ttk.Style()
        s.configure( "my.Label", background="#ffffff")
        for cellval in values:
            lbl = ttk.Label(parent, text=cellval, width = self._colW[c], style="my.Label")
            lbl.grid(row=0, column=c, sticky='nswe', padx = 1, pady = 1)
            c += 1

# class AnlageVTableView(TableView):
#     def __init__(self, parent):
#         TableView.__init__(self, parent)
#         self._headers = ["Z#", "Bezeichnung", "Wert", "Erläuterung"]
#         self.setColumns(self._headers)
#         self.setColumnWidth(self._headers[0], 30)
#         self.setColumnWidth(self._headers[3], 80)
#         self.setColumnStretch(self._headers[0], False)
#         self.setColumnStretch(self._headers[1], False)
#         self.setColumnStretch(self._headers[2], False)
#         self.alignColumn(self._headers[2], 'e')
#
# def wrap(string, length=20):
#     return '\n'.join(textwrap.wrap(string, length))


def test():
    avdata = AnlageVDataModel(testdict)
    root = Tk()
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    root.geometry('1300x800')
    atv = AnlageVTableView(root)
    atv.grid(row=0, column=0, sticky='nswe', padx=3, pady=3)
    atv.setData(avdata)
    root.mainloop()

if __name__ == '__main__':
    test()