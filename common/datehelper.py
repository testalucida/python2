from datetime import datetime, date
import dateutil.parser
from PySide2.QtCore import QDate
from dateutil.relativedelta import relativedelta
from typing import Tuple, Dict

import datehelper
from base.constants import monthLongNames, monatsletzter

def getNumberOfDays( monthNumber:int, year:int=None ) -> int:
    """
    Liefert die Anzahl Tage im gegebenen Monat. Schaltjahre werden berücksichtigt.
    :param monthNumber: 1 -> Januar, ... , 12 -> Dezember
    :param year: wenn nicht gesetzt: current year
    :return:
    """
    import calendar
    if not year: year = getCurrentYear()
    return calendar.monthrange( year, monthNumber )[1]
    #return monatsletzter[monthLongNames[monthNumber - 1]]

def currentDateIso() -> str:
    """
    short for getCurrentDateIso()
    :return:
    """
    return getCurrentDateIso()

def getCurrentDateIso() -> str:
    """
    returns current date in "yyyy-mm-dd" format
    :return:
    """
    return datetime.now().strftime( "%Y-%m-%d" )

def getCurrentYearAndMonth() -> Dict:
    """
    Returns a dictionary containing current year and month.
    :return: a dictionary with key "year" containing the current year as an Integer
                          and  key "month" containing the month as an Integer where *1* (!!) represents January and so on.
    """
    d = { }
    d["month"] = datetime.now().month
    d["year"] = datetime.now().year
    return d

def getCurrentYearMonthDay() -> Dict:
    d = { }
    d["month"] = datetime.now().month
    d["year"] = datetime.now().year
    d["day"] = datetime.now().day
    return d

def getCurrentTimestampIso() -> str:
    return datetime.now().strftime( "%Y-%m-%d:%H.%M.%S.%f" )

def getFirstOfNextMonth() -> str:
    """
    returns start of next month in ISO format: "2021-04-01"
    :return:
    """
    d = getCurrentYearAndMonth()
    last = getNumberOfDays( d["month"] )
    dt = "%d-%02d-%02d" % ( d["year"], d["month"], last )
    dt = addDaysToIsoString( dt, 1 )
    return dt

def getFirstOfFollowingMonth( isodate:str ) -> str:
    """
    returns start of month following <isodate>
    :param isodate:
    :return:
    """
    y, m, d = getDateParts( isodate )
    if m < 12:
        m += 1
    else:
        m = 1
        y += 1
    first = "%d-%02d-%02d" % ( y, m, 1 )
    return first

def getMonthIndex( month:str ) -> int:
    """
    returns index of month given as (german) string, e.g.: return 1 if month == "Januar"
    :param month: "Januar", "Februar",... according to monthLongNames in base/constants.py
    :return: index of given month
    """
    for i in range( len( monthLongNames ) ):
        if monthLongNames[i] == month:
            return i+1
    raise Exception( "Wrong month name: '%s'" % (month) )

def getDateParts( datestring:str ) -> Tuple[int, int, int]:
    """
    Returns the given ISO or EUR datestring converted in
    integer parts (y, m, d)
    :param datestring:  yyyy-mm-dd (ISO) or dd.mm.yyyy (EUR)
    :return:
    """
    if isValidIsoDatestring( datestring ):
        y = int( datestring[0:4] )
        m = int( datestring[5:7] )
        d = int( datestring[-2:] )
        return y, m, d
    if isValidEurDatestring( datestring ):
        d = int( datestring[0:2] )
        m = int( datestring[3:5] )
        y = int( datestring[-4:] )
        return y, m, d
    raise Exception( "datehelper.getDateParts(): '%s' is not a valid date string" % (datestring) )

def convertIsoToEur(isostring: str) -> str:
    """
    converts an isodatestring into an eur datestring
    (2019-08-05 into 05.08.2019)
    :param isostring:
    :return: a converted datestring
    """
    if not isostring:
        return ''

    iso = isostring.split('-')
    eur = ''.join((iso[2], '.', iso[1], '.', iso[0]))
    return eur

def isValidEurDatestring(eurstring: str) -> bool:
    try:
        datetime.strptime(eurstring, '%d.%m.%Y')
        return True
    except ValueError as err:
        return False

def isValidIsoDatestring(isostring: str) -> bool:
    try:
        datetime.strptime(isostring, '%Y-%m-%d')
        return True
    except ValueError as err:
        return False

def convertEurToIso(eurstring: str) -> str:
    """
    converts an eurdatestring int an iso datestring
    ('29.08.2019' into '2019-08-29')
    :param eurstring:
    :return: a converted datestring
    """
    if not isValidEurDatestring(eurstring): return ''

    eur = eurstring.split('.')
    iso = ''.join((eur[2], '-', eur[1], '-', eur[0]))
    return iso

