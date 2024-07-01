import math
import threading
from operator import itemgetter, attrgetter
from typing import List, Dict, Iterable

from pandas import DataFrame, Series
import pandas as pd
from yfinance.scrapers.quote import FastInfo

import datehelper
from base.basetablemodel import BaseTableModel, SumTableModel
from data.db.investmonitordata import InvestMonitorData
from data.finance.tickerhistory import Period, Interval, TickerHistory, SeriesName
from imon.enums import InfoPanelOrder
from interface.interfaces import XDepotPosition, XDelta, XDetail, XDividend
from imon.definitions import DATABASE_DIR, DEFAULT_PERIOD, DEFAULT_INTERVAL

# class WorkerSignals( QObject ):
#     finished = Signal()
#     error = Signal( tuple )
#     result = Signal( object )
#
# ##############################################################
# class Worker( QRunnable ):
#     def __init__( self, fn, wkn_ticker_list:List[Dict], allOrders:List[XDelta] ):
#         super( Worker, self ).__init__()
#         # Store constructor arguments (re-used for processing)
#         self.fn = fn
#         self._wkn_ticker_list = wkn_ticker_list
#         self._allOrders = allOrders
#         self.signals = WorkerSignals()
#
#     @Slot()
#     def run( self ):
#         try:
#             result = self.fn( self._wkn_ticker_list, self._allOrders )
#         except:
#             traceback.print_exc()
#             exctype, value = sys.exc_info()[:2]
#             self.signals.error.emit( (exctype, value, traceback.format_exc()) )
#         else:
#             self.signals.result.emit( result )  # Return the result of the processing
#         finally:
#             self.signals.finished.emit()  # Done

