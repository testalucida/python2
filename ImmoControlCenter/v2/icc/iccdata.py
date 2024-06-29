from typing import List, Tuple, Dict

import datehelper
from base.databasecommon2 import DatabaseCommon
from base.interfaces import XBase
from v2.icc.constants import EinAusArt, Umlegbar

from v2.icc.definitions import DATABASE
from v2.icc.interfaces import XHandwerkerKurz, XEinAus, XMietverhaeltnisKurz, XVerwaltung, XMasterobjekt, XMietobjekt, \
    XKreditorLeistung, XLeistung, XMtlHausgeld, XVerwalter, XVerwalter2


class DbAction:
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

class IccData( DatabaseCommon ):
    """
    Enthält die DB-Zugriffe für Miet- UND Masterobjekte
    """
    def __init__(self):
        self._dbCommon = DatabaseCommon.__init__( self, DATABASE )

    def getIccTabellen( self ) -> List[str]:
        sql = "select name from sqlite_master where type = 'table' order by name"
        tupleList = self.read( sql )
        l = [x[0] for x in tupleList]
        return l

    def getJahre( self ) -> List[int]:
        """
        Liefert die Jahreszahlen, zu denen Daten in der Tabelle einaus erfasst sind.
        :return:
        """
        sql = "select distinct jahr " \
              "from einaus " \
              "order by jahr desc "
        l: List[Dict] = self.readAllGetDict( sql )
        return [d["jahr"] for d in l]

    # def getUpdateStmtFromDict(self, table:str, colVals:Dict) -> str:
    #     """
    #     Erstellt ein SQL-Update-Statement für die Tabelle <table> mit
    #     den zu ändernden Columns.
    #     :param table: NAme der Tabelle
    #     :param colVals: Dictionary mit dem Aufbau:
    #                 column name : column value
    #                 Achtung: in value muss der neue Wert so stehen, wie
    #                 er in die DB geschrieben wird, also strings mit
    #                 Hochkomma, numerische Werte ohne.
    #     :return: das erstellte Statment
    #     """
    #     sql = "update %s set " % table
    #     for col, val in colVals.items():
    #         sql += (col + " = " + ??) # todo

    def getMietverhaeltnisseKurz( self, jahr: int, orderby: str = None ) -> List[XMietverhaeltnisKurz]:
        """
        Liefert zu allen Mietverhältnissen, die in <jahr> aktiv sind, die Werte der Spalten mv_id, mobj_id, von, bis.
        Geliefert werden also neben den "Langläufern" MV, die während <jahr> enden und MV, die während MV beginnen.
        :param jahr:
        :param orderby:
        :return:
        """
        sql = "select id, mv_id, mobj_id, von, bis " \
              "from mietverhaeltnis " \
              "where substr(von, 0, 5) <= '%s' " \
              "and (bis is NULL or bis = '' or substr(bis, 0, 5) >= '%s') " % (jahr, jahr)
        if orderby:
            sql += "order by %s " % (orderby)
        return self.readAllGetObjectList( sql, XMietverhaeltnisKurz )

    def getKreditoren( self ) -> List[str]:
        sql = "select distinct kreditor from kreditorleistung order by kreditor "
        tuplelist = self.read( sql )
        return [t[0] for t in tuplelist]

    def existsKreditor( self, master_name:str, kreditor:str ) -> bool:
        sql = "select count(*) as cnt " \
              "from kreditorleistung " \
              "where master_name = '%s' " \
              "and kreditor = '%s' " % ( master_name, kreditor )
        tuplelist = self.read( sql )
        return tuplelist[0][0] > 0

    def existsKreditorLeistung( self, master_name:str, kreditor:str, leistung:str ) -> bool:
        sql = "select count(*) as cnt " \
              "from kreditorleistung " \
              "where master_name = '%s' " \
              "and kreditor = '%s' " \
              "and leistung = '%s' " % ( master_name, kreditor, leistung )
        tuplelist = self.read( sql )
        return tuplelist[0][0] > 0

    def getHandwerkerKurz( self, orderby:str=None ) -> List[XHandwerkerKurz]:
        """
        Selektiert alle Handwerkerdaten aus der Tabelle <handwerker>.
        :param orderby: Wenn angegeben, muss der Inhalt dem Spaltennamen entsprechen, nach dem sortiert werden soll.
                        Defaultmäßig wird nach dem Namen sortiert.
        :return:
        """
        if not orderby: orderby = "name"
        sql = "select id, name, branche, adresse from handwerker order by %s " % orderby
        xlist = self.readAllGetObjectList( sql, XHandwerkerKurz )
        return xlist

    def getMasterobjekte( self ) -> List[XMasterobjekt]:
        sql = "select master_id, master_name, lfdnr, strasse_hnr, plz, ort, gesamt_wfl, anz_whg, " \
              "afa_wie_vj, afa, afa_proz, hauswart, hauswart_telefon, hauswart_mailto, heizung, " \
              "angeschafft_am, veraeussert_am, bemerkung " \
              "from masterobjekt " \
              "where aktiv = 1 " \
              "order by master_name asc "
        xlist = self.readAllGetObjectList( sql, XMasterobjekt )
        return xlist

    def getMastername( self, mobj_id:str ) -> str:
        sql = "select master_name from mietobjekt where mobj_id = '%s' " % mobj_id
        tpl:List[Tuple] = self.read( sql )
        if len( tpl ) == 0:
            return ""
        return tpl[0][0]

    def getMietobjekte( self, master_name:str ) -> List[XMietobjekt]:
        # Wird vom Dialog "Neue Zahlung anlegen" benutzt
        sql = "select mobj_id, whg_bez, qm, container_nr, bemerkung " \
              "from mietobjekt " \
              "where master_name = '%s' " \
              "order by mobj_id " % master_name
        xlist = self.readAllGetObjectList( sql, XMietobjekt )
        return xlist

    def getVerwaltung( self, vwg_id:int ) -> XVerwaltung:
        sql = "select vwg_id, master_name, vw_id, weg_name, von, bis " \
              "from verwaltung " \
              "where vwg_id = %d " % vwg_id
        return self.readOneGetObject( sql, XVerwaltung )

    def getVerwaltungen( self, jahr:int ) -> List[XVerwaltung]:
        minbis = "%d-%02d-%02d" % (jahr, 1, 1)
        maxvon = "%d-%02d-%02d" % (jahr, 12, 31)
        sql = "select vwg_id, master_name, " \
              "vw_id, coalesce(weg_name, '') as weg_name, von, coalesce(bis, '') as bis " \
              "from verwaltung " \
              "where (bis is NULL or bis = '' or bis >= '%s') " \
              "and not von > '%s' " \
              "order by weg_name asc " % ( minbis, maxvon )
        l: List[XVerwaltung] = self.readAllGetObjectList( sql, XVerwaltung )
        return l

    def getVerwalterNameTelMailto( self, master_name:str ) -> Dict or None:
        """
        Liefert den aktuelle Verwalter zu einem Mietobjekt
        :param master_name:
        :return: ein Dict mit den keys name und telefon_1
        """
        sql = "select vw.name, vw.telefon_1, mailto " \
              "from verwalter vw " \
              "inner join verwaltung vwg on vwg.vw_id = vw.vw_id " \
              "where vwg.master_name = '%s' " \
              "and vwg.von <= CURRENT_DATE " \
              "and (vwg.bis is NULL or vwg.bis = '' or vwg.bis >= CURRENT_DATE )" % master_name
        return self.readOneGetDict( sql )

    def getVerwalterDetails( self, vw_id:str ) -> XVerwalter:
        """
        DEPRECATED: Liefert die beiden Ansprechpartner aus Tabelle verwalter.
        Sinnvoller wäre es, den einen Ansprechpartner für ein bestimmtes Objekt aus Tabelle verwaltung
        zu selektieren. Genau das macht die Methode getVerwalterDetails2()

        Liefert alle Daten zu Verwalter <vw_id>
        :param vw_id:
        :return:
        """
        sql = "select vw_id, name, strasse, plz_ort, telefon_1, telefon_2, mailto, ansprechpartner_1, ansprechpartner_2, " \
              "bemerkung " \
              "from verwalter " \
              "where vw_id = '%s' " % vw_id
        return self.readOneGetObject( sql, XVerwalter )

    def getVerwalterDetails2( self, vw_id:str, master_name:str ) -> XVerwalter2:
        """
        Liefert alle Daten zu Verwalter <vw_id> außer den beiden Ansprechpartnern.
        Der objektbezogene Ansprechpartner wird aus Tab. verwaltung geliefert.
        :param vw_id:
        :param master_name: um den Ansprechpartner für dieses Objekt zu ermitteln
        :return:
        """
        sql = "select vw.vw_id, vw.name, vw.strasse, vw.plz_ort, vw.telefon_1, vw.telefon_2, vw.mailto, vw.bemerkung, " \
              "vwg.vwg_id, vwg.vw_ap " \
              "from verwalter vw " \
              "inner join verwaltung vwg on vwg.vw_id = vw.vw_id " \
              "where vw.vw_id = '%s' " \
              "and vwg.master_name = '%s' " \
              "and vwg.von <= CURRENT_DATE " \
              "and (vwg.bis is NULL or vwg.bis = '' or vwg.bis >= CURRENT_DATE) " % (vw_id, master_name)
        return self.readOneGetObject( sql, XVerwalter2 )

    def getAnschaffungsUndVerkaufsdatum( self, mobj_id:str ) -> [str, str]:
        sql = "select master.angeschafft_am, master.veraeussert_am " \
              "from masterobjekt master " \
              "inner join mietobjekt mobj on mobj.master_name = master.master_name " \
              "where mobj.mobj_id = '%s' " % mobj_id
        d = self.readOneGetDict( sql )
        veraeussert_am = "" if not d["veraeussert_am"] else d["veraeussert_am" ]
        return [d["angeschafft_am"], veraeussert_am]

    def getAnschaffungsUndVerkaufsdatum2( self, master_name:str ) -> [str, str]:
        sql = "select angeschafft_am, veraeussert_am " \
              "from masterobjekt " \
              "where master_name = '%s' " % master_name
        d = self.readOneGetDict( sql )
        veraeussert_am = "" if not d["veraeussert_am"] else d["veraeussert_am" ]
        return [d["angeschafft_am"], veraeussert_am]

    def getKreditorLeistungen( self, master_name:str ) -> List[XKreditorLeistung]:
        sql = "select kredleist_id, master_name, kreditor, leistung, umlegbar, ea_art, bemerkung " \
              "from kreditorleistung " \
              "where master_name = '%s' " % master_name
        l: List[XKreditorLeistung] = self.readAllGetObjectList( sql, XKreditorLeistung )
        for leist in l:
            leist.ea_art = EinAusArt.getDisplay( leist.ea_art )
        return l

    def getLeistungen( self, master_name:str, kreditor:str ) -> List[XLeistung]:
        sql = "select leistung, umlegbar, ea_art " \
              "from kreditorleistung " \
              "where master_name = '%s' " \
              "and kreditor = '%s' " % (master_name, kreditor)
        l: List[XKreditorLeistung] = self.readAllGetObjectList( sql, XKreditorLeistung )
        for leist in l:
            leist.ea_art = EinAusArt.getDisplay( leist.ea_art )
        return l

    def _getLetzteBuchung_alt( self ) -> Dict:
        """
        Liefert ein paar Kenndaten der letzten Zahlung, die im Hauptfenster als "Letzte Buchung" angezeigt werden.
        :return: einen Dict mit den keys debi_kredi, leistung, betrag, buchungsdatum, write_time
        """
        sql = "select max(write_time) as write_time from einaus "
        dic = self.readOneGetDict( sql )
        write_time = dic["write_time"]
        if not write_time: return {"debi_kredi":"", "leistung": "",
                                   "betrag": 0.0, "buchungsdatum":"1900-01-01", "write_time": "1900-01-01:00.00.00"}
        sql = "select debi_kredi, leistung, betrag, buchungsdatum, write_time " \
              "from einaus " \
              "where write_time = '%s' " % write_time
        d = self.readOneGetDict( sql )
        return d

    def getLetzteBuchung( self ) -> Dict:
        return self.readOneGetDict( "select datum, text from letztebuchung" )

    def deleteLetzteBuchung( self ) -> int:
        sql = "delete from letztebuchung"
        return self.write( sql )

    def insertLetzteBuchung( self, datum: str, text: str ) -> int:
        sql = "insert into letztebuchung (datum, text) values ('%s', '%s')" % (datum, text)
        return self.write( sql )

    def insertKreditorLeistung( self, x:XKreditorLeistung ):
        bemerkung = "NULL" if not x.bemerkung else "'%s'" % x.bemerkung
        leistung = "NULL" if not x.leistung else "'%s'" % x.leistung
        ea_art_dbvalue = EinAusArt.getDbValue( x.ea_art )
        sql = "insert into kreditorleistung " \
              "(master_name, kreditor, leistung, umlegbar, ea_art, bemerkung) " \
              "values" \
              "('%s', '%s', %s, '%s', '%s', %s) " % (x.master_name, x.kreditor, leistung, x.umlegbar, ea_art_dbvalue, bemerkung )
        inserted_id = self.writeAndLog( sql, DbAction.INSERT, "kreditorleistung", "kredleist_id", 0,
                                        newvalues=x.toString( printWithClassname=True ), oldvalues=None )
        x.kredleist_id = inserted_id

    def updateVerwalterKontakt(self, vw_id:str, telefon_1:str, telefon_2:str, mailto:str):
        # aktuellen Satz holen wg WriteLog:
        sql = "select telefon_1, telefon_2, mailto " \
              "from verwalter " \
              "where vw_id = '%s'" % vw_id
        oldD = self.readOneGetDict(sql)
        sql = "update verwalter " \
              "set telefon_1 = '%s', " \
              "telefon_2 = '%s', " \
              "mailto = '%s' " \
              "where vw_id = '%s' " % (telefon_1, telefon_2, mailto, vw_id)
        newD = {"telefon_1": telefon_1, "telefon_2" : telefon_2, "mailto" : mailto}
        rowsAffected = self.writeAndLog(sql, DbAction.UPDATE,
                                        table="verwalter", id_name="vw_id", id_value=vw_id,
                                        newvalues=str(newD), oldvalues=str(oldD))
        return rowsAffected

    def updateVerwaltungAnsprechpartner(self, vwg_id:int, vw_ap:str):
        # aktuellen Satz holen wg WriteLog:
        sql = "select vw_ap from verwaltung where vwg_id = %d" % vwg_id
        oldAp = self.readOneGetDict( sql )
        sql = "update verwaltung " \
              "set vw_ap = '%s' " \
              "where vwg_id = %d " % (vw_ap, vwg_id)
        newAp = {"vw_ap": vw_ap}
        rowsAffected = self.writeAndLog(sql, DbAction.UPDATE,
                                        table="verwaltung", id_name="vwg_id", id_value=vwg_id,
                                        newvalues=str(newAp), oldvalues=str(oldAp))
        return rowsAffected

    def writeAndLog( self, sql: str, action:str, table:str, id_name:str, id_value:int or str,
                     newvalues:str=None, oldvalues:str=None ) -> int:
        """
        Führt <sql> aus.
        Veranlasst einen Log-Eintrag in Tabelle <writelog>
        :param sql: die auszuführende Query. Wird im Anschluss in <writelog> eingetragen.
        :param action:  insert, update, delete - gem. class DbAction
        :param table: der Name der Tabelle, die vom Schreibvorgang betroffen ist. Für Log-Zwecke
        :param id_name: der Name der Id in <table>
        :param id_value: der Wert der Id in <table> (Identifikation des zu ändernden/zu löschenden Satzes.
                        Ist 0 im Insert-Fall.)
        :param newvalues: die Werte im String-Format, mit denen der Insert/Update erfolgt. Z.B. ermittelt mit
                          XBase.toString()
        :param oldvalues: die Werte vor dem Update. None bei Insert
        :param commit:
        :return:
        """
        try:
            ret = self.write( sql )
        except Exception as ex:
            msg = "Exception\n" + str(ex) + "\nbei Ausführung des Statements\n" + sql + "\n"
            raise Exception( msg )
        if action == DbAction.INSERT:
            id_value = ret
        self._writeLog( sql, action, table, id_name, id_value, newvalues, oldvalues )
        return ret

    def _writeLog( self, sql:str, action:str, table:str, id_name:str, id_value:int or str,
                   newvalues:str=None, oldvalues:str=None ):
        sql = sql.replace( "'", "\"" )
        if newvalues:
            newvalues = newvalues.replace( "'", "\"" )
        if oldvalues:
            oldvalues = oldvalues.replace( "'", "\"" )
        ts = datehelper.getCurrentTimestampIso()
        transId = self.getTransactionId()
        if isinstance( id_value, str ):
            id_value = "'" + id_value + "'"
        sql2 = "insert into writelog " \
              "(trans_id, sql, action, table_name, id_name, id_value, newvalues, oldvalues, timestamp) " \
              "values " \
              "( %d,      '%s', '%s',  '%s',         '%s',    %s,     '%s',        '%s',      '%s' )" \
              % (transId, sql, action, table,     id_name, id_value, newvalues, oldvalues,    ts )
        try:
            self.write( sql2 )
        except Exception as ex:
            print( "Fehler beim write in Tabelle writelog. SQL:\n%s" % sql2 )
            msg = "Exception\n" + str(ex) + "\nbei Ausführung des Statements\n" + sql2 + "\n"
            raise Exception( msg )

########################################################################################
########################################################################################

def testupdateVerwalterKontakt():
    data = IccData()
    data.updateVerwalterKontakt( "palm", "", "", "mailtome@mycheri.fr")
    data.commit()

def testupdateVerwaltungAnsprechpartner():
    data = IccData()
    data.updateVerwaltungAnsprechpartner( 22, "Frau HellsBells")
    data.commit()

# if __name__ == "__main__":
#     testupdateVerwaltungAnsprechpartner()

def testInsertKreditorleistung():
    data = IccData()
    x = XKreditorLeistung()
    x.ea_art = EinAusArt.REPARATUR.display
    x.master_name = "HOM_Remigius"
    x.kreditor = "Bullenhaupt"
    x.leistung = "Küchenberatung"
    x.umlegbar = Umlegbar.NEIN.value
    data.insertKreditorLeistung( x )
    ########data.commit()
    print( "okay" )

def test():
    data = IccData()
    a, v = data.getAnschaffungsUndVerkaufsdatum( "kleist_12")
    print( a, ", ", v )
    verwlist = data.getVerwaltungen( 2022 )
    print( verwlist )
