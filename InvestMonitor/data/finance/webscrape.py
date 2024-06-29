#import urllib.parse

import requests # calling cgi produces error AttributeError: module 'cgi' has no attribute 'parse_header'
import cgi  # deprecated - see https://docs.python.org/3/library/cgi.html
#print( cgi.__file__ )
#dir( cgi )
#print("Content-type: text/htmlrnrn")

#url = "https://justetf.com/en/etf-profile.html?isin=IE00B652H904#dividends"
#url = "https://api.exchangerate-api.com/v4/latest/USD"
# ??urllib.parse.parse_qsl( ??)
url = "https://extraetf.com/de/etf-profile/IE00B652H904?tab=dividends"

response = requests.get(url)
print( "done.")