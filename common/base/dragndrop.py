from typing import List, Tuple

from PySide2.QtGui import QFont, QMouseEvent
from PySide2.QtWidgets import (QWidget, QScrollArea, QMainWindow, QFrame, QLayoutItem)
from PySide2.QtCore import Qt, QSize, QPoint, QRect
from PySide2 import QtWidgets
import sys

from base.baseqtderivates import BaseGridLayout, BaseLabel, GridLayoutItem

###################################################
class DragWidgetsContainer( QWidget ):
    """
    Widget, auf dem alle Widgets angeordnet werden.
    Derzeit können keine Child-Layouts behandelt werden.
    Der Container kann z.B. auf einer QScrollArea platziert werden.
    Die hinzugefügten Widgets werden in einem BaseGridLayout ausgelegt.
    Getestet ist DragWidgetsContainer nur für Widggets mit rowspan und colspan == 1
    """
    def __init__( self ):
        QWidget.__init__( self )
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._dragWidget:QWidget = None
        self._dragWidgetIndex:int = -1
        self._dragWidgetPositon:Tuple = None # (Pos.info des _dragWidget: (row,  col, rowspan,  colspan) )
        self._dragWidgetOldX:int = None
        self._dragWidgetOldY: int = None
        self._lastPos:QPoint = None
        self._mouseRelToLeft:int = None
        self._mouseRelToTop:int = None
        self._insertIndicator:QWidget = None
        self._itemList:List[GridLayoutItem] = None

    def getRowAndColumnCount( self ) -> Tuple:
        rows = self._layout.rowCount()
        cols = self._layout.columnCount()
        return rows, cols

    def removeWidget( self, widget:QWidget ):
        self._layout.removeWidget( widget )
        # todo -- was tun mit der Lücke?

    def addWidget( self, widget: QWidget, row:int, col:int, rowspan=1, colspan=1, alignment=Qt.AlignCenter ):
        self._layout.addWidget( widget, row, col, rowspan, colspan, alignment )

    def mousePressEvent( self, event ):
        self._itemList = self._layout.getAddedItems() # Reihenfolge VOR Drag-Vorgang
        widget = self.childAt( event.pos() )
        self._dragWidget = widget
        self._dragWidgetIndex = self._layout.indexOf( widget )
        self._dragWidgetPositon = self._layout.getItemPosition( self._dragWidgetIndex )
        self._dragWidgetOldX = widget.x()
        self._dragWidgetOldY = widget.y()
        others = self._layout.getAddedItems()
        for other in others:
            if other.item == widget: continue
            other.item.stackUnder( widget )
        self._lastPos = event.pos()
        self._mouseRelToLeft = self._lastPos.x() - widget.x()
        self._mouseRelToTop = self._lastPos.y() - widget.y()
        self._dragWidget.setCursor( Qt.DragMoveCursor )

    def mouseReleaseEvent( self, event:QMouseEvent ):
        self._dragWidget.setCursor( Qt.ArrowCursor )
        intersectedItem:GridLayoutItem = self._findIntersectedItem() # das ist das "verdr#ngte" Item
        if intersectedItem:
            # Drag-Vorgang beendet.
            # Jetzt die Widgets neu anordnen
            self._rearrange( intersectedItem )
        else:
            # das nicht genügend bewegte Panel wieder an seinen Platz verfrachten
            self._dragWidget.move( self._dragWidgetOldX, self._dragWidgetOldY )
        self._dragWidget = None
        self._dragWidgetIndex = -1
        self._dragWidgetOldX = None
        self._dragWidgetOldY = None
        self._lastPos = None
        self._insertIndicator = None

    def mouseMoveEvent( self, event ):
        if self._lastPos:
            widget = self._dragWidget
            x = event.pos().x() - self._mouseRelToLeft
            y = event.pos().y() - self._mouseRelToTop
            widget.move( x, y )
            self._lastPos = event.pos()

    def _findIntersectedItem( self, minOverlap=0.5 ) -> GridLayoutItem or None:
        """
        Ermittelt das Widget, das vom _dragWidget am Ende des Drag-Vorgangs am meisten überdeckt ist.
        Maßgeblich ist, dass die überdeckende Fläche des _dragWidgets mindestens seiner Fläche * minOverlap entspricht.
        :param minOverlap: Quotient der Fläche des _dragWidgets, mit dem ausgerechnet wird, welche Teilfläche des
                        _dragWidgets mindestens über das andere Widget drübergeschoben sein muss.
        :return: das am meisten überdeckte Widget bzw. None, wenn
        """
        dragwidgetrect = self._dragWidget.geometry()
        r = self._dragWidget.rect()
        dragwidgetarea = r.width() * r.height()
        minDragWidgetOverlapArea = int( dragwidgetarea * minOverlap )
        interarea_memo = 0
        dragitem_memo = None
        gridLayoutItems: List[GridLayoutItem] = self._layout.getAddedItems()
        for gli in gridLayoutItems:
            if gli.item != self._dragWidget and gli.isWidget():
                widget = gli.item
                r: QRect = widget.geometry()
                widgetArea = r.width() * r.height()
                if widgetArea <= dragwidgetarea:
                    # die Fläche des überlappten Widgets ist kleiner/gleich der FLäche des _dragWidget.
                    # D.h., wir berechnen die minOverlapArea mit dem überlappten Widget.
                    minOverlapArea = int( widgetArea * minOverlap )
                else:
                    # die Fläche des überlappten Widgets ist größer als die FLäche des _dragWidget.
                    # D.h., die minOverlapArea entspricht der oben berechneten minDragWidgetOverlapArea.
                    minOverlapArea = minDragWidgetOverlapArea
                interrect = r.intersected( dragwidgetrect )
                interarea = interrect.width() * interrect.height()  # von _dragWidget überdeckte Fläche des anderen Widgets
                if interarea >= minOverlapArea and interarea > interarea_memo:
                    interarea_memo = interarea
                    dragitem_memo = gli
        return dragitem_memo

    def _rearrange( self, intersectedItem:GridLayoutItem ):
        # zuerst das _dragWidget (bzw. dessen Item) aus der _itemList entfernen und an der Position
        # des intersectedItem einfügen. Dieses rutscht dadurch an die folgende Position.
        # !!!ACHTUNG!!! Derzeitige Einschränkung: rowspan und colspan > 1 werden nicht berücksichtigt!!!
        #       (Bzw. der entsprechende Code ist nicht getestet)
        def getOldDragItem():
            dragItem = None
            oldDragItemIdx = -1
            for item in self._itemList:
                oldDragItemIdx += 1
                if item.item == self._dragWidget:
                    dragItem = item
                    break
            return dragItem, oldDragItemIdx

        def getIntersectedItemListIndex():
            interItemIdx = -1
            for item in self._itemList:
                interItemIdx += 1
                if item.item == intersectedItem.item:
                    break
            return interItemIdx

        def removeItemsFromLayout( startIdx:int ):
            for i in range( startIdx, len( self._itemList ) ):
                gridLayoutItem: GridLayoutItem = self._itemList[i]
                if gridLayoutItem.isWidget():
                    self._layout.removeWidget( gridLayoutItem.item )
                else:
                    layoutItem:QLayoutItem = self._layout.itemAt( gridLayoutItem.index )
                    self._layout.removeItem( layoutItem )

        def rebuildLayout( startIdx:int, startrow:int, startcol:int ):
            def getMaxColumn() -> int:
                maxcol = 0
                for item in self._itemList:
                    if item.column > maxcol:
                        maxcol = item.column + item.colspan - 1
                return maxcol

            row = startrow
            col = startcol
            maxcolIdx = getMaxColumn()
            for i in range( startIdx, len( self._itemList ) ):
                gridLayoutItem: GridLayoutItem = self._itemList[i]
                if gridLayoutItem.isWidget():
                    self._layout.addWidget( gridLayoutItem.item, row, col, gridLayoutItem.rowspan, gridLayoutItem.colspan )
                else:
                    self._layout.addLayout( gridLayoutItem.item, row, col, gridLayoutItem.rowspan, gridLayoutItem.colspan )
                col += gridLayoutItem.colspan
                if col > maxcolIdx:
                    col = 0
                    row += 1

        # Das DragItem aus der Liste _itemList entfernen und an der richtigen Stelle wieder einsetzen.
        # Die richtige Stelle ist die, wo im Moment noch das intersectedItem sitzt. An dessen Stelle
        # muss das DragItem eingefügt werden.
        # Alle nachfolgenden List-Items werden dadurch um eine Position nach rechts verschoben.
        dragItem, oldDragItemListIdx = getOldDragItem()
        del self._itemList[oldDragItemListIdx]
        newDragItemListIdx = getIntersectedItemListIndex()
        self._itemList.insert( newDragItemListIdx, dragItem )
        # Bestimmen des Index, ab dem die _itemList im Layout neu aufgebaut werden muss.
        # Alle Items ab diesem Index müssen vom Layout entfernt und neu arrangiert werden.
        if newDragItemListIdx < oldDragItemListIdx:
            startListIdx = newDragItemListIdx
            startRow = intersectedItem.row
            startCol = intersectedItem.column
        else:
            startListIdx = oldDragItemListIdx
            startRow = dragItem.row
            startCol = dragItem.column
        # Nachfolgende Items vom Layout entfernen...
        removeItemsFromLayout( startListIdx )
        # und neu aufbauen:
        rebuildLayout( startListIdx, startRow, startCol )

