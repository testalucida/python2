import copy
from typing import Type, List, Any

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QWidget, QDialog, QHBoxLayout

from base.baseqtderivates import BaseWidget, BaseGridLayout, BaseEdit, LineEdit, MultiLineEdit, BaseCheckBox, IntEdit, \
    BaseLabel, FloatEdit, BaseComboBox, BaseDialogWithButtons, getOkCancelButtonDefinitions, OkApplyCancelDialog, \
    BaseButton
from base.interfaces import XBase, XBaseUI, VisibleAttribute, ButtonDefinition


class DynamicAttributeView( BaseWidget ):
    def __init__(self, xbaseui:XBaseUI, title="", parent=None, flags=Qt.WindowFlags()):
        BaseWidget.__init__( self, parent, flags )
        self.setWindowTitle( title )
        self._xbaseui = xbaseui
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._widgets:List[BaseWidget] = list()
        self._firstEditableWidget:QWidget = None
        self._createUI()

    def _createUI( self ):
        row, col = 0, 0
        attrlist = self._xbaseui.getVisibleAttributes()
        for attr in attrlist:
            lbl = BaseLabel( attr.label )
            self._layout.addWidget( lbl, row, col )
            col += 1
            w = self._createWidget( attr.key, attr.type, attr.editable, attr.getWidgetWidth(), attr.getWidgetHeight() )
            if attr.tooltip:
                w.setToolTip( attr.tooltip )
            self._widgets.append( w )
            if attr.trailingButton:
                btn = self._createButton( attr.trailingButton )
                boxlayout = QHBoxLayout()
                boxlayout.addWidget( w, alignment=Qt.AlignLeft )
                boxlayout.addWidget( btn, alignment=Qt.AlignLeft )
                self._layout.addLayout( boxlayout, row, col, alignment=Qt.AlignLeft )
            else:
                self._layout.addWidget( w, row, col, 1, attr.columnspan )
            comboValues = attr.getComboValues()
            if comboValues and isinstance( w, BaseComboBox ):
                comboValues = list( comboValues )
                if len( comboValues ) > 0:
                    w.addItems( comboValues )
            value = self._xbaseui.getXBase().getValue( attr.key )
            if value:
                w.setValue( value )
            if isinstance( w, BaseComboBox ):
                # das Signal darf erst mit der Callback-Funktion verknüpft werden, wenn der Wert zugewiesen ist.
                w.currentTextChanged.connect( attr.comboCallback )
            if attr.nextRow:
                row += 1
                col = 0
            else:
                col += attr.columnspan

    def _createWidget( self, key:str, type_:Type, editable:bool, widgetWidth:int=-1, widgetHeight=-1 ) -> QWidget:
        w:QWidget = type_()
        w.setObjectName( key )
        try:
            # Pfui: mit setEditable( False ) erscheinen die Widgets grau in grau und es funktioniert kein Copy.
            # Deshalb rufen wir nicht setEditable, sondern versuchen, setReadOnly auf True oder False zu setzen.
            # Nicht jedes Widget verfügt über diese Methode, deshalb via try
            w.setReadOnly( not editable )
        except:
            try:
                w.setEnabled( editable )
            except:
                pass
        if editable and self._firstEditableWidget is None:
            self._firstEditableWidget = w
        if widgetWidth > 0:
            w.setFixedWidth( widgetWidth )
        if widgetHeight > 0:
            w.setFixedHeight( widgetHeight )
        return w

    @staticmethod
    def _createButton( buttondef:ButtonDefinition ) -> BaseButton:
        btn = BaseButton()
        if buttondef.ident:
            btn.setIdent( buttondef.ident )
        if buttondef.text:
            btn.setText( buttondef.text )
        if buttondef.iconpath:
            icon = QIcon( buttondef.iconpath )
            btn.setIcon( icon )
        if buttondef.tooltip:
            btn.setToolTip( buttondef.tooltip )
        if buttondef.maxW:
            btn.setMaximumWidth( buttondef.maxW )
        if buttondef.maxH:
            btn.setMaximumHeight( buttondef.maxH )
        btn.setCallback( buttondef.callback )
        return btn

    def getButton( self, ident:Any ) -> BaseButton:
        for w in self._widgets:
            if isinstance( w, BaseButton ) and w.getIdent() == ident:
                return w

    def getWidget( self, key:str ) -> BaseWidget:
        for w in self._widgets:
            if w.objectName() == key: return w
        raise Exception( "DynamicAttributeView.getWidget(): Kein Widget für Key '%s' gefunden." % key )

    def setFocusToFirstEditableWidget( self ):
        if self._firstEditableWidget:
            self._firstEditableWidget.setFocus()

    def getXBaseUI( self ) -> XBaseUI:
        return self._xbaseui

    def getXBase( self ) -> XBase:
        """
        :return: the original XBase object. Unchanged, unless updateData() was called before.
                 Calling updateData() results in updating the original XBase object with the user made changes.
        """
        return self._xbaseui.getXBase()

    def getModifiedXBaseCopy( self ) -> XBase:
        """
        returns a copy of the wrapped XBase-Object with modifications made by user
        :return: a copy of the wrapped XBase-Object
        """
        xbasecopy = copy.deepcopy( self._xbaseui.getXBase() )
        self._updateData( xbasecopy )
        return xbasecopy

    def updateUI( self, key:str ):
        x = self._xbaseui.getXBase()
        w = self.getWidget( key )
        w.setValue( x.getValue( key ) )

    def updateUI2( self, keys:List[str] ):
        x = self._xbaseui.getXBase()
        for key in keys:
            self.updateUI( key )

    def updateData( self ):
        # übernimmt die vom User im View geänderten Werte ins Datenmodell (xbase)
        xbase = self._xbaseui.getXBase()
        self._updateData( xbase )

    def _updateData( self, xbase:XBase ):
        """
        updates the wrapped XBase-Object with the (modified) values of the edit fields.
        :return:
        """
        # xbase = self._xbaseui.getXBase()
        for w in self._widgets:
            key = w.objectName()
            val = w.getValue()
            xbase.setValue( key, val )

