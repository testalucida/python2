import enum
import math
from datetime import date
from enum import Enum
from typing import List, Dict

import yfinance
#from currency_converter import CurrencyConverter
#from forex_python.converter import CurrencyRates
from pandas import DataFrame, Series
from yfinance.scrapers.quote import FastInfo

import datehelper
from imon.enums import Period, Interval, SeriesName


def getOneYearAgo() -> str:
    currentDate: date = datehelper.getCurrentDate()
    oneyearago = datehelper.addYears( currentDate, -1 )
    return datehelper.getIsoStringFromDate( oneyearago )

######################################################################
import requests
import json
class CurrencyConverter:
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    rel_keys = "EUR, GBP, CHF"
    one_dollar_conversions:Dict = None

    @staticmethod
    def _loadCurrencies():
        CurrencyConverter.one_dollar_conversions = dict()
        response = requests.get( CurrencyConverter.url )
        dic = json.loads( response.content )
        rates = dic["rates"]
        rel_keys = "USD, EUR, GBP, CHF"
        for key, value in rates.items():
            if key in rel_keys:
                CurrencyConverter.one_dollar_conversions[key] = value

    @staticmethod
    def convert( amount:float, fromCurrency:str, toCurrency:str="EUR" ) -> float:
        if not CurrencyConverter.one_dollar_conversions:
            CurrencyConverter._loadCurrencies()
        oneDollarInFromCurrency = CurrencyConverter.one_dollar_conversions[fromCurrency]
        oneDollarInToCurrency = CurrencyConverter.one_dollar_conversions[toCurrency]
        vh = oneDollarInToCurrency/oneDollarInFromCurrency
        amountInToCurrency = vh * amount
        return amountInToCurrency

def testConversion():
    eur = CurrencyConverter.convert( 1, "USD" )
    print( "1 Dollar makes %f Euro" % eur )

def testRequests():
    url = "https://justetf.com/en/etf-profile.html?isin=IE00B9F5YL18#dividends"
    response = requests.get( url )
    print( response )


######################################################################
class TickerHistory:
    currentDate = datehelper.getIsoStringFromDate( datehelper.getCurrentDate() )
    oneYearAgo = getOneYearAgo()
    default_period:Period = Period.oneYear
    default_interval:Interval = Interval.oneWeek
    # currConverter = CurrencyConverter()
    # forex_curr_converter = CurrencyRates()

    @staticmethod
    def getFastInfo( ticker:str ) -> FastInfo:
        yf_ticker = yfinance.Ticker( ticker )
        fast_info = yf_ticker.fast_info
        # while fast_info is None:
        #     fast_info = yf_ticker.fast_info
        return fast_info

    @staticmethod
    def getCurrency( ticker:str ) -> str:
        fi = TickerHistory.getFastInfo( ticker )
        return fi.currency

    @staticmethod
    def convertToEuro( value, fromCurr: str ) -> float:
        curr = fromCurr
        if curr == "GBp":
            value /= 100
            curr = "GBP"
        eur = CurrencyConverter.convert( value, curr )
        return eur

    @staticmethod
    def getTickerHistoryByPeriod( ticker: str,
                                  period:Period = default_period, interval:Interval = default_interval ) -> DataFrame:
        """
        :param ticker: Ticker like "goog", "SEDM.L", ...
        :param period: Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        :param interval: Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                Intraday data cannot extend last 60 days
        :return:
        """
        yf_ticker = yfinance.Ticker( ticker )
        df = yf_ticker.history( period.value, interval.value )
        return df

    @staticmethod
    def getTickerHistoryByDates( ticker: str, interval:Interval = default_interval,
                                 start: str = oneYearAgo, end: str = currentDate ) -> DataFrame:
        """
        :param ticker: Ticker like "goog", "SEDM.L", ...
        :param interval: Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                Intraday data cannot extend last 60 days
        :param start: Download start date string (YYYY-MM-DD) or _datetime.
                Default is 1900-01-01
        :param end: Download end date string (YYYY-MM-DD) or _datetime.
                Default is now
        :return:
        """
        yf_ticker = yfinance.Ticker( ticker )
        df = yf_ticker.history( interval.value, start, end )
        return df

    @staticmethod
    def getTickerHistoriesByPeriod( tickers: List[str],
                                    period: Period = default_period, interval: Interval = default_interval ) -> DataFrame:
        """
        :param tickers: List of Tickers like "goog", "SEDM.L", ...
        :param period: Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        :param interval: Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                Intraday data cannot extend last 60 days
        :return:
        """
        if len( tickers ) == 1:
            return TickerHistory.getTickerHistoryByPeriod( tickers[0], period, interval )
        yf_tickers = yfinance.Tickers( tickers )
        df = yf_tickers.history( period.value, interval.value )
        return df

    @staticmethod
    def getTickerHistoriesByDates( tickers: List[str], interval: Interval = default_interval,
                                   start: str = oneYearAgo, end: str = currentDate ) -> DataFrame:
        """
        :param tickers: List of Tickers like "goog", "SEDM.L", ...
        :param interval: Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                Intraday data cannot extend last 60 days
        :param start: Download start date string (YYYY-MM-DD) or _datetime.
                Default is 1900-01-01
        :param end: Download end date string (YYYY-MM-DD) or _datetime.
                Default is now
        :return:
        """
        yf_tickers = yfinance.Tickers( tickers )
        df = yf_tickers.history( interval.value, start, end )
        return df

    @staticmethod
    def getSeries( df:DataFrame, seriesName:SeriesName ) -> Series:
        return df[seriesName.name]




