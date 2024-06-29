from typing import Dict

from pandas import DataFrame, Series
from yfinance.scrapers.quote import FastInfo

from base.interfaces import XBase
from imon.enums import Period, Interval

class XDepotPosition( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.id = 0 # Primärschlüssel in Tabelle depotposition
        self.isin = ""
        self.ticker = ""
        self.wkn = ""
        self.basic_index = ""
        self.name = ""
        self.gattung = ""
        self.ter = 0.0  # annual total expense ratio
        self.waehrung = ""
        self.flag_acc = False
        self.beschreibung = ""
        self.toplaender = ""
        self.topfirmen = ""
        self.topsektoren = ""
        self.anteil_usa = 0  # Anteil von US-Firmen
        self.history:Series = None
        self.history_period = Period.unknown
        self.history_interval = Interval.unknown
        self.dividends:Series = None # Dividenden, die im Lauf von history_period ausgeschüttet wurden.
        self.dividend_period = 0.0 # Summe der Dividenden PRO STÜCK, die während history_period ausgeschüttet wurden
        self.dividend_yield = 0.0 # Dividenden-Rendite
        # self.dividend_vj = 0  # Die Summe der Dividenden, die für diese Depotposition im Vorjahr ausbezahlt wurde
        self.dividend_paid_period = 0  # Die Summe der Dividenden, die für diese Depotposition in der eingestellten
                                       # Periode ausbezahlt wurde
        self.dividend_paid_lfd_jahr = 0 # Summe der Dividendenzahlungen, die für diese Depotposition im lfd. Jahr
                                        # ausbezahlt wurden
        # self.low_price = 0.0 # todo: der niedrigste Preis in der Periode
        # self.high_price = 0.0 # todo: der höchste Preis in der Periode
        self.stueck = 0 # Restbestand (Käufe und Verkäufe saldiert)
        #self.gesamtkaufpreis = 0 #Kaufpreis des gesamten Bestands -- eigentlich irrelevant: wenn von 995 Stück 900 verkauft werden,
                                 # was soll dann der Gesamtkaufpreis aussagen?
        self.einstandswert_restbestand = 0 # Einstandswert des (Rest-)Bestandes, ermittelt nach der Formel:
                                      # Stückzahl * durchschnittlicher Stück-Kaufpreis
        self.preisprostueck = 0.0 # durchschnittl. Preis pro Stück nach der Formel: Gesamtkaufpreis / Stück
        self.maxKaufpreis = 0.0 # Max. Kaufpreis / Stück
        self.minKaufpreis = 0.0 # Min. Kaufpreis / Stück
        self.erster_kauf = "" # DAtum des ersten Kaufs
        self.letzter_kauf = "" # Datum des letzten Kaufs
        self.gesamtwert_aktuell = 0 # Stück * kurs_aktuell
        self.anteil_an_summe_gesamtwerte = 0  # wie hoch der Anteil dieser Depotposition an der Gesamtsumme der
                                              # im IMON befindlichen Positionen ist (in Prozent)
        self.kurs_aktuell = 0.0
        self.delta_proz = 0.0 #prozentualer Unterschied zwischen preisprostueck und kurs_aktuell
        self.fastInfo:FastInfo = None # fast_info aus yfinance.Ticker
        self.delta_kurs_1_percent = 0.0 # Kursentwicklung seit letztem Close in Prozent
        # self.avg_kurs_50 = 0.0 # average Kurs letzte 50 Tage
        # self.avg_kurs_200 = 0.0  # average Kurs letzte 200 Tage
        self.depot_id = ""
        self.bank = ""
        self.depot_nr = ""
        self.depot_vrrkto = ""
        if valuedict:
            self.setFromDict( valuedict )

class XDelta( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.id = 0
        self.name = ""
        self.wkn = ""
        self.isin = ""
        self.ticker = ""
        self.delta_stck = 0
        self.delta_datum = ""
        self.preis_stck = 0.0
        self.order_summe = 0.0 # delta_stck * preis_stck (Kurs, zu dem gekauft wurde)
        self.verkauft_stck = 0 # wieviel Stück von einem früheren, bereits existenten Kauf-Satz verkauft wurden
        self.verkaufskosten = 0.0 # Kosten, die bei einem Verkauf anfallen. Werden steuerlich berücksichtigt bei der
                                  # Ermittlung des Veräußerungsgewinnes
        self.bemerkung = ""
        if valuedict:
            self.setFromDict( valuedict )

class XDividend( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self )
        self.name = ""
        self.wkn = ""
        # self.isin = ""
        self.ticker = ""
        self.pay_day = "" # Datum der Dividendenzahlung
        self.div_pro_stck = 0.0 # Div.Zahlunge pro Stück
        self.div_summe = 0.0 # Div.Zahlung pro Stück * Stück unter Berücksichtigung des am Zahltag vorhandenen Bestands.
        if valuedict:
            self.setFromDict( valuedict )

class XDetail(XBase):
    """
    Wird für die Detail-Anzeige im InfoPanel benötigt (nach Drücken des Detail-Buttons).
    Enthält den Ausschnitt der Daten von XDepotPosition, die nicht im InfoPanel angezeigt werden.
    """
    def __init__(self):
        XBase.__init__( self )
        self.basic_index = ""
        self.beschreibung = ""
        self.toplaender = ""
        self.topfirmen = ""
        self.topsektoren = ""
        self.bank = ""
        self.depot_nr = ""
        self.depot_vrrkto = ""
