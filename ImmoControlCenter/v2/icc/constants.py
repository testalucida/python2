from enum import Enum, IntEnum, auto
from typing import List
from numpy import sort

iccMonthShortNames = ("jan", "feb", "mrz", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "dez")
iccMonthIdxToShortName = {
    0 : iccMonthShortNames[0],
    1 : iccMonthShortNames[1],
    2 : iccMonthShortNames[2],
    3 : iccMonthShortNames[3],
    4 : iccMonthShortNames[4],
    5 : iccMonthShortNames[5],
    6 : iccMonthShortNames[6],
    7 : iccMonthShortNames[7],
    8 : iccMonthShortNames[8],
    9 : iccMonthShortNames[9],
    10 : iccMonthShortNames[10],
    11 : iccMonthShortNames[11]
}

def getMonthIdxFromShortName( monthShortName:str ) -> int:
    """
    :param monthShortName:
    :return: Index of monthShortName from 0 (jan) to 11 (dez)
    """
    return iccMonthShortNames.index( monthShortName )

class Action( IntEnum ):
    SHOW_MASTEROBJEKT = auto()
    SHOW_MIETOBJEKT = auto()
    SHOW_MIETVERHAELTNIS = auto()
    KUENDIGE_MIETVERHAELTNIS = auto()
    SHOW_NETTOMIETE_UND_NKV = auto()
    SHOW_NEBENKOSTEN_ABRECHNUNG = auto()
    SHOW_WEG_UND_VERWALTER = auto()
    SHOW_HAUSGELD_UND_RUEZUFUE = auto()
    SHOW_HAUSGELD_ABRECHNUNG = auto()
    SHOW_LEISTUNGSVERTRAG = auto()
    DUPLICATE_AND_SAVE = auto()
    DUPLICATE_AND_EDIT = auto()
    COMPUTE_SUMME = auto()
    COPY = auto() # Kopiere ganze Selektion
    COPY_CELL = auto() # Kopiere nur den Wert der geklickten Zelle
    COPY_BETRAEGE = auto() # Kopiere die Beträge der markierten Zeilen


class ValueMapper:
    def __init__( self, display, dbvalue ):
        self.display = display
        self.dbvalue = dbvalue

class ValueMapperHelper:
    @staticmethod
    def getDisplayValues( T:type, issorted:bool = True ) -> List[str]:
        l = list()
        for attr in T.__dict__.values():
            if isinstance( attr, ValueMapper ):
                l.append( attr.display )
        if issorted:
            l = list( sort( l ) )
        return l

    @staticmethod
    def getDisplay( T:type, dbvalue: str ) -> str:
        for attr in T.__dict__.values():
            if isinstance( attr, ValueMapper ):
                if attr.dbvalue == dbvalue:
                    return attr.display
        raise Exception( "ValueMapperHelper.getDisplay():\nDB-Value '%s' nicht gefunden." % dbvalue )

    @staticmethod
    def getDbValue( T:type, display: str ) -> str:
        for attr in T.__dict__.values():
            if isinstance( attr, ValueMapper ):
                if attr.display == display:
                    return attr.dbvalue
        raise Exception( "ValueMapperHelper.getDbValue():\nDisplay value '%s' nicht gefunden." % display )

class Modus:
    NEW = "new"
    MODIFY = "mod"
    UNK = "unk"

class Umlegbar( Enum ):
    NEIN = "nein"
    JA = "ja"
    NONE = ""


class Heizung:
    NOT_SET = ValueMapper( "", "" )
    GASZENTRAL = ValueMapper( "Gaszentralheizung", "GZH" )
    OELZENTRAL = ValueMapper( "Ölzentralheizung", "ÖZH" )
    GASETAGE = ValueMapper( "Gasetagenheizung", "GEH" )
    NACHTSPEICHER = ValueMapper( "Nachtspeicheröfen", "NSÖ" )

#
# if __name__ == "__main__":
#     disp = Heizung.GASZENTRAL.display
#     print( disp )
#     hzg = Heizung.getHeizungFromDisplay( disp )
#     print( hzg )


def test():
    values = ValueMapperHelper.getDisplayValues( Heizung, issorted=False )
    print( values )
    dispval = ValueMapperHelper.getDisplay( Heizung, Heizung.GASZENTRAL.dbvalue )
    print( dispval )
    dbval = ValueMapperHelper.getDbValue( Heizung, Heizung.GASZENTRAL.display )
    print( dbval )

