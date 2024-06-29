import numbers
import sqlite3
from typing import List, Dict, Tuple, Type

from PySide2.QtWidgets import QApplication

import datehelper
from base.interfaces import XBase
from base.messagebox import WarningBox, InfoBox, ErrorBox, MessageBox
from v2.geschaeftsreise.geschaeftsreiselogic import GeschaeftsreiseLogic
from v2.icc.constants import EinAusArt, Umlegbar, iccMonthShortNames
#from v2.icc.definitions import DATENUEBERNAHME_DIR, ROOT_DIR
from v2.icc.interfaces import XPauschale, XGeschaeftsreise, XEinAus
from v2.sammelabgabe.sammelabgabelogic import SammelabgabeLogic


class Data:
    def __init__( self, pathToDb ):
        self._pathToDb = pathToDb
        self._sqliteCon: sqlite3.dbapi2.Connection = sqlite3.connect( pathToDb )

    def selectTable( self, tablename, whereCond: str = "" ) -> List[Dict]:
        sql = "select * from " + tablename + " " + whereCond
        return self.readAllGetDict( sql )

    def read( self, sql: str ) -> List[Tuple]:
        cur = self._sqliteCon.cursor() # sieht umständlich aus, muss aber so gemacht werden:
                                 # mit jedem cursor()-call wird ein neuer Cursor erzeugt!
        cur.execute( sql )
        records = cur.fetchall()
        cur.close()
        return records

    @staticmethod
    def dict_factory( cursor, row ):
        d = { }
        for idx, col in enumerate( cursor.description ):
            d[col[0]] = row[idx]
        return d

    def readAllGetDict( self, sql: str ) -> List[Dict] or None:
        self._sqliteCon.row_factory = self.dict_factory
        cur = self._sqliteCon.cursor()
        cur.execute( sql )
        dicList = cur.fetchall()
        self._sqliteCon.row_factory = None
        cur.close()
        return dicList

    def readOneGetDict( self, sql: str ) -> Dict or None:
        self._sqliteCon.row_factory = self.dict_factory
        cur = self._sqliteCon.cursor()
        cur.execute( sql )
        dic = cur.fetchone()
        self._sqliteCon.row_factory = None
        cur.close()
        return dic

    def readOneGetObject( self, sql, xbase: Type[XBase] ) -> XBase or None:
        dic = self.readOneGetDict( sql )
        if dic:
            x = xbase( dic )
            return x
        return None

