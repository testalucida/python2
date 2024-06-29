from base.basetableview import BaseTableView
from base.basetableviewframe import BaseTableViewFrame

#########################   IccTableView   #####################
class IccTableView( BaseTableView ):
    def __init__(self):
        BaseTableView.__init__( self )

#########################   IccTableViewFrame   #####################
class IccTableViewFrame( BaseTableViewFrame ):
    def __init__( self, tableView:IccTableView, withEditButtons=False ):
        BaseTableViewFrame.__init__( self, tableView, withEditButtons )

###############  IccCheckTableViewFrame  #############
class IccCheckTableViewFrame( IccTableViewFrame ):
    def __init__( self, tableView:BaseTableView ):
        IccTableViewFrame.__init__( self, tableView )

def test():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    v = IccTableView()
    f = IccTableViewFrame( v )
    f.show()
    app.exec_()