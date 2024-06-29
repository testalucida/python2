import json
import utils
import datetime
from typing import Dict, List, Text
from business import DataProvider, WvException
import datehelper
from interfaces import XErhaltungsaufwand, XImmoStammdaten, \
    XMtlEinnahmen, XMtlEinnahmenList, XAfa

class AnlageVData:
    """
    Sammelt alle Daten, die zur Erstellung der Anlage V für eine Wohnung
    für ein Veranlagungsjahr benötigt werden
    und schreibt sie in eine JSON-Schnittstelle mit folgendem Aufbau:
        {
            "vj": 2018,
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
                        "value": "2"
                    }
                ],
                "4": [
                    {
                        "name": "Stra\u00dfe, Hausnummer",
                        "value": "Mendelstr. 24"
                    },
                    {
                        "name": "Angeschafft am",
                        "value": "13.02.1989"
                    }
                ],
                "5": [
                    {
                        "name": "Postleitzahl",
                        "value": "90429"
                    },
                    {
                        "name": "Ort",
                        "value": "N\u00fcrnberg"
                    }
                ],
                "6": [
                    {
                        "name": "Einheitswert-Aktenzeichen",
                        "value": "123456789"
                    }
                ],
                "7": [
                    {
                        "name": "Als Ferienwohnung genutzt",
                        "value": "2"
                    },
                    {
                        "name": "An Angeh\u00f6rige vermietet",
                        "value": "2"
                    }
                ],
                "8": [
                    {
                        "name": "Gesamtwohnfl\u00e4che",
                        "value": "53"
                    }
                ],
                "9": [
                    {
                        "name": "Mieteinnahmen ohne Umlagen",
                        "value": "3750"
                    }
                ],
                "13": [
                    {
                        "name": "Umlagen, verrechnet mit Erstattungen",
                        "value": "348"
                    }
                ],
                "21": [
                    {
                        "name": "Summe der Einnahmen",
                        "value": "4098"
                    }
                ],
                "33": [
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
                        "value": "5.5"
                    },
                    {
                        "name": "wie_vorjahr",
                        "value": "X"
                    },
                    {
                        "name": "betrag",
                        "value": "2252"
                    }
                ],
                "39": [
                    {
                        "name": "voll_abzuziehende",
                        "value": "223"
                    }
                ],
                "41": [
                    {
                        "name": "gesamtaufwand_vj",
                        "value": "659"
                    },
                    {
                        "name": "anteil_vj",
                        "value": "146"
                    }
                ],
                "42": [
                    {
                        "name": "vj_minus_4",
                        "value": "0"
                    }
                ],
                "43": [
                    {
                        "name": "vj_minus_3",
                        "value": "0"
                    }
                ],
                "44": [
                    {
                        "name": "vj_minus_2",
                        "value": "0"
                    }
                ],
                "45": [
                    {
                        "name": "vj_minus_1",
                        "value": "438"
                    }
                ],
                "47": [
                    {
                        "name": "verwaltungskosten",
                        "value": "813"
                    }
                ],
                "49": [
                    {
                        "name": "sonstige",
                        "value": "592"
                    }
                ],
                "22": [
                    {
                        "name": "summe_werbungskosten",
                        "value": "4464"
                    }
                ],
                "50": [
                    {
                        "name": "summe_werbungskosten",
                        "value": "4464"
                    }
                ],
                "23": [
                    {
                        "name": "ueberschuss",
                        "value": "-366"
                    }
                ],
                "24": [
                    {
                        "name": "zurechng_mann",
                        "value": "-329"
                    },
                    {
                        "name": "zurechng_frau",
                        "value": "-37"
                    }
                ]
            }
        }
    """
    def __init__(self, whg_id: int,
                 anlage_nr: int,
                 vj: int,
                 savepath: str,
                 dataprovider: DataProvider):
        self._whg_id = whg_id
        self._anlage_nr = anlage_nr
        self._vj = vj
        self._xdatadict = dict()  # Dictionary für die Schnittstellendaten
        self._dataProvider = dataprovider
        self._savePath = savepath
        self._fileIdent = ''
        self._log = None
        self._wohnungIdent = None
        self._stammdaten = None
        self._summe_einnahmen = 0
        self._summe_wk = 0
        self._logtext = ""

        self._xdatadict['vj'] = self._vj
        self._xdatadict['zeilen'] = dict()

    # def _checkForSavePath(self) -> None:
    #     """
    #     Setzt einen vom Default abweichenden Pfad.
    #     :param path: der gewünschte Pfad
    #     :return: None
    #     """
    #     jsonfile = self._savePath + "/anlagevconfig.json"
    #     try:
    #         f = open(jsonfile)
    #         j = json.load(f)
    #     except:
    #         pass # no file specified

    def startWork(self) -> str:
        """
        - prüft, ob es im current directory eine Config-Datei gibt,
          die einen alternativen SavePath vorgibt ### not yet implemented
        - sammelt die notwendigen Daten:
            - Mieteinnahmen
            - vereinnahmte Nebenkostenabschläge
            - bezahlte Hausgelder ohne Rücklagen-Zuführung
            - vereinnahmte und verausgabte NK- und Hausgeld-
              Abrechnungen (die das Vj-Vorjahr betreffen,
              aber im VJ berücksichtigt werden)
            - Rechnungen
            - sonstige Einnahmen und Ausgaben, Grundsteuer etc.
            - AfA-Informationen
        - erstellt aus diesen Daten ein Dictionary, das als
          JSON-Struktur in die spezifizierte Datei geschrieben
          wird

        :return: path and name of the written json file
        """

        #self._checkForSavePath()
        now = datetime.datetime.now()
        self._getStammdaten()
        data: XImmoStammdaten = self._stammdaten

        self._wohnungIdent = ''.join((data.plz, ' ', data.ort,
                                      ', ', data.strasse, ' / ', data.whg_bez))

        #prepare parts for logfile name:
        self._fileIdent = \
            data.plz + '_' + data.ort + '_' + data.strasse + '_' + data.whg_bez
        self._fileIdent = self._fileIdent.replace('/', '_')
        self._fileIdent = self._fileIdent.replace(' ', '')
        #create logfile name:
        logfile = self._savePath + '/log_' + self._fileIdent + '.txt'

        self._log = open(logfile, 'w')
        self._writeLog('Starte Verarbeitung um ' + str(now))
        self._writeLog('')
        self._writeLog(''.join(('>>>> ', self._wohnungIdent, ' <<<<')))
        self._writeLog('')

        self.getAnlageVData()
        if len(self._logtext) > 0:
            self._log.write(self._logtext)
        else:
            self._log.write("Keine Fehler entdeckt.")

        jsonfile = self._writeInterface()

        now = datetime.datetime.now()
        self._writeLog('\n\nBeende Verarbeitung um ' + str(now))
        self._log.close()

        return jsonfile

    def getAnlageVData(self) -> List:
        """
        Ermittelt die AnlageV-Daten für die übergebene Wohnung und das
        übergebene Veranlagungsjahr.
        :return: Eine Liste, die eine Fehlermeldung enthält (Index 0)
                 und das Dictionary mit den ermittelten Werten für die Anlage V
                 (Index 1).
                 Die Fehlermeldung ist leer, wenn keine Unstimmigkeiten entdeckt wurden.
        """
        self._getStammdaten()
        self._getZeile_1_to_8()
        self._getZeile_9_to_14_mtlEinn()
        self._sectionWerbungskosten()
        self._getZeile_23_24_ueberschuss_zurechnung()
        return (self._logtext, self._xdatadict)

    def _getStammdaten(self) -> None:
        self._stammdaten: XImmoStammdaten = \
            self._dataProvider.getAnlageVData_1_to_8(self._whg_id, self._vj)

    def _writeLog(self, txt: str) -> None:
        # txt = ''.join((txt, '\n'))
        # self._log.write(txt)
        self._logtext += txt
        self._logtext += "\n"

    def _writeInterface(self) -> str:
        jsonfile = self._savePath + "/anlagevdata_" + self._fileIdent + ".json"
        f = open(jsonfile, 'w')
        json.dump(self._xdatadict, f, indent=4)
        #f.write(x)
        f.close()
        return jsonfile

    def _writeRechnungenLog(self, rg: dict) -> None:
        """
        rg:
            {
                'rg_id': '48',
                'rg_datum': '30.08.2019',
                'rg_nr': 'BBB222',
                'betrag': '222.00',
                'verteilung_jahre': '1',
                'firma': 'zweierle',
                'bemerkung': 'fjsdlfdsjklfsdjil',
                'rg_bezahlt_am': '02.09.2019',
                'year_bezahlt_am': '2019',
                'voll_abzugsfaehig': True,
                'anteiliger_betrag': 222.00
            }
        """
        txt = ''.join(('\tFirma ', rg['firma'], ', Rg.Nr. ',
                        rg['rg_nr'], ' vom ', rg['rg_datum'], ', Betrag ', rg['betrag'],
                       '\n\t\tBezahlt am ', rg['rg_bezahlt_am'],
                       ', zu verteilen auf ', rg['verteilung_jahre'], ' Jahr(e). ',
                       '\n\t\tAnzusetzender Betrag: ', str(rg['anteiliger_betrag'])))
        self._writeLog(txt)

    def _getZeile_1_to_8(self):
        data: XImmoStammdaten = self._stammdaten
        self._log_missing_data_1_to_8(data)

        self._createZeile(1, ('Name', data.name))
        self._createZeile(2, ('Vorname', data.vorname))
        self._createZeile(3, ('Steuernummer', data.steuernummer),
                             ('lfd. Nr.', self._anlage_nr))
        z4str = data.strasse + ' / ' + data.whg_bez
        self._createZeile(4, ('Straße, Hausnummer', z4str),
                             ('Angeschafft am', data.angeschafft_am))
        self._createZeile(5, ('Postleitzahl', data.plz), ('Ort', data.ort))
        self._createZeile(6, ('Einheitswert-Aktenzeichen', data.einhwert_az))
        self._createZeile(7, ('Als Ferienwohnung genutzt', data.fewontzg),
                             ('An Angehörige vermietet', data.isverwandt))
        self._createZeile(8, ('Gesamtwohnfläche', '' if not data.qm else data.qm))

    def _log_missing_data_1_to_8(self, data: XImmoStammdaten) -> None:
        log = self._writeLog
        if not data.einhwert_az:
            log('Einheitswert-Aktenzeichen fehlt.')
        if data.fewontzg is None:
            log('Angabe fehlt, ob als Ferienwohnung genutzt.')
        if data.isverwandt is None:
            log('Angabe fehlt, ob das Objekt an Verwandte vermietet ist.')
        if data.qm is None:
            log('Angabe der Quadratmeter fehlt')

    def _getZeile_9_to_14_mtlEinn(self) -> None:
        mtlEinList: XMtlEinnahmenList = self._dataProvider.\
                getAnlageVData_9_to_14_mtlEinn(self._whg_id, self._vj)

        self._log_missing_data_9_to_14(mtlEinList)

        #count the number of months to be considered in each dictionary
        #and multiply them by netto_miete and nk_abschlag adjustments:
        netto_miete = nk_abschlag = 0
        for me in mtlEinList.getList():
            cnt = datehelper.getNumberOfMonths(me.gueltig_ab, me.gueltig_bis, self._vj)
            netto_miete += (float(me.netto_miete) * cnt) #Zeile 9
            nk_abschlag += (float(me.nk_abschlag) * cnt) #Zeile 13

        #Grundsteuer: wird ignoriert, da sie ein durchlaufender Posten ist

        #get nebenkosten adjustment of last vj
        nkAdjustList: List[Dict[str, str]] = self._dataProvider. \
            getAnlageVData_13_nkKorr(self._whg_id, self._vj)
        """
        nkAdjustList: list of dictionaries:
            [
                {
                    'sea_id': '11', 
                    'vj': '2018', 
                    'betrag': '93.00', 
                    'art_id': '3', 
                    'art': 'Nebenkostennachzahlung (Mieter->Verm.)',
                    'ein_aus': 'e'
                }
            ]
        """
        adjustment = 0
        for adjust in nkAdjustList:
            betrag = float(adjust['betrag'])
            if adjust['ein_aus'] == 'a': betrag *= -1
            adjustment += betrag

        nk_eff = nk_abschlag + adjustment
        einnahme = round(netto_miete + nk_eff) #Zeile 21

        self._createZeile(9, ('Mieteinnahmen ohne Umlagen', round(netto_miete)))
        self._createZeile(13, ('Umlagen, verrechnet mit Erstattungen', round(nk_eff)))
        self._createZeile(21, ('Summe der Einnahmen', einnahme))
        self._summe_einnahmen = einnahme

    def _log_missing_data_9_to_14(self, xmelist: XMtlEinnahmenList) -> str:
        log = self._writeLog
        if len(xmelist.getList()) == 0:
            log('!Keine monatlichen Einnahmen vorhanden!')
            return

        firstgueltigab = lastgueltigbis = ''
        for xme in xmelist.getList():
            if firstgueltigab == '' or xme.gueltig_ab < firstgueltigab:
                firstgueltigab = xme.gueltig_ab
            if lastgueltigbis == '' or xme.gueltig_bis > lastgueltigbis:
                lastgueltigbis = xme.gueltig_bis
            if not xme.netto_miete:
                log('Keine Nettomiete angegeben für den Zeitraum vom ' +
                    xme.gueltig_ab + ' bis ' + xme.gueltig_bis)
            if not xme.nk_abschlag:
                log('Kein Nebenkostenabschlag angegeben für den Zeitraum vom ' +
                    xme.gueltig_ab + ' bis ' + xme.gueltig_bis)

        vjstart = ''.join(('01.01.', str(self._vj)))
        if datehelper.compareEurDates(
                datehelper.convertIsoToEur(firstgueltigab), vjstart) > 0:
            log('Mieteinnahmen beginnen erst ab ' + firstgueltigab)
        vjend = ''.join(('31.12.', str(self._vj)))
        if datehelper.compareEurDates(
                datehelper.convertIsoToEur(lastgueltigbis), vjend) < 0:
            log('Mieteinnahmen enden am ' + lastgueltigbis)

    def _sectionWerbungskosten(self):
        self._getZeile_33_to_35_afa()
        self._getZeile_39_to_45_erhaltung()
        self._getZeile_46_grundsteuer()
        self._getZeile_47_verwaltkosten()
        self._getZeile_49_sonstiges()
        self._getZeile_22_und_50_summe_wk()

    def _getZeile_33_to_35_afa(self):
        afa: XAfa = self._dataProvider.\
            getAnlageVData_33_to_35_afa(self._whg_id, self._vj)
        self._log_missing_data_33_to_35(afa)

        afa_art = 'linear' if afa.lin_deg_knz == 'l' else 'degressiv'
        linear = 'X' if afa.lin_deg_knz == 'l' else ' '
        degressiv = ' ' if linear == 'X' else 'X'
        wie_vj = 'X' if afa.afa_wie_vorjahr == 'Ja' else ' '
        proz = '' if (afa.prozent == '0' or afa.prozent == '0.0') \
            else str(float(afa.prozent))
        self._createZeile(33,
                          ('linear', linear),
                          ('degressiv', degressiv),
                          ('prozent', proz),
                          ('wie_vorjahr', wie_vj),
                          ('betrag', afa.betrag))

        self._summe_wk += int(afa.betrag)

        #todo: createZeile 34, 35

    def _log_missing_data_33_to_35(self, afa: XAfa):
        log = self._writeLog
        if not afa.lin_deg_knz:
            log("Afa-Art nicht angegeben. Muss 'linear' oder 'degressiv' sein.")
        elif afa.lin_deg_knz == 'd' and not afa.prozent:
            log("Prozentsatz fehlt bei Afa-Art 'degressiv'.")

        if not afa.afa_wie_vorjahr:
            log("Angabe ob 'Afa wie Vorjahr' fehlt.")

        if not afa.betrag:
            log("Afa-Betrag fehlt.")

    def _getZeile_36_to_37_kredit(self) -> None:
        #todo
        pass

    def _getZeile_38_renten(self) -> None:
        #todo
        pass

    def _getZeile_39_to_45_erhaltung(self) -> None:
        # eigenen Absatz für die als Nachweis
        # benötigten Rechnungen im Log schreiben:
        txt = "\nFolgende Rechnungen werden zum Nachweis benötigt:\n"
        self._writeLog(txt)

        #die für dieses Vj relevanten Rechnungen finden:
        rgfilter = RechnungFilter(self._whg_id, self._vj, self._dataProvider)
        rgfilter.registerCallback(self._writeRechnungenLog)
        aufwaende: XErhaltungsaufwand = rgfilter.getErhaltungsaufwaende()

        if aufwaende.voll_abzuziehen == 0:
            self._writeLog('Keine voll abziehbaren Aufwände im Vj.')

        # die notwendigen Einträge in die Schnittstellendatei machen,
        # auch wenn der Aufwand == 0:
        self._createZeile(39, ('voll_abzuziehende',
                               round(aufwaende.voll_abzuziehen)))
        self._summe_wk += aufwaende.voll_abzuziehen

        if aufwaende.vj_gesamtaufwand == 0:
            self._writeLog('Kein verteilbarer Aufwand im Vj (Zeile 41)')

        z = 41 #erste Zeile für zu verteilende Erhalt.Aufwendungen
        # in Zeile 41 kommt der Gesamtaufwand des Vj und der Anteil für das Vj:
        self._createZeile(z,
                          ('gesamtaufwand_vj', round(aufwaende.vj_gesamtaufwand)),
                          ('anteil_vj', round(aufwaende.abzuziehen_vj)))
        self._summe_wk += aufwaende.abzuziehen_vj

        z += 1 # in die nächste Zeile (42) kommt der Anteil für Vj - 4 Jahre
        for y in range(4, 0, -1):
            ident = ''.join(('vj_minus_', str(y)))
            aufwand = aufwaende.get_abzuziehen_aus_vj_minus(y)
            self._createZeile(z, (ident, round(aufwand)))
            self._summe_wk += aufwand
            z += 1

    def _getZeile_46_grundsteuer(self) -> None:
        gs: int = self._dataProvider.getAnlageVData_46_grundsteuer(
                    self._whg_id, self._vj)
        if gs == 0:
            self._writeLog('Keine Grundsteuer für diese Wohnung eingetragen.')

        self._createZeile(46, ('grundsteuer_txt', 'Grundsteuer'),
                              ('grundsteuer', gs))
        self._summe_wk += gs

    def _getZeile_47_verwaltkosten(self) -> None:
        """
        Zeile 47 enthält nichts weiter als das um
        Nach- und Rückzahlungen bereinigte Hausgeld - ohne Zuführung Rücklagen.
        """
        vwkost: int = self._dataProvider.\
                getAnlageVData_47_hausgeld(self._whg_id, self._vj)
        if vwkost == 0:
            self._writeLog('Keine Verwaltungskosten (Hausgelder) im Vj (Zeile 47).')
        self._createZeile(47, ('hausgeld', 'Hausgeld OHNE Zuführg. Rücklagen'),
                              ('verwaltungskosten', vwkost))
        self._summe_wk += vwkost

    def _getZeile_49_sonstiges(self) -> None:
        """
        Zeile 49 enthält z.B. Porto, Fahrtkosten (ETVn), RA-Kosten, H&G-Beiträge.
        In der Tabelle sonstige_ein_aus ist das die kostenart 'sonst_kost'
        :return: None
        """
        sonstige: int = self._dataProvider.\
            getAnlageVData_49_sonstiges(self._whg_id, self._vj)
        if sonstige == 0:
            self._writeLog('Keine sonstigen Kosten im Vj (Zeile 49).')
        self._createZeile(49, ('sonst_kost', 'Porto, Fahrtkosten, H&G etc.'),
                              ('sonstige', sonstige))
        self._summe_wk += sonstige

    def _getZeile_22_und_50_summe_wk(self) -> None:
        summe_wk = round(self._summe_wk)
        self._createZeile(22, ('summe_werbungskosten', summe_wk))
        self._createZeile(50, ('summe_werbungskosten', summe_wk))

    def _getZeile_23_24_ueberschuss_zurechnung(self) -> None:
        ueberschuss = round(self._summe_einnahmen - self._summe_wk)
        self._createZeile(23, ('ueberschuss', ueberschuss))

        zurechng_mann, zurechng_frau = \
            self._dataProvider.getAnlageVData_24_zurechnung(self._whg_id) # prozentsätze
        zurechng_mann = int(zurechng_mann)
        zurechng_frau = int(zurechng_frau)
        self._log_missing_data_24(zurechng_mann, zurechng_frau)

        betrag_mann = zurechng_mann/100 * ueberschuss
        betrag_frau = ueberschuss - betrag_mann
        self._createZeile(24, ('zurechng_mann', round(betrag_mann)),
                              ('zurechng_frau', round(betrag_frau)))

    def _log_missing_data_24(self, zurechng_mann: int, zurechng_frau: int):
        log = self._writeLog
        if zurechng_frau == 0 and zurechng_mann == 0:
            log('Angabe fehlt, wie der Überschuss aufzuteilen ist (Zeile 24).')
        if zurechng_mann + zurechng_frau != 100:
            log('Die Summe der Zurechnungen ergibt nicht 100% (Zeile 24).')

    def _createZeile(self, nr: int, *args):
        """
        create a dictionary representing the fields in a Zeile of Anlage V
        :param args: each arg is a list containing a key (field's name)
                     and a value (field's value)
                     e.g. ('Straße, Hausnummer', 'Mendelstr. 24')
        :return: dict:
            {
                "zeile": 4,
                "felder": [
                    {
                        "name": "Straße, Hausnummer",
                        "value": "Mendelstr. 24"
                    },
                    {
                        "name": "Angeschafft am",
                        "value": "13.05.1997"
                    }
                ]
            }
        """
        feldlist = list()
        for item in args:
            d = dict()
            d['name'] = item[0]
            d['value'] = str(item[1])
            feldlist.append(d)

        self._xdatadict['zeilen'][nr] = feldlist

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class RechnungFilter:
    def __init__(self, whg_id: int, vj: int, dataprovider: DataProvider):
        self._whg_id = whg_id
        self._vj = vj
        self._dataprovider = dataprovider
        self._callback = None

    def registerCallback(self, cb) -> None:
        # the function to register has to accept a dictionary
        # (representing a rechnung)
        self._callback = cb

    def getErhaltungsaufwaende(self):
        rechnungen: List[Dict[str, str]] = self._dataprovider.getRechnungsUebersicht(self._whg_id)
        """
        rechnungen: list of dictionaries: 
            {
                'rg_id': '48', 
                'rg_datum': '30.08.2019', 
                'rg_nr': 'BBB222', 
                'betrag': '222.00',
                'verteilung_jahre': '1', 
                'firma': 'zweierle', 
                'bemerkung': 'fjsdlfdsjklfsdjil',
                'rg_bezahlt_am': '02.09.2019',
                'year_bezahlt_am': '2019'
            }
        """
        aufwand = XErhaltungsaufwand()
        for rg in rechnungen:
            year_bezahlt_am = 0 if not rg['year_bezahlt_am'] else int(rg['year_bezahlt_am'])
            if not rg['year_bezahlt_am']: #Rechnung noch nicht bezahlt
                pass
            elif year_bezahlt_am > self._vj:
                #Rechnung noch nicht relevant, erst nach dem Vj bezahlt
                pass
            elif year_bezahlt_am + int(rg['verteilung_jahre']) <= self._vj:
                # Rechnung nicht mehr relevant - schon im Vor-Vj bezahlt oder
                # fertig abgeschrieben
                pass
            else:
                #in diesen Zweig läuft alles, was berücksichtigt werden soll,
                #entweder 'voll_abzuziehen' im Vj oder anteilig
                betrag = float(rg['betrag'])
                verteilung_jahre = int(rg['verteilung_jahre'])
                if year_bezahlt_am == self._vj and verteilung_jahre == 1:
                    aufwand.voll_abzuziehen += betrag
                    self._doCallback(rg, True, betrag)
                elif verteilung_jahre > 1:
                    # Versorgung der Zeilen 41 bis 45
                    if year_bezahlt_am == self._vj:
                        aufwand.vj_gesamtaufwand += betrag
                    anteil = betrag / verteilung_jahre
                    years = self._vj - year_bezahlt_am
                    aufwand.addto_abzuziehen_aus_vj_minus(years, anteil)
                    self._doCallback(rg, False, anteil)

        aufwand.roundAufwaende()
        return aufwand

    def _doCallback(self, rg: dict, vollAbz: bool, betrag: float):
        if self._callback:
            rg['voll_abzugsfaehig'] = vollAbz
            rg['anteiliger_betrag'] = betrag
            self._callback(rg)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def rechnungfiltercallback(rg: dict):
    print("logge: ", rg)

def test():
    from business import DataProvider, DataError
    dp = DataProvider()
    dp.connect('d02bacec')

    avdata = AnlageVData(2, 2, 2018,
                         '/home/martin/Projects/python/Wohnungsverwaltung/anlagen_v/2018',
                         dp)
    avdata.startWork()

    # filter = RechnungFilter(1, 2018, dp)
    # filter.registerCallback(rechnungfiltercallback)
    # betraege: dict = filter.getBetraege()
    # print(betraege)

if __name__ == '__main__':
    test()