class SrcData( Data ):
    """
    Zugriffe auf die alte Datenbank - nur lesend
    """
    def __init__(self, pathToSrcDb ):
        Data.__init__( self, pathToSrcDb )

    def selectMietobjekte( self ):
        sql = "select mobj.mobj_id, mobj.master_id, master.master_name, mobj.whg_bez, mobj.qm, mobj.container_nr, " \
              "mobj.bemerkung, mobj.aktiv " \
              "from mietobjekt mobj " \
              "inner join masterobjekt master on master.master_id = mobj.master_id " \
              "where mobj_id > ' ' and mobj_id not like '%*' "
        return self.readAllGetDict( sql )

    def selectVerwaltung( self ):
        sql = "select vwg.master_id, vwg.mobj_id, vwg.vw_id, vwg.weg_name, vwg.von, vwg.bis, master.master_name " \
              "from verwaltung vwg " \
              "inner join masterobjekt master on master.master_id = vwg.master_id " \
              "where vwg.vw_id not in ('eickhoff', 'fritsche', 'mueller')"
        return self.readAllGetDict( sql )

    def selectMieten( self ):
        sql = "select 'bruttomiete' as ea_art, " \
              "z.mobj_id, master.master_name, mea.mv_id as debi_kredi, " \
              "z.jahr, z.monat, z.betrag, z.write_time " \
              "from zahlung z " \
              "inner join masterobjekt master on master.master_id = z.master_id " \
              "inner join mtleinaus mea on mea.meinaus_id = z.meinaus_id " \
              "where z.zahl_art = 'bruttomiete' "
        return self.readAllGetDict( sql )

    def selectSollHausgeld( self ):
        sql = "select soll.vwg_id, master.master_name, soll.von, soll.bis, soll.netto, soll.ruezufue, soll.bemerkung, " \
                "vwg.mobj_id, vwg.vw_id, vwg.weg_name " \
                "from sollhausgeld soll " \
                "inner join verwaltung vwg on vwg.vwg_id = soll.vwg_id " \
                "inner join masterobjekt master on master.master_id = vwg.master_id "
        return self.readAllGetDict( sql )

    def selectHgvZahlungen( self ):
        sql = "select 'hgv' as ea_art, " \
              "z.mobj_id, z.master_id, master.master_name, vwg.weg_name, " \
              "z.jahr, z.monat, z.betrag, z.write_time " \
              "from zahlung z " \
              "inner join masterobjekt master on master.master_id = z.master_id " \
              "inner join mtleinaus mea on mea.meinaus_id = z.meinaus_id " \
              "inner join verwaltung vwg on vwg.vwg_id = mea.vwg_id " \
              "where z.zahl_art = 'hgv' " \
              "and z.mobj_id not like '%*' "
        return self.readAllGetDict( sql )

    def selectNkaZahlungen( self ):
        sql = "select 'nka' as ea_art, " \
              "z.nka_id, z.mobj_id, z.jahr, z.monat, z.betrag, z.write_time, " \
              "nka.ab_jahr, nka.mv_id as debi_kredi, " \
              "master.master_name " \
              "from zahlung z " \
              "inner join nk_abrechnung nka on nka.nka_id = z.nka_id " \
              "inner join mietobjekt mo on mo.mobj_id = z.mobj_id " \
              "inner join masterobjekt master on master.master_id = mo.master_id "
        return self.readAllGetDict( sql )

    def selectHga( self ):
        sql = "select ab_jahr, hga.vwg_id, vwg.vw_id, vwg.mobj_id, master.master_name, " \
              "hga.betrag as forderung, hga.entnahme_rue, hga.ab_datum, hga.bemerkung " \
              "from hg_abrechnung hga " \
              "inner join verwaltung vwg on vwg.vwg_id = hga.vwg_id " \
              "inner join masterobjekt master on master.master_id = vwg.master_id "
        return self.readAllGetDict( sql )

    def selectNka( self ):
        sql = "select ab_jahr, mv_id, betrag as forderung, ab_datum, bemerkung " \
              "from nk_abrechnung "
        return self.readAllGetDict( sql )

    def selectSammelabgabeDetail( self ):
        sql = "select sam.*, master.master_name " \
              "from sammelabgabe_detail sam " \
              "inner join masterobjekt master on master.master_id = sam.master_id "
        return self.readAllGetDict( sql )

    def selectSammelzahlungen( self ):
        sql = "select z.master_id, master.master_name, z.jahr, z.betrag, z.buchungsdatum, z.buchungstext, z.write_time " \
              "from zahlung z " \
              "inner join masterobjekt master on master.master_id = z.master_id " \
              "where kostenart = 'sam'"
        return self.readAllGetDict( sql )

    def selectHgaZahlungen( self ):
        sql = "select 'hga' as ea_art, z.mobj_id, z.hga_id, z.jahr, z.monat, z.betrag, z.buchungsdatum, " \
              "z.write_time, " \
              "hga.ab_jahr, vwg.weg_name as debi_kredi, master.master_name " \
              "from zahlung z " \
              "inner join hg_abrechnung hga on hga.hga_id = z.hga_id " \
              "inner join verwaltung vwg on vwg.vwg_id = hga.vwg_id " \
              "inner join masterobjekt master on master.master_id = vwg.master_id " \
              "where zahl_art = 'hga'"
        return self.readAllGetDict( sql )

    def selectSonstAusZahlungen( self ):
        sql = "select z.kostenart as ea_art, z.mobj_id, z.hga_id, z.jahr, z.monat, z.betrag, z.umlegbar, " \
              "z.buchungstext as zbuchungstext, z.buchungsdatum, z.write_time, " \
              "sa.kreditor as debi_kredi, sa.buchungstext, sa.rgtext, sa.verteilen_auf_jahre as verteilt_auf, " \
              "master.master_name " \
              "from zahlung z " \
              "inner join sonstaus sa on sa.saus_id = z.saus_id " \
              "inner join masterobjekt master on master.master_id = z.master_id " \
              "where zahl_art = 'sonstaus' " \
              "and z.kostenart <> 'sam' " \
              "and z.mobj_id not like '%*' "
        return self.readAllGetDict( sql )

    def selectReisekosten( self ):
        sql = "select reise.id, reise.mobj_id, master.master_name, reise.von, reise.bis, reise.jahr, reise.ziel, reise.zweck, " \
              "reise.km, reise.personen, reise.uebernachtung, reise.uebernacht_kosten " \
              "from geschaeftsreise reise " \
              "inner join mietobjekt mobj on mobj.mobj_id = reise.mobj_id " \
              "inner join masterobjekt master on master.master_id = mobj.master_id "
        return self.readAllGetDict( sql )

