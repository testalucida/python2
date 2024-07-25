import sqlite3
from datetime import datetime
from typing import List, Tuple, Dict, Type
from base.interfaces import XBase

###########################  DatabaseCommon  ############################
class DatabaseCommon:
    """
    Basisklasse für Anmeldung und Zugriffe auf eine Sqlite-Datenbank.
    Mit jeder Instanzierung wird eine Sqlite3.dbapi2.Connection erzeugt.
    """
    _sqliteCon: sqlite3.dbapi2.Connection = None
    _pathToDatabase = None
    def __init__( self, pathToDatabase:str ):
        if DatabaseCommon._pathToDatabase and DatabaseCommon._pathToDatabase != pathToDatabase :
            raise Exception( "Each application may connect to only one database" )
        DatabaseCommon._pathToDatabase = pathToDatabase
        if not DatabaseCommon._sqliteCon:
            DatabaseCommon._sqliteCon:sqlite3.dbapi2.Connection = sqlite3.connect( pathToDatabase )
        # self._pathToDatabase = pathToDatabase
        self._transId = 0
        self._transIdFile = pathToDatabase + "transid.txt"

    def closeConnection( self ) -> None:
        self._sqliteCon.close()

    def getTransactionId( self ) -> int:
        """
        Die TransactionId hat nichts mit Sqlite zu tun.
        Sie kann von Anwendungen verwendet werden, um zusammengehörige Schreibzugriffe zu kennzeichnen.
        Mit jedem Aufruf von commit() wird sie auf 0 gesetzt, mit jedem Aufruf von write wird eine neue gezogen, sofern
        sie gerade auf 0 steht.
        :return:
        """
        return self._transId

    def commit( self ):
        self._sqliteCon.commit()
        self._transId = 0

    def rollback( self ):
        self._sqliteCon.rollback()

    def readTable( self, table: str ) -> List[Dict]:
        sql = "select * from " + table
        dictList = self.readAllGetDict( sql )
        return dictList

    def getMaxId( self, table: str, id_name: str ) -> int:
        sql = "select max(%s) as max_id from %s" % (id_name, table)
        d = self.readOneGetDict( sql )
        return d["max_id"]

    def getCurrentTimestamp( self ):
        return datetime.now().strftime( "%Y-%m-%d:%H.%M.%S" )

    def read( self, sql: str ) -> List[Tuple]:
        cur = self._sqliteCon.cursor() # sieht umständlich aus, muss aber so gemacht werden:
                                 # mit jedem cursor()-call wird ein neuer Cursor erzeugt!
        cur.execute( sql )
        records = cur.fetchall()
        cur.close()
        return records

    def dict_factory( self, cursor, row ):
        d = { }
        for idx, col in enumerate( cursor.description ):
            d[col[0]] = row[idx]
        return d

    def readOneGetDict( self, sql: str ) -> Dict or None:
        self._sqliteCon.row_factory = self.dict_factory
        cur = self._sqliteCon.cursor()
        cur.execute( sql )
        dic = cur.fetchone()
        self._sqliteCon.row_factory = None
        cur.close()
        return dic

    def readAllGetDict( self, sql: str ) -> List[Dict] or None:
        self._sqliteCon.row_factory = self.dict_factory
        cur = self._sqliteCon.cursor()
        cur.execute( sql )
        dicList = cur.fetchall()
        self._sqliteCon.row_factory = None
        cur.close()
        return dicList

    def readOneGetObject( self, sql, xbase: Type[XBase] ) -> XBase or None:
        dic = self.readOneGetDict( sql )
        if dic:
            x = xbase( dic )
            return x
        return None

    def readAllGetObjectList( self, sql, xbase:Type[XBase] ) -> List[XBase]:
        """
        :param sql:
        :param xbase: der gewünschte Rückgabetyp: eine von XBase abgeleitete Klasse
        :return: eine Liste von Objekten, die der gewünschten Klasse entsprechen - oder eine leere Liste
        """
        self._sqliteCon.row_factory = self.dict_factory
        cur = self._sqliteCon.cursor()
        cur.execute( sql )
        dictlist = cur.fetchall()
        retList = list()
        for d in dictlist:
            x = xbase( d )
            retList.append( x )
        self._sqliteCon.row_factory = None
        cur.close()
        return retList

    def write( self, sql: str ) -> int:
        """
        Macht einen Schreibzugriff auf die Datenbank, ABER KEINEN COMMIT.
        Ein Commit wird nur nach Aufruf von DatabaseCommon.commit() ausgeführt.
        :param sql: das auszuführende SQL-Stmt
        :return: die lastrowid eines eingefügten Satzes bzw. rowcount nach einem Update
        """
        if self._transId == 0:
            self._createNewTransId()
        c = self._sqliteCon.cursor().execute( sql )
        s = sql.lower()
        isInsert = True if "insert" in s else False
        if isInsert:
            return c.lastrowid
        else:
            return c.rowcount

    def _createNewTransId( self ):
        try:
            f = open( self._transIdFile, "r" )
            self._transId = int( f.read() ) + 1
            f.close()
        except Exception:
            self._transId = 1

        try:
            f = open( self._transIdFile, "w" )
            f.write( str( self._transId ) )
            f.close()
        except Exception as ex:
            raise Exception( "DatabaseCommon._createNewTransId(): Fehler beim Schreiben der TransactionId:\n" + str(ex) )