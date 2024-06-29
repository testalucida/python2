

import requests

def testDividend():
    key = "FOA327FEAKS1OKZB"
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&apikey=FOA327FEAKS1OKZB"
    data = requests.get(url)
    print(data)