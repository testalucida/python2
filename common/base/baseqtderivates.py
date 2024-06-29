import enum
import numbers
from abc import abstractmethod
from enum import Enum
from typing import Any, List, Tuple, Callable, Iterable, Union

from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import QDate, Qt, QAbstractTableModel, QRect, Signal, QSize, QMargins, QEvent, QObject
from PySide2.QtGui import QDoubleValidator, QIntValidator, QFont, QGuiApplication, QStandardItemModel, QStandardItem, \
    QMouseEvent, QTextDocument, QIcon, QFontMetrics, QValidator, QCursor
from PySide2.QtWidgets import QDialog, QCalendarWidget, QVBoxLayout, QBoxLayout, QLineEdit, QGridLayout, QPushButton, \
    QHBoxLayout, QApplication, QListView, QComboBox, QLabel, QTextEdit, QCheckBox, QFrame, QWidget, QAction, QTabWidget, \
    QToolBar, QMenuBar, QStatusBar, QMessageBox, QLayout

import datehelper
from base import constants
from base.directories import BASE_IMAGES_DIR
from base.interfaces import XAttribute
#from definitions import ICON_DIR
from base.messagebox import ErrorBox, WarningBox, QuestionBox

from datehelper import isValidIsoDatestring, isValidEurDatestring, getRelativeQDate, getQDateFromIsoString
#################  BaseAction  ########################
from iconfactory import IconFactoryS


class BaseAction( QAction ):
    def __init__( self, text:str="", tooltip:str="", ident:Any=None, icon:QIcon=None, parent=None, userdata:Any=None,
                  callback:Callable=None):
        QAction.__init__( self )
        if icon: self.setIcon( icon )
        self.setText( text )
        self.setToolTip( tooltip )
        self.setParent( parent )
        self.ident = ident
        self.userdata = userdata
        self.callback = callback

class Separator( QAction ):
    def __init__( self ):
        QAction.__init__( self )
        self.setSeparator( True )

#################  BaseWidget  ########################
class BaseWidget( QWidget ):
    def __init__( self, parent=None, flags=Qt.WindowFlags() ):
        QWidget.__init__( self, parent, flags )
        self._isChanged = False
        self.ident = None

    def setStyleSheetOnlySelf( self, stylesheet: str ) -> None:
        """
        :param stylesheet: z.B. "background: lightgray;"
        :return:
        """
        objectName = self.objectName() if self.objectName() != "" else str( id( self ) )
        self.setObjectName( objectName )
        self.setStyleSheet( "#%s {%s}" % (objectName, stylesheet) )

    def setChanged( self, changed:bool ) -> None:
        self._isChanged = changed

    def isChanged( self ) -> bool:
        return self._isChanged

##################  BaseTabbedWindow  #################
class BaseTabWidget( QTabWidget ):
    def __init__( self, parent=None ):
        QTabWidget.__init__( self, parent )

#################  BaseToolBar  #######################
class BaseToolBar( QToolBar ):
    def __init__( self, parent=None ):
        QToolBar.__init__( self, parent )

#################  BaseMenuBar  #######################
class BaseMenuBar( QMenuBar ):
    def __init__( self, parent=None ):
        QMenuBar.__init__( self, parent )

##################   GetSet   ###################
class GetSetValue:
    @abstractmethod
    def getValue( self ) -> Any:
        pass

    @abstractmethod
    def setValue( self, value: Any ) -> None:
        pass

#################  BaseStatusBar  #######################
class BaseStatusBar( QStatusBar ):
    def __init__( self, parent=None ):
        QStatusBar.__init__( self, parent )

#################  BaseComboBox  ########################
class BaseComboBox( QComboBox, GetSetValue ):
    def __init__(self, parent=None ):
        QComboBox.__init__( self )
        self._userData:Any = None
        self._changeCurrentByMouseWheel = False

    def setChangeCurrentByMouseWheel( self, change=True ):
        self._changeCurrentByMouseWheel = True

    def wheelEvent(self, e:QtGui.QWheelEvent):
        if self._changeCurrentByMouseWheel:
            super().wheelEvent( e )
        else:
            pass

    def getValue( self ) -> str:
        return self.currentText()

    def setValue( self, currentText: str ) -> None:
        self.setCurrentText( currentText )

    def setUserData( self, data:Any ):
        self._userData = data

    def getUserData( self ) -> Any:
        return self._userData

class BaseBoldComboBox( BaseComboBox ):
    def __init__( self, parent=None ):
        BaseComboBox.__init__( self, parent )
        self.setFont( FontArialBold12() )

#####################   YearComboBox  #######################
class YearComboBox( BaseComboBox ):
    year_changed = Signal( int ) # arg: the new year
    def __init__( self, years:List[int]=() ):
        BaseComboBox.__init__( self )
        for y in years:
            self.addItem( str( y ) )
        self.currentIndexChanged.connect(lambda: self.year_changed.emit( int(self.currentText() ) ) )
        self.setMaximumWidth( 100 )

    def addYears( self, years:Iterable[int] ):
        syears = [str(y) for y in years]
        self.addItems( syears )

    def setYear( self, year:int ) -> None:
        self.setCurrentText( str(year) )

    def setCurrentYear( self, year:int ) -> None:
        self.setYear( year )

#################  MonthComboBox  #########################
class MonthComboBox( BaseComboBox ):
    month_changed = Signal( int, str, str ) # args: month idx, month short name, month long name
    def __init__( self ):
        BaseComboBox.__init__( self )
        self.addItems( constants.monthLongNames )
        self.currentIndexChanged.connect( lambda: self.month_changed.emit( self.currentIndex(),
                                                                           constants.monthShortNames[self.currentIndex()],
                                                                           self.currentText() ) )

    def setMonthIdx( self, monthIdx:int ):
        """
        :param monthIdx: 0 = Januar etc.
        :return:
        """
        self.setCurrentIndex( monthIdx )

#################  EditableComboBox  ########################
class EditableComboBox( BaseComboBox, GetSetValue ):
    def __init__(self, parent=None ):
        BaseComboBox.__init__( self )
        self.setEditable( True )

#################  BaseDialog  ########################
class BaseDialog( QDialog ):
    def __init__(self, parent=None, flags=Qt.WindowFlags() ):
        QDialog.__init__( self, parent, flags )

class ButtonIdent( Enum ):
    IDENT_OK = enum.auto()
    IDENT_APPLY = enum.auto()
    IDENT_CANCEL = enum.auto()
    IDENT_CLOSE = enum.auto()
    IDENT_NEXT = enum.auto()
    IDENT_PREV = enum.auto()
    IDENT_NONE = enum.auto()

###########################   BaseDialogWithButtons  etc.  #############################
class BaseButtonDefinition:
    def __init__( self, text, tooltip:str, callback:Callable, callbackData:Any=None, icon:QIcon=None,
                  ident:ButtonIdent=ButtonIdent.IDENT_NONE ):
        self.text = text
        self.icon:QIcon = icon
        self.ident:ButtonIdent = ident
        self.tooltip = tooltip
        self.callback:Callable = callback
        self.callbackData:Any = callbackData
        self.default = False
        self.width = -1 # autowidth
        self.height = -1 # autoheight

#########################
def getOkCancelButtonDefinitions( okCallback:Callable, cancelCallback:Callable ):
        ok = BaseButtonDefinition( "  OK  ", "Übernimmt die Änderungen und schließt das Fenster.",
                                        okCallback, ident=ButtonIdent.IDENT_OK )
        cancel = BaseButtonDefinition( "Abbrechen", "Bricht die Änderungen ab, ohne sie zu übernehmen "
                                                    "und schließt das Fenster.",
                                        cancelCallback, ident=ButtonIdent.IDENT_CANCEL )
        return ( ok, cancel )


