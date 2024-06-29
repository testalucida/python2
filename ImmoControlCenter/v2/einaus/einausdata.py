from typing import List, Dict
import datehelper
#from v2.einaus.einauswritedispatcher import EinAusWriteDispatcher

from v2.icc.constants import EinAusArt, Umlegbar
from v2.icc.iccdata import IccData, DbAction
from v2.icc.interfaces import XEinAus, XLetzteBuchung


class EinAusData( IccData ):
    def __init__(self):
        IccData.__init__( self )
        #self._dispatch:EinAusWriteDispatcher = EinAusWriteDispatcher.inst()
        # Dass der Dispatcher von EinAusData aufgerufen wird, ist unscharf, da in diesem Modul nicht
        # bekannt ist, ob der Schreibzugriff im Rahmen einer größeren Transaktion stattfindet oder ob die
        # Transaktion nur einen einzigen Schreibzugriff beinhaltet.
        # Wenn also 10 Inserts stattfinden sollen, nach dem neunten aber ein Rollback erfolgt, wurde der
        # Dispatcher fälschlicherweise 9 mal über ein hinzugefügtes EinAus-Objekt informiert.
        # Da dieses Modul aber schön zentral ist, und der Dispatcher nur für die *Anzeige* der Gesamteinnahmen und -ausgaben
        # sorgt, erscheint diese Ungenauigkeit tolerabel.

    def insertEinAusZahlung( self, x:XEinAus ):
        """
        Fügt der Tabelle <einaus> eine Zahlung hinzu.
        Macht keinen Commit.
        :param x: Daten der Zahlung
        :return: die id des neu angelegten einaus-Satzes
        """
        mobj_id = "NULL" if not x.mobj_id else "'%s'" % x.mobj_id
        sab_id = "NULL" if not x.sab_id else str( x.sab_id )
        hga_id = "NULL" if not x.hga_id else str( x.hga_id )
        nka_id = "NULL" if not x.nka_id else str( x.nka_id )
        reise_id = "NULL" if not x.reise_id else str( x.reise_id )
        ea_art_db = EinAusArt.getDbValue( x.ea_art )
        verteilt_auf = "NULL" if not x.verteilt_auf else str( x.verteilt_auf )
        umlegbar = "NULL" if not x.umlegbar else "'" + x.umlegbar + "'"
        buchungsdatum = "NULL" if not x.buchungsdatum else "'" + x.buchungsdatum + "'"
        buchungstext = "NULL" if not x.buchungstext else "'" + x.buchungstext + "'"
        leistung = "NULL" if not x.leistung else "'" + x.leistung + "'"
        writetime = datehelper.getCurrentTimestampIso()
        sql = "insert into einaus " \
              "( master_name, mobj_id, debi_kredi, leistung, sab_id, hga_id, nka_id, reise_id, " \
              "  jahr, monat, betrag, ea_art, verteilt_auf, umlegbar, " \
              "  buchungsdatum, buchungstext, write_time ) " \
              "values" \
              "(   '%s',       %s,       '%s',        %s,       %s,    %s,     %s,      %s,  " \
              "    %d, '%s',   %.2f,   '%s',     %s,           %s," \
              "    %s,         %s,        '%s' ) " % ( x.master_name, mobj_id, x.debi_kredi, leistung, sab_id,
                                                       hga_id, nka_id, reise_id,
                                                        x.jahr, x.monat, x.betrag,
                                                        ea_art_db, verteilt_auf, umlegbar,
                                                        buchungsdatum, buchungstext, writetime )
        inserted_id = self.writeAndLog( sql, DbAction.INSERT, "einaus", "ea_id", 0,
                                        newvalues=x.toString( printWithClassname=True ), oldvalues=None )
        x.ea_id = inserted_id
        x.write_time = writetime

    def updateEinAusZahlung( self, x:XEinAus ) -> int:
        """
        Ändert die Ein-Aus-Zahlung mit der ID x.ea_id mit den in <x> enthaltenen Werten.
        :param x:
        :return: die Anzahl der geänderten Sätze, also 1 bzw. 0, wenn es die angegebene x.ea_id nicht gibt.
        """
        # den alten Zustand lesen, er wird in die Log-Tabelle geschrieben
        oldX = self.getEinAusZahlung( x.ea_id )
        oldX.ea_art = EinAusArt.getDbValue( oldX.ea_art )
        sab_id = "NULL" if not x.sab_id else str( x.sab_id )
        hga_id = "NULL" if not x.hga_id else str( x.hga_id )
        nka_id = "NULL" if not x.nka_id else str( x.nka_id )
        reise_id = "NULL" if not x.reise_id else str( x.reise_id )
        ea_art_db = EinAusArt.getDbValue( x.ea_art )
        verteilt_auf = "NULL" if not x.verteilt_auf else str( x.verteilt_auf )
        umlegbar = "NULL" if not x.umlegbar else "'" + x.umlegbar + "'"
        buchungsdatum = "NULL" if not x.buchungsdatum else "'" + x.buchungsdatum + "'"
        buchungstext = "NULL" if not x.buchungstext else "'" + x.buchungstext + "'"
        leistung = "NULL" if not x.leistung else "'" + x.leistung + "'"
        writetime = datehelper.getCurrentTimestampIso()
        sql = "update einaus " \
              "set " \
              "master_name = '%s', " \
              "mobj_id = '%s', " \
              "debi_kredi = '%s', " \
              "leistung = %s, " \
              "sab_id = %s, " \
              "hga_id = %s, " \
              "nka_id = %s, " \
              "reise_id = %s, " \
              "jahr = %d, " \
              "monat = '%s', " \
              "betrag = %.2f, " \
              "ea_art = '%s', " \
              "verteilt_auf = %s, " \
              "umlegbar = %s, " \
              "buchungsdatum = %s, " \
              "buchungstext = %s, " \
              "write_time = '%s' " \
              "where ea_id = %d " % (x.master_name, x.mobj_id, x.debi_kredi, leistung, sab_id, hga_id, nka_id, reise_id,
                                       x.jahr, x.monat, x.betrag,
                                       ea_art_db, verteilt_auf, umlegbar,
                                       buchungsdatum, buchungstext,
                                       writetime, x.ea_id )
        rowsAffected = self.writeAndLog( sql, DbAction.UPDATE, "einaus", "ea_id", x.ea_id,
                                         newvalues=x.toString( True ), oldvalues=oldX.toString( True ) )
        x.write_time = writetime
        #self._dispatch.einaus_updated( x, oldX )
        return rowsAffected

    def deleteEinAusZahlung( self, ea_id:int ):
        """
        Löscht eine Zahlung aus <einaus>.
        Macht keinen Commit.
        :param ea_id:
        :return:
        """
        x = self.getEinAusZahlung( ea_id )
        sql = "delete from einaus where ea_id = %d" % ea_id
        self.writeAndLog( sql, DbAction.DELETE, "einaus", "ea_id", ea_id,
                          newvalues=None, oldvalues=x.toString( printWithClassname=True )  )
        #self._dispatch.einaus_deleted( ea_id )

    def getEinnahmenSumme( self, jahr:int ) -> float:
        """ Liefert die Summe aller Einnahmen (betrag > 0) im Jahr <jahr>"""
        sql = "select sum(betrag) as sum_ein " \
              "from einaus " \
              "where jahr = %d " \
              "and betrag > 0 " % jahr
        d = self.readOneGetDict( sql )
        summe = d["sum_ein"]
        return 0 if not summe else summe

    def getAuszahlungenSummeOhneHGV( self, jahr:int ) -> float:
        """ Liefert die Summe aller Auszahlungen (= negative Beträge) OHNE HG-Vorausz. im Jahr <jahr>"""
        sql = "select sum(betrag) as sum_aus from einaus " \
             "where jahr = %d " \
             "and betrag < 0 " \
             "and ea_art != '%s' " % ( jahr, EinAusArt.HAUSGELD_VORAUS.dbvalue )
        d = self.readOneGetDict( sql )
        summe = d["sum_aus"]
        return 0 if not summe else summe

    def getHGVAuszahlungenSumme( self, jahr:int ) -> float:
        """ Liefert die Summe der HGV-Zahlungen im Jahr <jahr>"""
        sql = "select sum(betrag) as sum_hgv from einaus " \
              "where jahr = %d " \
              "and ea_art = '%s' " % (jahr, EinAusArt.HAUSGELD_VORAUS.dbvalue)
        d = self.readOneGetDict( sql )
        summe = d["sum_hgv"]
        return 0 if not summe else summe

    def getEinAusZahlung( self, ea_id:int ) -> XEinAus:
        sql = "select ea_id, master_name, mobj_id, debi_kredi, leistung, sab_id, hga_id, nka_id, reise_id, jahr, monat, " \
              "betrag, ea_art, verteilt_auf, umlegbar, buchungsdatum, buchungstext, write_time " \
              "from einaus " \
              "where ea_id = %d " % ea_id
        x = self.readOneGetObject( sql, XEinAus )
        self._mapDbValueToDisplay( (x,) )
        return x

    def getEaIdAndBetragByForeignKey( self, foreignKeyName:str, foreignKeyValue:int ) -> Dict:
        """
        :param foreignKeyName:
        :param foreignKeyValue:
        :return: Dictionary mit den Keys ea_id und betrag
        """
        sql = "select ea_id, betrag " \
              "from einaus " \
              "where %s = %d " % (foreignKeyName, foreignKeyValue )
        dic = self.readOneGetDict( sql )
        return dic

    def getEinAuszahlungenJahr( self, jahr:int ) -> List[XEinAus]:
        """
        Liefert alle Ein- und Auszahlungen im jahr <jahr>
        :param jahr: z.B. 2022
        :return:
        """
        sql = "select ea_id, master_name, coalesce(mobj_id, '') as mobj_id, coalesce(debi_kredi, '') as debi_kredi, " \
              "coalesce(leistung, '') as leistung, " \
              "sab_id, hga_id, nka_id, reise_id, jahr, monat, betrag, ea_art, " \
              "coalesce(verteilt_auf, '') as verteilt_auf, umlegbar, " \
              "coalesce( buchungsdatum, '') as buchungsdatum, coalesce(buchungstext, '') as buchungstext, " \
              "write_time " \
              "from einaus " \
              "where jahr = %d "  % jahr
        xlist = self.readAllGetObjectList( sql, XEinAus )
        self._mapDbValueToDisplay( xlist )
        return xlist

    def getEinAusZahlungen( self, ea_art_display:str, jahr: int, additionalWhereClause="" ) -> List[XEinAus]:
        """
        Liefert eine nicht sortierte Liste von XEinAus-Objekten, die den gegebenen Kriterien genügen
        :param ea_art_display: erwartet wird hier der display-Wert der versch. EinAusArten, z.B. "Bruttomiete"
        :param jahr: yyyy
        :param additionalWhereClause: optionale zusätzliche Selektionsbedingung ( z.B. "and sab_id > 0")
        :return:  List[XEinAus]
        """
        ea_art_db = EinAusArt.getDbValue( ea_art_display )
        sql = "select ea_id, master_name, mobj_id, debi_kredi, leistung, sab_id, hga_id, nka_id, reise_id, " \
              "jahr, monat, betrag, " \
              "ea_art, verteilt_auf, umlegbar, buchungsdatum, buchungstext, write_time " \
              "from einaus " \
              "where jahr = %d " \
              "and ea_art = '%s' " % ( jahr, ea_art_db )
        if additionalWhereClause:
            sql += additionalWhereClause
        xlist = self.readAllGetObjectList( sql, XEinAus )
        self._mapDbValueToDisplay( xlist )
        return xlist

    # def getAnzahlEinAus( self, ea_art_display:str, jahr: int, additionalWhereClause="" ) -> int:
    #     ea_art_db = EinAusArt.getDbValue( ea_art_display )
    #     sql = "select count(*) " \
    #           "from einaus " \
    #           "where jahr = %d " \
    #           "and ea_art = '%s' " % (jahr, ea_art_db)
    #     if additionalWhereClause:
    #         sql += additionalWhereClause

    def getEinAuszahlungen2( self, ea_art_display:str, jahr:int, monat:str, mobj_id:str ) -> List[XEinAus]:
        """
        Liefert eine Liste von XEinAus-Objekten, die den gegebenen Kriterien genügen
        :param ea_art_display: EinAusArt
        :param jahr: yyyy
        :param monat: z.B. "jan", "mrz",... siehe iccMonthShortNames
        :param mobj_id: z.B. "thomasmann"
        :return: List[XEinAus]
        """
        ea_art_db = EinAusArt.getDbValue( ea_art_display )
        sql = "select ea_id, master_name, mobj_id, debi_kredi, leistung, sabid, hga_id, nka_id, reise_id, " \
              "jahr, monat, betrag, " \
              "ea_art, verteilt_auf, umlegbar, buchungsdatum, buchungstext, write_time " \
              "from einaus " \
              "where jahr = %d " \
              "and monat = '%s' " \
              "and mobj_id = '%s' " \
              "and ea_art = '%s' " % (jahr, monat, mobj_id, ea_art_db)
        xlist = self.readAllGetObjectList( sql, XEinAus )
        self._mapDbValueToDisplay( xlist )
        return xlist

    def getEinAuszahlungen3( self, ea_art_display:str, jahr:int, monat:str, debikredi:str ) -> List[XEinAus]:
        """
        Liefert eine Liste von XEinAus-Objekten, die den gegebenen Kriterien genügen
        :param ea_art_display: display value (string) der EinAusArt
        :param jahr: yyyy
        :param monat: z.B. "jan", "mrz",... siehe iccMonthShortNames
        :param debikredi: ID des Mieters oder Name der WEG oder Firma
        :return: List[XEinAus]
        """
        ea_art_db = EinAusArt.getDbValue( ea_art_display )
        sql = "select ea_id, master_name, mobj_id, debi_kredi, leistung, sab_id, hga_id, nka_id, reise_id, " \
              "jahr, monat, betrag, " \
              "ea_art, verteilt_auf, umlegbar, buchungsdatum, buchungstext, write_time " \
              "from einaus " \
              "where jahr = %d " \
              "and monat = '%s' " \
              "and debi_kredi = '%s' " \
              "and ea_art = '%s' " % (jahr, monat, debikredi, ea_art_db)
        xlist = self.readAllGetObjectList( sql, XEinAus )
        self._mapDbValueToDisplay( xlist )
        return xlist

    def getEinAuszahlungen4( self, sab_id:int, jahr:int, monat:str ) -> List[XEinAus]:
        """
        Liefert eine Liste von XEinAus-Objekten, die den gegebenen Kriterien genügen
        :param sab_id: SollAbschlag-ID
        :param jahr: yyyy
        :param monat: z.B. "jan", "mrz",... siehe iccMonthShortNames
        :param mv_id: ID des Mieters
        :return: List[XEinAus]
        """
        sql = "select ea.ea_id, ea.master_name, ea.mobj_id, ea.debi_kredi, ea.leistung, ea.sab_id, ea.hga_id, " \
              "ea.nka_id, ea.reise_id, " \
              "ea.jahr, ea.monat, ea.betrag, " \
              "ea.ea_art, ea.verteilt_auf, ea.umlegbar, ea.buchungsdatum, ea.buchungstext, ea.write_time," \
              "sab.vnr " \
              "from einaus ea " \
              "inner join sollabschlag sab on sab.sab_id = ea.sab_id " \
              "where ea.jahr = %d " \
              "and ea.monat = '%s' " \
              "and ea.sab_id = %d " % (jahr, monat, sab_id )
        xlist = self.readAllGetObjectList( sql, XEinAus )
        self._mapDbValueToDisplay( xlist )
        return xlist

    def getEinAuszahlungen5( self, ea_art_display: str, jahr: int, monat: str, debikredi: str, mobj_id:str ) -> List[XEinAus]:
        """
        Liefert eine Liste von XEinAus-Objekten, die den gegebenen Kriterien genügen
        :param ea_art_display: display value (string) der EinAusArt
        :param jahr: yyyy
        :param monat: z.B. "jan", "mrz",... siehe iccMonthShortNames
        :param debikredi: ID des Mieters oder Name der WEG oder Firma
        :param mobj_id: ID des Mietobjekts
        :return: List[XEinAus]
        """
        ea_art_db = EinAusArt.getDbValue( ea_art_display )
        sql = "select ea_id, master_name, mobj_id, debi_kredi, leistung, sab_id, hga_id, nka_id, reise_id, " \
              "jahr, monat, betrag, " \
              "ea_art, verteilt_auf, umlegbar, buchungsdatum, buchungstext, write_time " \
              "from einaus " \
              "where jahr = %d " \
              "and monat = '%s' " \
              "and debi_kredi = '%s' " \
              "and mobj_id = '%s' " \
              "and ea_art = '%s' " % (jahr, monat, debikredi, mobj_id, ea_art_db)
        xlist = self.readAllGetObjectList( sql, XEinAus )
        self._mapDbValueToDisplay( xlist )
        return xlist

    def getEinAuszahlungenByHgaId( self, hga_id:int ) -> List[XEinAus]:
        sql = "select ea_id, master_name, debi_kredi, hga_id, jahr, monat, betrag, " \
              "ea_art, buchungsdatum, buchungstext, write_time " \
              "from einaus " \
              "where hga_id = %d " % hga_id
        xlist = self.readAllGetObjectList( sql, XEinAus )
        self._mapDbValueToDisplay( xlist )
        return xlist

    def getEinAuszahlungenByNkaId( self, nka_id:int ) -> List[XEinAus]:
        sql = "select ea_id, master_name, debi_kredi, hga_id, jahr, monat, betrag, " \
              "ea_art, buchungsdatum, buchungstext, write_time " \
              "from einaus " \
              "where nka_id = %d " % nka_id
        xlist = self.readAllGetObjectList( sql, XEinAus )
        self._mapDbValueToDisplay( xlist )
        return xlist

    def _mapDbValueToDisplay( self, xlist:List[XEinAus] ):
        for x in xlist:
            if x.ea_art:
                x.ea_art = EinAusArt.getDisplay( x.ea_art )