#################   DynamicAttributeDialog   #######################
class DynamicAttributeDialog( OkApplyCancelDialog ):
    def __init__(self,  xbaseui:XBaseUI, title="Ändern eines Datensatzes", okButton=True, applyButton=True, cancelButton=True ):
        OkApplyCancelDialog.__init__( self, title, okButton=okButton, applyButton=applyButton, cancelButton=cancelButton )
        self._view = DynamicAttributeView( xbaseui )
        self.setMainWidget( self._view )
        self._view.setFocusToFirstEditableWidget()

    def getDynamicAttributeView( self ) -> DynamicAttributeView:
        return self._view

######################   TEST  TEST  TEST   ############################
def test():
    class XTest( XBase ):
        def __init__(self):
            XBase.__init__( self )
            self.master = "SB_Kaiser"
            self.mobj_id = "kaiser_22"
            self.mv_id = "marion_decker"
            self.jahr = 2022
            self.monat = "jun"
            self.betrag = 234.56
            self.umlegbar = False
            self.text = "Testtext"

    def onOk():
        print( "Okee" )
        v = d.getDynamicAttributeView()
        xcopy = v.getModifiedXBaseCopy()
        v.updateData()
        x = v.getXBase()
        equal = x.equals( xcopy )
        print( equal )
        # dicx = x.__dict__
        # dicxcopy = xcopy.__dict__
        # print( dicx == dicxcopy )
        # valsx = list( dicx.values() )
        # valscopy = list( dicxcopy.values() )
        # print( valsx == valscopy )
        # print( "modified: ", "no" if not x.equals( xcopy ) else "yes" )


    x = XTest()
    xui = XBaseUI( x )
    #xui.setEditables( (("betrag", float), ("umlegbar",bool), ("text", str) ) )
    vislist = ( VisibleAttribute( "master", BaseEdit, "Master: ", editable=False, nextRow=False ),
                VisibleAttribute( "mobj_id", BaseEdit, "Wohnung: ", editable=False ),
                VisibleAttribute( "betrag", FloatEdit, "Betrag: ", editable=True, widgetWidth=60 ) )
    xui.addVisibleAttributes( vislist )
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    d = DynamicAttributeDialog( xui )
    if d.exec_() == QDialog.Accepted:
        onOk()
    else:
        print( "Cancelled" )
    #d.okClicked.connect( onOk )
    #d.show()
    # v = DynamicAttributeView( xui, "View zum Testen" )
    # v.show()
    #app.exec_()

def test2():
    from PySide2.QtWidgets import QApplication
    app = QApplication()
    type_ = BaseComboBox
    inst = type_()
    print( inst )