def getOkApplyCancelButtonDefinitions( okCallback: Callable, applyCallback:Callable, cancelCallback: Callable ):
    ok = BaseButtonDefinition( "  OK  ", "Übernimmt die Änderungen und schließt das Fenster.",
                               okCallback, ident=ButtonIdent.IDENT_OK )
    apply = BaseButtonDefinition( "Übernehmen", "Übernimmt die Änderungen; das Fenster bleibt geöffnet.",
                               applyCallback, ident=ButtonIdent.IDENT_APPLY )
    cancel = BaseButtonDefinition( "Abbrechen", "Bricht die Änderungen ab, ohne sie zu übernehmen "
                                                "und schließt das Fenster.",
                                   cancelCallback, ident=ButtonIdent.IDENT_CANCEL )
    return (ok, apply, cancel)

def getCloseButtonDefinition( callback: Callable ):
    defi = BaseButtonDefinition( "Schließen", "Schließt das Fenster.", callback, ident=ButtonIdent.IDENT_CLOSE )
    return (defi,)

#########################
class BaseDialogWithButtons( BaseDialog ):
    def __init__( self, title:str, buttonDefinitions:Iterable[BaseButtonDefinition], parent=None, flags=Qt.WindowFlags() ):
        BaseDialog.__init__( self, parent, flags )
        self.setWindowTitle( title )
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._buttonList:List[BaseButton] = list()
        self._mainrow = 0
        self._buttonrow = 1
        self._createGui( buttonDefinitions )

    def _createGui( self, buttonDefinitions:[BaseButtonDefinition] ):
        col = 0
        for defi in buttonDefinitions:
            btn = BaseButton()
            self._buttonList.append( btn )
            if defi.text:
                btn.setText( defi.text )
            if defi.icon:
                btn.setIcon( defi.icon )
            if defi.ident != ButtonIdent.IDENT_NONE:
                btn.setIdent( defi.ident )
            btn.setToolTip( defi.tooltip )
            btn.setDefault( defi.default )
            if defi.width > -1:
                btn.setFixedWidth( defi.width )
            if defi.height > -1:
                btn.setFixedHeight( defi.height )
            if defi.callback:
                btn.setCallback( defi.callback, defi.callbackData )
            self._layout.addWidget( btn, self._buttonrow, col )
            col += 1

    def getButtons( self ) -> List:
        return self._buttonList

    def getButton( self, ident:ButtonIdent ):
        for btn in self._buttonList:
            if btn.getIdent() == ident:
                return btn
        return None

    def setMainWidget( self, widget:BaseWidget ):
        self._layout.addWidget( widget, self._mainrow, 0, 1, self._layout.columnCount() )

    def getColumnCount( self ) -> int:
        return self._layout.columnCount()



#################  OkApplyCancelDialog  #############################
class OkApplyCancelDialog( BaseDialogWithButtons ):
    def __init__( self, title:str, parent=None, flags=Qt.WindowFlags(), okButton=True, applyButton=True, cancelButton=True ):
        BaseDialogWithButtons.__init__( self, title,
                                        getButtonDefs( self, okButton, applyButton, cancelButton ),
                                        #getOkApplyCancelButtonDefinitions( self.onOk, self.onApply, self.onCancel ),
                                        parent, flags )
        self.setWindowTitle( title )
        self._beforeAcceptCallback:Callable = None
        self._applyCallback:Callable = None
        self._beforeRejectCallback:Callable = None

    def setCallbacks( self, beforeAcceptCallback:Callable, applyCallback:Callable=None, beforeRejectCallback:Callable=None ):
        """
        die Callback-Funktionen empfangen keinen Aufruf-PArameter und müssen True oder False zurückliefern.
        Wird True zurückgeliefert, wird der Dialog geschlossen, bei False bleibt er offen.
        :param beforeAcceptCallback:
        :param applyCallback:
        :param beforeRejectCallback:
        :return: None
        """
        self._beforeAcceptCallback = beforeAcceptCallback
        self._applyCallback = applyCallback
        self._beforeRejectCallback = beforeRejectCallback

    def getOkButton( self ):
        return self.getButton( ident=ButtonIdent.IDENT_OK )

    def getApplyButton( self ):
        return self.getButton( ident=ButtonIdent.IDENT_APPLY )

    def getCancelButton( self ):
        return self.getButton( ident=ButtonIdent.IDENT_CANCEL )

    def onOk( self ):
        msg = ""
        if self._beforeAcceptCallback:
            msg = self._beforeAcceptCallback()
        if msg:
            box = ErrorBox( "Validierungsfehler", msg, "" )
            box.exec_()
        else:
            self.accept()

    def onApply( self ):
        msg = ""
        if self._applyCallback:
            msg = self._applyCallback()
        if msg:
            box = ErrorBox( "Validierungsfehler", msg, "" )
            box.exec_()

    def onCancel( self ):
        msg = ""
        if self._beforeRejectCallback:
            msg = self._beforeRejectCallback()
        if msg:
            box = QuestionBox( "Bestätigung", msg, "Ja", "Nein" )
            if box.exec_() == QMessageBox.StandardButton.Yes:
                self.reject()
        else:
            self.reject()

###########################################################################
def getButtonDefs( inst: OkApplyCancelDialog, okButton: bool, applyButton: bool, cancelButton: bool ):
    if okButton and applyButton and cancelButton:
        return getOkApplyCancelButtonDefinitions( inst.onOk, inst.onApply, inst.onCancel )
    if okButton and cancelButton:
        return getOkCancelButtonDefinitions( inst.onOk, inst.onCancel )
    return getCloseButtonDefinition( inst.onCancel )

################  BaseButton  ##########################
class BaseButton( QPushButton ):
    def __init__( self, text= "", parent=None, callback:Callable=None, callbackData:Any=None, ident:Any=None ):
        QPushButton.__init__( self, text=text, parent= parent )
        self._callback:Callable = None
        self._callbackData:Any = None
        self._ident:Any=ident
        if callback:
            self.setCallback( callback, callbackData )

    def setCallback( self, callback:Callable, callbackData:Any=None ):
        self._callback: Callable = callback
        self._callbackData: Any = callbackData
        self.clicked.connect( self._doCallback )

    def _doCallback( self ):
        if self._callbackData:
            self._callback( self._callbackData )
        else:
            self._callback()

    def getIdent( self ) -> Any:
        return self._ident

    def setIdent( self, ident:Any ) -> None:
        self._ident = ident

################  BaseIconButton  #####################
class BaseIconButton( BaseButton ):
    def __init__( self, icon:QIcon, size=QSize(28, 28), parent=None ):
        BaseButton.__init__( self, "", parent )
        self.setIcon( icon )
        self.setFixedSize( size )

###################  PrintButton  #######################
class PrintButton( BaseIconButton ):
    def __init__( self, size=QSize(28, 28), parent=None ):
        icon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "print.png" )
        BaseIconButton.__init__( self, icon, size, parent )

##########################################################
class ExportButton( BaseIconButton ):
    def __init__( self, size=QSize(28, 28), parent=None ):
        icon = IconFactoryS.inst().getIcon( BASE_IMAGES_DIR + "export.png" )
        BaseIconButton.__init__( self, icon, size, parent )

####################  BaseIconTextButton  ################
class BaseIconTextButton( BaseButton ):
    def __init__( self, icon:QIcon, text:str, parent=None ):
        BaseButton.__init__( self, text, parent )
        self.setText( text )

