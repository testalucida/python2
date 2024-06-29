from v2.icc.icccontroller import IccController
from v2.icc.iccwidgets import IccCheckTableViewFrame, IccTableView


class SonstEinAusController( IccController ):
    def __init__( self ):
        IccController.__init__( self )
        self._tableViewFrame:IccCheckTableViewFrame = None
        self._tv:IccTableView = None