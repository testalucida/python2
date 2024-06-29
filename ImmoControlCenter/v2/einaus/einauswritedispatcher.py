from typing import List
from PySide2.QtCore import QObject, Signal
from v2.icc.interfaces import XEinAus

class EinAusWriteDispatcher( QObject ):
    ea_inserted = Signal( XEinAus )
    ea_updated = Signal( XEinAus, int or float ) # das geänderte XEinAus-Objekt und die Betragsänderung (ggf. 0)
    ea_deleted = Signal( list, str, int or float ) # Liste von ea_id (gelöschte Sätze), die betroffene ea_art
                                                # (darf nur *eine* sein) und das Delta, um das sich die Summe
                                                # aller Zahlungen geändert hat
    __instance = None
    def __init__( self ):
        QObject.__init__( self )
        if EinAusWriteDispatcher.__instance:
            raise Exception( "EinAusWriteDispatcher is a Single. It may only be instantiated once." )
        else:
            EinAusWriteDispatcher.__instance = self

    @staticmethod
    def inst() -> __instance:
        if EinAusWriteDispatcher.__instance is None:
            EinAusWriteDispatcher()
        return EinAusWriteDispatcher.__instance

    def einaus_inserted( self, x:XEinAus ):
        self.ea_inserted.emit( x )

    def einaus_updated( self, x:XEinAus, delta ):
        self.ea_updated.emit( x, delta )

    def einaus_deleted( self, ea_id_list:List[int], ea_art:str, delta: int or float ):
        """
        :param ea_id_list: Liste der gelöschten ea_id*s
        :param ea_art: EinAusArt, diese muss für alle ea_id*s in ea_id_list gleich sein
        :param delta: der Betrag, um den sich der Gesamtbetrag der Zahlungen durch die Löschung(en) von
        EinAus-Sätzen geändert hat.
        NB: Wenn ein negativer Betrag aus <einaus> gelöscht wurde, muss delta > 0 sein (und umgekehrt)!
        :return:
        """
        self.ea_deleted.emit( ea_id_list, ea_art, delta )

def test():
    def catch( idlist, delta ):
        print( idlist, " -- ", delta )
    EinAusWriteDispatcher.inst().ea_deleted.connect( catch )
    EinAusWriteDispatcher.inst().einaus_deleted( [1,], 2.0 )