#################  NewIconButton  #########################
class NewIconButton( BaseIconButton ):
    def __init__( self, parent=None ):
        BaseIconButton.__init__( self, QIcon( BASE_IMAGES_DIR + "new.png" ), QSize(28, 28), parent )
        self.setToolTip( "Neues Element anlegen" )

#################  EditIconButton  ########################
class EditIconButton( BaseIconButton ):
    def __init__( self, parent=None ):
        BaseIconButton.__init__( self, QIcon( BASE_IMAGES_DIR + "edit_30x30.png" ), QSize(28, 28), parent )
        self.setToolTip( "Ausgewähltes Element bearbeiten" )

##################### DeleteIconButton  ####################
class DeleteIconButton( BaseIconButton ):
    def __init__( self, parent=None ):
        BaseIconButton.__init__( self, QIcon( BASE_IMAGES_DIR + "delete.png" ), QSize( 28, 28 ), parent )
        self.setToolTip( "Ausgewählte Elemente löschen" )

#################  SortIconButton  #####################
class SortIconButton( BaseIconButton ):
    def __init__( self, parent=None ):
        BaseIconButton.__init__( self, QIcon( BASE_IMAGES_DIR + "sort.png" ), QSize( 28, 28 ), parent )

#################  SettingsIconButton  #####################
class SettingsIconButton( BaseIconButton ):
    def __init__( self, parent=None ):
        BaseIconButton.__init__( self, QIcon( BASE_IMAGES_DIR + "settings.png" ), QSize( 28, 28 ), parent )
        self.setToolTip( "Öffnet den Einstellungen-Dialog" )

#################  CaseSensitiveButton  #####################
class CaseSensitiveButton( BaseIconButton ):
    def __init__( self, parent=None ):
        BaseIconButton.__init__( self, QIcon( BASE_IMAGES_DIR + "casesensitive_i.png" ), QSize( 28, 28 ), parent )
        self.setToolTip( "Schaltet um zwischen Case Sensitive ja/nein" )
        self.setCheckable( True )

#################  WholeWordButton  #####################
class WholeWordButton( BaseIconButton ):
    def __init__( self, parent=None ):
        BaseIconButton.__init__( self, QIcon( BASE_IMAGES_DIR + "wholeword_i.png" ), QSize( 28, 28 ), parent )
        self.setToolTip( "Schaltet um zwischen Vergleich nur von ganzen Wörtern ja/nein" )
        self.setCheckable( True )

#################  HistoryButton  #####################
class HistoryButton( BaseIconButton ):
    def __init__( self, tooltip="Zeigt die Historie an", parent=None ):
        BaseIconButton.__init__( self, QIcon( BASE_IMAGES_DIR + "history.png" ), QSize( 28, 28 ), parent )
        self.setToolTip( tooltip )

#################   BaseGridLayout  #########################
class GridLayoutItem:
    def __init__( self, item:Union[QWidget, QLayout] = None, index:int = -1, posInfo:Tuple = None ):
        self.item = item
        self.index = index
        self.row = -1
        self.column = -1
        self.rowspan = 1
        self.colspan = 1
        if posInfo:
            self.row = posInfo[0]
            self.column = posInfo[1]
            self.rowspan = posInfo[2]
            self.colspan = posInfo[3]

    @classmethod
    def fromLayout( cls, layout:QLayout, index:int, posInfo:Tuple ):
        return cls( layout, index, posInfo )

    @classmethod
    def fromWidget( cls, widget:QWidget, index:int, posInfo:Tuple ):
        return cls( widget, index, posInfo )

    def isWidget( self ) -> bool:
        return isinstance( self.item, QWidget )

    def getItemType( self ) -> Union[QWidget, QLayout]:
        return type( self.item )


#################   BaseGridLayout  #########################
class BaseGridLayout( QGridLayout ):
    def __init__( self ):
        QGridLayout.__init__( self )

    def addPair( self, lbl:str, widget:QWidget, row:int, startCol:int=0, rowspan:int=1, colspan:int=1 ):
        """
        Platziert ein Widget mit vorausgestelltem Label in diesem GridLayout.
        :param lbl:  das vorangestellte Label, immer in Column <startCol>
        :param widget:  das Widget, beginnend ab column startCol + 1
        :param row:  : gewünschte Zeile im GridLayout
        :param startCol: Column, in die das Label platziert wird
        :param rowspan:
        :param colspan: Anzahl der Column (beginnend ab startCol + 1), die <widget> umfassen soll.
        :return:
        """
        self.addWidget( BaseLabel( lbl ), row, startCol )
        startCol += 1
        self.addWidget( widget, row, startCol, rowspan, colspan )

    def getAddedItems( self ) -> List[GridLayoutItem]:
        """
        Liefert eine Liste der Items (Widgets oder Layouts), die dem Layout hinzugefügt wurden.
        Die Items in der Liste sind nach Index sortiert.
        :return:
        """
        l:List[GridLayoutItem] = list()
        for i in range( 0, self.count() ):
            item = self.itemAt( i )
            if isinstance( item, QLayout ):
                gli = GridLayoutItem.fromLayout( item, i )
            else:
                posInfo: Tuple = self.getItemPosition( i )
                gli = GridLayoutItem.fromWidget( item.widget(), i, posInfo )
            l.append( gli )
        return l

    def createHLine( self, r: int, columns: int = -1 ):
        line = HLine()
        if columns < 0: columns = self.columnCount()
        self.addWidget( line, r, 0, 1, columns )

    def createVLine( self, c: int, rows: int = -1 ):
        line = VLine()
        if rows < 0: rows = self.rowCount()
        self.addWidget( line, 0, c, rows, 1 )

##################  CalenderDialog   #####################
class CalendarDialog( QDialog ):
    def __init__( self, parent ):
        QDialog.__init__(self, parent)
        self.setModal( True )
        self.setTitle( "Datum auswählen" )
        self._calendar:QCalendarWidget = None
        self._buttonBox:QtWidgets.QDialogButtonBox = None
        self._callback = None
        self.createCalendar()

    def setTitle( self, title:str ) -> None:
        self.setWindowTitle( title )

    def setCallback( self, cbfnc ):
        self._callback = cbfnc

    def setMinimumDate( self, y:int, m:int, d:int ):
        self._calendar.setMinimumDate( QDate( y, m, d ) )

    def setMaximumDate( self, y:int, m:int, d:int ):
        self._calendar.setMaximumDate( QDate( y, m, d ) )

    def createCalendar(self):
        vbox = QVBoxLayout()
        self._calendar = QCalendarWidget()
        self._calendar.setGridVisible( True )
        self._calendar.setFirstDayOfWeek( Qt.Monday )
        vbox.addWidget( self._calendar )
        self.setLayout(vbox)

        self._buttonBox = QtWidgets.QDialogButtonBox( self )
        self._buttonBox.setOrientation( QtCore.Qt.Horizontal )
        self._buttonBox.setStandardButtons( QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel )
        self._buttonBox.layout().setDirection( QBoxLayout.RightToLeft )
        self._buttonBox.button( QtWidgets.QDialogButtonBox.Ok ).clicked.connect( self._onOk )
        self._buttonBox.button( QtWidgets.QDialogButtonBox.Cancel ).clicked.connect( self._onCancel )
        vbox.addWidget( self._buttonBox )

    def setSelectedDate( self, date:QDate ):
        self._calendar.setSelectedDate( date )

    def setSelectedDateFromString( self, datestring:str ):
        """
        datestring needs to be given as "yyyy-mm-dd" or "dd.mm.yyyy"
        day and month may be given one-digit.
        :param datestring:
        :return:
        """
        parts = datestring.split( "-" )
        if len( parts ) == 0:
            parts = datestring.split( "." )
        else: # yyyy-mm-dd
            dt = QDate( int(parts[0]), int(parts[1]), int(parts[2]) )
            self.setSelectedDate( dt )
        if len( parts ) == 0:
            raise Exception( "CalendarDialog.setSelectedDateFromString: wrong date format '%s'"
                             % (datestring) )
        else: # dd.mm.yyyy
            dt = QDate( int( parts[2] ), int( parts[1] ), int( parts[0] ) )
            self.setSelectedDate( dt )

    def _onOk( self ):
        date:QDate =  self._calendar.selectedDate()
        self.hide()
        if self._callback:
            self._callback( date )

    def _onCancel( self ):
        self.hide()

