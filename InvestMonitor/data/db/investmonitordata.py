from typing import List, Dict

from base.databasecommon2 import DatabaseCommon
from interface.interfaces import XDepotPosition, XDelta
from imon.definitions import DATABASE


class InvestMonitorData( DatabaseCommon ):
    def __init__( self ):
        DatabaseCommon.__init__( self, DATABASE )

    def getDepotPositions( self ) -> List[XDepotPosition]:
        sql = "select pos.id, isin, ticker, wkn, basic_index, name, gattung, ter, waehrung, flag_acc, beschreibung, " \
              "toplaender, topsektoren, topfirmen, anteil_usa, " \
              "dep.id as depot_id, dep.bank, dep.nr as depot_nr, dep.vrrkto as depot_vrrkto " \
              "from depotposition pos " \
              "inner join depot dep on dep.id = pos.depot_id " \
              "where flag_displ = 1 " \
              "order by wkn "
        xlist = self.readAllGetObjectList( sql, XDepotPosition )
        return xlist

    def getDepotPosition( self, ticker:str ) -> XDepotPosition:
        sql = "select pos.id, isin, ticker, wkn, basic_index, name, gattung, ter, waehrung, flag_acc, beschreibung, " \
              "toplaender, topsektoren, topfirmen, anteil_usa, " \
              "dep.id as depot_id, dep.bank, dep.nr as depot_nr, dep.vrrkto as depot_vrrkto " \
              "from depotposition pos " \
              "inner join depot dep on dep.id = pos.depot_id " \
              "where ticker = '%s' " % ticker
        x = self.readOneGetObject( sql, XDepotPosition )
        return x

    def getDeltas( self, wkn:str ) -> List[XDelta]:
        sql = "select id, wkn, delta_stck, delta_datum, preis_stck, verkauft_stck, verkaufskosten, bemerkung, " \
              "delta_stck*preis_stck as order_summe " \
              "from delta " \
              "where wkn = '%s' " \
              "order by delta_datum desc " % wkn
        deltalist = self.readAllGetObjectList( sql, XDelta )
        return deltalist

    def getKaeufe( self, wkn:str ) -> List[XDelta]:
        sql = "select id, wkn, delta_stck, delta_datum, preis_stck, verkauft_stck, bemerkung " \
              "from delta " \
              "where wkn = '%s' " \
              "and delta_stck > 0 " \
              "order by delta_datum asc " % wkn
        deltalist = self.readAllGetObjectList( sql, XDelta )
        return deltalist

    def getAllDeltas( self, distributingOnly=False, flag_displ=1 ) -> List[XDelta]:
        sql = "select delta.id, delta.delta_stck, delta.delta_datum, delta.preis_stck, " \
              "delta.verkauft_stck, delta.verkaufskosten, " \
              "delta.bemerkung, delta_stck*preis_stck as order_summe, " \
              "dp.name, dp.depot_id, delta.wkn, dp.isin, dp.ticker " \
              "from delta delta " \
              "inner join depotposition dp on dp.wkn = delta.wkn " \
              "where dp.flag_displ = %d " % flag_displ
        if distributingOnly:
            sql += " and dp.flag_acc = 0 "
        sql += "order by delta.delta_datum desc, delta.id desc "
        deltalist = self.readAllGetObjectList( sql, XDelta )
        return deltalist

    def getAllMyTickers( self ) -> List[str]:
        sql = "select ticker " \
              "from depotposition pos " \
              "where flag_displ = 1 "
        tupleList = self.read( sql )
        tickerlist = [tpl[0] for tpl in tupleList]
        return tickerlist

    def getAllWknAndTickers( self, distributingOnly=False, flag_displ=1 ) -> List[Dict]:
        sql = "select wkn, ticker " \
              "from depotposition " \
              "where flag_displ = %d " % flag_displ
        if distributingOnly:
            sql += " and flag_acc = 0 "
        dictlist = self.readAllGetDict( sql )
        return dictlist

    def insertDelta( self, delta:XDelta ):
        """
        Der Insert ist entweder ein Kauf oder ein Verkauf.
        Das Feld verkauft_stck spielt beim Insert nie eine Rolle, deswegen bleibt es hier unberücksichtigt
        :param delta:
        :return:
        """
        if not delta.bemerkung: bemerkung = "NULL"
        else: bemerkung = "'%s'" % delta.bemerkung
        sql = "insert into delta " \
              "(wkn, delta_stck, delta_datum, preis_stck, verkaufskosten, bemerkung) " \
              "values " \
              "( '%s', %d, '%s', %.3f, %.2f, %s )" % ( delta.wkn, delta.delta_stck, delta.delta_datum, delta.preis_stck,
                                                       delta.verkaufskosten, bemerkung )
        self.write( sql )

    def updateDelta( self, delta:XDelta ):
        if not delta.bemerkung: bemerkung = "NULL"
        else: bemerkung = "'%s'" % delta.bemerkung
        sql = "update delta " \
              "set delta_stck = %d, " \
              "delta_datum = '%s', " \
              "preis_stck = %.3f, " \
              "verkauft_stck = %d, " \
              "verkaufskosten = %.2f," \
              "bemerkung = %s " \
              "where id = %d " % ( delta.delta_stck, delta.delta_datum, delta.preis_stck, delta.verkauft_stck,
                                   delta.verkaufskosten, bemerkung, delta.id )
        self.write( sql )

    def updateDeltaVerkaufteStuecke( self, delta_id:int, verkauft_stck:int ):
        sql = "update delta " \
              "set verkauft_stck = %d " \
              "where id = %d " % (verkauft_stck, delta_id)
        self.write( sql )

def test():
    data = InvestMonitorData()
    li = data.getAllWknAndTickers( distributingOnly=True )

    li = data.getAllDeltas( distributingOnly=False )
    print( li )
    #l = data.getDepotPositions()
    strlist = data.getAllMyTickers()
    print( strlist )
    deltalist = data.getDeltas( "WTEM.DE" )
    print( deltalist )
