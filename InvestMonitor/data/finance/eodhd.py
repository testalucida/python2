import requests

def testDividend():
    url = f'http://eodhd.com/api/div/AAPL?from=2023-01-01&api_token=6224bfc9283350.13970601'
    data = requests.get(url)
    print(data)