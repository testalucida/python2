from v2.icc.iccwidgets import IccCheckTableViewFrame
from v2.mtleinaus.mtleinausview import MtlEinAusTableView

##############   UebrigeRegelmaessTableView   #################
class UebrigeRegelmaessTableView( MtlEinAusTableView ):
    def __init__( self ):
        MtlEinAusTableView.__init__( self )

##############  UebrigeRegelmaessTableViewFrame  #############
class UebrigeRegelmaessTableViewFrame( IccCheckTableViewFrame ):
    def __init__( self, tableView:UebrigeRegelmaessTableView ):
        IccCheckTableViewFrame.__init__( self, tableView )