def compareEurDates(eurstring1: str, eurstring2: str) -> int:
    """
    compare 2 dates given in eur strings ('mm.dd.yyyy').
    :param eurstring1:
    :param eurstring2:
    :return:    -1 if eurstring1 < eurstring2 (earlier)
                 0 if eurstring1 == eurstring2
                 1 if eurstring1 > eurstring2
    """
    eur1 = eurstring1.split('.')
    eur2 = eurstring2.split('.')
    date1 = datetime(int(eur1[2]), int(eur1[1]), int(eur1[0]))
    date2 = datetime(int(eur2[2]), int(eur2[1]), int(eur2[0]))
    if date1 > date2: return 1
    if date1 == date2: return 0
    return -1

def getDateFromIsoString( isostring:str ) -> date:
    """
    Liefert ein datetime.date - Objekt zurück, das aus isostring erzeugt wurde
    :param isostring: ein Datum im Format "yyyy-mm-dd"
    :return: datetime.date
    """
    y, m, d = getDateParts( isostring )
    d = date( y, m, d )
    return d

def getLastOfMonthAsIsoString() -> str:
    """
    returns an iso date string representing the last day of current month and year
    :return:
    """
    d = getCurrentYearAndMonth()
    monthIdx = d["month"]
    year = d["year"]
    month = monthLongNames[monthIdx - 1]
    lastofmonth = monatsletzter[month]
    lastDayInMonth = "%d-%2d-%2d" % (year, monthIdx, lastofmonth )
    return lastDayInMonth

def getLastOfMonth() -> date:
    """
    returns a date representing the last day of current month and year
    :return:
    """
    d = getCurrentYearAndMonth()
    monthIdx = d["month"]
    year = d["year"]
    month = monthLongNames[monthIdx - 1]
    lastofmonth = monatsletzter[month]
    return date( year, monthIdx, lastofmonth )


def getQDateFromIsoString( isostr:str ) -> QDate:
    """
    Liefert ein QDate - Objekt zurück, das aus isostring erzeugt wurde
    :param isostring: ein Datum im Format "yyyy-mm-dd"
    :return: QDate
    """
    parts = isostr.split( "-" )
    return QDate( int(parts[0]), int(parts[1]), int(parts[2]) )

def getIsoStringFromQDate( date:QDate ) -> str:
    return getIsoStringFromDateParts( date.year(), date.month(), date.day() )

def getIsoStringFromDate( dt:date ) -> str:
    return getIsoStringFromDateParts( dt.year, dt.month, dt.day )

def getIsoStringFromDateParts( yyyy:int, mm:int, dd:int ) -> str:
    return str( yyyy ) + "-%.2d-%.2d" % ( mm, dd )

def isWithin(datestring2check: str, startdatestring: str, enddatestring: str) -> bool:
    """
    checks if datestring2check is part of the given interval.
    datestring2check being equal startdatestring or enddatestring means it is
    part of the interval
    :param datestring2check: date in eur or iso string format (dd.mm.yyyy or yyyy-mm-dd)
    :param startdatestring: date in eur or iso string format (dd.mm.yyyy or yyyy-mm-dd)
    :param enddatestring: date in eur or iso string format or '' or None - will then be replaced by '9999-12-31'
    :return:
    """
    if not isValidEurDatestring( datestring2check ):
        datestring2check = convertIsoToEur( datestring2check )
    if not isValidEurDatestring( startdatestring ):
        startdatestring = convertIsoToEur( startdatestring )
    if not enddatestring:
        enddatestring = '31.12.9999'
    else:
        if not isValidEurDatestring( enddatestring ):
            enddatestring = convertIsoToEur( enddatestring )

    if compareEurDates(datestring2check, startdatestring) < 0:
        return False
    if compareEurDates(datestring2check, enddatestring) > 0:
        return False
    return True

def compareToToday(eurstring: str) -> int:
    """
    compares a given date in eur string format with today's date.
    :param eurstring:  the date to check
    :return: -1 if eurstring is in the past, 0 if eurstring == today,
    +1 if eurstring is in the future.
    """
    eurtoday = date.today().strftime('%d.%m.%Y')
    return compareEurDates(eurstring, eurtoday)

def getCurrentYear() -> int:
    return date.today().year

def getLastYears(cnt: int) -> list:
    current = date.today().year
    yearlist = []
    for n in range(cnt):
        yearlist.append(current - n)
    return yearlist

def getTodayAsIsoString() -> str:
    return date.today().isoformat()

