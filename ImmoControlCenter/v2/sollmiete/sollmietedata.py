from typing import List, Dict, Iterable

from base import constants
from datehelper import getNumberOfDays
from v2.icc.constants import getMonthIdxFromShortName
from v2.icc.iccdata import IccData, DbAction
from v2.icc.interfaces import XSollMiete


class SollmieteData( IccData ):
    def __init__( self ):
        IccData.__init__( self )

    def getAlleSollMieten( self ) -> List[XSollMiete]:
        sql = "select sm.sm_id, sm.mv_id, sm.von, coalesce(sm.bis, '') as bis, " \
              "sm.netto, sm.nkv, (sm.netto + sm.nkv) as brutto, " \
              "coalesce(sm.bemerkung, '') as bemerkung, mv.mobj_id " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "order by sm.mv_id asc, sm.von desc"
        l: List[XSollMiete] = self.readAllGetObjectList( sql, XSollMiete )
        return l

    def getSollMieten( self, jahr: int ) -> List[XSollMiete]:
        minbis = "%d-%02d-%02d" % (jahr, 1, 1)
        maxvon = "%d-%02d-%02d" % (jahr, 12, 31)
        sql = "select sm.sm_id, sm.mv_id, sm.von, coalesce(sm.bis, '') as bis, " \
              "sm.netto, sm.nkv, (sm.netto + sm.nkv) as brutto, " \
              "coalesce(sm.bemerkung, '') as bemerkung, mv.mobj_id " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "where (sm.bis is NULL or sm.bis = '' or sm.bis >= '%s') " \
              "and not sm.von > '%s' " \
              "order by sm.mv_id, sm.von desc" % (minbis, maxvon)
        l: List[XSollMiete] = self.readAllGetObjectList( sql, XSollMiete )
        return l

    def getSollmietenMobjJahr( self, mobj_id:str, jahr:int ):
        minbis = "%d-%02d-%02d" % (jahr, 1, 1)
        maxvon = "%d-%02d-%02d" % (jahr, 12, 31)
        sql = "select sm.sm_id, sm.mv_id, sm.von, coalesce(sm.bis, '') as bis, " \
              "sm.netto, sm.nkv, (sm.netto + sm.nkv) as brutto, " \
              "coalesce(sm.bemerkung, '') as bemerkung, mv.mobj_id " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "where (sm.bis is NULL or sm.bis = '' or sm.bis >= '%s') " \
              "and not sm.von > '%s' " \
              "order by sm.mv_id, sm.von desc" % (minbis, maxvon)
        l: List[XSollMiete] = self.readAllGetObjectList( sql, XSollMiete )
        return l

    def getLetzteSollmiete( self, mv_id:str ) -> XSollMiete:
        """
        Liefert die letzte (jüngste) Sollmiete für <mv_id>.
        Diese Sollmiete kann auch schon inaktiv sein (<bis> LT current date).
        Sie kann aber auch in der Zukunft liegen (also noch nicht aktiv, <von> GT current date)
        :param mv_id:
        :return: ein Sollmiete-Objekt
        """
        sql = "select sm.sm_id, mv.mv_id, mv.mobj_id, sm.von, coalesce(sm.bis, '') as bis, " \
              "netto, nkv, netto+nkv as brutto, sm.bemerkung " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "where sm.mv_id = '%s' " \
              "order by sm.von desc " % mv_id
        dictlist:List[Dict] = self.readAllGetDict( sql )
        if len( dictlist ) > 0:
            d = dictlist[0]
            x = XSollMiete( d )
            return x
        else:
            raise Exception( "SollmieteData.getLetzteSollmiete:\nZu '%s' keine aktuelle Sollmiete gefunden." % mv_id )

    def getAktuelleSollmiete( self, mv_id:str ) -> XSollMiete:
        """
        Liefert die aktuelle Sollmiete für <mv_id>.
        Diese kann auch schon inaktiv sein (<bis> LT current date)
        Sie kann aber NICHT in der Zukunft liegen.
        :param mv_id:
        :return: ein Sollmiete-Objekt oder None, wenn keines gefunden wurde
        """
        sql = "select sm_id, mv.mv_id, mv.mobj_id, sm.von, coalesce(sm.bis, '') as bis, " \
              "netto, nkv, netto+nkv as brutto, sm.bemerkung " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "where sm.mv_id = '%s' " \
              "and sm.von <= CURRENT_DATE " \
              "order by sm.von desc " % mv_id

        l:List[XSollMiete] = self.readAllGetObjectList( sql, XSollMiete )
        if len( l ) < 1:
            raise Exception( "SollmieteData.getAktuelleSollmiete:\nZu '%s' keine aktuelle Sollmiete gefunden." % mv_id )
        return l[0]

    def getSollmieteHistorie( self, mv_id ) -> List[XSollMiete]:
        """
        Liefert eine Liste aller Sollmieten für <mv_id>.
        Diese kann sowohl inaktive wie auch zukünftige Sollmieten enthalten.
        :param mv_id:
        :return: ein Liste von Sollmiete-Objekten
        """
        sql = "select sm_id, mv.mv_id, mv.mobj_id, sm.von, coalesce(sm.bis, '') as bis, " \
              "netto, nkv, netto+nkv as brutto, sm.bemerkung " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "where sm.mv_id = '%s' " \
              "order by sm.von desc " % mv_id
        return self.readAllGetObjectList( sql, XSollMiete )

    def getSollmieteAm( self, mv_id, jahr:int, monthNumber:int ) -> XSollMiete or None:
        """
        :param mv_id:
        :param jahr:
        :param monthNumber: 1 -> Januar, ... , 12 -> Dezember
        :return:
        """
        von = "%4d-%.2d-01" % ( jahr, monthNumber )
        lastday = getNumberOfDays( monthNumber )
        bis = "%4d-%.2d-%d" % ( jahr, monthNumber, lastday )
        sql = "select sm_id, mv.mv_id, mv.mobj_id, sm.von, coalesce(sm.bis, '') as bis, " \
              "netto, nkv, netto+nkv as brutto, sm.bemerkung " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "where sm.mv_id = '%s' " \
              "and sm.von <= '%s' " \
              "and (sm.bis is NULL or sm.bis = '' or sm.bis  >= '%s' ) " % ( mv_id, von, bis )
        x = self.readOneGetObject( sql, XSollMiete )
        return x

    def getSollmiete( self, sm_id:int ) -> XSollMiete:
        sql = "select sm_id, mv.mv_id, mv.mobj_id, sm.von, coalesce(sm.bis, '') as bis, " \
              "netto, nkv, netto+nkv as brutto, sm.bemerkung " \
              "from sollmiete sm " \
              "inner join mietverhaeltnis mv on mv.mv_id = sm.mv_id " \
              "where sm_id = %d " % sm_id
        x = self.readOneGetObject( sql, XSollMiete )
        return x

    def insertSollmiete( self, x: XSollMiete ) -> int:
        bis = "NULL" if not x.bis else "'" + x.bis + "'"
        sql = "insert into sollmiete " \
              "(mv_id, von, bis, netto, nkv, bemerkung ) " \
              "values( '%s', '%s', %s, %.2f, %.2f, '%s' ) " % (x.mv_id, x.von, bis, x.netto, x.nkv, x.bemerkung)
        lastRowId = self.write( sql )
        x.sm_id = self.getMaxId( "sollmiete", "sm_id" )
        return lastRowId

    def updateSollmiete( self, x: XSollMiete ):
        """
        Macht einen Update auf genau einen Satz in <sollmiete>.
        !!!Beachte: Die mv_id kann mit dieser Methode nicht geändert werden!!!
        Denn: bei Änderung der mv_id können mehrere Sätze in <sollmiete> betroffen sein,
        es wäre komplett sinnlos, nur einen davon zu ändern.
        :param x:
        :param commit:
        :return:
        """
        bis = "NULL" if not x.bis else "'" + x.bis + "'"
        sql = "update sollmiete set " \
              "von = '%s', " \
              "bis = %s, " \
              "netto = %.2f, " \
              "nkv = %.2f, " \
              "bemerkung = '%s' " \
              "where sm_id = %d" % (x.von, bis, x.netto, x.nkv, x.bemerkung, x.sm_id)
        return self.write( sql )

    def deleteSollmiete( self, sm_id:int ):
        currentX = self.getSollmiete( sm_id )
        sql = "delete from sollmiete where sm_id = %d " % sm_id
        self.writeAndLog( sql, DbAction.DELETE, "sollmiete", "shg_id", sm_id,
                          newvalues=None, oldvalues=currentX.toString( printWithClassname=True ) )

    def terminateSollmiete( self, sm_id:int, bis:str ) -> int:
        """
        Beendet die Gültigkeit eines Sollmiete-Intervalls
        :param sm_id: Spezifikation des Satzes, dessen Gültigkeit terminiert werden soll
        :param bis: Ende-Datum des Intervalls
        :return:
        """
        sql = "update sollmiete " \
              "set bis = '%s' " \
              "where sm_id = %d " % ( bis, sm_id )
        return self.write( sql )

def test():
   data = SollmieteData()
   l = data.getSollmieteHistorie( "lukas_franz" )
   for x in l:
       x.print()
   x = data.getLetzteSollmiete( "lukas_franz" )
   x.print()
   x = data.getAktuelleSollmiete( "lukas_franz" )
   x.print()
   x = data.getSollmieteAm( "lukas_franz", 2022, 1 )
   x.print()