#################################################################
class DestData( Data ):
    """
    Zugriffe auf die neue v2-Datenbank -- schreibend
    """
    def __init__(self, pathToDestDb ):
        Data.__init__( self, pathToDestDb )
        self._sqliteCon.isolation_level = None
        self._cursor = self._sqliteCon.cursor()
        self._cursor.execute( "begin" )

    def selectHgaKerndaten( self ):
        sql = "select hga.hga_id, hga.ab_jahr, hga.vwg_id, hga.mobj_id, vwg.weg_name, ab_datum " \
              "from hg_abrechnung hga " \
              "inner join verwaltung vwg on vwg.vwg_id = hga.vwg_id "
        return self.readAllGetDict( sql )

    def selectNkaKerndaten( self ):
        sql = "select nka_id, ab_jahr, mv_id " \
              "from nk_abrechnung "
        return self.readAllGetDict( sql )

    def selectVwgDaten( self, mobj_id:str, von:str, bis:str or None ) -> Dict:
        """
        Ermittelt Verwaltungsdaten für das übergebene <mobj_id>.
        Es können mehrere Ergebnisse gefunden werden (Bsp. Thomas-Mann-Str.)
        :param mobj_id:
        :param von:
        :param bis:
        :return: ein Dictionary mit den Keys master_name, vw_id, weg_name, vwg.von, vwg.bis
        """
        if bis is None: bis = "''"
        else: bis = "'%s'" % bis
        sql = "select vwg.vwg_id, vwg.master_name, vwg.vw_id, vwg.weg_name, vwg.von, vwg.bis, " \
              "mobj.mobj_id " \
              "from verwaltung vwg " \
              "inner join mietobjekt mobj on mobj.master_name = vwg.master_name " \
              "where mobj.mobj_id = '%s' " \
              "and vwg.von <= '%s' " \
              "and (vwg.bis >= %s or vwg.bis = '' or vwg.bis is NULL)" % (mobj_id, von, bis)
        dic = self.readOneGetDict( sql )
        return dic

    def selectReisen( self ):
        sql = "select reise.reise_id, reise.mobj_id, reise.master_name, reise.von, reise.bis, reise.jahr, reise.ziel, reise.zweck, " \
              "reise.km, reise.personen, reise.uebernachtung, reise.uebernacht_kosten " \
              "from geschaeftsreise reise " \
              "order by jahr "
        return self.readAllGetDict( sql )

    def selectPauschalen( self, jahr: int ) -> XPauschale:
        sql = "select jahr_von, jahr_bis, km, vpfl_8, vpfl_24 " \
              "from pauschale " \
              "where jahr_von <= %d " \
              "and (jahr_bis >= %d or jahr_bis is NULL) " % (jahr, jahr)
        x = self.readOneGetObject( sql, XPauschale )
        return x

    def selectSammelabgabeDetail( self, stadtkennung:str, jahr:int ) -> List[Dict]:
        """
        :param stadtkennung: "NK_" oder "OTW_"
        :param jahr:
        :return:
        """
        stadtkennung += "%"
        sql = "select master_name, jahr, grundsteuer, abwasser, strassenreinigung, bemerkung " \
              "from sammelabgabe_detail " \
              "where master_name like '%s' " \
              "and jahr = %d " % ( stadtkennung, jahr )
        return self.readAllGetDict( sql )

    def clearTable( self, tablename:str ):
        sql = "delete from " + tablename
        self._cursor.execute( sql )

    def getColumnNames( self, table:str ) -> List:
        sql = "select sql from sqlite_master where type = 'table' and tbl_name = '%s' " % table
        dic = self.readOneGetDict( sql )
        create_stmt = dic["sql"]
        return self._createColumnNameList( create_stmt )

    def resetAutoIncrement( self, table:str ):
        stmt = "UPDATE `sqlite_sequence` SET `seq` = 0 WHERE  `name` = '%s' " % table
        self._cursor.execute( stmt )

    @staticmethod
    def _createColumnNameList( create_stmt:str ) -> List:
        l = list()
        p1 = create_stmt.find( "(" )
        p2 = create_stmt.find( ")" )
        s = create_stmt[p1:p2]
        p1 = s.find( '"' )
        p2 = s.find( '"', p1 + 1 )
        while p1 > -1 and p2 > -1 :
            col = s[p1+1:p2]
            #print( col )
            p1 = s.find( '"', p2+1 )
            p = s.find( "AUTOINCREMENT", p2, p1 )
            if p < 0:
                l.append( col )
            p2 = s.find( '"', p1+1 )
        return l

    @staticmethod
    def createInsertStatement( dest_table: str, dest_columns: List[str], row: [Dict] ) -> str:
        columns = list()
        values = list()
        for col in dest_columns:
            try:
                # prüfen, ob die Spalte auch in der Src-Tabelle enthalten ist. Wenn nein, übergehen wir
                # diese Spalte und kommen zur nächsten
                val = row[col]
                if not val is None:
                    if not isinstance( val, numbers.Number ):
                        val = val.replace( "'", "''" )
                        val = "'" + val + "'"
                    columns.append( col )
                    values.append( val )
                else:
                    # wenn der Wert in der Src-Tabelle None (NULL) ist, hoffen wir mal, dass die
                    # entsprechende Spalte in der Dest-Tabelle auch Nullable ist und lassen sie aus
                    # dem Insert-Stmt raus.
                    continue
            except Exception as ex:
                # dürfte eigtl. nur auftreten, wenn die Spalte in der Dest-Tabelle, aber nicht in der Src-Tabelle
                # vorhanden ist. Dann wird sie beim Insert ignoriert.
                # (Sie ist dann hoffentlich in der Dest-Tabelle nullable, sonst knallt's beim Insert.)
                #print( "DestData.createInsertStatment():\n", str(ex) )
                continue

        anz_cols = len( columns )
        if anz_cols <= 0:
            raise Exception( "DestData.createInsertStatment():\nTabelle '%s' hat keine Spalten" % dest_table )
        stmt = "insert into " + dest_table + "("
        for col in columns:
            stmt += (col + ",")
        stmt = stmt[:-1]
        stmt += ") values ("
        for val in values:
            if isinstance( val, numbers.Number ):
                stmt += str(val)
            else:
                stmt += val
            stmt += ","
        stmt = stmt[:-1]
        stmt += ")"
        return stmt

    def insert( self, stmt:str ):
        c = self._cursor.execute( stmt )
        return c.lastrowid

    def commit( self ):
        self._cursor.execute( "commit" )

    def rollback( self ):
        self._cursor.execute( "rollback" )

