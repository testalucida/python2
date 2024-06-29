from abc import abstractmethod
from typing import List

from v2.icc.iccdata import IccData, DbAction
from v2.icc.interfaces import XAbrechnung, XHGAbrechnung, XNKAbrechnung

##################   Base class AbrechnungData   ###################
class AbrechnungData( IccData ):
    def __init__( self ):
        IccData.__init__( self )

    @abstractmethod
    def getObjekteUndAbrechnungen( self, ab_jahr:int ) -> List[XAbrechnung]:
        """
        Liefert eine Liste aller aktiven Objekte mit Verwaltungs- und Abrechnungsdaten für das Jahr <ab_jahr>,
        soweit vorhanden. Die Liste enthält alle Objekte, egal, ob schon eine Abrechnung erstellt wurde oder nicht.
        :param ab_jahr:
        :return:
        """

    @abstractmethod
    def getAbrechnung( self, hga_id:int ) -> XAbrechnung:
        pass

###################   HGAbrechnungData   #########################
"""
# Die Tabelle hg_abrechnung wurde nachträglich um die Spalte mobj_id erweitert.
# Um sie zu initialisieren, wird folgendes Update-Statement verwendet:
update hg_abrechnung 
set mobj_id = (
	select mo.mobj_id 
	from mietobjekt mo 
	inner join verwaltung vwg on vwg.master_name = mo.master_name
	where vwg.vwg_id = hg_abrechnung.vwg_id
)
"""

