from typing import List, Dict

from v2.icc.iccdata import IccData, DbAction
from v2.icc.interfaces import XMietobjektAuswahl, XMietobjektExt, XMietobjekt


class MietobjektData( IccData ):
    def __init__(self):
        IccData.__init__( self )

    def getMietobjekte( self ) -> List[XMietobjektAuswahl]:
        """
        Liefert Mietobjekte mit den *aktuellen* Mietern (oder ohne, wenn gerade nicht vermietet ist)
        :return:
        """
        sql = "select mobj.master_name, mobj.mobj_id, mv.mv_id " \
              "from mietobjekt mobj " \
              "inner join mietverhaeltnis mv on mv.mobj_id = mobj.mobj_id " \
              "where mobj.aktiv = 1 " \
              "and mv.von <= current_date " \
              "and (mv.bis is NULL or mv.bis = '' or mv.bis >= current_date) " \
              "UNION " \
              "select mobj.master_name, mobj.mobj_id, '' " \
              "from mietobjekt mobj " \
              "where mobj.aktiv = 1 " \
              "and mobj.mobj_id not in " \
              "(select mv.mobj_id " \
              "from mietverhaeltnis mv " \
              "where mv.von <= current_date " \
              "and (mv.bis is NULL or mv.bis = '' or mv.bis >= current_date)) " \
              "order by mobj.master_name, mobj.mobj_id "

        l:List[XMietobjektAuswahl] = self.readAllGetObjectList( sql, XMietobjektAuswahl )
        return l

    def getMietobjektExt( self, mobj_id:str ) -> XMietobjektExt:
        """
        Liefert alle Daten zu einer mobj_id aus den Tabellen masterobjekt und mietobjekt.
        Liefert aus Tabelle verwaltung die Spalten vw_id und weg_name.
        :param mobj_id:
        :return:
        """
        sql = "select m.master_id, m.master_name, m.strasse_hnr, m.plz, m.ort, m.gesamt_wfl, m.anz_whg, m.veraeussert_am," \
              "m.hauswart, m.hauswart_telefon, m.hauswart_mailto, m.heizung, m.energieeffz, m.bemerkung as bemerkung_masterobjekt, " \
              "o.mobj_id, o.whg_bez, o.qm, o.container_nr, o.bemerkung as bemerkung_mietobjekt," \
              "vwg.vw_id as vw_id, vwg.vw_id as verwalter, vwg.vw_ap as verwalter_ap, vwg.weg_name " \
              "from mietobjekt o " \
              "inner join masterobjekt m on m.master_name = o.master_name " \
              "left outer join verwaltung vwg on vwg.master_name = o.master_name " \
              "where o.mobj_id = '%s' " \
              "and vwg.von <= CURRENT_DATE " \
              "and (vwg.bis is NULL or vwg.bis = '' or vwg.bis >= CURRENT_DATE) " % mobj_id
        return self.readOneGetObject( sql, XMietobjektExt )

    def getMietobjektData( self, mobj_id:str ) -> XMietobjekt:
        """
        Liefert die Daten, die von der MietobjektView benötigt werden.
        (Teil der MasterMietobjektMieterView)
        :param mobj_id:
        :return:
        """
        sql = "select mobj_id_num, mobj_id, qm, whg_bez, container_nr, bemerkung " \
              "from mietobjekt " \
              "where mobj_id = '%s' " % mobj_id
        xmobj = self.readOneGetObject( sql, XMietobjekt )
        return xmobj

    def getMietobjektData1( self, mobj_id:str ) -> Dict:
        """
        Liefert whg_bez, container_nr und bemerkung zu einer mobj_id.
        Wird von updateMietobjekt1 verwendet, um das WriteLog schreiben zu können.
        :param mobj_id:
        :return:
        """
        sql = "select mobj_id_num, whg_bez, container_nr, bemerkung " \
              "from mietobjekt " \
              "where mobj_id = '%s' " % mobj_id
        di = self.readOneGetDict( sql )
        return di

    def updateMietobjekt1( self, mobj_id, whg_bez, container_nr, bemerkung ) -> int:
        """
        Speichert Änderungen an einem Mietobjekt: whg_bez, container_nr, bemerkung.
        ACHTUNG: Vor Aufruf dieser Methode müssen die Werte, die *nicht* verändert werden sollen,
                 gelesen und dem Aufruf dieser Methode mitgegeben werden (z.B. mit getMietobjektData1).
        :param mobj_id: Identifizierende ID des Objekts, an dem die Änderungen durchgeführt werden sollen.
        :param whg_bez:
        :param container_nr:
        :param bemerkung:
        :return: die Anzahl der vom Update betroffenen Sätze (sollte 1 sein)
        """
        # aktuelles Objekt holen, wegen WriteLog
        oldD:Dict = self.getMietobjektData1( mobj_id )
        mobj_id_num = oldD["mobj_id_num"]
        oldD.pop( "mobj_id_num", None )
        sql = "update mietobjekt " \
              "set whg_bez = '%s', " \
              "container_nr = '%s', " \
              "bemerkung = '%s' " \
              "where mobj_id = '%s' " % (whg_bez, container_nr, bemerkung, mobj_id)
        newD = { "whg_bez": whg_bez, "container_nr": container_nr, "bemerkung": bemerkung }
        rowsAffected = self.writeAndLog( sql, DbAction.UPDATE,
                                         table="mietobjekt", id_name="mobj_id_num", id_value=mobj_id_num,
                                         newvalues=str(newD), oldvalues=str(oldD) )
        return rowsAffected


#####################################################################################################################
#####################     TESTS  TESTS  TESTS
#####################################################################################################################
def testUpdateMietobjekt():
    data = MietobjektData()
    mobj_id = "kleist_11"
    whg_bez = "1. OG links"
    container_nr = "123ABC"
    bemerkung = "Testbemerkung zu testwohnung"
    data.updateMietobjekt1( mobj_id, whg_bez, container_nr, bemerkung )
    data.commit()
    print( "done." )

def testExt():
    data = MietobjektData()
    xext = data.getMietobjektExt( "kleist_12" )
    xext.print()

def test():
    data = MietobjektData()
    l = data.getMietobjekte()
    print( l )