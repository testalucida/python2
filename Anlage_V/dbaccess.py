import sqlite3
from typing import List, Tuple, Dict


# def dict_factory(cursor, row):
#     d = {}
#     for idx, col in enumerate(cursor.description):
#         d[col[0]] = row[idx]
#     return d

class DbAccess:
    def __init__( self ):
        self._con = None
        self._cursor = None

    def open( self ) -> None:
        self._con = sqlite3.connect( 'anlage_v.db' )
        self._cursor = self._con.cursor()

    def close( self ) -> None:
        self._cursor.close()
        self._con.close()

    def getMaxId( self, table:str, id_name:str ) -> int:
        sql = "select max(%s) from %s" %(id_name, table)
        records = self._doRead( sql )
        return records[0][0]

    def insertErhaltungsaufwand( self, obj_id:int, veranl_jahr:int,
                                 voll_abziehbar:int=0,
                                 zu_verteilen_gesamt_neu:int=0, verteilen_auf_jahre:int=0,
                                 abziehbar_vj:int=0, abziehbar_vj_minus_1:int=0, abziehbar_vj_minus_2:int=0, abziehbar_vj_minus_3:int=0, abziehbar_vj_minus_4:int=0,
                                 commit:bool=True ) -> int:
        sql = "insert into erhaltungsaufwand (obj_id, veranl_jahr, " \
              "voll_abziehbar, " \
              "zu_verteilen_gesamt_neu, verteilen_auf_jahre, abziehbar_vj, abziehbar_vj_minus_1, abziehbar_vj_minus_2, abziehbar_vj_minus_3, abziehbar_vj_minus_4 ) " \
              "values (%d, '%d', '%d', '%d', '%d', '%d', '%d', '%d', '%d', '%d');" \
              % (obj_id, veranl_jahr,
                 voll_abziehbar,
                 zu_verteilen_gesamt_neu, verteilen_auf_jahre, abziehbar_vj, abziehbar_vj_minus_1, abziehbar_vj_minus_2, abziehbar_vj_minus_3, abziehbar_vj_minus_4)
        self._doWrite( sql, commit )
        return self.getMaxId( "erhaltungsaufwand", "id" )

    def updateErhaltungsaufwand1( self, obj_id:int, veranl_jahr:int, voll_abziehbar:int, commit:bool=True ):
        sql = "update erhaltungsaufwand " \
              "set voll_abziehbar = %d where obj_id = %d and veranl_jahr = %d; " % (voll_abziehbar, obj_id, veranl_jahr)
        if self._doWrite( sql, commit ) != 1:
            msg = "Tabelle erhaltungsaufwand enthält keinen Satz mit obj_id = %d und veranl_jahr = %d."  % (obj_id, veranl_jahr)
            raise KeyError( msg )
        return

    def updateErhaltungsaufwand2( self, obj_id:int, veranl_jahr:int,
                                  voll_abziehbar:int,
                                  zu_verteilen_gesamt_neu:int, verteilen_auf_jahre:int,
                                  abziehbar_vj:int,
                                  abziehbar_vj_minus_1:int,
                                  abziehbar_vj_minus_2:int,
                                  abziehbar_vj_minus_3:int,
                                  abziehbar_vj_minus_4:int,
                                  commit:bool=True ):
        sql = "update erhaltungsaufwand " \
              "set voll_abziehbar = %d " \
              "   ,zu_verteilen_gesamt_neu = %d " \
              "   ,verteilen_auf_jahre = %d" \
              "   ,abziehbar_vj = %d" \
              "   ,abziehbar_vj_minus_1 = %d" \
              "   ,abziehbar_vj_minus_2 = %d" \
              "   ,abziehbar_vj_minus_3 = %d" \
              "   ,abziehbar_vj_minus_4 = %d " \
              "where obj_id = %d and veranl_jahr = %d;" \
              % (voll_abziehbar,
                 zu_verteilen_gesamt_neu,
                 verteilen_auf_jahre,
                 abziehbar_vj,
                 abziehbar_vj_minus_1,
                 abziehbar_vj_minus_2,
                 abziehbar_vj_minus_3,
                 abziehbar_vj_minus_4,
                 obj_id, veranl_jahr)
        if self._doWrite(sql, commit) != 1:
            msg = "Tabelle erhaltungsaufwand enthält keinen Satz mit obj_id = %d und veranl_jahr = %d." % (
            obj_id, veranl_jahr)
            raise KeyError(msg)
        return

    def commit( self ):
        self._con.commit()

    def getAllSteuerpflichtige( self ) -> List[Dict]:
        sql = "select id, name, vorname, steuernummer, coalesce(persoenl_identnr, ' ') as persoenl_identnr " \
              "from steuerpflichtiger"
        diclist: List[Dict] = self._doReadAllGetDict(sql)
        return diclist

    def getSteuerpflichtigen(self, id:int ) -> Dict:
        sql = "select id, name, vorname, steuernummer, coalesce(persoenl_identnr, ' ') as persoenl_identnr " \
              "from steuerpflichtiger " \
              "where id = %d;" % id
        dic = self._doReadOneGetDict( sql )
        return dic

    def getObjekte( self, stpfl_id:int ) -> List[Dict]:
        sql = "select id, strasse_hnr, plz, ort, coalesce(einh_wert_az, ' ') as einh_wert_az, " \
              "coalesce(angeschafft_am, ' ') as angeschafft_am, coalesce(verkauft_am, ' ') as verkauft_am " \
              "from objekt where stpfl_id = %d order by ort, strasse_hnr;" % stpfl_id
        diclist:List[Dict] = self._doReadAllGetDict( sql )
        return diclist

    def getSomeObjekte( self, idlist:List[int] ) -> List[Dict]:
        idstrlist:str = ",".join( str( x ) for x in idlist )
        sql = "select id, stpfl_id, strasse_hnr, plz, ort, einh_wert_az, angeschafft_am, verkauft_am " \
              "from objekt where id in (%s);" % idstrlist
        diclist: List[Dict] = self._doReadAllGetDict(sql)
        return diclist

    def getErhaltungsAufwand( self, obj_id:int, veranl_jahr:int ) -> Dict or None:
        sql = "select id, obj_id, veranl_jahr, " \
              "voll_abziehbar, zu_verteilen_gesamt_neu, verteilen_auf_jahre, " \
              "abziehbar_vj, abziehbar_vj_minus_1, abziehbar_vj_minus_2, abziehbar_vj_minus_3, abziehbar_vj_minus_4 " \
              "from erhaltungsaufwand where obj_id = %d and veranl_jahr = %d" % (obj_id, veranl_jahr)
        dic = self._doReadOneGetDict( sql )
        return dic

    def _doRead( self, sql:str ) -> List[Tuple]:
        self._cursor.execute( sql )
        records = self._cursor.fetchall()
        return records

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _doReadOneGetDict( self, sql:str ) -> Dict or None:
        self._con.row_factory = self.dict_factory
        cur = self._con.cursor()
        cur.execute( sql )
        return cur.fetchone()

    def _doReadAllGetDict( self, sql:str ) -> Dict or None:
        self._con.row_factory = self.dict_factory
        cur = self._con.cursor()
        cur.execute( sql )
        return cur.fetchall()

    def _doWrite( self, sql:str, commit:bool ) -> int:
        c = self._cursor.execute( sql )
        if commit:
            self._con.commit()
        return c.rowcount

