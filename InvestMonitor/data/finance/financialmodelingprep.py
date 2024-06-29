from typing import List, Dict
import requests
from pandas import DataFrame, json_normalize, Series

import datehelper
from imon.enums import Period, Interval

class TickerData():
    def __init__(self, ticker:str="" ):
        self.ticker = ticker
        self.close:DataFrame = None
        self.dividend:DataFrame = None

class FMP:
    def __init__( self ):
        self._apiKey = "apikey=554aa031d25c1457115803e9c2562cb8"
        self._url = "https://financialmodelingprep.com/api/v3/"
        self._endpointHistoricalPrice = "historical-price-full/"
        self._endpointDividends = "historical-price-full/stock_dividend/"

    def getHistoricalPricesByTickerlist( self, tickers:str, period:Period=Period.oneYear, interval:Interval=Interval.oneWeek ) -> List[TickerData]:
        """

        :param tickers: like "AAPL,MSFT,ISPA.DE"
        :param period:
        :param interval:
        :return: eine Liste von TickerData-Objekten. Je Ticker in <tickers> wird ein TickerData-OBjekt geliefert.
        """
        from_ = self._createFrom( period )
        to_ = "to=" + datehelper.getCurrentDateIso()
        url = self._url + self._endpointHistoricalPrice + tickers + "?" + from_ + "&" + to_ + "&" + self._apiKey
        response = requests.get( url )
        historicalStockList = response["historicalStockList"]
        tickerdatalist = list()
        for historicalStock in historicalStockList:
            ticker = historicalStock["symbol"]
            historical = historicalStock["historical"]
            df = DataFrame( historical, columns=["date", "close"] )
            df.set_index( "date", inplace=True )

        return tickerdatalist

    def getHistoricalPricesByTicker( self, ticker:str, period=Period.oneYear, interval=Interval.oneWeek ) -> TickerData:
        """

        :param ticker:
        :param period:
        :param interval:
        :return:
        """
        from_ = self._createFrom( period )
        to_ = "to=" + datehelper.getCurrentDateIso()
        url = self._url + self._endpointHistoricalPrice + ticker + "?" + from_ + "&" + to_ + "&" + self._apiKey
        historicalStock = requests.get( url ).json()
        ticker = historicalStock["symbol"]
        historical = historicalStock["historical"]
        df = DataFrame( historical, columns=["date", "close"] )
        df.set_index( "date", inplace=True )
        tickerdata = TickerData( ticker )
        tickerdata.close = df
        return tickerdata

    @staticmethod
    def _createFrom( period:Period ) -> str:
        return "from=2023-10-01"

###########################################################################################################

def testFMPhistPrices():
    import matplotlib.pyplot as plt
    fmp = FMP()
    td:TickerData = fmp.getHistoricalPricesByTicker( "IBCQ" )
    # print( td.ticker )
    # print( td.close )
    td.close.plot()
    plt.grid()
    plt.gcf().autofmt_xdate()
    plt.tick_params( axis='x', which='major', labelsize=8 )
    plt.show()

def testCurrency():
    url = "https://financialmodelingprep.com/api/v3/search?query=bl-equities&apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    print( data )

def testRealTimePrice():
    url = "https://financialmodelingprep.com/api/v3/stock/real-time-price/IBCQ?apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    print( data )

def testDividend():
    # url = "https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/H4ZJ.DE?from=2023-01-01&to=2023-12-31&apikey=554aa031d25c1457115803e9c2562cb8"
    #url = "https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/VDPX.L?from=2023-01-01&to=2023-12-31&apikey=554aa031d25c1457115803e9c2562cb8"
    url = "https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/IEDY.L?from=2023-01-01&to=2023-12-31&apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get(url)
    print(data)

def testPrice():
    # url = "https://financialmodelingprep.com/api/v3/historical-price-full/ISPA.DE?from=2019-01-01&to=2023-12-31&apikey=554aa031d25c1457115803e9c2562cb8"
    url = "https://financialmodelingprep.com/api/v3/historical-price-full/ISPA.DE,TDIV.AS?from=2023-01-01&to=2023-12-31&apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    print( data )

def testStatementSymbols():
    url = "https://financialmodelingprep.com/api/v3/financial-statement-symbol-lists?apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    print( data )

def testETFsearch():
    url = "https://financialmodelingprep.com/api/v3/etf/list?apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    print( data )

def testBatchQuote():
    # url = "https://financialmodelingprep.com/api/v4/batch-pre-post-market/VDJP.L,ISPA.DE?from=2023-01-01&to=2023-12-31&apikey=554aa031d25c1457115803e9c2562cb8"
    url = "https://financialmodelingprep.com/api/v4/batch-pre-post-market/AAPL,MSFT?from=2023-01-01&to=2023-12-31&apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    return data

def testHistoricalPrice():
    url = "https://financialmodelingprep.com/api/v3/historical-price-full/AAPL,MSFT?from=2023-12-01&to=2023-12-10&apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    return data

def testCountryWeighting():
    url = "https://financialmodelingprep.com/api/v3/etf-country-weightings/ISPA.DE?apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    return data

def testSectorWeighting():
    url = "https://financialmodelingprep.com/api/v3/etf-sector-weightings/ISPA.DE?apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    return data

def testEtfInformation():
    url = "https://financialmodelingprep.com/api/v4/etf-info?symbol=ISPA.DE&apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    return data

def testEtfHoldings():
    # nur für Enterprise oder Premium Plan
    url = "https://financialmodelingprep.com/api/v4/etf-holdings?symbol=ISPA.DE&apikey=554aa031d25c1457115803e9c2562cb8"
    data = requests.get( url )
    return data


