from typing import List, Dict

import datehelper
from v2.icc.iccdata import IccData, DbAction
from v2.icc.interfaces import XSollHausgeld


class SollHausgeldData( IccData ):
    def __init__(self):
        IccData.__init__( self )

    def getAllSollHausgelder( self ) -> List[XSollHausgeld]:
        sql = "select shg.shg_id, shg.vwg_id, shg.mobj_id, vwg.vw_id, vwg.weg_name, shg.von, shg.bis, " \
              "shg.netto, shg.ruezufue, shg.bemerkung " \
              "from sollhausgeld shg " \
              "inner join verwaltung vwg on vwg.vwg_id = shg.vwg_id " \
              "order by shg.mobj_id asc, shg.von desc"
        l: List[XSollHausgeld] = self.readAllGetObjectList( sql, XSollHausgeld )
        for x in l:
            x.brutto = x.netto + x.ruezufue
        return l

    def getSollHausgelder( self, jahr: int ) -> List[XSollHausgeld]:
        minbis = "%d-%02d-%02d" % (jahr, 1, 1)
        maxvon = "%d-%02d-%02d" % (jahr, 12, 31)
        sql = "select shg.shg_id, shg.vwg_id, shg.mobj_id, vwg.weg_name, shg.von, shg.bis, " \
              "shg.netto, shg.ruezufue, shg.bemerkung " \
              "from sollhausgeld shg " \
              "inner join verwaltung vwg on vwg.vwg_id = shg.vwg_id " \
              "where (shg.bis is NULL or shg.bis = '' or shg.bis >= '%s') " \
              "and not shg.von > '%s' " \
              "order by vwg.weg_name, shg.von desc" % (minbis, maxvon)
        l: List[XSollHausgeld] = self.readAllGetObjectList( sql, XSollHausgeld )
        for x in l:
            x.brutto = x.netto + x.ruezufue
        return l

    def getCurrentSollHausgeld( self, mobj_id: str ) -> XSollHausgeld:
        """
        liefert das momentan gültige Soll-Hausgeld für mobj_id
        :param mobj_id:
        :return: ein XHausgeld-Objekt
        """
        sql = "select s.shg_id, v.vw_id, s.mobj_id, s.vwg_id, s.von, coalesce(s.bis, '') as bis, s.netto, s.ruezufue, " \
              "(s.netto + s.ruezufue) as brutto, " \
              "v.weg_name,  coalesce(s.bemerkung, '') as bemerkung " \
              "from sollhausgeld s " \
              "inner join verwaltung v on v.vwg_id = s.vwg_id " \
              "where s.mobj_id = '%s' " \
              "and (s.bis is NULL or s.bis = '' or s.bis >= CURRENT_DATE) " \
              "and s.von <= CURRENT_DATE" % mobj_id
        x = self.readOneGetObject( sql, XSollHausgeld )
        return x

    def getSollHausgeldHistorie( self, mobj_id:str, order:str="desc", jahr:int=None ) -> List[XSollHausgeld]:
        """
        Liefert eine Liste von XSollHausgeld-Objekten, sortiert nach <von> absteigend - also
        das jüngste (evtl. zukünftige!) Objekt ist das erste in der Liste
        :param mobj_id: betroffenes Mietobjekt
        :param order: desc (descending) oder asc (ascending). Default ist desc
        :param jahr: wenn angegeben: es werden nur die XSollHausgeld-Objekte geliefert, die irgendwann im Jahr <jahr>
                    gültig waren.
        :return:
        """
        maxVon = minBis = ""
        if jahr:
            maxVon = "%d-12-01" % jahr
            minBis = "%d-01-31" % jahr
        sql = self._getSelectClauseMitVerwaltungJoin()
        sql += "where s.mobj_id = '%s' " % mobj_id
        if jahr:
            sql += "and s.von <= '%s' and (s.bis is NULL or s.bis = '' or s.bis >= '%s' ) " % ( maxVon, minBis )
        sql += "order by s.von %s " % order
        return self.readAllGetObjectList( sql, XSollHausgeld )

    def getSollHausgeldAm( self, mobj_id:str, jahr:int, monthNumber:int ) -> XSollHausgeld:
        """
        :param mobj_id:
        :param jahr:
        :param monthNumber: 1: Januar ... 12: Dezember
        :return:
        """
        lastday = datehelper.getNumberOfDays( monthNumber )
        minbis = "%d-%02d-%02d" % (jahr, monthNumber, 1)
        maxvon = "%d-%02d-%02d" % (jahr, monthNumber, lastday)
        sql = self._getSelectClauseMitVerwaltungJoin()
        sql += "where s.mobj_id = '%s' " \
              "and not s.von > '%s' " \
              "and (s.bis is NULL or s.bis = '' or s.bis >= '%s' ) "  % ( mobj_id, maxvon, minbis )
        x = self.readOneGetObject( sql, XSollHausgeld )
        return x

    def getSollHausgeld( self, shg_id:int ) -> XSollHausgeld:
        """
        Liefert ein XSollHausgeld-Objekt
        :param shg_id:
        :return:
        """
        sql = self._getSelectClauseMitVerwaltungJoin()
        sql += "where s.shg_id = %d " % shg_id
        x = self.readOneGetObject( sql, XSollHausgeld )
        if not x:
            raise  Exception( "SollHausgeldData.getSollHausgeld()\n"
                              "SollHausgeld mit shg_id %d nicht gefunden. " % shg_id )
        return x

    def getLetztesSollHausgeld( self, mobj_id:str ) -> XSollHausgeld:
        """
        Liefert das letzte (jüngste) Soll-Hausgeld für <mobj_id>.
        Dieses Soll-Hausgeld kann auch schon inaktiv sein (<bis> LT current date).
        Es kann aber auch in der Zukunft liegen (also noch nicht aktiv, <von> GT current date)
        :param mobj_id:
        :return: ein SollHausgeld-Objekt
        """
        sql = self._getSelectClauseMitVerwaltungJoin()
        sql += "where s.mobj_id = '%s' " \
               "order by s.von desc " % mobj_id
        dictlist: List[Dict] = self.readAllGetDict( sql )
        if len( dictlist ) > 0:
            d = dictlist[0]
            x = XSollHausgeld( d )
            return x
        else:
            raise Exception( "SollHausgeldData.getLetztesSollHausgeld:\nZu '%s' kein aktuelles Soll-Hausgeld gefunden."
                             % mobj_id )

    def _getSelectClause( self ) -> str:
        """
        Liefert die Select-Klausel für Tabelle sollhausgeld
        Es ist KEINE from und KEINE where-Clause enthalten.
        Der Alias für sollhausgeld ist <s>
        """
        return \
            "select s.shg_id, s.vwg_id, s.mobj_id, s.von, coalesce(s.bis, '') as bis, s.netto, s.ruezufue, " \
            "(s.netto + s.ruezufue) as brutto, s.bemerkung "

    def _getSelectClauseMitVerwaltungJoin( self ) -> str:
        """
        Liefert die Select-Klausel für Tabelle sollhausgeld MIT Verwaltungsspalten <vw_id> und <weg_name>
        und *MIT JOIN* auf die Tabellen verwaltung und mietobjekt.
        Es ist KEINE where-Clause enthalten.
        Der Alias für sollhausgeld ist <s>, für verwaltung <vwg>
        Außerdem ist die Tabelle mietobjekt verjoint. Ihr Alias ist <mo>
        """
        return \
            "select s.shg_id, s.vwg_id, s.mobj_id, s.von, coalesce(s.bis, '') as bis, s.netto, s.ruezufue, " \
            "(s.netto + s.ruezufue) as brutto, s.bemerkung, " \
            "vwg.vw_id, vwg.weg_name "\
            "from sollhausgeld s " \
            "inner join verwaltung vwg on vwg.vwg_id = s.vwg_id " \
            "inner join mietobjekt mo on mo.mobj_id = s.mobj_id "

    def insertSollHausgeld( self, xsh:XSollHausgeld ):
        bis = "NULL" if not xsh.bis else ("'%s'" % xsh.bis)
        bemerkung = "NULL" if not xsh.bemerkung else ("'%s'" % xsh.bemerkung)
        sql = "insert into sollhausgeld " \
              "( vwg_id,     mobj_id,      von,    bis,    netto,     ruezufue,   bemerkung ) " \
              "values " \
              "(   %d,          '%s',      '%s',    %s,    %.2f,       %.2f,       %s)" % \
              ( xsh.vwg_id, xsh.mobj_id, xsh.von,   bis, xsh.netto, xsh.ruezufue, bemerkung )
        rc = self.writeAndLog( sql, DbAction.INSERT, "sollhausgeld", "shg_id", 0, xsh.toString( printWithClassname=True ) )
        return rc

    def updateSollHausgeld( self, xsh:XSollHausgeld ) -> int:
        """
        :param xsh: das XSollHausgeld-Objekt, das die modifizierten Werte enthält, mit denen der Update vorgenommen wird.
        :return: rowcount. Ist 1, wenn xsh.shg_id eine gültige ID ist.
        """
        bis = "NULL" if not xsh.bis else ("'%s'" % xsh.bis)
        bemerkung = "NULL" if not xsh.bemerkung else ("'%s'" % xsh.bemerkung)
        currentX = self.getSollHausgeld( xsh.shg_id )
        sql = "update sollhausgeld " \
              "set vwg_id = %d, " \
              "mobj_id = '%s', " \
              "von = '%s', " \
              "bis = %s, " \
              "netto = %.2f, " \
              "ruezufue = %.2f, " \
              "bemerkung = %s " \
              "where shg_id = %d " % ( xsh.vwg_id, xsh.mobj_id, xsh.von, bis,
                                       xsh.netto, xsh.ruezufue, bemerkung, xsh.shg_id )
        rc = self.writeAndLog( sql, DbAction.UPDATE, "sollhausgeld", "shg_id", xsh.shg_id,
                               xsh.toString(printWithClassname=True), currentX.toString( printWithClassname=True ) )
        return rc

    def deleteSollHausgeld( self, shg_id:int ):
        currentX = self.getSollHausgeld( shg_id )
        sql = "delete from sollhausgeld where shg_id = '%d' " % shg_id
        self.writeAndLog( sql, DbAction.DELETE, "sollhausgeld", "shg_id", shg_id,
                          newvalues=None, oldvalues=currentX.toString( printWithClassname=True ) )

