from typing import List, Iterable, Dict

import datehelper
from base.basetablemodel import BaseTableModel, SumTableModel
from base.interfaces import XBase
from v2.icc.iccdata import IccData

######################   IccTableModel   ########################
from v2.icc.interfaces import XMasterobjekt, XMietobjekt, XKreditorLeistung, XLeistung, XLetzteBuchung, XEinAus


class IccTableModel( BaseTableModel ):
    def __init__( self, rowList:List[XBase]=None, jahr:int=None ):
        BaseTableModel.__init__( self, rowList, jahr )

######################   IccSumTableModel   #####################
class IccSumTableModel( SumTableModel ):
    def __init__( self, objectList:List[XBase], jahr:int, colsToSum:Iterable[str] ):
        SumTableModel.__init__( self, objectList, jahr, colsToSum )

########################   IccLogic   ###########################
class IccLogic:
    def __init__(self):
        self._iccdata = IccData()
        self._masterobjekte:List[XMasterobjekt] = None
        self._yearsInDatabase:List[int] = None

    def getJahre( self ) -> List[int]:
        """
        Liefert eine Liste der Jahre, für die Daten in der Datenbank vorhanden sind PLUS das aktuelle Jahr,
        sofern es nicht in der Liste vorhanden ist.
        :return:
        """
        if self._yearsInDatabase and len( self._yearsInDatabase ) > 0:
            return self._yearsInDatabase
        jahre = self._iccdata.getJahre()
        current = datehelper.getCurrentYear()
        if not current in jahre:
            jahre.insert( 0, current )
        self._yearsInDatabase = jahre
        return jahre

    def getYearToStartWith( self ) -> int:
        if not self._yearsInDatabase:
            self.getJahre()
        return self._yearsInDatabase[0]

    @staticmethod
    def getMonthToStartWith():
        dic = datehelper.getCurrentYearAndMonth()
        return dic["month"] - 1

    def getMasterobjekte( self ) -> List[XMasterobjekt]:
        if not self._masterobjekte:
            self._masterobjekte = self._iccdata.getMasterobjekte()
        return self._masterobjekte

    def getMasterNamen( self ) -> List[str]:
        li = self.getMasterobjekte()
        names = [o.master_name for o in li]
        return names

    def getMietobjekte( self, master_name:str ) -> List[XMietobjekt]:
        return self._iccdata.getMietobjekte( master_name )

    def getMietobjektNamen( self, master_name:str ) -> List[str]:
        li = self.getMietobjekte( master_name )
        names = [o.mobj_id for o in li]
        if len( names ) > 1: # es handelt sich um ein Haus mit mehreren Wohnungen - der Liste ein "" voranstellen.
            names.insert( 0, "" )
        return names

    def getKreditorLeistungen( self, master_name:str, mobj_id:str=None ) -> List[XKreditorLeistung]:
        li:List[XKreditorLeistung] = self._iccdata.getKreditorLeistungen( master_name )
        if mobj_id:
            li = [k for k in li if k.mobj_id == mobj_id]
        return li

    def getKreditoren( self, master_name:str ) -> List[str]:
        kredleistlist = self.getKreditorLeistungen( master_name )
        kredlist = list( set( [k.kreditor for k in kredleistlist] ) )
        kredlist.insert( 0, "" )
        return kredlist

    def checkKreditorLeistung( self, master_name:str, kreditor:str, leistung:str, umlegbar:str, ea_art_display ) -> \
            XKreditorLeistung or None:
        """
        Prüft, ob eine bestimmte Kombination master_name/kreditor/leistung in Tabelle kreditorleistung existiert.
        Wenn nein, wird sie angelegt.
        :param master_name:
        :param kreditor:
        :param leistung:
        :param umlegbar:
        :param ea_art_display:
        :return: die neu angelegte Kreditorleistung bzw. None, wenn sie bereits existiert.
        """
        if not self._iccdata.existsKreditorLeistung( master_name, kreditor, leistung ):
            x = XKreditorLeistung()
            x.master_name = master_name
            x.kreditor = kreditor
            x.leistung = leistung
            x.umlegbar = umlegbar
            x.ea_art = ea_art_display
            self._iccdata.insertKreditorLeistung( x )
            self._iccdata.commit()
            return x
        return None

    @staticmethod
    def getNachnameVornameFromMv_id( mv_id:str ) -> str:
        nameparts = mv_id.split( "_" )
        if len( nameparts ) == 2:
            vorname = nameparts[1].capitalize()
            nachname = nameparts[0].capitalize()
            return nachname + ", " + vorname
        else:
            return mv_id

    def getLeistungen( self, master_name, kreditor:str ) -> List[str]:
        kredleistlist:List[XLeistung] = self._iccdata.getLeistungen( master_name, kreditor )
        leistungen = [l.leistung for l in kredleistlist]
        leistungen.insert( 0, "" )
        return leistungen

    def getLeistungskennzeichen( self, master_name, kreditor, leistung ) -> XLeistung or None:
        leistungslist: List[XLeistung] = self._iccdata.getLeistungen( master_name, kreditor )
        if len( leistungslist ) > 0:
            leistungslist = [l for l in leistungslist if l.leistung == leistung]
            if len( leistungslist ) > 0:
                return leistungslist[0]
        else: return None

    # def _getLetzteBuchung_alt( self ) -> [str, str]:
    #     """
    #     Liefert den letzten Eintrag aus der Tabelle einaus
    #     :return: datum, text, so wie es im Mainwindow angezeigt werden soll
    #     """
    #     ea = self._iccdata.getLetzteBuchung()
    #     if not ea: return "", ""
    #     text = ea["debi_kredi"] + ":  " + str( ea["betrag"] ) + " €  "
    #     buchungsdatum = ea["buchungsdatum"]
    #     if buchungsdatum:
    #         datum = buchungsdatum
    #         text += " (Datum=Buchung)"
    #     else:
    #         datum = ea["write_time"][0:10]
    #         text += " (Datum=Eintragung)"
    #     return datum, text

    def getLetzteBuchung( self ) -> [str, str]:
        """
        Liefert den beim letzten Shutdown gespeicherten (einzigen) Satz aus Tabelle letztebuchung
        :return: datum, text, so wie es im Mainwindow angezeigt werden soll
        """
        datumtext:Dict = self._iccdata.getLetzteBuchung()
        return datumtext["datum"], datumtext["text"]