def testConvertIntoDataFrame():
    # data = testHistoricalPrice()
    # jsondata = data.json()
    jsondata:Dict = \
    { 'historicalStockList':
        [
            { 'symbol': 'AAPL',
              'historical':
                [
                    { 'date': '2023-12-08', 'open': 194.2, 'high': 195.99, 'low': 193.67, 'close': 195.71, 'adjClose': 195.71,
                      'volume': 53383658, 'unadjustedVolume': 53377300, 'change': 1.51, 'changePercent': 0.77755, 'vwap': 195.16,
                      'label': 'December 08, 23', 'changeOverTime': 0.0077755 },
                    { 'date': '2023-12-07', 'open': 193.63, 'high': 195, 'low': 193.59, 'close': 194.27, 'adjClose': 194.27,
                      'volume': 47413955, 'unadjustedVolume': 47477700, 'change': 0.64, 'changePercent': 0.33053, 'vwap': 194.4,
                      'label': 'December 07, 23', 'changeOverTime': 0.0033053 },
                    { 'date': '2023-12-06', 'open': 194.45, 'high': 194.76, 'low': 192.11, 'close': 192.32, 'adjClose': 192.32,
                      'volume': 41055862, 'unadjustedVolume': 41089700, 'change': -2.13, 'changePercent': -1.1, 'vwap': 192.8,
                      'label': 'December 06, 23', 'changeOverTime': -0.011 },
                    { 'date': '2023-12-05', 'open': 190.21, 'high': 194.4, 'low': 190.18, 'close': 193.42, 'adjClose': 193.42,
                      'volume': 66628398, 'unadjustedVolume': 66628400, 'change': 3.21, 'changePercent': 1.69, 'vwap': 193.17,
                      'label': 'December 05, 23', 'changeOverTime': 0.0169 },
                    { 'date': '2023-12-04', 'open': 189.98, 'high': 190.05, 'low': 187.4511, 'close': 189.43, 'adjClose': 189.43,
                      'volume': 43389519, 'unadjustedVolume': 43389500, 'change': -0.55, 'changePercent': -0.2895, 'vwap': 188.92,
                      'label': 'December 04, 23', 'changeOverTime': -0.002895 },
                    { 'date': '2023-12-01', 'open': 190.33, 'high': 191.56, 'low': 189.23, 'close': 191.24, 'adjClose': 191.24,
                      'volume': 45676673, 'unadjustedVolume': 45679300, 'change': 0.91, 'changePercent': 0.47812, 'vwap': 190.86,
                      'label': 'December 01, 23', 'changeOverTime': 0.0047812 }
                ]
            },
            { 'symbol': 'MSFT',
              'historical':
                [
                    { 'date': '2023-12-08', 'open': 369.2, 'high': 374.46, 'low': 368.23, 'close': 374.23, 'adjClose': 374.23,
                      'volume': 20142366, 'unadjustedVolume': 20144800, 'change': 5.03, 'changePercent': 1.36, 'vwap': 372.78,
                      'label': 'December 08, 23', 'changeOverTime': 0.0136 },
                    { 'date': '2023-12-07', 'open': 368.23, 'high': 371.4527, 'low': 366.32, 'close': 370.95, 'adjClose': 370.95,
                      'volume': 23118104, 'unadjustedVolume': 23118900, 'change': 2.72, 'changePercent': 0.73867, 'vwap': 369.86,
                      'label': 'December 07, 23', 'changeOverTime': 0.0073867 },
                    { 'date': '2023-12-06', 'open': 373.54, 'high': 374.18, 'low': 368.03, 'close': 368.8, 'adjClose': 368.8,
                      'volume': 21174417, 'unadjustedVolume': 21182100, 'change': -4.74, 'changePercent': -1.27, 'vwap': 369.97,
                      'label': 'December 06, 23', 'changeOverTime': -0.0127 },
                    { 'date': '2023-12-05', 'open': 366.45, 'high': 373.075, 'low': 365.621, 'close': 372.52, 'adjClose': 372.52,
                      'volume': 23017535, 'unadjustedVolume': 23065000, 'change': 6.07, 'changePercent': 1.66, 'vwap': 371.21,
                      'label': 'December 05, 23', 'changeOverTime': 0.0166 },
                    { 'date': '2023-12-04', 'open': 369.1, 'high': 369.52, 'low': 362.9, 'close': 369.14, 'adjClose': 369.14,
                      'volume': 32063301, 'unadjustedVolume': 32063300, 'change': 0.04, 'changePercent': 0.01083717, 'vwap': 367.21,
                      'label': 'December 04, 23', 'changeOverTime': 0.0001083717 },
                    { 'date': '2023-12-01', 'open': 376.76, 'high': 378.16, 'low': 371.31, 'close': 374.51, 'adjClose': 374.51,
                      'volume': 33036672, 'unadjustedVolume': 33020400, 'change': -2.25, 'changePercent': -0.5972, 'vwap': 374.01,
                      'label': 'December 01, 23', 'changeOverTime': -0.005972 }
                ]
            }
        ]
    }
    #diclist = jsondata["historicalStockList"][0]["historical"]
    historicalStockList = jsondata["historicalStockList"]
    for historicalStock in historicalStockList:
        ticker = historicalStock["symbol"]
        historical = historicalStock["historical"]
        df = DataFrame( historical, columns=["date", "close"] )
        df.set_index( "date", inplace=True )

    print( "done." )