def testDest():
    dest = DestData( "/home/martin/Projects/python/ImmoControlCenter/v2/icc/immo.db" )
    dic = dest.selectVwgDaten( "zweibrueck", '2022-09-01', None )
    print( dic )

##################################################################
class DatenUebernahmeLogic:
    def __init__(self, pathToSrcDb, pathToDestDb ):
        self._srcData = SrcData( pathToSrcDb ) # die "alte" Datenbank mit den zu übernehmenden Daten ("Quelle") -- LESEZUGRIFF
        self._destData = DestData( pathToDestDb )  # die "neue" v2-Datenbank, in die die Daten geschrieben werden ("Ziel")
                                                                                                # -- SCHREIBZUGRIFF
    def run( self ):
        self._copyMaster()
        self._copyMietobjekt()
        self._copyMietverhaeltnisse()
        self._copyVerwalter()
        self._copyVerwaltung()
        self._copySollHausgeld()
        self._copySollMiete()
        self._copyAbrechnungen()
        self._copySammelabgabeDetail()
        self._copyReisekosten() # kopiert die Daten aus der Src-Tabelle Geschaeftsreise in die Dest-Tabelle Geschaeftsreise
        # # die Daten aus Tabelle geschaeftsreise in Zahlungen umwandeln und in Tabelle einaus schreiben:
        self._processReisekosten( clearEinAusBeforeWrite=True )
        self._copyZahlungen( clearEinAusBeforeWrite=False ) # ACHTUNG: muss auf False stehen, wenn vorher die Reisekosten gelaufen sind!
        self._splitSammelAbgaben()
        self._processSternSternZahlungen()
        self._destData.commit()

    def _copySollMiete( self ):
        table = "sollmiete"
        dictlist = self._srcData.selectTable( table )
        self._writeDestTable( table, dictlist )

    def _copySollHausgeld( self ):
        table = "sollhausgeld"
        shglist = self._srcData.selectSollHausgeld()
        # die Soll-Hausgelder haben alle die "alte" vwg_id.
        # wir müssen die in der dest-Datenbank bereits angelegten Verwaltungen holen, die "neuen" vwg_id entnehmen und
        # in die Soll-Hausgelder der shglist eintragen.
        shgDestList = list()
        for shg in shglist:
            vwg = self._destData.selectVwgDaten( shg["mobj_id"], shg["von"], shg["bis"] )
            try:
                shg["vwg_id"] = vwg["vwg_id"]
                shgDestList.append( shg )
            except Exception as ex:
                print( "Verwaltung für Master ", shg["master_name"],  " not found." )
        self._writeDestTable( table, shgDestList )

    def _copyAbrechnungen( self ):
        self._copyHga()
        self._copyNka()

    def _copyNka( self ):
        nkalist = self._srcData.selectNka()
        self._writeDestTable( "nk_abrechnung", nkalist )

    def _copyHga( self ):
        hgalist = self._srcData.selectHga()
        # jetzt die vw_id in den einzelnen hga-Objekten umsetzen auf die neue vw_id
        vwglist = self._destData.selectTable( "verwaltung" )
        for hga in hgalist:
            for vwg in vwglist:
                try:
                    if hga["master_name"] == vwg["master_name"] \
                    and hga["vw_id"] == vwg["vw_id"]:
                        hga["vwg_id"] = vwg["vwg_id"]
                        break
                except Exception as ex:
                    print( str(ex), "\n", "hga: ", hga, "\t", "vwg: ", vwg )
                    raise ex
        self._writeDestTable( "hg_abrechnung", hgalist )

    def _copySammelabgabeDetail( self ):
        diclistsrc = self._srcData.selectSammelabgabeDetail()
        self._writeDestTable( "sammelabgabe_detail", diclistsrc )

    def _copyReisekosten( self ):
        # zuerst die Reisekosten von Tabelle geschaeftsreise (src) in Tabelle geschaeftsreise (dest) übertragen.
        # Dann den Reisen anhand der tats. Hotelkosten und der steuerl. Verpfleg.- u. km-Pauschalen die entstandenen
        # Kosten zuordnen.
        reiselist: List[Dict] = self._srcData.selectReisekosten()
        self._writeDestTable( "geschaeftsreise", reiselist )

    def _copyZahlungen( self, clearEinAusBeforeWrite:bool ):
        # überträgt die Daten aus Tabelle zahlung in Tabelle einaus in mehreren Schritten
        self._copyMieten( clearBefore=clearEinAusBeforeWrite )
        self._copyHgvZahlungen()
        self._copyHgaZahlungen()
        self._copyNkaZahlungen()
        self._copySonstAus()

    def _splitSammelAbgaben( self ):
        # Jede Zahlung aus der Src-Tabelle <zahlung> mit master_id in (28, 29 --> Ottweiler, Neunkirchen) wird
        # anhand des zutreff. Eintrags in Tabelle sammelabgabe_detail in 2 einaus-Sätze pro Objekt gesplittet
        # (Grundsteuer, Abwasser+Str.reinigung)
        # Also: eine Zahlung aus <zahlung> beinhaltet 1/4 der von OTW bzw. NK geforderten Jahres-Gesamtsumme.
        # Z.B. waren es in 2021 in NK 7 Objekte. Jede der 4 Zahlungen mit master_id 29 wird aufgebrochen in 14 einaus-
        # Sätze (2 Sätze gs und allg für jedes der 7 Objekte).
        samdictlist = self._srcData.selectSammelzahlungen()
        for sammelzahlung in samdictlist:
            # sammelzahlung ist eine Zahlung aus <zahlung>, repräsentiert durch ein Dict
            # mit den keys master_id, master_name, jahr, betrag, buchungsdatum, buchungstext, write_time.
            # Eine Sammelzahlung bezieht sich entweder auf alle Objekte der Stadt Neunkirchen oder der Gemeinde OTtweiler.
            # Jede Sammelzahlung wird in soviele einaus-Sätze aufgebrochen, wie es im betreff. Ort Objekte gibt.
            if sammelzahlung["master_name"] == "*NK_Alle*":
                stadtkennung = "NK_"
                debi_kredi = "Kreisstadt Neunkirchen"
            else: # *OTW_Alle*
                stadtkennung = "OTW_"
                debi_kredi = "Gemeinde Ottweiler"
            ealist = self._createEinAusSaetzeFuerObjekteInOrt( stadtkennung, debi_kredi,
                                                               sammelzahlung["jahr"],
                                                               sammelzahlung["betrag"],
                                                               sammelzahlung["buchungsdatum"],
                                                               sammelzahlung["write_time"] )

            self._writeDestTable( "einaus", ealist, clearTableBeforeWrite=False )

    def _createEinAusSaetzeFuerObjekteInOrt( self, stadtkennung:str, debi_kredi:str, jahr:int, sammelbetrag:float,
                                             buchungsdatum:str, write_time:str  ) -> List[Dict]:
        # Aus der Tabelle <sammelabgabe_detail> alle Sätze (1 Satz = 1 Objekt) für den betreff. Ort im betreff. Jahr
        # holen. Jeder dieser Sätze gibt Auskunft über die Einzel-Abgaben des Objekts (Grundsteuer, Abwasser,
        # Straßenreinigung).
        detaildictlist = self._destData.selectSammelabgabeDetail( stadtkennung, jahr )
        monat = int(write_time[5:7])
        monat = iccMonthShortNames[monat-1]
        ealist = list()
        for detail in detaildictlist:
            # detail ist ein Dict aus Tabelle sammelabgabe_detail
            # mit den Keys master_name, jahr, grundsteuer, abwasser, strassenreinigung, bemerkung
            # für jedes detail-Dict werden 2 einaus-Sätze geschrieben:
            # einer für Grundsteuer, einer für die Summe aus Abwasser u. Str.reinigg.

            ealist2 = self._createEinAusSaetzeFuerObjekt( detail, debi_kredi, monat, sammelbetrag, buchungsdatum, write_time )
            ealist.extend( ealist2 )
        return ealist

    def _createEinAusSaetzeFuerObjekt( self, abgaben:Dict, debi_kredi, monat:str, sammelbetrag:float,
                                       buchungsdatum:str, write_time:str ) -> List[Dict]:
        """
        Erzeugt 2 Sätze für das in <abgaben> enthaltene Objekt, einen für Grundsteuer, einen für Abwasser u. Str.reinigg.
        :param abgaben: Daten eines Satzes aus Tabelle <sammelabgabe_detail>
        :param debi_kredi: Gemeinde, an die die Abgaben zu entrichten sind
        :param monat: Monat aus Src-Tabelle <zahlung>
        :param buchungsdatum: Bu.datum aus Src-Tabelle <zahlung>
        :param write_time: write_time aus Src-Tabelle <zahlung>
        :return:
        """
        ealist: List[Dict] = list()
        gs = round( abgaben["grundsteuer"] / 4, 2 )  # 4 Zahlungen pro Jahr
        abw_strr = round( (abgaben["abwasser"] + abgaben["strassenreinigung"]) / 4, 2 )
        bem = abgaben["bemerkung"]
        if bem is None: bem = ""
        if bem > " ": bem += "\n"
        bem += "Abbuchung: %.2f €.\nEintrag entstand durch algorithmische Splittung." % sammelbetrag
        imax = 2 if abw_strr != 0 else 1 # in OTW gibt's nur Grundsteuer
        for i in range( imax ):
            einaus = {
                "master_name": abgaben["master_name"],
                "leistung": "Grundsteuer" if i == 0 else "Abwasser u. Str.reinigg.",
                "jahr": abgaben["jahr"],
                "debi_kredi": debi_kredi,
                "monat": monat,
                "betrag": gs if i == 0 else abw_strr,
                "ea_art": EinAusArt.GRUNDSTEUER.dbvalue if i == 0 else EinAusArt.ALLGEMEINE_KOSTEN.dbvalue,
                "umlegbar": Umlegbar.JA.value,
                "buchungsdatum": buchungsdatum,
                "buchungstext": bem,
                "write_time": write_time
            }
            ealist.append( einaus )
        return ealist

    def _processReisekosten( self, clearEinAusBeforeWrite:bool ):
        # def isBetween( jahr, jahr_von, jahr_bis ) -> bool:
        #     return jahr >= jahr_von and jahr <= jahr_bis

        ######## ACHTUNG ##########
        # !!!Darf nicht mehr laufen - die Kosten werden falsch berechnet!!!
        ########## ACHTUNG #########

        reiselist: List[Dict] = self._destData.selectReisen()
        jahr = 0
        xpausch:XPauschale = None
        einausdictlist:List[Dict] = list()
        for reise in reiselist:
            if jahr != reise["jahr"]:
                jahr = reise["jahr"]
                xpausch = self._destData.selectPauschalen( jahr )
            kosten:float = self._getReisekosten( reise, xpausch )
            einausdict:Dict = self._createEinAusDictFromReisekosten( reise, kosten )
            einausdictlist.append( einausdict )
        self._writeDestTable( "einaus", einausdictlist, clearEinAusBeforeWrite )

    def _getReisekosten( self, reise:Dict, xpausch:XPauschale ) -> float:
        """
        Erreicht aus den Daten der übergebenen <reise> die Kosten.
        :param reise:
        :param xpausch:
        :return:
        """
        dauer = datehelper.getNumberOfDays2( reise["von"], reise["bis"], reise["jahr"] )
        if dauer == 1:
            f = 1
        else:
            f = 2
        vpflkosten = xpausch.vpfl_8 * f  # Hin- u. Rückfahrt
        if dauer > 2:
            ganzetage = dauer - 2
            vpflkosten += (ganzetage * xpausch.vpfl_24)
        vpflkosten = vpflkosten * -1
        uebn = reise["uebernacht_kosten"]
        kmkosten = reise["km"] * -1
        return vpflkosten+uebn+kmkosten

    def _createEinAusDictFromReisekosten( self, reise:Dict, kosten:float  ) -> Dict:
        """
        Macht aus den Reisedaten <reise> und den bereits errechneten Kosten der Reise einein in die Tabelle <einaus>
        zu schreibenden Datensatz in der Form eines Dictionary.
        :param reise: 
        :param kosten: 
        :return: 
        """
        monat = reise["bis"][5:7]
        monat = iccMonthShortNames[int(monat)-1]
        einaus = {
            "master_name": reise["master_name"],
            "mobj_id": reise["mobj_id"],
            "leistung": "Geschaeftsreise",
            "reise_id": reise["reise_id"],
            "jahr": reise["jahr"],
            "monat": monat,
            "betrag": kosten,
            "ea_art": EinAusArt.SONSTIGE_KOSTEN.dbvalue,
            "umlegbar": Umlegbar.NEIN.value,
            "buchungsdatum": reise["bis"],
            "buchungstext": reise["zweck"],
            "write_time": reise["bis"] + ":23.59.59"
        }
        return einaus


    def _copySonstAus( self, clearBefore=False ):
        zlist = self._srcData.selectSonstAusZahlungen()
        for z in zlist:
            if z["ea_art"] == "a":
                z["ea_art"] = EinAusArt.ALLGEMEINE_KOSTEN.dbvalue
            elif z["ea_art"] == "g":
                z["ea_art"] = EinAusArt.GRUNDSTEUER.dbvalue
            elif z["ea_art"] == "s":
                z["ea_art"] = EinAusArt.SONSTIGE_KOSTEN.dbvalue
            elif z["ea_art"] == "r":
                z["ea_art"] = EinAusArt.REPARATUR.dbvalue
            elif z["ea_art"] == "v":
                z["ea_art"] = EinAusArt.VERSICHERUNG.dbvalue
            butext = z["zbuchungstext"] # !Z!
            if butext is None:
                butext = ""
            if len( butext ) > 0:
                if z["buchungstext"]:
                    if not butext == z["buchungstext"]:
                        butext += ( "\n" + z["buchungstext"] )
            if z["rgtext"]:
                butext += ( "\n" + z["rgtext"] )
            z["buchungstext"] = butext
            if z["umlegbar"] == 1:
                z["umlegbar"] = Umlegbar.JA.value
            else:
                z["umlegbar"] = Umlegbar.NEIN.value
        self._writeDestTable( "einaus", zlist, clearBefore )

    def _copyNkaZahlungen( self, clearBefore=False ):
        dictlist = self._srcData.selectNkaZahlungen()
        nkalist = self._destData.selectNkaKerndaten()
        for dic in dictlist:
            for nka in nkalist:
                if dic["debi_kredi"] == nka["mv_id"] \
                and dic["ab_jahr"] == nka["ab_jahr"]:
                    dic["nka_id"] = nka["nka_id"]
                    dic["leistung"] = "NKA " + str(dic["ab_jahr"])
        self._writeDestTable( "einaus", dictlist, clearBefore )

    def _copyHgaZahlungen( self,  clearBefore=False ):
        dictlist = self._srcData.selectHgaZahlungen()
        # die gelieferten Sätze haben alle die alte hga_id an Bord, die muss ausgetauscht werden
        hgalist = self._destData.selectHgaKerndaten()
        for dic in dictlist:
            for hga in hgalist:
                if dic["mobj_id"] == hga["mobj_id"] \
                and dic["debi_kredi"] == hga["weg_name"] \
                and dic["ab_jahr"] == hga["ab_jahr"]:
                    dic["hga_id"] = hga["hga_id"]
                    dic["leistung"] = "HGA " + str(dic["ab_jahr"])
                    break
        self._writeDestTable( "einaus", dictlist, clearBefore )

    def _copyHgvZahlungen( self, clearBefore=False ):
        def createEinAus( hgv:Dict ) -> Dict:
            # hgv repräsentiert einen Satz aus der Tabelle zahlung mit der zahl_art == 'hgv'
            debi_kredi = hgv["weg_name"]
            mobj_id = hgv["mobj_id"]
            ea_art = EinAusArt.ALLGEMEINE_KOSTEN.dbvalue # nur für Kleist und Kaiser, sonst hgv
            umlegbar = Umlegbar.JA.value # nur für Kleist und Kaiser (Hauswart), sonst nein (Verwaltung)
            leistung = "Verwaltung"
            if hgv["master_name"] == "NK_Kleist":
                debi_kredi = "Müller, H.J."
                mobj_id = ""
                leistung = "Hauswart"
            elif hgv["master_name"] == "SB_Kaiser":
                mobj_id = ""
                leistung = "Hauswart"
                if hgv["write_time"] > "2022-07":
                    debi_kredi = "Eickhoff, Sascha"
                else:
                    debi_kredi = "Fritsche"
            else:
                ea_art = EinAusArt.HAUSGELD_VORAUS.dbvalue
                umlegbar = Umlegbar.NEIN.value
            einaus = {
                "master_name": hgv["master_name"],
                "mobj_id": mobj_id,
                "debi_kredi" : debi_kredi,
                "leistung": leistung,
                "jahr": hgv["jahr"],
                "monat": hgv["monat"],
                "betrag": hgv["betrag"],
                "ea_art": ea_art,
                "umlegbar": umlegbar,
                "write_time": hgv["write_time"]
            }
            return einaus

        dictlist = self._srcData.selectHgvZahlungen()
        einausdictlist = list()
        for hgv in dictlist:
            einausdict = createEinAus( hgv )
            einausdictlist.append( einausdict)
        self._writeDestTable( "einaus", einausdictlist, clearBefore )

    def _copyMieten( self, clearBefore=False ):
        dictlist = self._srcData.selectMieten()
        self._writeDestTable( "einaus", dictlist , clearBefore )

    def _copyVerwaltung( self ):
        dictlist = self._srcData.selectVerwaltung()
        self._writeDestTable( "verwaltung", dictlist )

    def _copyVerwalter( self ):
        table = "verwalter"
        dictlist = self._srcData.selectTable( table, "where vw_id not in ('eickhoff', 'fritsche', 'mueller')" )
        self._writeDestTable( table, dictlist )

    def _copyMietverhaeltnisse( self ):
        table = "mietverhaeltnis"
        dictlist = self._srcData.selectTable( table )
        self._writeDestTable( table, dictlist )

    def _copyMietobjekt( self ):
        table = "mietobjekt"
        dictlist = self._srcData.selectMietobjekte()
        self._writeDestTable( table, dictlist )

    def _copyMaster( self ):
        table = "masterobjekt"
        dictlist = self._srcData.selectTable( table, "where master_name not like '%*'" )
        self._writeDestTable( table, dictlist )

    def _processSternSternZahlungen( self ):
        """
        Alle Zahlungen mit mobj_id "**alle** werden umgebogen auf SB_Kaiser
        :return:
        """
        dictlist = self._srcData.selectTable( "zahlung", "where mobj_id = '**alle**'" )
        ealist = list()
        for z in dictlist:
            einaus = {
                "master_name": "SB_Kaiser",
                "jahr": z["jahr"],
                "monat": z["monat"],
                "betrag": z["betrag"],
                "ea_art": EinAusArt.SONSTIGE_KOSTEN.dbvalue,
                "umlegbar": Umlegbar.NEIN.value,
                "buchungsdatum": z["buchungsdatum"],
                "buchungstext": z["buchungstext"],
                "write_time": z["write_time"]
            }
            ealist.append( einaus )
        self._writeDestTable( "einaus", ealist, clearTableBeforeWrite=False )

    def _writeDestTable( self, table:str, srcContent:List[Dict], clearTableBeforeWrite=True ):
        if clearTableBeforeWrite:
            self._destData.clearTable( table )
            self._destData.resetAutoIncrement( table )
        destcols = self._destData.getColumnNames( table )
        for dic in srcContent:
            insert_stmt = self._destData.createInsertStatement( table, destcols, dic )
            # insert:
            try:
                lastrowid = self._destData.insert( insert_stmt )
            except Exception as ex:
                box = ErrorBox( "Insert-Fehler", str( ex ), "" )
                box.exec_()
                return