# =============================================================================
# crsr.execute("CREATE TABLE employees( \
#                  id integer PRIMARY KEY, \
#                  name text, \
#                  salary real, \
#                  department text, \
#                  position text, \
#                  hireDate text)")
#
# con.commit()
# =============================================================================

def test():
    db = DbAccess()
    db.open()

    #diclist:List[Dict] = db.getObjekte( 1 )
    diclist = db.getAllSteuerpflichtige()
    for dic in diclist:
        for k, v in dic.items():
            print( k, ": ", v)

    # dic:Dict = db.getErhaltungsAufwand( 11, 2015 )
    # if dic is None: print( "Keinen Satz gefunden")
    # else:
    #     for k, v in dic.items():
    #         print( k, ": ", v)

    #max = db.insertErhaltungsaufwand( 1, 2014, voll_abziehbar=1234, zu_verteilen_gesamt_neu=32100, verteilen_auf_jahre=4, abziehbar_vj=8000)
    #db.updateErhaltungsaufwand2( 11, 2015, voll_abziehbar=1234, zu_verteilen_gesamt_neu=9876, verteilen_auf_jahre=5,
    #                             abziehbar_vj=987, abziehbar_vj_minus_1=1,abziehbar_vj_minus_2=2, abziehbar_vj_minus_3=3,abziehbar_vj_minus_4=4)
    db.close()

if __name__ == '__main__':
    test()