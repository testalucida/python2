from typing import Dict, List

from v2.icc.iccdata import IccData
from v2.icc.interfaces import XMietverhaeltnis, XMietverhaeltnisKurz


class MietverhaeltnisData( IccData ):
    def __init__(self):
        IccData.__init__( self )

    def getAktuellesMietverhaeltnis( self, mv_id: str ) -> XMietverhaeltnis or None:
        """
        Liefert das aktuelle Mietverhältnis zur gegebenen mv_id (aktiv oder gekündigt).
        Wird für mv_id kein Mietverhältnis gefunden, wird None zurückgegeben.
        NICHT abgedeckt ist der Fall, dass ein Mieter 2 Wohnungen bewohnt.
        Dann wird eine Exception geworfen.
        :param mv_id: Selektionsparameter
        :return: XMietverhaeltnis
        """
        sql = "select mv.id, mv.mv_id, mv.mobj_id, mv.von, coalesce(mv.bis, '') as bis, mv.name, mv.vorname, " \
              "coalesce(mv.name2, '') as name2, coalesce(mv.vorname2, '') as vorname2, " \
              "coalesce(mv.telefon, '') as telefon, coalesce(mv.mobil, '') as mobil, coalesce(mv.mailto, '') as mailto," \
              "mv.anzahl_pers, mv.IBAN, " \
              "mv.bemerkung1, mv.bemerkung2, mv.kaution, coalesce(mv.kaution_bezahlt_am, '') as kaution_bezahlt_am, " \
              "sm.netto as nettomiete, sm.nkv " \
              "from mietverhaeltnis mv " \
              "inner join sollmiete sm on sm.mv_id = mv.mv_id " \
              "where mv.mv_id = '%s' " \
              "and mv.von <= CURRENT_DATE " \
              "and sm.von <= CURRENT_DATE " \
              "and (sm.bis is NULL or sm.bis = '' or sm.bis >= CURRENT_DATE)" \
              "order by mv.von desc, sm.von desc " % mv_id
        listofdicts = self.readAllGetDict( sql )
        if len( listofdicts ) == 0:
            return None
        l = [d["mobj_id"] for d in listofdicts]
        l = list( set( l ) )
        if len( l ) > 1:
            raise Exception( "MietverhaeltnisData.getAktuellesMietverhaeltnis:\n"
                             "Für '%s' existieren mehrere Mietverhältnisse!" % mv_id )
        x = XMietverhaeltnis( listofdicts[0] )
        return x

    def getAktuellesMietverhaeltnisVonBis( self, mv_id:str ) -> Dict:
        """
        Liefert für eine Mietverhältnis-ID das letzte (aktuelle) von/bis.
        Das Mietverhältnis kann noch aktiv oder bereits gekündigt sein.
        "Von" darf nicht in der Zukunft liegen.
        :param mv_id:
        :return: ein Dict mit den Keys id, mv_id, mobj_id, von, bis
        """
        sql = "select id, mv_id, mobj_id, von, bis from mietverhaeltnis " \
              "where mv_id = '%s' " \
              "and von <= CURRENT_DATE " \
              "order by von desc " % mv_id
        dictlist = self.readAllGetDict( sql )
        return dictlist[0]

    def existsAktivesOderZukuenftigesMietverhaeltnis( self, mv_id:str ) -> bool:
        """
        Dient zur Dublettenprüfung einer mv_id
        :param mv_id:
        :return:
        """
        sql = "select id " \
              "from mietverhaeltnis " \
              "where (bis is NULL or bis = '' or bis >= CURRENT_DATE) " \
              "and mv_id = '%s' " % mv_id
        tupleList = self.read( sql )
        return len( tupleList ) > 0

    def getAktuelleMV_IDzuMietobjekt( self, mobj_id:str ) -> str:
        """
        Aktuell heißt: "von" muss
            a) kleiner sein als current date
            b) größer sein als alle anderen "von" in der Vergangenheit
        Es spielt keine Rolle, ob "bis" NULL, in der Vergangenheit oder in der Zukunft liegt.
        :param mobj_id:
        :return:
        """
        sql = "select mv_id " \
              "from mietverhaeltnis " \
              "where mobj_id = '%s' " \
              "and von <= CURRENT_DATE " \
              "order by von desc " % mobj_id
        tuplelist:List[tuple] = self.read( sql )
        if len( tuplelist ) == 0:
            return ""
        return tuplelist[0][0]

    def getMietverhaeltnisse( self, mobj_id:str ) -> List[XMietverhaeltnis]:
        """
        Liefert alle Mietverhältnisse zu einem Mietobjekt.
        Die Attribute XMietverhaeltnis.nettomiete und XMietverhaeltnis.nkv werden nicht versorgt,
        da es sonst zur Verdopplung von Mietverhältnissen käme, die mehr als 1 Sollmiete in ihrer Historie haben.
        :param mobj_id:
        :return:
        """
        sql = "select mv.id, mv.mv_id, mv.mobj_id, mv.von, coalesce(mv.bis, '') as bis, mv.name, mv.vorname, " \
              "coalesce(mv.name2, '') as name2, coalesce(mv.vorname2, '') as vorname2, " \
              "coalesce(mv.telefon, '') as telefon, coalesce(mv.mobil, '') as mobil, coalesce(mv.mailto, '') as mailto," \
              "mv.anzahl_pers, mv.IBAN,  " \
              "mv.bemerkung1, mv.bemerkung2, " \
              "coalesce(mv.kaution, 0) as kaution, coalesce(mv.kaution_bezahlt_am, '') as kaution_bezahlt_am " \
              "from mietverhaeltnis mv " \
              "where mv.mobj_id = '%s' " \
              "order by mv.von desc " % mobj_id
        return self.readAllGetObjectList( sql, XMietverhaeltnis )

    def getMietverhaeltnisById( self, id: int ) -> XMietverhaeltnis:
        """
        Liefert das Mietverhältnis mit der id <id>
        :param id:
        :return:
        """
        sql = "select mv.id, mv.mv_id, mv.mobj_id, mv.von, coalesce(mv.bis, '') as bis, mv.name, mv.vorname, " \
              "coalesce(mv.name2, '') as name2, coalesce(mv.vorname2, '') as vorname2, " \
              "coalesce(mv.telefon, '') as telefon, coalesce(mv.mobil, '') as mobil, coalesce(mv.mailto, '') as mailto," \
              "mv.anzahl_pers, mv.IBAN,  " \
              "mv.bemerkung1, mv.bemerkung2, " \
              "coalesce(mv.kaution, 0) as kaution, coalesce(mv.kaution_bezahlt_am, '') as kaution_bezahlt_am " \
              "from mietverhaeltnis mv " \
              "where mv.id = %d " % id
        d = self.readOneGetDict( sql )
        x = XMietverhaeltnis( d )
        return x

    def getFutureMietverhaeltnis( self, mobj_id:str ) -> XMietverhaeltnis or None:
        """
        Liefert für ein Mietobjekt das nächste in der Zukunft liegende Mietverhältnis bzw. None, wenn kein
        solches existiert.
        Wenn mehrere existieren, wird eine Exception geworfen
        :param mobj_id:
        :return:
        """
        sql = "select mv.id, mv.mv_id, mv.mobj_id, mv.von, coalesce(mv.bis, '') as bis, mv.name, mv.vorname, " \
              "coalesce(mv.name2, '') as name2, coalesce(mv.vorname2, '') as vorname2, " \
              "coalesce(mv.telefon, '') as telefon, coalesce(mv.mobil, '') as mobil, coalesce(mv.mailto, '') as mailto," \
              "mv.anzahl_pers, mv.IBAN, " \
              "mv.bemerkung1, mv.bemerkung2, mv.kaution, coalesce(mv.kaution_bezahlt_am, '') as kaution_bezahlt_am, " \
              "sm.netto as nettomiete, sm.nkv " \
              "from mietverhaeltnis mv " \
              "inner join sollmiete sm on sm.mv_id = mv.mv_id " \
              "where mv.mobj_id = '%s' " \
              "and mv.von > CURRENT_DATE " \
              "order by mv.von asc, sm.von desc " % mobj_id
        listofdicts = self.readAllGetDict( sql )
        if len( listofdicts ) == 0:
            return None
        elif len( listofdicts ) > 1:
            raise Exception( "MietverhaeltnisData.getFutureMietverhaeltnis():\n"
                             "Zu '%s' mehrere zukünftige Mietverhältnisse gefunden." % mobj_id )
        else:
            x = XMietverhaeltnis( listofdicts[0] )
            return x

    def getAktiveMietverhaeltnisseKurz( self, jahr: int, orderby: str = None ) -> List[XMietverhaeltnisKurz]:
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

    def insertMietverhaeltnis( self, x:XMietverhaeltnis ) -> int:
        sql = "insert into mietverhaeltnis " \
              "(mv_id, mobj_id, von, bis, name, vorname, name2, vorname2, telefon, mobil, mailto, anzahl_pers, " \
              "IBAN, kaution, kaution_bezahlt_am, bemerkung1, bemerkung2) " \
              "values " \
              "('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %d, " \
              "'%s', %d, '%s', '%s', '%s') " % \
              ( x.mv_id, x.mobj_id, x.von, x.bis, x.name, x.vorname, x.name2, x.vorname2, x.telefon, x.mobil, x.mailto,
               x.anzahl_pers, x.IBAN, x.kaution, x.kaution_bezahlt_am, x.bemerkung1, x.bemerkung2 )
        return self.write( sql )

    def updateMietverhaeltnis( self, x: XMietverhaeltnis ) -> int:
        """
        macht einen Update mit den in x enthaltenen Daten
        auf einen durch x.id spezifizierten Satz in der Tabelle mietverhaeltnis.
        Ein Update auf mv_id kann mit dieser Methode nicht gemacht werden.
        (Sonst müssten auch die entsprechenden Werte
         in den Tabellen mtleinaus, nk_abrechnung, sollmiete geändert werden)
        :param x:
        :param commit:
        :return:
        """
        sql = "update mietverhaeltnis set " \
              "von = '%s', " \
              "bis = '%s', " \
              "name = '%s', " \
              "vorname = '%s', " \
              "name2 = '%s', " \
              "vorname2 = '%s', " \
              "telefon = '%s', " \
              "mobil = '%s', " \
              "mailto = '%s', " \
              "anzahl_pers = %d, " \
              "bemerkung1 = '%s', " \
              "bemerkung2 = '%s', " \
              "kaution = %d, " \
              "kaution_bezahlt_am = '%s'," \
              "IBAN = '%s' " \
              "where id = %d " % (
              x.von, x.bis, x.name, x.vorname, x.name2, x.vorname2, x.telefon, x.mobil, x.mailto,
              x.anzahl_pers, x.bemerkung1, x.bemerkung2, x.kaution, x.kaution_bezahlt_am, x.IBAN, x.id)
        return self.write( sql )

    def updateMietverhaeltnis2( self, id: int, column: str, newVal: str ):
        sql = "update mietverhaeltnis set %s = '%s' where id = %d " % (column, newVal, id)
        return self.write( sql )

    def updateMietverhaeltnis3( self, id:int, telefon:str, mailto:str, bemerkung1:str, bemerkung2:str ):
        sql = "update mietverhaeltnis set " \
              "telefon = '%s', " \
              "mailto = '%s', " \
              "bemerkung1 = '%s', " \
              "bemerkung2 = '%s' " \
              "where id = %d " % (telefon, mailto, bemerkung1, bemerkung2, id)
        return self.write( sql )

def test4():
    mvsql = MietverhaeltnisData()
    try:
        x: XMietverhaeltnis = mvsql.getMietverhaeltnisById( 44 )
    except Exception as ex:
        print( str(ex) )
    print( "Ende Test." )


def test3():
    mvsql = MietverhaeltnisData()
    mvlist = mvsql.getMietverhaeltnisse( "mendel_8" )
    print( mvlist )

def test2():
    mvsql = MietverhaeltnisData()
    mv_id = mvsql.getAktuelleMV_IDzuMietobjekt( "mendel_8" )
    print( mv_id )

def test():
    mvsql = MietverhaeltnisData()
    # dic = mvsql.getAktuellesMietverhaeltnisVonBis( "yilmaz_yasar" )
    # print( dic )
    x:XMietverhaeltnis = mvsql.getAktuellesMietverhaeltnis( "yilmaz_yasar" )
    # x: XMietverhaeltnis = mvsql.getAktuellesMietverhaeltnis( "wagner_irmgardottilie" )
    print( "Ende Test." )



if __name__ == "__main__":
    test()