################  TEST TEST TEST   ###########################
# def test5():
#     l = TickerHistory.getFastInfoList( ("IEDY.L", "ISPA.DE") )
#     print( l )

def test4():
    tick = TickerHistory()
    fi = tick.getFastInfo( "VJPN.SW" )
    print( fi )

def test3():
    tick_hist = TickerHistory()
    df = tick_hist.getTickerHistoriesByPeriod( ["EZTQ.F", "IEFV.L"] )
    series = df["Close"]
    series._plot()
    print( "fertig" )

def test2():
    import yfinance as yf
    ticker = "IEDY.L"
    data = yf.download( ticker, start="2023-01-20", end="2024-01-19" )
    print( data )

    # info = yf_ticker.info
    # if info:
    #     print( 'Forward PE:' )
    #     print( info['forwardPE'] )
    # print( 'Dividends:' )
    # div = yf_ticker.info.get( 'trailingAnnualDividendYield' )
    # print( div )


def testDividend():
    ticker = "ISPA.DE"  # "SEDY.L"
    tick_hist = TickerHistory()
    df = tick_hist.getTickerHistoryByPeriod( ticker, Period.oneYear, Interval.oneWeek )
    dividends: Series = df["Dividends"]
    print( dividends.index[0] )

def test():
    ticker = "EUNY.DE" #"IEDY.L" #"ISPA.DE" #"SEDY.L"
    tick_hist = TickerHistory()
    df = tick_hist.getTickerHistoryByPeriod( ticker, Period.oneYear, Interval.oneWeek )
    series:Series = df["Close"]
    fastinfo = tick_hist.getFastInfo( ticker )
    last_price = fastinfo.last_price
    if fastinfo.currency != "EUR":
        last_price = tick_hist.convertToEuro( last_price, str(fastinfo.currency) )
    print( ticker, " last_price in ", fastinfo.currency, ": ", fastinfo.last_price, " in EURO: ", last_price )
    series.plot()

def testDf():
    tick_hist = TickerHistory()
    df = tick_hist.getTickerHistoriesByPeriod( ["EZTQ.F", "IEFV.L"], period=Period.twoYears, interval=Interval.oneMonth )
    close:Series = df["Close"]
    row = close.tail(1)
    for name, series in row.items():
        print( row )
        print( name, "\t", series, "\t", series[0] )
        if math.isnan( series[0] ):
            df = df[:-1]
            break
    print( len(df) )

def testGetTickerHistoriesByDates():
    tick_hist = TickerHistory()
    df = tick_hist.getTickerHistoriesByPeriod( ["IEDY.L", "ISPA.DE"], period=Period.fiveDays,
                                               interval=Interval.oneDay )
    closeDf = df["Close"]
    fast_info = tick_hist.getFastInfo( "IEDY.L" )
    print( df )

def testFastInfo():
    ticker = "SEDM.L"
    tick = TickerHistory()
    euro = tick.convertToEuro( 1.00, "USD" )
    print( "one dollar makes '%f' euros" % euro )
    fast_info = tick.getFastInfo( ticker )
    euro = tick.convertToEuro( fast_info.last_price, str( fast_info.currency ) )
    print( "currency: ", fast_info.currency, " last_price: ", fast_info.last_price, " in Euro: ", euro )

def testGetMethods():
    import yfinance as yf
    msft = yf.Ticker( "IEDY.L" )
    #h = msft.history( )
    a = msft.get_actions()
    d = msft.get_dividends()
    print( d )

def testYahooFinance():
    url = "http://finance.yahoo.com/quote/AAPL/history"
    data = requests.get( url )
    print( data )

def testFMP():
    def test():
        ticker = "EUNY.DE"  # "IEDY.L" #"ISPA.DE" #"SEDY.L"
        tick_hist = TickerHistory()
        df = tick_hist.getTickerHistoryByPeriod( ticker, Period.oneYear, Interval.oneWeek )
        series: Series = df["Close"]
        fastinfo = tick_hist.getFastInfo( ticker )
        last_price = fastinfo.last_price
        if fastinfo.currency != "EUR":
            last_price = tick_hist.convertToEuro( last_price, str( fastinfo.currency ) )
        print( ticker, " last_price in ", fastinfo.currency, ": ", fastinfo.last_price, " in EURO: ", last_price )
        series.plot()
