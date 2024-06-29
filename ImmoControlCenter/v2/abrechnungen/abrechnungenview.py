from base.interfaces import XBaseUI
from v2.icc.iccwidgets import IccCheckTableViewFrame, IccTableView, IccTableViewFrame
from v2.icc.interfaces import XAbrechnung
from v2.mtleinaus.mtleinausview import MtlEinAusTableView

##############   UebrigeRegelmaessTableView   #################
class AbrechnungTableView( IccTableView ):
    def __init__( self ):
        IccTableView.__init__( self )

##############  UebrigeRegelmaessTableViewFrame  #############
class AbrechnungTableViewFrame( IccTableViewFrame ):
    def __init__( self, tableView:AbrechnungTableView ):
        IccTableViewFrame.__init__( self, tableView, withEditButtons=True )
        self.setNewButtonEnabled( False )
        self.setDeleteButtonEnabled( True )

###############   HGAbrechnungTableView  ################
class HGAbrechnungTableView( AbrechnungTableView ):
    def __init__(self):
        AbrechnungTableView.__init__( self )

###############   HGAbrechnungTableViewFrame   ##############
class HGAbrechnungTableViewFrame( AbrechnungTableViewFrame ):
    def __init__( self, hgaTv:HGAbrechnungTableView ):
        AbrechnungTableViewFrame.__init__( self, hgaTv )

###############   NKAbrechnungTableView  ################
class NKAbrechnungTableView( AbrechnungTableView ):
    def __init__( self ):
        AbrechnungTableView.__init__( self )

###############   NKAbrechnungTableViewFrame   ##############
class NKAbrechnungTableViewFrame( AbrechnungTableViewFrame ):
    def __init__( self, nkaTv: NKAbrechnungTableView ):
        AbrechnungTableViewFrame.__init__( self, nkaTv )

##################  XAbrechnungUI  #########################
class XAbrechnungUI( XBaseUI ):
    def __init__( self, x:XAbrechnung ):
        XBaseUI.__init__( self, x )