class HGAbrechnungData( AbrechnungData ):
    def __init__( self ):
        AbrechnungData.__init__( self )

    def insertAbrechnung( self, xhga:XHGAbrechnung ) -> int:
        vwg_id = "NULL" if not xhga.vwg_id else str(xhga.vwg_id)
        bemerkung = "NULL" if not xhga.bemerkung else ("'%s'" % xhga.bemerkung)
        sql = "insert into hg_abrechnung " \
              "(mobj_id, ab_jahr, vwg_id, forderung, entnahme_rue, ab_datum, bemerkung) " \
              "values " \
              "( '%s',    %d,     %s,      %.2f,      %.2f,         '%s',     %s )" % \
                                                                                (xhga.mobj_id, xhga.ab_jahr, vwg_id,
                                                                                 xhga.forderung, xhga.entnahme_rue,
                                                                                 xhga.ab_datum, bemerkung)
        inserted_id = self.writeAndLog( sql, DbAction.INSERT, "hg_abrechnung", "hga_id", 0,
                                        newvalues=xhga.toString( printWithClassname=True ), oldvalues=None )
        xhga.abr_id = inserted_id
        return inserted_id

    def updateAbrechnung( self, xhga:XHGAbrechnung ) -> int:
        oldX = self.getAbrechnung( xhga.abr_id )
        if oldX.mobj_id == xhga.mobj_id \
        and oldX.ab_jahr == xhga.ab_jahr \
        and oldX.vwg_id == xhga.vwg_id \
        and oldX.forderung == xhga.forderung \
        and oldX.entnahme_rue == xhga.entnahme_rue \
        and oldX.ab_datum == xhga.ab_datum \
        and oldX.bemerkung == xhga.bemerkung:
            return 0
        else:
            bemerkung = "NULL" if not xhga.bemerkung else ("'%s'" % xhga.bemerkung)
            sql = "update hg_abrechnung " \
                  "set mobj_id = '%s', " \
                  "ab_jahr = %d, " \
                  "vwg_id = %d, " \
                  "forderung = %.2f, " \
                  "entnahme_rue = %.2f, " \
                  "ab_datum = '%s', " \
                  "bemerkung = %s " \
                  "where hga_id = %d " % (xhga.mobj_id, xhga.ab_jahr, xhga.vwg_id, xhga.forderung, xhga.entnahme_rue,
                                          xhga.ab_datum, bemerkung, xhga.abr_id)
            rowsAffected = self.writeAndLog( sql, DbAction.UPDATE, "hg_abrechnung", "hga_id", xhga.abr_id,
                                             newvalues=xhga.toString( True ), oldvalues=oldX.toString( True ) )
            return rowsAffected

    def deleteAbrechnung( self, xhga:XHGAbrechnung ):
        sql = "delete from hg_abrechnung where hga_id = %d " % xhga.abr_id
        self.writeAndLog( sql, DbAction.DELETE, "hg_abrechnung", "hga_id", xhga.abr_id,
                          newvalues=None, oldvalues=xhga.toString( printWithClassname=True ) )

    # def getObjekteUndAbrechnungen( self, ab_jahr:int ) -> List[XHGAbrechnung]:
    #     sql = "select master.master_name, " \
    #           "vwg.vwg_id, coalesce(vwg.weg_name, '') as weg_name, " \
    #           "coalesce(vwg.vw_id, '') as vw_id, " \
    #           "coalesce(vwg.von, '') as vwg_von, coalesce(vwg.bis, '') as vwg_bis, " \
    #           "coalesce(hga.hga_id, 0) as abr_id, " \
    #           "coalesce(hga.mobj_id, '') as mobj_id, " \
    #           "coalesce(hga.ab_datum, '') as ab_datum, " \
    #           "coalesce(hga.forderung, 0) as forderung, coalesce(hga.entnahme_rue, 0) as entnahme_rue, " \
    #           "coalesce(hga.bemerkung, '') as bemerkung " \
    #             "from masterobjekt master " \
    #             "inner join verwaltung vwg on vwg.master_name = master.master_name " \
    #             "left outer join hg_abrechnung hga on (hga.ab_jahr = %d and hga.vwg_id = vwg.vwg_id) " \
    #             "where master.aktiv > 0 " \
    #             "order by master.master_name, vwg.von " % ab_jahr
    #     return self.readAllGetObjectList( sql, XHGAbrechnung )

    def getObjekteUndAbrechnungen( self, ab_jahr: int ) -> List[XHGAbrechnung]:
        max_vwg_von = str(ab_jahr) + "-12-31"
        min_vwg_bis = str(ab_jahr) + "-01-01"
        sql = "select mo.master_name, mo.mobj_id, " \
              "vwg.vwg_id, vwg.weg_name, " \
              "vwg.vw_id, vwg.von, coalesce(vwg.bis, '') as vwg_bis, " \
              "coalesce(hga.hga_id, 0) as abr_id, " \
              "coalesce(hga.ab_jahr, 0) as ab_jahr, " \
              "coalesce(hga.ab_datum, '') as ab_datum, " \
              "coalesce(hga.forderung, 0) as forderung, " \
              "coalesce(hga.entnahme_rue, 0) as entnahme_rue, " \
              "coalesce(hga.bemerkung, '') as bemerkung " \
              "from mietobjekt mo " \
              "inner join verwaltung vwg on vwg.master_name = mo.master_name " \
              "left outer join hg_abrechnung hga on (hga.ab_jahr = %d and hga.mobj_id = mo.mobj_id) " \
              "\n--where mo.aktiv > 0 \n " \
              "where vwg.von <= '%s' " \
              "and (vwg.bis is NULL or vwg.bis = '' or vwg.bis >= '%s') " \
              "order by mo.master_name, vwg.von " % (ab_jahr, max_vwg_von, min_vwg_bis)
        abrlist = self.readAllGetObjectList( sql, XHGAbrechnung )
        return abrlist

    def getAbrechnung( self, hga_id:int ) -> XHGAbrechnung:
        sql = "select hga_id, mobj_id, ab_jahr, vwg_id, forderung, entnahme_rue, ab_datum, bemerkung " \
              "from hg_abrechnung " \
              "where hga_id = %d " % hga_id
        x = self.readOneGetObject( sql, XHGAbrechnung )
        return x