class InvestMonitorLogic:
    #summe_gesamtwerte = 0.0
    def __init__( self ):
        self._db = InvestMonitorData()
        self._tickerHist = TickerHistory()
        self._defaultPeriod = DEFAULT_PERIOD #Period.oneYear
        self._defaultInterval = DEFAULT_INTERVAL
        self._minPeriod = Period.oneDay
        self._minInterval = Interval.oneMin

    # def saveMyHistories( self ):
    #     histDf:DataFrame = self.getMyTickerHistories( self._defaultPeriod, self._defaultInterval )
    #     histDf.to_pickle( DATABASE_DIR + "/histories.df" ) # + datehelper.getCurrentDateIso() )
    #     actDf:DataFrame = self.getMyTickerHistories( Period.oneDay, Interval.oneMin )
    #     actDf.to_pickle( DATABASE_DIR + "/todayhistories.df" )
    #
    # @staticmethod
    # def loadMyHistories( todayHistory:bool = False) -> DataFrame:
    #     if todayHistory:
    #         df = pd.read_pickle( DATABASE_DIR + "/todayhistories.df" )
    #     else:
    #         df = pd.read_pickle( DATABASE_DIR + "/histories.df" )
    #     return df
    #
    # @staticmethod
    # def getHistory( ticker:str, series:SeriesName, dfAllHistories:DataFrame=None ) -> Series:
    #     """
    #     Ermittelt aus dem DataFrame, der alle Historien aller Ticker enthält, die gewünschte Serie.
    #     !!! Ist dfAllHistories nicht angegeben, wird der DataFrame ***DER AUF PLATTE GESPEICHERT IST*** geladen. !!!
    #     :param ticker:
    #     :param series:
    #     :param dfAllHistories:
    #     :return:
    #     """
    #     if not dfAllHistories:
    #         dfAllHistories = InvestMonitorLogic.loadMyHistories()
    #     allSeries:DataFrame = dfAllHistories[series.value]
    #     tickerhist:Series = allSeries[ticker]
    #     return tickerhist

    # def getMyTickerHistories( self, period=Period.oneYear, interval=Interval.oneWeek ):
    #     # Alle Ticker aus dem Depot holen:
    #     tickerlist = self._db.getAllMyTickers()
    #     # Mit der TickerList die Historien holen:
    #     tickerHistories: DataFrame = self._tickerHist.getTickerHistoriesByPeriod( tickerlist,
    #                                                                               period=period,
    #                                                                               interval=interval )
    #     return tickerHistories

    # @staticmethod
    # def getSummeGesamtwerte():
    #     return InvestMonitorLogic.summe_gesamtwerte

    def getDepotPosition( self, ticker:str, period=Period.oneYear, interval=Interval.fiveDays ) -> XDepotPosition:
        """
        Liefert alle Daten für die Depotposition <ticker>.

        :param ticker:
        :param period:
        :param interval:
        :return:
        """
        deppos:XDepotPosition = self._db.getDepotPosition( ticker )
        #self.provideTickerHistories( [deppos,], period=period, interval=interval )
        self._provideOrderData( deppos )
        self.provideFastInfo( [deppos,] )
        tickerHistory:DataFrame = self._tickerHist.getTickerHistoryByPeriod( ticker, period, interval )
        closeHist:Series = tickerHistory[SeriesName.Close.value]
        dividends:Series = tickerHistory[SeriesName.Dividends.value]
        self._provideWertpapierData( deppos, closeHist, dividends )
        return deppos

    def getDepotPositions( self, period:Period, interval:Interval, TEST=False ) -> List[XDepotPosition]:
        """
        Liefert die Depot-Positionen inkl. der Bestände und der Kursentwicklung in der Default-Periode und
        im Default-Zeitintervall
        :return:
        """
        # Depotpositonen holen:
        if TEST:
            poslist = list()
            for i in range( 0, 5 ):
                xdeppos = XDepotPosition()
                poslist.append( xdeppos )
            return poslist
        ###################################
        poslist:List[XDepotPosition] = self._db.getDepotPositions()
        # Wertpapierdaten in Positionen eintragen (Kursverlauf, Dividenden etc.)
        # thread = threading.Thread( target=InvestMonitorLogic.provideFastInfo, args=(poslist,) )
        # thread.start()
        poslist = self.provideTickerHistories( poslist, period, interval )
        # thread.join()
        return poslist

    @staticmethod
    def provideFastInfo( poslist:Iterable[XDepotPosition] ):
        """
        Wird von getDepotPositions() in einem separaten Thread aufgerufen und versorgt
        in aas Attribut fastInfo in allen übergebenen XDepotPositon-Objekten
        :param poslist: Iterable of XDepotPosition
        :return:
        """
        for deppos in poslist:
            deppos.fastInfo =TickerHistory.getFastInfo( deppos.ticker )

    def provideTickerHistories( self, poslist:List[XDepotPosition], period:Period, interval:Interval ) -> List[XDepotPosition]:
        tickerlist = [pos.ticker for pos in poslist]
        tickerHistories: DataFrame = self._tickerHist.getTickerHistoriesByPeriod( tickerlist,
                                                                                  period=period,
                                                                                  interval=interval )
        tickerHistories = self._checkForNaN( tickerHistories )
        closeDf: DataFrame = tickerHistories[SeriesName.Close.value]
        dividendsDf: DataFrame = tickerHistories[SeriesName.Dividends.value]
        for deppos in poslist:
            self._provideOrderData( deppos )
            try:
                if isinstance( closeDf, Series ):
                    closeHist:Series = closeDf
                    dividends: Series = dividendsDf
                else:
                    closeHist: Series = closeDf[deppos.ticker]
                    dividends: Series = dividendsDf[deppos.ticker]
            except Exception as ex:
                print( deppos.ticker, " not found in DataFrame closeDf" )
                return poslist

            self._provideWertpapierData( deppos, closeHist, dividends )
        return poslist

    @staticmethod
    def _checkForNaN( df:DataFrame ) -> DataFrame:
        row = df.tail(1) # damit haben wir die letzte Zeile des DataFrame, also die letzten Values aller Series (columns)
        for name, cellValues in row.items():
            # name: Spaltenkopf, z.B. EZTQ.F
            # cellValues: die Values von row
            if math.isnan( cellValues[0] ):
                df = df[:-1]
                break
        return df

    def _provideWertpapierData( self, deppos:XDepotPosition, closeHist:Series, dividends:Series ) -> None:
        deppos.history = closeHist
        deppos.history_period = self._defaultPeriod
        deppos.history_interval = self._defaultInterval
        deppos.dividends = dividends
        deppos.dividend_yield = 0.0

        orig_currency = self._provideFastInfoData( deppos )
        if not orig_currency:
            return
        if deppos.kurs_aktuell == 0:
            print( deppos.wkn, "/", deppos.ticker,
                   ": _provideWertpapierData(): call to getKursAktuellInEuro() failed.\nNo last_price availabel.")

        deppos.dividend_period = self._getSumDividends( deppos.dividends ) # Summe der Div. PRO STÜCK während d. Periode
        if orig_currency != "EUR":
            deppos.history = self._convertSeries( deppos.history, orig_currency )
            if deppos.dividend_period > 0:
                deppos.dividends = self._convertSeries( deppos.dividends, orig_currency )
                deppos.dividend_period = \
                    round( TickerHistory.convertToEuro( deppos.dividend_period, orig_currency ), 3 )
        if deppos.dividend_period > 0:
            first_kurs_period = closeHist.array[0]
            deppos.dividend_yield = self._computeDividendYield( first_kurs_period, deppos.dividend_period )
        self._provideGesamtwertAndDelta( deppos )
        deltas = self._db.getDeltas( deppos.wkn )
        deppos.dividend_paid_period = \
            self._getPaidDividends( deppos.dividends, deltas ) # Summe der Dividendenzahlungen,
                                                               # die während d. Perdiode
                                                               # auf meinen Bestand gezahlt wurden

    def _getPaidDividends( self, dividends:Series, deltas:List[XDelta], callback=None ) -> int:
        """
        Ermittelt die Dividendenzahlungen, die für <deppos> gemäß Eintragungen in <dividends> angefallen sind.
        Für jede Dividendenzahlung wird nur der zum Zahlungszeitpunkt vorhandene Depotbestand berücksichtigt.
        :param dividends: Die Dividenden-Serie. Es wird vorausgesetzt, dass sie in Euro übergeben wird.
        :param deltas: Alle Orders, die sich auf <wkn> beziehen
        :param callback: Funktion, die aufgerufen wird für jede Dividendensumme, die durch _computeDividendOnBestand
                        ausgerechnet wurde.
                        Die Callback-Funktion muss 3 Argumente empfangen: den Div.-Zahltag (ISO), die Div. pro Stück
                        und die Gesamt-Dividende, die auf den am Zahltag vorhandenen Bestand ausgezahlt wurde.
        :return:
        """
        deltas.sort( key=attrgetter( "delta_datum" ) )
        sum_dividends = 0
        for pay_ts, value in dividends.items():
            if value > 0:
                #print( "paid: ", str(pay_ts)[:10], ": ", value )
                # den Depotbestand der Position <deppos> zum Datum <paydate> ermitteln:
                div_pro_stck = float( value )
                pay_day = str( pay_ts )[:10]
                div = self._computeDividendOnBestand( deltas, div_pro_stck, pay_day )
                if callback:
                    callback( pay_day, div_pro_stck, div )
                sum_dividends += div
        return sum_dividends

    @staticmethod
    def _computeDividendOnBestand( deltas:List[XDelta], dividend:float, paydate:str ) -> int:
        """
        Errechnet die Dividende, die auf den am Ausschüttungstag <paydate> vorhandenen Bestand bezahlt wurde.
        :param deltas: Alle Käufe u. Verkäufe eines bestimmten Fonds (oder Aktie)
                       Es wird vorausgesetzt, dass deltas nach <delta_datum> aufsteigend sortiert ist.
        :param dividend: an paydate bezahlte Dividende pro Stück
        :param paydate: Ausschüttungstag (ISO-Format)
        :return:
        """
        summe_stck = 0
        for delta in deltas:
            if delta.delta_datum < paydate:
                summe_stck += delta.delta_stck # gekaufte Stücke werden addiert, verkaufte subtrahiert.
                                               # <delta.verkauft_stck> braucht nicht berücksichtigt werden,
                                               # da sie nur eine Aufteilung der Verkäufe (die hier subtrahiert werden)
                                               # auf die Käufe darstellen (im Sinne verfügbarer Stücke)
            else:
                break
        return int(round( summe_stck * dividend, 2 ) )

    @staticmethod
    def _provideGesamtwertAndDelta( deppos:XDepotPosition ):
        deppos.gesamtwert_aktuell = int( round( deppos.stueck * deppos.kurs_aktuell, 2 ) )
        #if deppos.gesamtkaufpreis > 0:
        if deppos.einstandswert_restbestand > 0:
            deppos.delta_proz = round( (deppos.gesamtwert_aktuell / deppos.einstandswert_restbestand - 1) * 100, 2 )

    @staticmethod
    def _getSumDividends( dividends: Series ) -> float:
        div: float = sum( [v for v in dividends.values if not math.isnan( v )] )
        return round( div, 3 )

    def updateWertpapierData( self, x:XDepotPosition, period:Period, interval:Interval ) -> None:
        """
        Ermittelt für das übergebene Wertpapier (repräsentiert durch <x>) die Historie gem. <period> und <interval>
        und schreibt diese Werte in <x> (x.history, x.history_period, x.history_interval.
        :param x: die zu aktualisierende Depot-Position
        :param period:
        :param interval:
        :return:
        """
        df:DataFrame = self._tickerHist.getTickerHistoryByPeriod( x.ticker, period, interval )
        self._provideWertpapierData( x, df[SeriesName.Close.value], df[SeriesName.Dividends.value] )
        x.history_period = period
        x.history_interval = interval

    def updateKursAndDivYield( self, deppos:XDepotPosition ):
        self._provideFastInfoData( deppos )
        if deppos.kurs_aktuell > 0 and deppos.dividend_period > 0:
            first_kurs_period = deppos.history.array[0]
            # deppos.dividend_yield = self._computeDividendYield( deppos.kurs_aktuell, deppos.dividend_period )
            deppos.dividend_yield = self._computeDividendYield( first_kurs_period, deppos.dividend_period )

    @staticmethod
    def _computeDividendYield( kurs:float, dividend:float ) -> float:
        divYield = dividend / kurs
        return round( divYield*100, 3 )

    @staticmethod
    def getSimulatedDividendYield( kurs_aktuell:float, dividends:Series ) -> float:
        """
        Berechnet die theoretische Dividendenrendite auf Basis des aktuellen Kurses und des Durchschnitts der
        Dividendenzahlungen in der eingestellten Periode
        :return: die Rendite in Prozent, gerundet auf 2 Stellen genau
        """
        sumDiv = 0.0
        startDayIso = ""
        endDayIso = ""
        for index, value in dividends.items():
            dateIso = str(index)[:10]
            if not startDayIso:
                startDayIso = dateIso
            endDayIso = dateIso
            if value and value > 0:
                sumDiv += value
        days = datehelper.getNumberOfDays3( startDayIso, endDayIso )
        years = days/365
        if years > 0:
            avg_annual_yield = sumDiv / years
            return round( avg_annual_yield/kurs_aktuell*100, 2 )
        return 0.0

    def _provideFastInfoData( self, deppos:XDepotPosition ) -> str:
        """
        Ermittelt die yfinance.Ticker.fast_info des Wertpapiers und schreibt sie in <deppos>
        Transformiert den letzten Kurs (fast_info.last_price) in EUR, wenn er nicht in EUR geliefert wird.
        :param deppos: das XDepotPosition-Objekt, das mit den FastInfo-Daten versorgt werden soll.
        :return: die ursprüngliche Währung (EUR oder Fremdwährung, die konvertiert wurde)
        """
        fastInfo: FastInfo = self._tickerHist.getFastInfo( deppos.ticker )
        if fastInfo:
            deppos.fastInfo = fastInfo
            last_price = fastInfo.last_price
            currency = str( fastInfo.currency )
            if currency != "EUR":
                last_price = TickerHistory.convertToEuro( last_price, currency )
            deppos.kurs_aktuell = round( last_price, 3 )
            try:
                # wegen des lazy loading der fast_info geht das hin und wieder schief
                previous_close = fastInfo.previous_close
                if previous_close:
                    deltaPrice = fastInfo.last_price - previous_close
                    # Verhältnis des akt. Kurses zum Schlusskurs des Vortages:
                    deppos.delta_kurs_1_percent = round( deltaPrice / previous_close * 100, 2 )
                else:
                    deppos.delta_kurs_1_percent = 0
                    print( deppos.ticker, ": fastInfo.previous_close is None." )
            except Exception as ex:
                print( deppos.ticker, ": Zugriff auf Feld previous_close nicht möglich." )
            return currency
        else:
            print( "Ticker '%s':\nNo FastInfo available" % deppos.ticker )
            return ""

    def getKursAktuellInEuro( self, ticker: str ) -> (float, str):
        """
        Ermittelt den letzten Kurs des Wertpapiers.
        Transformiert ihn in EUR, wenn er nicht in EUR geliefert wird.
        :param ticker:
        :return: den letzten Kurs in Euro, gerundet auf 3 Stellen hinter dem Komma
                 UND die ursprüngliche Währung (EUR oder Fremdwährung, die konvertiert wurde)
        """
        fastInfo: FastInfo = self._tickerHist.getFastInfo( ticker )
        if fastInfo:
            last_price = fastInfo.last_price
            currency = str( fastInfo.currency )
            if currency != "EUR":
                last_price = TickerHistory.convertToEuro( last_price, currency )
            return round( last_price, 3 ), currency
        else:
            print( "Ticker '%s':\nNo FastInfo available" % ticker )
            return 0, ""

    @staticmethod
    def _convertSeries( series:Series, currency:str ):
        """
        Übersetzt alle Werte in series.values in Euro und schreibt sie in eine Liste.
        Macht daraus und aus series.index eine neue Series und gibt diese zurück.
        Das muss sein, damit die Beschriftung der y-Achse im Graphen stimmt.
        :param series:
        :param currency: Währung wie in FastInfo eingetragen. (GBp also noch nicht in GBP umgewandelt.)
        :return:
        """
        values = series.values
        vlist = list()
        for value in values:
            if not math.isnan( value ):
                value = TickerHistory.convertToEuro( value, currency )
            else:
                value = 0
            vlist.append( value )
        index = series.index
        serNew = Series(vlist, index)
        return serNew

    def _provideOrderData( self, deppos: XDepotPosition ):
        """
        Holt zur übergebenen Depotposition die delta-Daten aus der DB und trägt sie ein
        :param deppos:
        :return:
        """
        deltalist: List[XDelta] = self._db.getDeltas( deppos.wkn ) # sortiert nach delta_datum absteigend
        deppos.stueck = 0
        deppos.einstandswert_restbestand = deppos.maxKaufpreis = deppos.minKaufpreis = 0
        for delta in deltalist:
            if delta.delta_stck > 0:
                # Kauf; Verkäufe dürfen für die Ermittlung von max, min und Durchscnitt nicht
                # berücksichtigt werden
                if not deppos.letzter_kauf:
                    deppos.letzter_kauf = delta.delta_datum
                deppos.erster_kauf = delta.delta_datum
                deppos.stueck += ( delta.delta_stck - delta.verkauft_stck )
                deppos.einstandswert_restbestand += ( delta.delta_stck * delta.preis_stck )
                deppos.maxKaufpreis = delta.preis_stck if delta.preis_stck > deppos.maxKaufpreis else deppos.maxKaufpreis
                deppos.minKaufpreis = delta.preis_stck \
                    if delta.preis_stck < deppos.minKaufpreis or deppos.minKaufpreis == 0 \
                    else deppos.minKaufpreis
            else:
                # Verkauf
                deppos.einstandswert_restbestand += ( delta.delta_stck * delta.preis_stck ) # delta_stck < 0, deshalb "+"
        if deppos.stueck > 0: # es gibt noch einen Depot-Bestand
            deppos.preisprostueck = round( deppos.einstandswert_restbestand / deppos.stueck, 2 )
            deppos.einstandswert_restbestand = int( round( deppos.einstandswert_restbestand, 2 ) )

    def getHistoryByPeriod( self, ticker:str, period:Period, interval:Interval ):
        df:DataFrame = self._tickerHist.getTickerHistoryByPeriod( ticker, period, interval )
        return df

    def getSeriesHistoryByPeriod( self, ticker, seriesName:SeriesName, period:Period, interval:Interval ) -> Series:
        df:DataFrame = self.getHistoryByPeriod( ticker, period, interval )
        return df[seriesName.value]

    def getOrders( self, wkn:str ) -> SumTableModel:
        deltalist = self._db.getDeltas( wkn )
        tm = SumTableModel( deltalist, 0, ("delta_stck", "order_summe") )
        tm.setKeyHeaderMappings2( ("delta_datum", "delta_stck", "preis_stck", "order_summe",
                                   "verkauft_stck", "verkaufskosten", "bemerkung"),
                                  ("Datum",  "Stück", "Stück-\npreis (€)", "Order-\nsumme (€)",
                                   "Stück vk.", "Verk.kosten", "Bemerkung") )
        return tm

    @staticmethod
    def getDetails( deppos:XDepotPosition ) -> XDetail:
        """
        Liefert die Daten für die Detailanzeige.
        Diese befinden sich bereits in <deppos>, sie müssen nur in ein XDetail-Objekt überführt werden.
        :param deppos:
        :return:
        """
        x = XDetail()
        x.basic_index = deppos.basic_index
        x.beschreibung = deppos.beschreibung
        x.topfirmen = deppos.topfirmen
        x.toplaender = deppos.toplaender
        x.topsektoren = deppos.topsektoren
        x.bank = deppos.bank
        x.depot_nr = deppos.depot_nr
        x.depot_vrrkto = deppos.depot_vrrkto
        return x

    def getAllOrders( self ) -> SumTableModel:
        deltas:List[XDelta] = self._db.getAllDeltas()
        tm = SumTableModel( deltas, 0, ("order_summe",) )
        tm.setKeyHeaderMappings2(
            ( "id", "delta_datum", "name", "wkn", "isin", "ticker", "depot_id", "delta_stck", "preis_stck", "order_summe"),
            ( "Id", "Datum", "Name", "WKN", "ISIN", "Ticker", "Depot", "Stück", "Preis/Stck", "Ordersumme" ) )
        return tm

    def getAllOrdersList( self ) -> List[XDelta]:
        return self._db.getAllDeltas()

    def insertOrderAndUpdateDepotData( self, delta:XDelta, deppos:XDepotPosition ):
        """
        Fügt eine Order (Kauf oder Verkauf) in Tabelle delta ein.
        Danach werden die deppos-Attribute stueck, gesamtkaufpreis, preisprostueck und ggf. maxKaufpreis oder minKaufpreis
        geändert. Außerdem werden gesamtwert_aktuell und delta_proz neu berechnet.
        :param delta: die Daten der neuen Order
        :param deppos: die Depotposition, die sich durch die Order verändert
        :return:
        """
        delta.order_summe = abs( round( delta.preis_stck * delta.delta_stck, 2 ) )
        self._db.insertDelta( delta )
        if delta.delta_stck < 0:
            # es ist ein Verkauf, jetzt muss die verkaufte Stückzahl in einen oder mehrere Kauf-Sätze
            # gebucht werden
            self._bookShareSale( delta, deppos )
        self._db.commit()
        self._provideOrderData( deppos )
        self._provideGesamtwertAndDelta( deppos )

    def _bookShareSale( self, verkauf:XDelta, deppos:XDepotPosition ):
        """
        nach einem Anteilsverkauf muss zur späteren Berechnung der Abgeltungssteuer die Anzahl der verkauften Stücke
        auf die vorherigen Käufe verteilt werden.
        Beispiel:
        Verkauft wurden 100 Stück.
        Es gibt 2 Käufe, der ältere mit 80 Stück, der jüngere mit 40 Stück.
        Gem FIFO-Prinzip müssen nun im älteren Kauf 80 verkaufte Stück eingetragen werden und im neueren Kauf
        20 Stück.
        Nach diesen Datenbank-Updates müssen in der Schnittstelle <deppos> die Felder stueck und einstandswert_restbestand
        neu berechnet werden.
        :param verkauf:
        :param deppos:
        :return:
        """
        # Zuerst die Kauf-Orders dieses Wertpapiers holen:
        deltas:List[XDelta] = self._db.getKaeufe( verkauf.wkn ) # sortiert nach Kaufdatum aufsteigend, also ältester Kauf oben
        verkaufte_stuecke = verkauf.delta_stck * -1
        rest = verkaufte_stuecke
        deppos.stueck = 0
        deppos.einstandswert_restbestand = 0
        for delta in deltas:
            vfgbar = delta.delta_stck - delta.verkauft_stck
            if vfgbar >= rest:
                # es gibt in diesem Satz (Kauf) soviele verfügbare Stücke, dass der Verkauf aus ihnen bedient
                # werden kann
                delta.verkauft_stck += rest
                rest = 0
            else:
                # nicht genügend Stücke für den Verkauf vorhanden. Die vorhandenen in verkauft_stck eintragen.
                delta.verkauft_stck += vfgbar
                rest -= vfgbar
            self._db.updateDeltaVerkaufteStuecke( delta.id, delta.verkauft_stck )
            deppos.stueck += rest
            deppos.einstandswert_restbestand += (rest * delta.preis_stck)
            if rest == 0:
                break
        if deppos.stueck > 0:
            # Durchschnittl. Preis pro Stück:
            deppos.preisprostueck = round( deppos.einstandswert_restbestand / deppos.stueck, 2 )

    def computeAbgeltungssteuer( self, wkn:str, kurs:float, stck:int ) -> int:
        """
        Berechnet die Abgeltungssteuer, die bei einem Verkauf von <stck> Papieren <wkn> bei aktuellem Kurs <kurs>
        fällig würden
        :param wkn:
        :param kurs:
        :param stck:
        :return: die fällige Abgeltungssteuer
        """
        deltas: List[XDelta] = self._db.getKaeufe( wkn )  # sortiert nach Kaufdatum aufsteigend, also ältester Kauf oben
        rest = stck
        steuer = 0 # fällige Abgeltungssteuer
        for delta in deltas:
            vfgbar = delta.delta_stck - delta.verkauft_stck # so viele Stücke sind von dieser Order noch verfügbar
            if rest >= vfgbar:  # alle verfügbaren Stücke des Kaufes <delta> werden für den gewünschten Verkauf benötigt
                vk = vfgbar
                rest -= vk
            else:
                vk = rest
            if vk > 0:
                kaufpreis = vk * delta.preis_stck # das war der damalige Order-Preis
                vk_preis = vk * kurs  # das wäre der aktuelle Verkaufspreis
                delta = vk_preis - kaufpreis # Gewinn bzw. Verlust dieser Order bei jetzigem Verkauf; negativ bei Verlust
                steuer += (delta * 0.25) # 25% Abgeltungssteuer auf das Delta
        return int( round(steuer, 2) )

    def getAllWknTickersForDividendComputation( self ) -> List[Dict]:
        """
        Liefert eine Liste von Dictionaries mit den Keys "wkn" und "ticker".
        Dictionaries werden nur für ausschüttende und im Monitor angezeigte Fonds geliefert.
        :return: List[Dict]
        """
        return self._db.getAllWknAndTickers( distributingOnly=True, flag_displ=1 )

    def getPaidDividendsTableModel( self, period:Period ) -> SumTableModel:
        """
        Diese Methode wird *nicht* aus einem separaten Thread aufgerufen.
        Sie ermittelt die WKN-/Tickerlist, alle Orders und mittels TickerHistories alle Dividenden und
        baut daraus ein SumTableModel und liefert es zurück.
        :param period: Gibt die Periode an, für die die Dividendenzahlungen ermittelt werden sollen
        :return:
        """
        def getTicker( wkn:str) -> str:
            for dic in wkn_ticker_list:
                if dic["wkn"] == wkn:
                    return dic["ticker"]

        def createXDividendAndAddToList( pay_day, div_pro_stck, div ):
            #print( pay_day, div_pro_stck, div )
            xdiv = XDividend()
            xdiv.wkn = wkn
            xdiv.name = name
            xdiv.ticker = ticker
            xdiv.pay_day = pay_day
            xdiv.div_pro_stck = div_pro_stck
            xdiv.div_summe = div
            xdiv_list.append( xdiv )

        xdiv_list:List[XDividend] = list()
        wkn_ticker_list = self.getAllWknTickersForDividendComputation()
        wkn_ticker_list.sort( key=lambda x: x["wkn"] )
        ticker_list = [x["ticker"] for x in wkn_ticker_list]
        histlist: DataFrame = \
            self._tickerHist.getTickerHistoriesByPeriod( ticker_list, period=period, interval=Interval.fiveDays )
        dividends: DataFrame = histlist[SeriesName.Dividends.value]
        allOrders: List[XDelta] = self.getAllOrdersList()
        wkn_list = [x["wkn"] for x in wkn_ticker_list]
        for wkn in wkn_list:
            wkn_orders = [order for order in allOrders if order.wkn == wkn ]
            if len( wkn_orders ) > 0:
                name = wkn_orders[0].name
                ticker = getTicker( wkn )
                divs = dividends[ticker]
                currency = TickerHistory.getCurrency( ticker )
                if currency != "EUR":
                    divs = self._convertSeries( divs, currency )
                self._getPaidDividends( divs, wkn_orders, callback=createXDividendAndAddToList )

        tm = SumTableModel( xdiv_list, None, ("div_summe",) )
        tm.setKeyHeaderMappings2( ( "name", "wkn", "ticker", "pay_day", "div_pro_stck", "div_summe" ),
                                  ( "Name", "WKN", "Ticker", "Zahltag", "Dividende\nje Stck", "Dividende" ) )
        return tm

    def getSumDividendsCurrentYear( self, wkn_ticker_list:List[Dict], allOrders:List[XDelta] ) -> int:
        """
        Liefert die Summe aller Dividendenzahlungen für die im Monitor vertretenen Fonds für das laufende Jahr.
        "Im Monitor vertreten" heißt: depotposition.flag_displ == 1.
        Hier dürfen keine DB-Zugriffe gemacht werden, weil diese Methode auch aus einem separaten Thread aufgerufen wird.
        :param wkn_ticker_list: Liste aller WKN/Ticker, für die die Div.zahlungen ermittelt werden sollen.
        :param allOrders: Alle Orders aus Tabelle <delta>
        :return: die Dividendensumme
        """
        def getWkn( tickr:str ) -> str:
            for dic in wkn_ticker_list:
                if tickr == dic["ticker"]:
                    return dic["wkn"]
            raise Exception( "Ticker '%s' nicht in der Ticker-/WKN-Liste gefunden." )

        def getOrders( wkn:str ) -> List[XDelta]:
            orderlist = [order for order in allOrders if order.wkn == wkn]
            return orderlist

        tickers = [d["ticker"] for d in wkn_ticker_list]
        histlist:DataFrame = \
            self._tickerHist.getTickerHistoriesByPeriod( tickers, period=Period.currentYear, interval=Interval.fiveDays )
        dividends:DataFrame = histlist[SeriesName.Dividends.value]
        sum_dividends = 0
        for ticker in tickers:
            if isinstance( dividends, Series ):
                divs = dividends
            else:
                divs = dividends[ticker]
            currency = TickerHistory.getCurrency( ticker )
            if currency != "EUR":
                divs = self._convertSeries( divs, currency )
            wkn = getWkn( ticker )
            orders = getOrders( wkn )
            sum_dividends += self._getPaidDividends( divs, orders )
        return sum_dividends