######################################################################

def test5():
    data = EinAusData()
    x = data.getLetzteZahlung()
    print( x )

def test4():
    data = EinAusData()
    try:
        l = data.getEinAuszahlungenByHgaId( 28 )
        print( "l: ", len(l) )
    except Exception as ex:
        print( "Exception: " + str( ex ) )

def test3():
    data = EinAusData()
    try:
        master = data.getMastername( "remgius" )
        print( master )
    except Exception as ex:
        print( "Exception: " + str(ex) )


def test2():
    x = XEinAus()
    x.master_name = "GULP"
    x.mobj_id = "schluck"
    x.debi_kredi = "hans_otto"
    x.jahr = 2022
    x.monat = "okt"
    x.betrag = 234.55
    x.ea_art = EinAusArt.BRUTTOMIETE.dbvalue

    data = EinAusData()
    try:
        #data.begin_transaction()
        data.insertEinAusZahlung( x )
        data.commit()
        #data.commit_transaction()
    except Exception as ex:
        print( str(ex) )

def test1():
    #db = DatabaseCommon( "/home/martin/Projects/python/ImmoControlCenter/v2/icc/immo.db" )
    data = EinAusData()
    sql = "update einaus set ea_art = 'lfdskj' where ea_id = 3 "
    ret = data.write( sql )
    print( ret )
    #data.commit()
    data.rollback()


def test():
    x = XEinAus()
    x.master_name = "ER_Heuschlag"
    x.mobj_id = "heuschlag"
    x.ea_art = EinAusArt.ALLGEMEINE_KOSTEN.display
    x.jahr = 2022
    x.monat = "nov"
    x.umlegbar = "nein"
    x.verteilt_auf = 1
    x.buchungsdatum = "2022-11-29"
    x.betrag = 100.0

    data = EinAusData()
    try:
        data.insertEinAusZahlung( x )
        data.commit()
    except Exception as ex:
        print( str(ex) )