def getNumberOfMonths(d1: str, d2: str, year: int) -> int:
    """
    gets the number of months within the period beginning on d1 and
    ending on d2 which are in the given year
    NOTE: the day of month will not be considered.
          If year is 2019 and d1 is '2019-01-31' january '19 will be counted.
          If year is 2019 and d2 is '2019-12-01' december '19 will be counted.
    :param d1: date the period is beginning. Must be given as iso string 'YYYY-MM-DD'
    :param d2: date the period is ending. Must be given as iso string 'YYYY-MM-DD' OR None OR ''.
    :param year: a four digit integer like 2019
    :return: number of months
    """
    if d2 is None or d2 == '': d2 = "2999-12-31"
    start:datetime = dateutil.parser.parse(d1)
    dt:datetime = start
    end:datetime = dateutil.parser.parse(d2)
    if end.year > year:
        d2 = str(year) + "-12-31"
        end = dateutil.parser.parse(d2)

    while dt.year < year:
        dt = addMonths(dt, 1)

    cnt = 0
    while dt.year == year and dt <= end:
        dt = addMonths(dt, 1)
        cnt += 1

    return cnt

def getNumberOfDays2( d1:str, d2:str, year:int ):
    """
    Gets the number of days within the period given by d1 and d2 which is part of <year>
    Note that d2 must be the more recent date.
    :param d1: begin of period. Format "yyyy-mm-dd"
    :param d2: end of perion. Format "yyyy-mm-dd"
    :param year: an int value
    :return: number of days which are part of <year>
    """
    assert d2 >= d1
    y1, m1, d1 = getDateParts( d1 )
    assert y1 <= year
    y2, m2, d2 = getDateParts( d2 )
    if y1 < year:
        y1, m1, d1 = year, 1, 1
    if y2 > year:
        y2, m2, d2 = year, 12, 31
    d1 = date( y1, m1, d1 )
    d2 = date( y2, m2, d2 )
    delta = d2 - d1
    return delta.days + 1

def getNumberOfDays3( d1:str, d2:str ) -> int:
    """
    Returns the number of days between two given dates.
    :param d1: isodate like "2023-01-01"
    :param d2: same as d1. Must be greater (later) than d1
    :return:
    """
    assert d2 > d1
    date1 = dateutil.parser.parse( d1 )
    date2 = dateutil.parser.parse( d2 )
    delta = date2 - date1
    return delta.days + 1 # +1 since delta is computed as difference between the given dates, so delta would be 0
                          # if d1 == d2 which would be wrong.

def testNumberOfDays3( ):
    d1 = "2024-01-29"
    d2 = "2024-01-28"
    days = getNumberOfDays3( d1, d2 )
    print( days + 1 )

def getLastMonth() -> Tuple[int, str]:
    monat = datetime.now().month
    monat = 12 if monat == 1 else monat-1
    smonat = monthLongNames[monat - 1]
    return monat, smonat

def getRelativeQDate( monthdelta:int, day:int ) -> QDate:
    """
    Returns a date relative to current date.
    :param monthdelta: number of months to add or subtract from current month
    :param day: the day to set
    :return: the created QDate object
    """
    today = datetime.now()
    m = today.month
    y = today.year
    m += monthdelta
    if m == 0:
        m = 12
        y -= 1
    return QDate( y, m, day )


def addYears(mydate: date, cntYears: int) -> date:
    return mydate + relativedelta(years = cntYears)

def addMonths(mydate: date, cntMonths: int) -> date:
    return mydate + relativedelta(months = cntMonths)

def addDays(mydate: date, cntDays: int) -> date:
    return mydate + relativedelta(days = cntDays)

def addDaysToIsoString( isostring:str, cntDays:int ) -> str:
    d = getDateFromIsoString( isostring )
    d = addDays( d, cntDays )
    return getIsoStringFromDate( d )

def getCurrentDate() -> date:
    now = date.today()
    return now

def test4():
    today = datehelper.getCurrentDate()
    oneyearago = datehelper.addYears( today, -1 )
    print( oneyearago )

def test2():
    days = getNumberOfDays2( "2020-12-01", "2022-01-31", 2021 )
    print( days )

def test3():
    months = getNumberOfMonths( "2021-12-01", "2022-01-31", 2021 )
    print( months )

def test():
    dt = getFirstOfNextMonth()

    d = QDate( 2020, 12, 3 )
    print( d )
    iso = getIsoStringFromQDate( d )
    print( iso )

    y, m, d = getDateParts( "2020-05-25" )
    y, m, d = getDateParts( "13.11.2019" )
    i = getMonthIndex( "Dezember" )
    print( i )

    s = getTodayAsIsoString()
    d1 = '2019-12-01'
    d2 = '2020-03-10'
    cnt = getNumberOfMonths(d1, d2, 2019)
    print(cnt)

if __name__ == '__main__':
    test()