def runUebernahme():
    app = QApplication()
    # print( ROOT_DIR )
    # pathFile = DATENUEBERNAHME_DIR + "/datenuebernahmeTEST.path"
    # f = open( pathFile, "r" )
    # paths = f.read()
    # paths = paths.split( "\n" )
    # print( paths )
    # srcpath = paths[0].split( "=" )[1] + "immo.db"
    srcpath = "/home/martin/Vermietung/ImmoControlCenter/immo.db" ### !!! Das ist die PRODUKTIVE Datenbank !!!
    print( "SourcePath = ", srcpath )
    destpath = "/home/martin/Projects/python/ImmoControlCenter/v2/icc/immo.db"
    print( "DestPath = ", destpath )
    more = "Quelle: %s\n\nZiel: %s\n" % (srcpath, destpath)
    box = WarningBox( "Datenübernahme", "\nBei Drücken von OK startet die Datenübernahme!\n\n", more, "OK", "KREIIISCH NEIN" )
    rc = box.exec_()
    if rc != MessageBox.Yes:
        return
    due = DatenUebernahmeLogic( srcpath, destpath )
    due.run()
    box = InfoBox( "Datenübernahme", "Die Datenübernahme ist beendet.", "", "OK" )
    box.exec_()


def correctReisekosten():
    from v2.einaus.einauslogic import EinAusLogic
    ealogic = EinAusLogic()
    reiselogic = GeschaeftsreiseLogic()
    ealist:List[XEinAus] = ealogic.getZahlungen( EinAusArt.SONSTIGE_KOSTEN.display, 2021,
                                                 "and leistung = 'Geschaeftsreise' ")
    for ea in ealist:
        reise:XGeschaeftsreise = reiselogic.getGeschaeftsreise( ea.reise_id )
        ea_tmp:XEinAus = reiselogic._createXeinausFromXgeschaeftsreise( reise )
        kosten: float = reiselogic.getGeschaeftsreisekosten2( reise )
        print( "Kosten für Reise %d in Tabelle einaus: %.2f -- korrigiere zu %.2f" % (reise.reise_id, ea.betrag, kosten) )
        ea.betrag = kosten
        ea.buchungstext = ea_tmp.buchungstext
        ealogic.updateZahlung( ea )
    #ealogic.commit()

def test():
    #runUebernahme()
    #correctReisekosten()
    pass