from typing import List

from v2.icc.icclogic import IccTableModel
from v2.icc.interfaces import XEinAus


class SonstEinAusTableModel( IccTableModel ):
    def __init( self, rowList:List[XEinAus], jahr ):
        IccTableModel.__init__( rowList, jahr )
        self.setKeyHeaderMappings2(
            ( "master_name", "mobj_id", "debi_kredi", "buchungstext", "buchungsdatum", "ea_art", "verteilt_auf",
              "betrag", "mehrtext" ),
            ( "Haus",        "Whg",     "Debitor/Kreditor", "Buchungstext", "Buch.datum", "Art", "vJ",
              "Betrag", "Bemerkung" )
        )