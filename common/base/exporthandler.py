import os
import sys
from datetime import datetime
from os.path import isdir

from PySide2.QtCore import QAbstractItemModel, Qt
from PySide2.QtWidgets import QTableView


class ExportHandler:
    def __init__( self ):
        pass

    # def exportToCsv2( self, tv:QTableView ):
    #     self.exportToCsv( tv.model() )

    def exportToCsv( self, model:QAbstractItemModel, tablename:str="TableExport"  ):
        folder = "./csv"
        now = str( datetime.now() )
        if not isdir( folder ):
            os.makedirs( folder )
        csv = folder + "/" + tablename + "_" + now + ".csv"
        csv = csv.replace( " ", "-" )
        csv = csv.replace( ":", "-" )
        f = open( csv, "w" )
        rows = model.rowCount()
        cols = model.columnCount()
        #  Export headers
        for c in range( 0, cols ):
            header = model.headerData( c, Qt.Horizontal, Qt.DisplayRole )
            f.write( header )
            if not c == cols - 1:
                f.write( "\t" )

        for r in range( 0, rows ):
            f.write( "\n" )
            for c in range( 0, cols ):
                idx = model.index( r, c )
                val = model.data( idx, Qt.DisplayRole )
                if val is None: val = ""
                # print( "val=", val, " - r/c=", r, "/", c )
                if isinstance( val, int ) or isinstance( val, float ):
                    val = str( val )
                    val = val.replace( ".", "," )
                else:
                    if self._isIntOrFloatFormat( val ):
                        val = val.replace( ".", "," )
                    else:
                        val = val.replace( "\t", "   " )
                        val = val.replace( "\n", " " )

                f.write( val )
                if not c == cols - 1:
                    f.write( "\t" )
        f.close()

        if sys.platform.startswith( "linux" ):
            os.system( "xdg-open " + csv )

    @staticmethod
    def _isIntOrFloatFormat( val: str ) -> bool:
        points = 0
        minus = 0
        for c in val:
            if not c.isdigit():
                if c == ".":
                    points = points + 1
                    if points > 1: return False
                elif c == "-":
                    minus = minus + 1
                    if minus > 1: return False
                else:
                    return False
        return True