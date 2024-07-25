from enum import Enum
from typing import List

from utfsymbols import symDELTA, symAVG


class InfoPanelOrder( Enum ):
    Wkn = "WKN"
    Name = "Alphabetisch nach Name"
    Index = "Alphabetisch nach Index"
    Depot = "Depot, WKN"
    Wert = "Wert"
    Anteil = "Anteil an der Summe der akt. Gesamtwerte"
    Anteil_USA = "Anteil USA-Firmen"
    AccFirst = "Thesaurierende, WKN"
    AccLast = "Ausschüttende, WKN"
    LetzterKauf = "Letzter Kauf"
    DeltaWert = "Wertentwicklung"
    DividendYield = "Dividendenrendite"
    DividendPaid = "Ausschüttung in Periode"
    Buy = "Kaufen"
    DeltaKursAsc = symDELTA + " Kurs i. Vgl. z. Vortag (ASC)"
    RelKursAvgKp = symDELTA + " Verhältnis akt. Kurs zu " + symAVG + " Kaufpreis"
    #DeltaKurs_1 = "Kursentwicklung nach letztem Close"
    # AverageKurs_50 = "⌀ Kurs letzte 50 Tage"
    # AverageKurs_200 = "⌀ Kurs letzte 200 Tage"

class SortDirection( Enum ):
    ASC = 0
    DESC = 1

class SeriesName( Enum ):
    Close = "Close"
    Dividends = "Dividends"
    High = "High"
    Low = "Low"
    Open = "Open"

class Period( Enum ):
    # 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    oneDay = "1d"
    fiveDays = "5d"
    oneMonth = "1mo"
    threeMonths = "3mo"
    sixMonths = "6mo"
    currentYear = "ytd"
    oneYear = "1y"
    twoYears = "2y"
    threYears = "3y"
    fiveYears = "5y"
    tenYears = "10y"
    max = "max"
    unknown = "unk"

    @staticmethod
    def getPeriods() -> List[str]:
        """
        Liefert alle Values des Enum Period als Liste ["1d", "5d", ...]
        :return:
        """
        names = Period._member_names_
        l = list()
        for name in names:
            l.append( Period.__dict__[name].value )
        return l

# class PeriodLenInDays( Enum ):
#     oneDay = 1
#     fiveDays = 5
#     oneMonth =

class Interval( Enum ):
    # 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    oneMin = "1m"
    twoMins = "2m"
    fiveMins = "5m"
    fifteenMins = "15m"
    thirtyMins = "30m"
    sixtyMins = "60m"
    ninetyMins = "90m"
    oneHour = "1h"
    oneDay = "1d"
    fiveDays = "5d"
    oneWeek = "1wk" #gibt's offenbar nicht mehr
    oneMonth = "1mo"
    threeMonths = "3mo"
    unknown = "unk"

    @staticmethod
    def getIntervals() -> List[str]:
        """
        Liefert alle Values des Enum Interval als Liste ["1m", "2m", ...]
        :return:
        """
        names = Interval._member_names_
        l = list()
        for name in names:
            l.append( Interval.__dict__[name].value )
        return l

def test():
    p = Period.oneYear
    print( p.value )