#########################  SmartDateEdit  #####################################
class SmartDateEdit( QLineEdit, GetSetValue ):
    before_show_calendar = Signal()
    def __init__( self, parent=None, isReadOnly:bool=False ):
        QLineEdit.__init__( self, parent )
        self.setReadOnly( isReadOnly )
        self._defaultDate = ""

    def mouseDoubleClickEvent( self, event ):
        #print( "Double Click SmartDateEdit at pos: ", event.pos() )
        if not self.isReadOnly():
            self.showCalendar()

    def setDate( self, year:int, month:int, day:int, format:str="yyyy-MM-dd" ):
        dt = QDate( year, month, day )
        ds = dt.toString( format )
        self.setText( ds )

    def setDateFromIsoString( self, isostring:str ):
        self.setText( isostring )

    def setDefaultDateFromIsoString( self, isostring:str ):
        """
        Setzt ein Datum, das beim nächsten Öffnen des Kalenders voreingestellt wird.
        Dieses Datum wird nicht in das SmartDateEdit-Feld übernommen.
        :param isostring:
        :return:
        """
        self._defaultDate = isostring

    def clearDefaultDate( self ):
        """
        Löscht das durch setDefaultDateFromIsoString( isostring ) gesetzte Datum.
        Beim nächsten Öffnen des Kalenders wird das Datum eingestellt, das in diesem SmartDateEdit-Feld
        eingetragen wird, bzw. current date, wenn nichts eingetragen ist.
        :return:
        """
        self._defaultDate = ""

    def getDate( self ) -> str:
        """
        liefert das eingestellte Datum in dem Format, wie es im Feld zu sehen ist.
        Ist der Wert im Feld ungültig, wird ein Leerstring ("") zurückgegeben.
        :param format:
        :return:
        """
        ds = self.text()
        if ds.endswith( "\n" ): ds = ds[:-1]
        if isValidIsoDatestring( ds ) or isValidEurDatestring( ds ):
            return ds
        else:
            return ""

    def setValue( self, isostring:str ):
        self.setDateFromIsoString( isostring )

    def getValue( self ) -> str:
        return self.getDate()

    def isDateValid( self ) -> bool:
        """
        Prüft, ob der String im Edit-Feld ein gültiges Datum darstellt (True) oder nicht (False).
        Ein leeres Feld gilt als "gültig" (True)
        :return:
        """
        ds = self.text()
        if ds.endswith( "\n" ): ds = ds[:-1]
        if ds == "": return True
        return ( isValidIsoDatestring( ds ) or isValidEurDatestring( ds ) )

    def showCalendar( self ):
        self.before_show_calendar.emit()
        cal = CalendarDialog( self )
        text = self.text() if not self._defaultDate else self._defaultDate
        if text == "":
            d = getRelativeQDate( 0, 0 )
        else:
            if isValidIsoDatestring( text ):
                d = getQDateFromIsoString( text )
            else:
                d =getRelativeQDate( 0, 0 )
        cal.setSelectedDate( d )
        cal.setCallback( self.onDatumSelected )
        crsr = QCursor.pos()
        cal.move( crsr.x()-25, crsr.y()+50 )
        cal.show()

    def onDatumSelected( self, date:QDate ):
        self.setText( date.toString( "yyyy-MM-dd" ) )

###################  AutoWidth  ########################
class AutoWidth:
    def setTextAndAdjustWidth( self, text:str ):
        self.setText( text )
        width = self.getTextWidth( text )
        # font = self.font()
        # # ps = font.pixelSize()  # --> -1
        # font.setPixelSize( 0 )
        # fm = QFontMetrics( font )
        # width = fm.width( text )
        self.setFixedWidth( width + 6 )

    def getTextWidth( self, text:str ) -> int:
        font = self.font()
        # ps = font.pixelSize()  # --> -1
        font.setPixelSize( 0 )
        fm = QFontMetrics( font )
        width = fm.width( text )
        return width

######################  BaseLabel ##################################
class BaseLabel( QLabel, AutoWidth, GetSetValue ):
    def __init__( self, text:str="", parent=None ):
        QLabel.__init__( self, parent )
        self.setValue( text )

    # def mouseDoubleClickEvent( self, evt:QMouseEvent ):
    #     self.setSelection( 0, len( self.text() ) )

    # def mousePressEvent(self, ev:QMouseEvent ):
    #     print( "mousePressed:", ev )
    #     print( "fljds")

    def getValue( self ) -> str:
        return self.text()

    def setValue( self, value:str ):
        self.setText( value )

    def setBackground( self, color ):
        # color in der Form "solid white"
        self.setStyleSheet( "background: " + color + ";" )

    def setTextAndBackgroundColor( self, textcolor, backgroundcolor ):
        self.setStyleSheet( "QLabel { background-color : red; color : blue; }" )

    def setFixedWidthAuto( self ):
        w = self.getTextWidth( self.text() )
        self.setFixedWidth( w )

def testBaseLabelMousePress():
    app = QApplication()
    lbl = BaseLabel()
    lbl.setText( "Ich bin ein tooller Labbeltexxt" )
    lbl.show()
    app.exec_()

###################   BaseLink   ########################
class BaseLink( BaseLabel ):
    def __init__( self, text:str, parent=None ):
        BaseLabel.__init__( self, text, parent )
        self.setOpenExternalLinks( True )

#########################  BaseCheckBox  #############################
class BaseCheckBox( QCheckBox, GetSetValue ):
    def __init__( self, parent = None ):
        QCheckBox.__init__( self, parent )

    def getValue( self ) -> bool:
        return self.isChecked()

    def setValue( self, value: bool ):
        self.setChecked( value )

##########################  BoolSwitch  ################################
class BoolSwitch(QComboBox, AutoWidth):
    """
    Eine ComboBox mit 2 Werten True und False
    """
    def __init__( self, initBool:bool=True ):
        QComboBox.__init__( self )
        self.addItems( (str(True), str(False) ) )
        self.setCurrentText( str( initBool ) )

    def setBool( self, boolVal:bool ):
        self.setCurrentText( str( boolVal ) )