##################################################################################
##################################################################################
def testProvideFastInfoInSeparateThread():
    logic = InvestMonitorLogic()
    depposList:List[XDepotPosition] = logic.getDepotPositions( period=Period.oneYear, interval=Interval.fiveDays )
    print( depposList )

def testGetSumDividendsCurrentYear2():
    l = InvestMonitorLogic()
    sum = l.getPaidDividendsTableModel()
    print( sum )

def testGetSumDividendsCurrentYear():
    l = InvestMonitorLogic()
    sum = l.getSumDividendsCurrentYear()
    print( sum )

def testComputeAbgeltungssteuer():
    logic = InvestMonitorLogic()
    steuer = logic.computeAbgeltungssteuer( "ABCDEF", 31.00, 12 )
    print( "Steuer: ", steuer )

def test():
    logic = InvestMonitorLogic()
    lastPrice = logic.getKursAktuellInEuro( "PRIJ.L" )
    #poslist = logic.getDepotPositions()
    #print( poslist )

    # logic.saveMyHistories()

    poslist, dummy = logic.getDepotPositions()
    print( poslist )

    # df = logic.loadMyHistories()
    # close:DataFrame = df["Close"]
    # cols:Index = close.columns # <-- ticker-collection
    # print( cols[0] ) # <-- ticker
    # eusri:DataFrame = close["EUSRI.PA"]
    # print( eusri )

    #series = logic.getSeriesHistoryByPeriod( "WTEM.DE", SeriesName.Close, Period.fiveDays, Interval.oneDay )
    #print( series )