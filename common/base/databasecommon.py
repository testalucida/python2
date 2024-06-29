import sqlite3
from datetime import datetime
from sqlite3 import Connection
from typing import List, Tuple, Dict, Type

#from definitions import DATABASE
from base.interfaces import XBase

###########################  DatabaseConnection  ###########################
class DatabaseConnection:
    __instance = None
    def __init__( self ):
        self._con = None
        self._pathToDb = ""
        self._inTransaction = False

        if DatabaseConnection.__instance:
            raise Exception("DatabaseConnection is a Singleton. You may instantiate it only once." )
        else:
            DatabaseConnection.__instance = self

    @staticmethod
    def inst():
        if not DatabaseConnection.__instance:
            DatabaseConnection()
        return DatabaseConnection.__instance

    def createConnection( self, pathToDb:str ) -> Connection:
        self._pathToDb = pathToDb
        self._con = sqlite3.connect( pathToDb )
        return self._con

    def getConnection( self ):
        return self._con

    def begin_transaction( self ):
        self._inTransaction = True

    def commit_transaction( self ):
        self._con.commit()
        self._inTransaction = False

    def rollback_transaction( self ):
        self._con.rollback()
        self._inTransaction = False

    def isInTransaction( self ) -> bool:
        return self._inTransaction


###########################  DatabaseCommon  ############################
class DatabaseCommon:
    def __init__( self, pathToDatabase:str ):
        self._con = DatabaseConnection.inst().createConnection( pathToDatabase )

    def isInTransaction( self ) -> bool:
        return DatabaseConnection.inst().isInTransaction()

    def close( self ) -> None:
        self._con.close()

    def getConnection( self ):
        return self._con.cursor()

    def readTable( self, table: str ) -> List[Dict]:
        sql = "select * from " + table
        dictList = self.readAllGetDict( sql )
        return dictList

    def getMaxId( self, table: str, id_name: str ) -> int:
        sql = "select max(%s) as max_id from %s" % (id_name, table)
        d = self.readOneGetDict( sql )
        return d["max_id"]

    # def getWertebereiche( self, table:str=None, column:str=None ) -> List[XWertebereich]:
    #     """
    #     Liest alle Wertebereiche aus der Tabelle wertebereich
    #     :return:
    #     """
    #     sql = "select id, table_name, column_name, is_numeric, wert, beschreibung_kurz, beschreibung from wertebereich "
    #     if table:
    #         sql += "where table_name = '%s' and column_name = '%s' " % ( table, column )
    #     l: List[Dict] = self.readAllGetDict( sql )
    #     wbList: List[XWertebereich] = list()
    #     for d in l:
    #         x = XWertebereich( d )
    #         wbList.append( x )
    #     return wbList

    def getCurrentTimestamp( self ):
        return datetime.now().strftime( "%Y-%m-%d:%H.%M.%S" )

    # def getIccTabellen( self ) -> List[str]:
    #     sql = "select name from sqlite_master where type = 'table' order by name"
    #     tupleList = self.read( sql )
    #     l = [x[0] for x in tupleList]
    #     return l

    def read( self, sql: str ) -> List[Tuple]:
        cur = self._con.cursor() # sieht umständlich aus, muss aber so gemacht werden:
                                 # mit jedem cursor()-call wird ein neuer Cursor erzeugt!
        cur.execute( sql )
        records = cur.fetchall()
        return records

    def dict_factory( self, cursor, row ):
        d = { }
        for idx, col in enumerate( cursor.description ):
            d[col[0]] = row[idx]
        return d

    def readOneGetDict( self, sql: str ) -> Dict or None:
        self._con.row_factory = self.dict_factory
        cur = self._con.cursor()
        cur.execute( sql )
        dic = cur.fetchone()
        self._con.row_factory = None
        return dic

    def readAllGetDict( self, sql: str ) -> List[Dict] or None:
        self._con.row_factory = self.dict_factory
        cur = self._con.cursor()
        cur.execute( sql )
        dicList = cur.fetchall()
        self._con.row_factory = None
        return dicList

    def readOneGetObject( self, sql, xbase: Type[XBase] ) -> XBase:
        dic = self.readOneGetDict( sql )
        x = xbase( dic )
        return x

    def readAllGetObjectList( self, sql, xbase:Type[XBase] ) -> List[XBase]:
        """
        :param sql:
        :param xbase: der gewünschte Rückgabetyp: eine von XBase abgeleitete Klasse
        :return: eine Liste von Objekten, die der gewünschten Klasse entsprechen - oder eine leere Liste
        """
        self._con.row_factory = self.dict_factory
        cur = self._con.cursor()
        cur.execute( sql )
        dictlist = cur.fetchall()
        retList = list()
        for d in dictlist:
            x = xbase( d )
            retList.append( x )
        self._con.row_factory = None
        return retList

    def write( self, sql: str ) -> int:
        c = self._con.cursor().execute( sql )
        if not self.isInTransaction():
            self._con.commit()
        return c.rowcount

def test():
    db = DatabaseCommon( "/home/martin/Projects/python/ImmoControlCenter/immo.db" )
    sql = "select mv_id from mietverhaeltnis where mobj_id = 'bueb' and von <= CURRENT_DATE order by von desc"
    ret = db.read( sql )
    print( ret )
    ret = db.read( sql )
    print( ret )
    ret = db.read( sql )
    print( ret )
    # d = db.readOneGetDict( sql )
    # print( d )