def test2():
    data = SollHausgeldData()
    # finde minMon und maxMon für das Jahr 2022
    jahr = 2021
    l = data.getSollHausgeldHistorie( "kuchenberg_w", "asc", jahr )
    # in l befinden sich nur XHausgeld-Objekte, die irgendwann in 2022 gültig waren
    min = "%d-01-01" % jahr
    max = "%d-12-31" % jahr
    vonMon = "99"
    bisMon = "00"
    for s in l:
        if s.von < min: # <von> LT 1.1.<jahr>, also muss <bis> in <jahr> gültig (gewesen) sein, sonst hätten
                        # wir diesen Satz gar nicht selektiert. Also ist dieser Satz ab Januar gültig.
            vonMon = "01"
        else: # s.von beginnt in <jahr>, sonst hätten wir diesen Satz nicht selektiert
            von = s.von[5:7]
            if von < vonMon:
                vonMon = von
        if not s.bis or s.bis > max: # <bis> GT 31.12.<jahr>, also muss <von> in <jahr> (oder früher) liegen,
                                     # sonst hätten wir diesen Satz nicht selektiert.
                                     # Also ist dieser Satz im Dezember gültig.
            bisMon = "12"
        else:
            bis = s.bis[5:7]
            if bis > bisMon:
                bisMon = bis
    print( "Hausgeldzahlungen erfolgten im Jahr %d von Monat %s bis Monat %s." % (jahr, vonMon, bisMon ))


def test():
    data = SollHausgeldData()
    # x:XSollHausgeld = data.getCurrentSollHausgeld( "charlotte" )
    x: XSollHausgeld = data.getSollHausgeldAm( "charlotte", 2022, 5 )
    x.print()
    # x = data.getSollHausgeld( 141 )
    # x.bemerkung = "dslkjfdslkjfdskjlfds"
    #rc = data.updateSollHausgeld( x )
    # x = XSollHausgeld()
    # x.vwg_id = 999
    # x.mobj_id = "testmobj_id"
    # x.von = "2023-01-01"
    # x.netto = -111.111
    # x.ruezufue = -22.89
    # x.bemerkung = "löschen, nur Test"
    # data.insertSollHausgeld( x )
    # data.commit()
    #print( rc )