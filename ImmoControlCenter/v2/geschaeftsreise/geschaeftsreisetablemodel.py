from typing import List, Any

from base.basetablemodel import BaseTableModel
from v2.icc.interfaces import XGeschaeftsreise


class GeschaeftsreiseTableModel( BaseTableModel ):
    def __init__( self, reiseList:List[XGeschaeftsreise] ):
        BaseTableModel.__init__( self, reiseList )
        self.setKeyHeaderMappings2(
            ("reise_id", "master_name", "von", "bis", "zweck", "personen", "uebernachtung", "uebernacht_kosten", "km"),
            ( "ID", "Haus", "Beginn", "Ende", "Zweck", "Anz.\nPers.", "Übernachtung", "Übernacht.\nkosten", "Gef. km" )
        )
        # self.setKeyHeaderMappings( {
        #     "Haus": "master_name",
        #     "Beginn": "von",
        #     "Ende": "bis",
        #     "Zweck": "zweck",
        #     "Anz.\nPers.": "personen",
        #     "Übernachtung": "uebernachtung",
        #     "Übernacht.\nkosten": "uebernacht_kosten",
        #     "Gef. km": "km"
        # } )
        #self.setNumColumnsIndexes( (4, 6, 7) )

    def getBackground( self, indexrow: int, indexcolumn: int ) -> Any:
        return None