class EinAusArt: # EinAus-Arten, wie sie in die Tabelle einaus eingetragen werden.
    BRUTTOMIETE = ValueMapper( "Bruttomiete", "bruttomiete" )
    #NEBENKOSTEN_VORAUS = ValueMapper( "Nebenkostenvorauszahlung", "nkv" )
    HAUSGELD_VORAUS = ValueMapper( "Hausgeldvorauszahlung", "hgv" )
    #REGELM_ABSCHLAG = ValueMapper( "Mtl. Abschlag", "rab" )
    NEBENKOSTEN_ABRECHNG = ValueMapper( "Nebenkostenabrechnung", "nka" )
    HAUSGELD_ABRECHNG = ValueMapper( "Hausgeldabrechnung", "hga" )
    SONDERUMLAGE = ValueMapper( "Sonderumlage", "sonder" )
    ALLGEMEINE_KOSTEN = ValueMapper( "Allgemeine Hauskosten", "allg" )
    GRUNDSTEUER = ValueMapper( "Grundsteuer", "gs" )
    #KOMMUNALE_DIENSTE = ValueMapper( "Kommunale Dienste", "komm" )  # Abschläge und Abrechnungen für Strom, Gas etc.
    REPARATUR = ValueMapper( "Reparatur", "rep" )
    DIENSTREISE = ValueMapper( "Dienstreise", "reise" )
    SONSTIGE_KOSTEN = ValueMapper( "Sonstige Kosten", "sonst" )
    VERSICHERUNG = ValueMapper( "Versicherung", "vers" )

    @staticmethod
    def getDisplayValues( issorted:bool = True ) -> List[str]:
        l = list()
        for attr in EinAusArt.__dict__.values():
            if isinstance( attr, ValueMapper ):
                l.append( attr.display )
        if issorted:
            l = list( sort( l ) )
        return l

    @staticmethod
    def getEinAusDialogOptions( issorted:bool = True ) -> List[str]:
        """
        Liefert nur die EinAus-Arten, die in der Tabelle "Alle Zahlungen" bei der Erfassung einer neuen
        oder der Änderung einer bestehenden Zahlunge verwendet werden dürfen.
        :param issorted:
        :return:
        """
        l = list()
        l.append( EinAusArt.SONDERUMLAGE.display )
        l.append( EinAusArt.ALLGEMEINE_KOSTEN.display )
        l.append( EinAusArt.REPARATUR.display )
        l.append( EinAusArt.SONSTIGE_KOSTEN.display )
        l.append( EinAusArt.VERSICHERUNG.display )
        l.append( EinAusArt.GRUNDSTEUER.display )
        if issorted:
            l = list( sort( l ) )
        return l

    @staticmethod
    def getDbValue( display:str ) -> str:
        for attr in EinAusArt.__dict__.values():
            if isinstance( attr, ValueMapper ):
                if attr.display == display:
                    return attr.dbvalue
        raise Exception( "EinAusArt.getDbValue():\nDisplay value '%s' nicht gefunden." % display )

    @staticmethod
    def getDisplay( dbvalue:str ) -> str:
        for attr in EinAusArt.__dict__.values():
            if isinstance( attr, ValueMapper ):
                if attr.dbvalue == dbvalue:
                    return attr.display
        raise Exception( "EinAusArt.getDisplay():\nDB-Value '%s' nicht gefunden." % dbvalue )



def testEinAusArtNeu():
    print( EinAusArt.BRUTTOMIETE.display )
    l = EinAusArt.getDisplayValues()
    print( l )
    dbv = EinAusArt.getDbValue( EinAusArt.REPARATUR.display )
    print( dbv )

class abrechnung( Enum ):
    NK = 0
    HG = 1

class tableAction( IntEnum ):
    INSERT = 0
    UPDATE = 1
    DELETE = 2

actionList = ( "INSERT", "UPDATE", "DELETE" )

class SollType( IntEnum ):
    MIETE_SOLL = 0
    HAUSGELD_SOLL = 1

class DetailLink( Enum ):
    ERHALTUNGSKOSTEN = "REP",
    ZU_VERTEIL_GESAMTKOSTEN_VJ = "VJ_GES", # Zu verteilende Aufwände, die im Veranlag.jahr entstanden sind
    ERHALTUNGSKOSTEN_VERTEILT = "VREP",   # Teilbeträge der im Veranlagg.jahr zu berücksichtigenden Aufwände, die im VJ
                                         # oder in den zurückliegenden 4 Jahren entstanden und zu verteilen sind.
    MIETEN = "ME",
    HAUSGELD = "HG",
    ALLGEMEINE_KOSTEN = "AK",
    SONSTIGE_KOSTEN = "SK"