###################   NKAbrechnungData   #########################
class NKAbrechnungData( AbrechnungData ):
    def __init__( self ):
        AbrechnungData.__init__( self )

    def insertAbrechnung( self, xnka: XNKAbrechnung ) -> int:
        bemerkung = "NULL" if not xnka.bemerkung else ("'%s'" % xnka.bemerkung)
        sql = "insert into nk_abrechnung " \
              "(ab_jahr, mv_id, forderung, ab_datum, bemerkung) " \
              "values " \
              "(   %d,     '%s',  %.2f,      '%s',     %s )" % (xnka.ab_jahr, xnka.mv_id,
                                                                  xnka.forderung, xnka.ab_datum, bemerkung)
        inserted_id = self.writeAndLog( sql, DbAction.INSERT, "nk_abrechnung", "nka_id", 0,
                                        newvalues=xnka.toString( printWithClassname=True ), oldvalues=None )
        xnka.abr_id = inserted_id
        return inserted_id

    def updateAbrechnung( self, xnka:XNKAbrechnung ) -> int:
        oldX = self.getAbrechnung( xnka.abr_id )
        bemerkung = "NULL" if not xnka.bemerkung else ("'%s'" % xnka.bemerkung)
        sql = "update nk_abrechnung " \
              "set ab_jahr = %d, " \
              "mv_id = '%s', " \
              "forderung = %.2f, " \
              "ab_datum = '%s', " \
              "bemerkung = %s " \
              "where nka_id = %d " % (xnka.ab_jahr, xnka.mv_id, xnka.forderung, xnka.ab_datum,
                                      bemerkung, xnka.abr_id)
        rowsAffected = self.writeAndLog( sql, DbAction.UPDATE, "nk_abrechnung", "nka_id", xnka.abr_id,
                                         newvalues=xnka.toString( True ), oldvalues=oldX.toString( True ) )
        return rowsAffected

    def deleteAbrechnung( self, xnka: XNKAbrechnung ):
        sql = "delete from nk_abrechnung where nka_id = %d " % xnka.abr_id
        self.writeAndLog( sql, DbAction.DELETE, "nk_abrechnung", "nka_id", xnka.abr_id,
                          newvalues=None, oldvalues=xnka.toString( printWithClassname=True ) )

    def getObjekteUndAbrechnungen( self, ab_jahr:int ) -> List[XNKAbrechnung]:
        if not ab_jahr > 2000: raise  Exception( "Abrechnungsjahr muss vierstellig angegeben werden." )
        mv_min_bis = "'%d-01-01'" % ab_jahr
        mv_max_von = "'%d-12-31'" % ab_jahr
        sql = "select master.master_name, " \
              "mo.mobj_id, mv.mv_id, mv.von, coalesce(mv.bis, '') as bis, " \
              "coalesce(nka.nka_id, 0) as abr_id, coalesce(nka.ab_datum, '') as ab_datum, " \
              "coalesce(nka.forderung, 0) as forderung, " \
              "coalesce(nka.bemerkung, '') as bemerkung " \
              "from masterobjekt master " \
              "inner join mietobjekt mo on mo.master_name = master.master_name " \
              "inner join mietverhaeltnis mv on (mv.mobj_id = mo.mobj_id) " \
              "left outer join nk_abrechnung nka on (nka.ab_jahr = %d and nka.mv_id = mv.mv_id) " \
              "\n--where master.aktiv > 0\n " \
              "where mv.von < %s " \
              "and (mv.bis is null or mv.bis = '' or mv.bis > %s ) " \
              "order by master.master_name, mv.von desc " % (ab_jahr, mv_max_von, mv_min_bis)
        return self.readAllGetObjectList( sql, XNKAbrechnung )

    def getAbrechnung( self, nka_id: int ) -> XNKAbrechnung:
        sql = "select nka_id, ab_jahr, mv_id, forderung, ab_datum, bemerkung " \
              "from nk_abrechnung " \
              "where nka_id = %d " % nka_id
        x = self.readOneGetObject( sql, XNKAbrechnung )
        return x


def test():
    data = NKAbrechnungData()
    l = data.getObjekteUndAbrechnungen( 2021 )
    print( l )