###########################################################
class ScrollArea( QScrollArea ):
    def __init__(self):
        QScrollArea.__init__( self )
        self._allPanels = DragWidgetsContainer()
        self.setWidget( self._allPanels )
        self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )
        self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOn )
        self.setWidgetResizable( True )

    def addWidget( self, widget:QWidget, row:int, col:int, rowspan=1, colspan=1, alignment=Qt.AlignCenter ):
        self._allPanels.addWidget( widget, row, col, rowspan, colspan, alignment )

############################################################


class ExampleWidget( QFrame ):
    nr = 0
    labelfont = QFont( "Ubuntu", 16 )
    def __init__( self ):
        QFrame.__init__( self )
        self._nr = str( ExampleWidget.nr )
        #borderstyle = "#" + self._nr + " {border: 5px solid darkblue; }"
        borderstyle = "border: 3px solid darkblue;"
        self.setStyleSheet( borderstyle )
        self.setFixedSize( QSize(400, 400) )
        self._lbl = BaseLabel( self._nr )
        self._lbl.setFont( self.labelfont )
        self._lbl.setFixedWidth( 50 )
        self._lbl.setFixedHeight( 50 )
        self._lbl.setAlignment( Qt.AlignCenter )
        labelstyle = "border: 1px solid red;"
        self._lbl.setStyleSheet( labelstyle )
        ExampleWidget.nr += 1
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._layout.addWidget( self._lbl, 0, 0, 1, 1, alignment=Qt.AlignVCenter | Qt.AlignHCenter )

    def getLabel( self ) -> str:
        return self._nr


class ExampleMainWindow( QMainWindow ):
    def __init__(self):
        super().__init__()
        self.scroll = ScrollArea()
        self.panels = list()
        r = c = 0
        maxcol = 4
        for i in range(1, 20):
            panel = ExampleWidget()
            panel.setObjectName( "Panel " + str(i) )
            self.panels.append( panel )
            self.scroll.addWidget( panel, r, c )
            c += 1
            if c > maxcol:
                c = 0
                r += 1
        self.setCentralWidget( self.scroll )
        self.setGeometry(600, 100, 1500, 900)
        self.setWindowTitle('Scroll Area Demonstration')
        self.show()


def test():
    app = QtWidgets.QApplication( sys.argv )
    main = ExampleMainWindow()

    sys.exit( app.exec_() )