#######################  BaseEdit  ###################################
class BaseEdit( QLineEdit, AutoWidth, GetSetValue ):
    # key_pressed = Signal( int )
    tab_pressed = Signal()
    def __init__( self, parent=None, isReadOnly=False ):
        QLineEdit.__init__( self, parent )
        #self.textChanged.connect( self.on_change )
        self.setReadOnly( isReadOnly )
        self.installEventFilter( self )

    def getValue( self ) -> str:
        return self.text()

    def setValue( self, value: str ):
        self.setText( value )
        self.setCursorPosition( 0 )

    def setBold( self, bold=True ):
        font = self.font()
        font.setBold( bold )
        self.setFont( font )

    def setTextColor( self, color:str ):
        """
        changes the color of the displayed text
        :param color: like "red", "green", "black",...
        :return:
        """
        self.setStyleSheet( "color: %s;" % color )

    def setFixedWidthAuto( self ):
        w = self.getTextWidth( self.text() )
        self.setFixedWidth( w )

    def mousePressEvent(self, evt:QMouseEvent):
        self.setSelection( 0, len( self.text() ) )

    def focusInEvent( self, evt ):
        super().focusInEvent( evt )
        self.setSelection( 0, len( self.text() ) )

    def focusOutEvent( self, evt ):
        super().focusOutEvent( evt )
        self.setCursorPosition( 0 )

    # def focusOutEvent( self, evt ):
    #     super().focusOutEvent( evt )
    #     #print( "BaseEdit: focusOut" )

    def eventFilter( self, obj: QObject, event:QEvent ):
        #print( "BaseEdit: eventFilte - obj=", obj )
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                #print( "%s: TAB pressed" % obj )
                self.tab_pressed.emit()
                return False
        return super().eventFilter( obj, event )

    # def keyPressEvent( self, event ):
    #     super().keyPressEvent( event )
    #     print( "BaseEdit: keyPressEvent" )

    # def on_change( self, s:str ):
    #     print( s )

    # def setTextAndAdjustWidth( self, text:str ):
    #     self.setText( text )
    #     font = self.font()
    #     # ps = font.pixelSize()  # --> -1
    #     font.setPixelSize( 0 )
    #     fm = QFontMetrics( font )
    #     width = fm.width( text )
    #     self.setFixedWidth( width + 6 )

#########################  FloatEdit  ################################
class FloatEdit( BaseEdit ):
    def __init__( self, parent=None, showNegativNumbersRed:bool=True, isReadOnly=False ):
        BaseEdit.__init__( self, parent, isReadOnly=isReadOnly )
        self._showNegativNumbersRed = showNegativNumbersRed
        floatval = QDoubleValidator()
        self.setValidator( floatval )
        self.setAlignment( Qt.AlignRight )
        #self.setReadOnly( isReadOnly )

    def getFloatValue( self ) -> float:
        val = self.text()
        if not val:
            val = "0.0"
        else:
            val = val.replace( ",", "." )
        return float( val )

    def setValue( self, val:float ):
        self.setFloatValue( val )

    def getValue( self ) -> float:
        return self.getFloatValue()

    def setFloatValue( self, val:float ):
        self.setText( str( val ) )
        if self._showNegativNumbersRed:
            if val < 0:
                self.setStyleSheet( "color: red;" )
            else:
                self.setStyleSheet( "color: green;" )

    def setFloatStringValue( self, val:str ):
        try:
            floatval = float( val )
            self.setFloatValue( floatval )
        except:
            self.setText( "" )

#########################  SignedFloatEdit  ###########################
class SignedNumEdit( QWidget ):
    textChanged = Signal( str )
    class Sign( BaseButton ):
        PLUS = "+"
        MINUS = "-"
        def __init__( self, sign=MINUS, isEnabled=True, maySwitch=True ):
            BaseButton.__init__( self, text=sign )
            self.setEnabled( isEnabled )
            if not maySwitch and self.isEnabled():
                self.setEnabled( False )
            self._currentSign = sign
            font = QFont( "Arial", 20 )
            font.setBold( True )
            self.setFont( font )
            self.setMaximumWidth( 22 )
            self.setMaximumHeight( 22 )
            self._setSignStyleSheet( sign )
            self.pressed.connect( self.onPressed )

        def setPlus( self ):
            self._setSignStyleSheet( self.PLUS )
            self._currentSign = self.PLUS

        def setMinus( self ):
            self._setSignStyleSheet( self.MINUS )
            self._currentSign = self.MINUS

        def isPlus( self ) -> bool:
            return self._currentSign == self.PLUS

        def isMinus( self ) -> bool:
            return self._currentSign == self.MINUS

        def onPressed( self ):
            sign = self.PLUS if self._currentSign == self.MINUS else self.MINUS
            self._setSignStyleSheet( sign )
            self._currentSign = sign

        def _setSignStyleSheet( self, sign: str ):
            self.setText( sign )
            if sign == self.MINUS:
                self.setStyleSheet( "background-color: red; color: white" )
            else:
                self.setStyleSheet( "background-color: green; color: white" )

    def __init__( self, numtype:type=float, sign="-", parent=None, isReadOnly=False, maySwitch=True ):
        QWidget.__init__( self, parent )
        self._type = numtype
        self._sign = self.Sign( sign, isEnabled=not isReadOnly, maySwitch=maySwitch )
        if numtype == int:
            self._numEdit = IntEdit( showNegativNumbersRed=False, isReadOnly=isReadOnly )
        else:
            self._numEdit = FloatEdit( showNegativNumbersRed=False, isReadOnly=isReadOnly )
        self._numEdit.textChanged.connect( self.textChanged.emit )
        self._sign.pressed.connect( self.onSignPressed )
        self._setStyleSheet( self._sign.isPlus() )

        self._layout = QHBoxLayout()
        self.setLayout( self._layout )
        self._layout.addWidget( self._sign, stretch=0, alignment=Qt.AlignLeft )
        self._layout.addWidget( self._numEdit, stretch=0, alignment=Qt.AlignLeft )
        self._layout.setContentsMargins( 0, 0, 0, 0 )

    def onSignPressed( self ):
        self._setStyleSheet( self._sign.isPlus() )

    def _setStyleSheet( self, isPlus:bool ):
        if not isPlus:
            self._numEdit.setStyleSheet( "color: red" )
        else:
            self._numEdit.setStyleSheet( "color: green" )
        self._numEdit.setFocus()

    def setFocus( self ):
        self._numEdit.setFocus()

    def setPlaceholderText( self, text:str ):
        self._numEdit.setPlaceholderText( text )

    def setValidator( self, validator:QValidator ):
        self._numEdit.setValidator( validator )

    def setAlignment( self, align ):
        self._layout.setAlignment( align )

    def setPlus( self ):
        self._sign.setPlus()
        self._setStyleSheet( isPlus=True )

    def setMinus( self ):
        self._sign.setMinus()
        self._setStyleSheet( isPlus=False)

    def getValueAsString( self ):
        return str( self.getValue() )

    def getValue( self ) -> int or float:
        if self._type == int:
            val = self._numEdit.getIntValue()
        else:
            val = self._numEdit.getFloatValue()
        if self._sign.isMinus():
            val *= -1
        return val

    def setValue( self, value: int or float ):
        if value < 0 or ( value == 0 and self._sign.isMinus() ):
            self._sign.setMinus()
            value *= -1 # wir haben Sign auf "-" gesetzt, deswegen muss value positiv gemacht werden
            self._setStyleSheet( isPlus=False )
        else:
            self._sign.setPlus()
            self._setStyleSheet( isPlus=True )
        if self._type == int:
            self._numEdit.setIntValue( value )
        else:
            self._numEdit.setFloatValue( value )

    def setFloatValue( self, value:float ):
        if not self._type == float:
            raise ValueError( "SignedNumEdit was intantiated with type==int.\nUse method setIntValue()." )
        self.setValue( value )

    def getFloatValue( self ) -> float:
        if not self._type == float:
            raise ValueError( "SignedNumEdit was intantiated with type==int.\nUse method getIntValue()." )
        return self.getValue()

    def setIntValue( self, value:int ):
        if not self._type == int:
            raise ValueError( "SignedNumEdit was intantiated with type==float.\nUse method setFloatValue()." )
        self.setValue( value )

    def getIntValue( self ) -> int:
        if not self._type == int:
            raise ValueError( "SignedNumEdit was intantiated with type==float.\nUse method getFloatValue()." )
        return self.getValue()

######################### PositiveSignedFloatEdit ##################
class PositiveSignedFloatEdit( SignedNumEdit ):
    """
    Diese Klasse brauchen wir, damit wir im DynamicAttributeView ein SignedNumEdit Objekt instanzieren können,
    das per Default "+" statt "-" anzeigt.
    """
    def __init__( self, parent=None, isReadOnly=False ):
        SignedNumEdit.__init__( self, numtype=float, sign="+" )

######################## FixedNegativeSignedFloatEdit ##################
class FixedNegativeSignedFloatEdit( SignedNumEdit ):
    """
    Diese Klasse brauchen wir, damit wir im DynamicAttributeView ein SignedNumEdit Objekt instanzieren können,
    das per Default "-" anzeigt und dessen Sign nicht auf "+" gestellt werden kann
    """
    def __init__( self, parent=None, isReadOnly=False ):
        SignedNumEdit.__init__( self, numtype=float, sign="-", maySwitch=False )

#########################  IntEdit  ################################
class IntEdit( BaseEdit ):
    def __init__( self, parent=None, showNegativNumbersRed:bool=True, isReadOnly=False ):
        BaseEdit.__init__( self, parent, isReadOnly=isReadOnly )
        self._showNegativNumbersRed = showNegativNumbersRed
        intval = QIntValidator()
        self.setValidator( intval )
        self.setAlignment( Qt.AlignRight )

    def getIntValue( self ) -> int:
        val = self.text()
        if not val:
            val = "0"
        return int( val )

    def setIntValue( self, val:int ):
        self.setText( str( val ) )
        if self._showNegativNumbersRed:
            if val < 0:
                self.setStyleSheet( "color: red;" )
            else:
                self.setStyleSheet( "color: green;" )

    def setValue( self, val: int ):
        self.setIntValue( val )

    def getValue( self ) -> float:
        return self.getIntValue()

    def setIntStringValue( self, val:str ):
        try:
            intval = int( val )
            self.setIntValue( intval )
        except:
            self.setText( "" )

######################## Int Display  #############################
class IntDisplay( IntEdit ):
    def __init__( self, parent=None, showNegativNumbersRed:bool=True ):
        IntEdit.__init__( self, parent, showNegativNumbersRed, isReadOnly=True )
        intval = QIntValidator()
        self.setValidator( intval )
        font = QFont( "Times New Roman", 12, QFont.Bold )
        self.setFont( font )
        # self.setStyleSheet( "color: red;" )
        self.setAlignment( Qt.AlignRight )
# class IntDisplay( BaseEdit ):
#     def __init__( self, parent=None ):
#         BaseEdit.__init__( self, parent )
#         intval = QIntValidator()
#         self.setValidator( intval )
#         font = QFont( "Times New Roman", 12, QFont.Bold )
#         self.setFont( font )
#         # self.setStyleSheet( "color: red;" )
#         self.setAlignment( Qt.AlignRight )
#
#     def setIntValue( self, val:int ):
#         if val is None:
#             raise ValueError( "IntDisplay.setIntValue(): val is None" )
#         if not isinstance( val, int ):
#             if isinstance( val, float ):
#                 val = round( val )
#             else:
#                 raise ValueError( "IntDisplay.setIntValue(): val '%s' is not an int" % str(val) )
#         self.setText( str( val ) )
#         if val < 0:
#             self.setStyleSheet( "color: red;" )
#         else:
#             self.setStyleSheet( "color: green;" )
#
#     def getIntValue( self ) -> int:
#         val = self.text()
#         return int( val )


################ TextDocument #####################
class TextDocument( QTextDocument ):
    def __init__( self, text ):
        QTextDocument.__init__( self, text )

################ LineEdit #########################
class LineEdit( BaseEdit ):
    def __init__( self, parent=None, isReadOnly:bool=False ):
        BaseEdit.__init__( self, parent )
        self.setReadOnly( isReadOnly )

    def setValue( self, value:Any ) -> None:
        self.setText( value )
        if value is None or value == "": return
        if isinstance( value, numbers.Number ):
            self.setAlignment( Qt.AlignRight )
        else:
            self.setAlignment( Qt.AlignLeft )

    def getValue( self ) -> Any:
        return self.text()

################  MultiLineEdit  ##################
class MultiLineEdit( QTextEdit, GetSetValue ):
    def __init__( self, parent=None, isReadOnly:bool=False ):
        QTextEdit.__init__( self, parent )
        self.setReadOnly( isReadOnly )

    def getValue( self ) -> str:
        return self.toPlainText()

    def setValue( self, text:str ):
        self.setText( text )

################ SumDialog ########################
class SumDialog( QDialog ):
    def __init__( self, parent=None, title="Summe der selektierten Zahlen" ):
        QDialog.__init__( self, parent )
        self.setModal( True )
        self.setWindowTitle( title )
        layout = QGridLayout( self )
        self.label = QtWidgets.QLabel( self )
        self.label.setText( "Summe:" )
        layout.addWidget( self.label, 0, 0 )

        self._sumLabel = QtWidgets.QLabel( self )
        layout.addWidget( self._sumLabel, 0, 1 )

        self._btnCopyToClipboard = QPushButton( self, text="Kopieren" )
        layout.addWidget( self._btnCopyToClipboard, 1, 0 )
        self._btnCopyToClipboard.clicked.connect( self._copy2clipboard )

        self._btnClose = QPushButton( self, text="Schließen" )
        layout.addWidget( self._btnClose, 1, 1 )
        self._btnClose.clicked.connect( self._onClose )
        self.setLayout( layout )

    def _copy2clipboard( self ):
        """
        kopiert die angezeigte Zahl ins Clipboard
        :return:
        """
        clipboard = QGuiApplication.clipboard()
        clipboard.setText( self._sumLabel.text() )

    def _onClose( self ):
        self.close()

    def setSum( self, sum:int or float ) -> None:
        self._sumLabel.setText( str( sum ) )

####################################################################

class CustomItem( QStandardItem ):
    def __init__( self, text:str, userdata:Any=None ):
        QStandardItem.__init__( self, text )
        self.userdata = userdata

#####################################################################

class AuswahlDialog( QDialog ):
    def __init__( self, title=None,  parent=None ):
        QDialog.__init__( self, parent )
        self.title = title
        self.listView = QListView()
        self.font = QFont( "Arial", 14 )
        self.okButton = QPushButton( "OK" )
        self.cancelButton = QPushButton( "Abbrechen" )
        self.model = QStandardItemModel()
        self.listView.setModel( self.model )
        self._selectedIndexes = ""
        self._createGui()

    def _createGui( self ):
        hbox = QHBoxLayout()
        hbox.addStretch( 1 )
        hbox.addWidget( self.okButton )
        hbox.addWidget( self.cancelButton )

        vbox = QVBoxLayout( self )
        vbox.addWidget( self.listView, stretch=1 )
        # vbox.addStretch(1)
        vbox.addLayout( hbox )

        self.okButton.setDefault( True )

        if self.title:
            self.setWindowTitle( self.title )
        else:
            self.setWindowTitle( "Auswahl" )

        self.okButton.clicked.connect( self.onAccepted )
        self.cancelButton.clicked.connect( self.reject )

    def appendItemList( self, itemlist:List[str] ):
        for i in itemlist:
            self.appendItem( i, None )

    def appendItem( self, text:str, userdata:Any=None ):
        item = CustomItem( text )
        if userdata:
            item.userdata = userdata
        item.setFont( self.font )
        self.model.appendRow( item )
        if self.model.rowCount() == 1:
            self.listView.setCurrentIndex( self.model.index( 0, 0 ) )

    def onAccepted(self):
        self._selectedIndexes = self.listView.selectedIndexes()
        self.accept()

    def getSelectedIndexes( self ):
        return self._selectedIndexes

    def getSelection( self ) -> List[Tuple]:
        sel = self.getSelectedIndexes()
        l = list()
        for idx in sel:
            item:CustomItem = self.model.item( idx.row(), idx.column() )
            t = ( item.text(), item.userdata )
            l.append( t )

        return l

#####################################################################

class CheckableAuswahlDialog( QDialog ):
    def __init__( self, stringlist:List[str], checked=False, title=None, icon=None, parent=None ):
        QDialog.__init__( self, parent )
        self.title = title
        self.icon = icon
        self.listView = QListView()
        self.okButton = QPushButton( "OK" )
        self.cancelButton = QPushButton( "Abbrechen" )
        self.selectButton = QPushButton( "Alle auswählen" )
        self.unselectButton = QPushButton( "Auswahl aufheben" )
        self.font = QFont( "Arial", 14 )
        self.model = QStandardItemModel()
        self.choices:List[str] = list()
        self._createGui()
        self._createModel( stringlist, checked )

    def _createGui( self ):
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.okButton)
        hbox.addWidget(self.cancelButton)

        h2box = QHBoxLayout()
        h2box.addStretch( 1 )
        h2box.addWidget(self.selectButton)
        h2box.addWidget(self.unselectButton)

        vbox = QVBoxLayout(self)
        vbox.addLayout( h2box )
        vbox.addWidget(self.listView, stretch=1)
        #vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.okButton.setDefault( True )

        if self.title:
            self.setWindowTitle( self.title )
        else:
            self.setWindowTitle( "Auswahl" )

        if self.icon:
            self.setWindowIcon(self.icon)

        self.okButton.clicked.connect(self.onAccepted)
        self.cancelButton.clicked.connect(self.reject)
        self.selectButton.clicked.connect(self.select)
        self.unselectButton.clicked.connect(self.unselect)

    def _createModel( self, masterobjektList:List[str], checked:bool ):
        for obj in masterobjektList:
            item = QStandardItem( obj )
            item.setCheckable(True)
            item.setFont( self.font )
            check = (QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
            item.setCheckState(check)
            self.model.appendRow(item)
        self.listView.setModel( self.model )


    def onAccepted(self):
        self.choices = [self.model.item(i).text() for i in  range(self.model.rowCount() )
                        if self.model.item(i).checkState() == QtCore.Qt.Checked]
        self.accept()

    def select(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Checked)

    def unselect(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)

#################################################################


class FixedWidth20Dummy( BaseLabel ):
    def __init__( self, parent=None ):
        BaseLabel.__init__( self, parent )
        self.setFixedWidth( 20 )

class FixedWidthDummy( BaseLabel ):
    def __init__( self, w:int, parent=None ):
        BaseLabel.__init__( self, parent )
        self.setFixedWidth( w )

class FixedHeightDummy( BaseLabel ):
    def __init__( self, height:int=20, parent=None ):
        BaseLabel.__init__( self, parent )
        self.setFixedHeight( height )

class HLine(QFrame):
    def __init__(self):
        super(HLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class VLine(QFrame):
    def __init__(self):
        super( VLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

class FontTimesBold12( QFont ):
    def __init__( self ):
        QFont.__init__( self, "Times New Roman", 12, weight=QFont.Bold )

class FontArialBold12( QFont ):
    def __init__( self ):
        QFont.__init__( self, "Arial", 12, weight=QFont.Bold )


class BaseBoldEdit( BaseEdit ):
    def __init__( self, text:str="" ):
        BaseEdit.__init__( self, parent=None )
        if text:
            self.setText( text )
        self.setFont( FontArialBold12() )

class LabelTimes12( BaseLabel ):
    def __init__( self, text:str="", parent=None ):
        BaseLabel.__init__( self, text, parent )
        self.setFont( QFont( "Times New Roman", 12 ) )
        if text:
            self.setText( text )


class LabelTimesBold12( BaseLabel ):
    def __init__( self, text:str="", parent=None ):
        BaseLabel.__init__( self, text, parent )
        self.setFont( QFont( "Times New Roman", 12, weight=QFont.Bold ) )
        if text:
            self.setText( text )

class LabelArial12( BaseLabel ):
    def __init__( self, text:str="", parent=None ):
        BaseLabel.__init__( self, text, parent )
        self.setFont( QFont( "Arial", 12 ) )

class LabelArialBold12( BaseLabel ):
    def __init__( self, text:str="", background:str=None, parent=None ):
        # background in der Form "solid white"
        BaseLabel.__init__( self, text. parent )
        self.setFont( QFont( "Arial", 12, weight=QFont.Bold ) )
        if background:
            self.setBackground( background )

class FatLabel( BaseLabel ):
    def __init__( self, text:str="", parent=None ):
        BaseLabel.__init__( self, text, parent )
        self._font = QFont( "Arial", 12, weight=QFont.Bold )
        self.setFont( self._font )

class AttributeDialog( QDialog ):
    """
    Mit diesem Dialog können Attribute geändert werden.
    Ein Attribut ist zum Beispiel ein Datenbankwert oder ein Settings-Wert wie Höhe, Breite, Font, etc.
    Je Attribut wird im Dialog eine Zeile verwendet.
    Der Dialog wird mit einer Attributliste List[XAttribute] instanziert und enthält so viele Zeilen,
    wie Attribute in der Attributliste vorhanden sind.
    """
    def __init__( self, attributes:List[XAttribute], title:str= "SettingsDialog" ):
        QDialog.__init__( self )
        self._attributes = attributes
        self._btnOk = QPushButton( text="OK" )
        self._btnCancel = QPushButton( text="Abbrechen" )
        self.setWindowTitle( title )
        self._layout = QGridLayout()
        self.setLayout( self._layout )
        self._createGui()

    def _createGui( self ):
        l = self._layout
        r = 0
        for s in self._attributes:
            lbl = BaseLabel()
            lbl.setText( s.label + ": " )
            l.addWidget( lbl, r, 0 )
            l.addWidget( self._createEditWidget( s.type, s.value ), r, 1 )
            if len( s.options ) > 0:
                combo = QComboBox()
                combo.addItems( s.options )
                l.addWidget( combo, r, 2 )
            r += 1

        dummy = QLabel()
        dummy.setFixedHeight( 3 )
        l.addWidget( dummy, r, 0 )
        r += 1
        self._btnOk.setDefault( True )
        self._btnOk.clicked.connect( self.accept )
        self._btnCancel.clicked.connect( self.reject )
        l.addWidget( self._btnOk, r, 0 )
        l.addWidget( self._btnCancel, r, 1 )

    def _createEditWidget( self, type:str, value ) -> QWidget:
        if type == "int":
            e = IntEdit()
            if value:
                e.setIntValue( value )
            return e
        if type == "float":
            f = FloatEdit()
            if value:
                f.setFloatValue( value )
            return f
        if type == "str":
            e = LineEdit()
            if value:
                e.setText( value )
            return e
        if type == "bool":
            b = BoolSwitch()
            if value:
                b.setBool( value )
            return b
        else:
            raise ValueError( "AttributDialog._createEditWidget(): type " + type + " unbekannt." )


class SearchField( BaseEdit ):
    doSearch = Signal( str )
    searchTextChanged = Signal()

    def __init__( self ):
        BaseEdit.__init__( self )
        self.setMaximumWidth( 200 )
        self.setPlaceholderText( "Suchbegriff" )
        self.returnPressed.connect( self._onReturn )
        self.textChanged.connect( self._onTextChanged )
        self._textChangedAfterReturn = False
        self._backgroundColor = ""

    def _onReturn( self ):
        self._textChangedAfterReturn = False
        text = self.text()
        if len( text ) > 0:
            self.doSearch.emit( text )

    def _onTextChanged( self ):
        if not self._textChangedAfterReturn:
            self.searchTextChanged.emit()
            self._textChangedAfterReturn = True

    def setBackgroundColor( self, htmlColor:str ) -> None:
        if htmlColor != self._backgroundColor:
            self.setStyleSheet( "background-color: " + htmlColor + ";" )
            self._backgroundColor = htmlColor

class SearchWidget( BaseWidget ):
    doSearch = Signal( str )
    searchtextChanged = Signal()
    openSettings = Signal()

    def __init__( self, withSettings=True ):
        BaseWidget.__init__( self )
        self._layout = QHBoxLayout()
        self._searchfield = SearchField()
        # forward signals from searchfield:
        self._searchfield.doSearch.connect( self.doSearch.emit )
        self._searchfield.searchTextChanged.connect( self.searchtextChanged.emit )
        if withSettings:
            self._btnSettings = SettingsIconButton()
            self._btnSettings.clicked.connect( self.openSettings.emit )
        self._createGui( withSettings )

    def _createGui( self, withSettings:bool ):
        l = self._layout
        self.setLayout( l )
        l.setContentsMargins( 0, 0, 0, 0 )
        l.addWidget( self._searchfield, alignment=Qt.AlignLeft )
        if withSettings:
            self._btnSettings.setFixedSize( QSize(25, 25) )
            self._btnSettings.setFlat( True )
            self._btnSettings.setToolTip( "Öffnet den Dialog zum Einstellen der Suchmethodik")
            l.addWidget( self._btnSettings, alignment=Qt.AlignLeft )

    def setSearchFieldBackgroundColor( self, htmlColor:str ) -> None:
        self._searchfield.setBackgroundColor( htmlColor )

    def setFocusToSearchField( self ):
        self._searchfield.setFocus()



##########################  TEST  TEST  TEST  ################################

def testGridLayoutItems():
    app = QApplication()
    w = QWidget()
    l = BaseGridLayout()
    c1 = QWidget()
    c1.setObjectName( "c1" )
    l.addWidget( c1, 0, 0 )
    c2 = QWidget()
    c2.setObjectName( "c2" )
    l.addWidget( c2, 0, 1 )
    c3 = QHBoxLayout()
    c3.setObjectName( "HLayout")
    c4 = QWidget()
    c4.setObjectName( "c4" )
    c3.addWidget( c4 )
    l.addLayout( c3, 1, 0 )
    w.setLayout( l )
    w.show()
    items = l.getAddedItems()
    for item in items:
        print( "item name: ", item.item.objectName(), " is ", item.getItemType(), " - index: ", item.index )
    app.exec_()

def testBaseDialogWithButtons3():
    def onClose():
        print( "Close" )
        dlg.accept()

    app = QApplication()
    dlg = BaseDialogWithButtons( "Testdialog", getCloseButtonDefinition( onClose ) )
    dlg.exec_()

def testBaseDialogWithButtons2():
    def onOk( arg ):
        print( "OK: ", arg )
    def onCancel():
        print( "Brich ab" )

    app = QApplication()
    b1def = BaseButtonDefinition( "Na gut", "TT!", onOk, "Heavy Data" )
    b2def = BaseButtonDefinition( "War nix", "TTTTTT", onCancel )
    dlg = BaseDialogWithButtons( "Testdialog", (b1def, b2def) )
    dlg.exec_()

def testBaseDialogWithButtons():
    def onOk():
        print( "OK" )
    def onCancel():
        print( "Cancel" )

    app = QApplication()
    dlg = BaseDialogWithButtons( "Testdialog", getOkCancelButtonDefinitions( onOk, onCancel ) )
    dlg.exec_()
    #app.exec_()


def onSearch( txt ):
    print( "onSearch: ", txt )

def onSearchTextChanged():
    print( "search text changed" )

def onOpenSettings():
    print( "open settings" )

def testSearchWidget():
    app = QApplication()
    sw = SearchWidget()
    sw.doSearch.connect( onSearch )
    sw.searchtextChanged.connect( onSearchTextChanged )
    sw.openSettings.connect( onOpenSettings )
    sw.show()
    app.exec_()



def testLink():
    app = QApplication()
    lnk = BaseLink( text="Hier geht's lang" )
    lnk.resize( QSize(200, 50 ) )
    lnk.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
    #lnk.setText( "<b>Hello</b> <i>Qt!</i>" )
     #lnk.setText(" <a href=\"http://www.google.com\"> <font face=verdana size=12 color=black> This is a link</font> </a>" )
    lnk.setText( "<a> <font face=verdana size=12 color=black> This is a link</font> </a>" )
    lnk.show()
    app.exec_()

def testSearchField():
    app = QApplication()
    sf = SearchField()
    sf.doSearch.connect( onSearch )
    sf.searchTextChanged.connect( onSearchTextChanged )
    sf.show()
    app.exec_()

def testAuswahlDialog():
    app = QApplication()
    dlg = AuswahlDialog( title="Eine Auswahl" )
    dlg.appendItem( "dear me", 1 )
    dlg.appendItem( "dear you", 2 )
    if dlg.exec_() == QDialog.Accepted:
        l = dlg.getSelection()
        for t in l:
            print( "selected: ", t[0], t[1] )
        # indexes = dlg.getSelectedIndexes()
        # for i in indexes:
        #     print( "Selected: ", i.row() )

def onClick( l:List[str] ):
    print( l )


def createAttributes() -> List[XAttribute]:
    l = list()
    s = XAttribute()
    s.key = "width"
    s.type = int.__name__
    s.label = "Breite"
    s.value = 400

    l.append( s )

    s = XAttribute()
    s.key = "height"
    s.type = int.__name__
    s.label = "Höhe"
    s.value = 300

    l.append( s
              )
    s = XAttribute()
    s.key = "case_sensitiv"
    s.type = bool.__name__
    s.label = "Case Sensitiv"
    s.value = False

    l.append( s )
    return l

def testAttributeDialog():
    app = QApplication()
    dlg = AttributeDialog( createAttributes(), "Einstellungen für die Suche" )
    if dlg.exec_() == QDialog.Accepted:
        print( "accepted" )
    else:
        print( "cancelled" )

    #app.exec_()

def testButtons():
    app = QApplication()
    #btn = BaseButton( "Click Me" )
    btn = NewIconButton()
    #btn = EditIconButton()
    #btn = DeleteIconButton()
    # btn.setText( "Edit")
    # btn.setFixedWidth( 100 )
    btn.show()
    app.exec_()

def test():
    app = QApplication()
    dlg = CheckableAuswahlDialog( ["SB_Kaiser", "ILL_Eich", "NK_Kleist"], title="Freie Auswahl!", checked=True )
    if dlg.exec_() == QDialog.Accepted:
        print( '\n'.join( [str( s ) for s in dlg.choices] ) )
    #app.exec_()

def testSignedNumEdit():
    app = QApplication()
    sfe = SignedNumEdit( float, "-" )
    sfe.setValue( -2.3 )
    sfe.show()
    sfe.setFocus()
    app.exec_()

def testLabelColor():
    app = QApplication()
    lbl = BaseLabel( "test" )
    lbl.setStyleSheet( "QLabel { background-color : red; color : blue; }" );
    # lbl.setBackground( "red" )
    # lbl.setTextColor( "white" )
    lbl.show()
    app.exec_()

def testEditColor():
    app = QApplication()
    ed = BaseEdit( isReadOnly=True )
    ed.setValue( "ABVCLSDKI" )
    ed.setBold()
    ed.setTextColor( "red" )
    ed.show()
    ed.setFocusPolicy( Qt.NoFocus )
    app.exec_()

if __name__ == "__main__":
    #test()
    testAuswahlDialog()
