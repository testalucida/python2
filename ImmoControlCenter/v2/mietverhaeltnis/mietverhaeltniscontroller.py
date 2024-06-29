from typing import Any, List

from PySide2.QtCore import QPoint, Slot
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QWidget, QApplication, QMenu, QDialog

from base.baseqtderivates import BaseAction, BaseEdit, FloatEdit, IntEdit, SmartDateEdit
from base.dynamicattributeui import DynamicAttributeDialog
from base.interfaces import XBaseUI, VisibleAttribute
from base.messagebox import InfoBox, ErrorBox
from v2.icc.icccontroller import IccController
from v2.icc.interfaces import XMietverhaeltnis
from v2.mietobjekt.mietobjektcontroller import MietobjektAuswahl
from v2.mietverhaeltnis.mietverhaeltnisgui import MietverhaeltnisView, MietverhaeltnisDialog, \
    MietverhaeltnisKuendigenDialog
from v2.mietverhaeltnis.mietverhaeltnislogic import MietverhaeltnisLogic


class MietverhaeltnisController( IccController ):
    def __init__( self ):
        IccController.__init__( self )
        self._view:MietverhaeltnisView = None
        self._mvlogic = MietverhaeltnisLogic()
        self._mvlist:List[XMietverhaeltnis] = None # Liste der Mietverhältnisse eines Mietobjekts
        self._mv: XMietverhaeltnis = None # das aktuell im View angezeigte Mietverhältnis

    def createGui( self ) -> QWidget:
        pass

    def getMenu( self ) -> QMenu or None:
        """
        Jeder Controller liefert dem MainController ein Menu, das im MainWindow in der Menubar angezeigt wird
        :return:
        """
        menu = QMenu( "Mietverhältnis" )
        action = BaseAction( "Neues Mietverhältnis anlegen...", parent=menu )
        action.triggered.connect( self.onMietverhaeltnisNeu )
        menu.addAction( action )
        action = BaseAction( "Mietverhältnis anschauen und bearbeiten...", parent=menu )
        action.triggered.connect( self.onMietverhaeltnisShowOrEdit )
        menu.addAction( action )
        action = BaseAction( "Mietverhältnis kündigen...", parent=menu ) #
        action.triggered.connect( self.onMietverhaeltnisKuendigen )
        menu.addAction( action )
        return menu

    @Slot()
    def onMietverhaeltnisNeu( self, mobj_id:str=None ):
        """
        Wird aufgerufen, wenn in der Menübar der Anwendung "Mietverhältnis anlegen..." geklickt wurde
        :return:
        """
        def validateNewMv() -> bool:
            """
            Wird vom MietverhaeltnisDialog aufgerufen.
            Liefert True zurück, wenn die Validierung in Ordnung ist, sonst False.
            :return:
            """
            return self.validate( dlg, isNewMv=True )
        ################
        if not mobj_id:
            # zuerst über den Auswahldialog bestimmen, welche Daten für die View selektiert werden müssen
            mietobjektAuswahl = MietobjektAuswahl()
            xmo = mietobjektAuswahl.selectMietobjekt()
            if not xmo: return None
            mobj_id = xmo.mobj_id
        # letztes Mietverhältnis holen ("Vormieter")
        xmvVormieter:XMietverhaeltnis = self._mvlogic.getAktuellesMietverhaeltnisByMietobjekt( mobj_id )
        self._view = v = MietverhaeltnisView.createForNewMietverh( mobj_id,
                                                                   vormieterName=xmvVormieter.name + ", " + xmvVormieter.vorname,
                                                                   vormieterBis=xmvVormieter.bis )
        dlg = MietverhaeltnisDialog( v, "Neues Mietverhältnis anlegen für Wohnung '%s'" % mobj_id )
        dlg.setBeforeAcceptFunction( validateNewMv )
        if dlg.exec_() == QDialog.Accepted:
            try:
                v.applyChanges()
                vormieterBis = v.getVormieterMvBis()
                if vormieterBis != xmvVormieter.bis: # Mietende des Vormieters im Neuanlage-Dialog geändert
                    xmvVormieter.bis = vormieterBis
                    self._mvlogic.kuendigeMietverhaeltnis( xmvVormieter )
                xmvNeu = v.getMietverhaeltnis()
                self._mvlogic.createMietverhaeltnis( xmvNeu )
            except Exception as ex:
                dlg.showErrorMessage( "Datenbankfehler bei der Anlage des Mietverhältnisses", str(ex) )
        else:
            dlg.close()

    @Slot()
    def onMietverhaeltnisShowOrEdit( self, mv_id:str = None ):
        """
        Wird aufgerufen, wenn in der Menübar der Anwendung "Mietverhältnis anzeigen und bearbeiten..." geklickt wurde
        :return:
        """
        def validateEditedMv() -> bool:
            return self.validate( dlg, isNewMv=False )
        ###################################
        if not mv_id:
            # zuerst über den Auswahldialog bestimmen, welche Daten für die View selektiert werden müssen
            mietobjektAuswahl = MietobjektAuswahl()
            xmo = mietobjektAuswahl.selectMietobjekt()
            if not xmo: return None
            mobj_id = xmo.mobj_id
        else:
            xmv = self._mvlogic.getAktuellesMietverhaeltnis( mv_id )
            mobj_id = xmv.mobj_id
        self.createMvView( mobj_id )
        v = self._view
        dlg = MietverhaeltnisDialog( v )
        dlg.setBeforeAcceptFunction( validateEditedMv )
        if dlg.exec_() == QDialog.Accepted:
            try:
                xmv_orig = v.getMietverhaeltnis()
                xmv_copy = v.getMietverhaeltnisCopyWithChanges()
                if xmv_orig.equals( xmv_copy ):
                    return
                v.applyChanges()
                self._mvlogic.updateMietverhaeltnis( xmv_orig )
            except Exception as ex:
                dlg.showErrorMessage( "Datenbankfehler beim Ändern des Mietverhältnisses", str(ex) )

    @Slot()
    def onMietverhaeltnisKuendigen( self, mv_id:str=None ):
        """
        Wird aufgerufen, wenn in der Menübar der Anwendung "Mietverhältnis kündigen..." geklickt wurde
        :param mv_id: ist versorgt, wenn der Aufruf dieses Slots aus dem Context-Menü der Miete-TableView kommt.
                      Wenn der Aufruf aus der Toolbar der Anwendung kommt, ist mv_id leer.
        :return:
        """
        ctrl = MietverhaeltnisKuendigenController()
        ctrl.processKuendigung( mv_id )

    def showMietverhaeltnis( self, mv_id:str ):
        """
        Methode wird aus aer Mieten-Tabelle aufgerufen, nach Mausklick auf Kontextmenü "Mietverhältnis anzeigen"
        :param mv_id:
        :param point:
        :return:
        """
        #mv:XMietverhaeltnis = BusinessLogic.inst().getAktuellesOderZukuenftigesMietverhaeltnis( mv_id )
        xmv:XMietverhaeltnis = self._mvlogic.getAktuellesMietverhaeltnis( mv_id )
        if not xmv: # wenn z.B. der Mieter schon in der Tabelle erscheint, aber das Mietverhältnis noch nicht begonnen hat.
            box = InfoBox( "Sorry...", "Die Daten können nicht angezeigt werden.",
                           "Das Mietverhältnis hat noch nicht begonnen.", "OK" )
            box.exec_()
        else:
            dlg = MietverhaeltnisDialog.fromMietverhaeltnis( xmv )
            dlg.exec_()

    def createMvView( self, mobj_id:str ):
        """
        Erzeugt den MvView, der für Anzeige und Änderung, NICHT für Neuanlage (siehe onMietverhaeltnisNeu) benötigt wird.
        :param mobj_id:
        :return:
        """
        self._mvlist = self._mvlogic.getMietverhaeltnisListe( mobj_id )
        mvlist_len = len( self._mvlist )
        if mvlist_len > 0:
            self._mv = self._mvlist[0]
            enableBrowsing = True if mvlist_len > 1 else False
            self._view = MietverhaeltnisView( self._mv, enableBrowsing=enableBrowsing )
            self._view.prevMv.connect( self.onPrevMv )
            self._view.nextMv.connect( self.onNextMv )
        else:
            box = InfoBox( "Mietverhältnis anzeigen", "Das Objekt '" + mobj_id + "' ist nicht vermietet.", "", "OK" )
            box.moveToCursor()
            box.exec_()

    def onPrevMv( self ):
        self._browse( False )

    def onNextMv( self ):
        self._browse( True )

    def _browse( self, next:bool ):
        if len( self._mvlist ) < 2:
            box = InfoBox( "Blättern in Mietverhältnissen", "Blättern nicht möglich.", "Es gibt nur ein Mietverhältnis.", "OK" )
            box.moveToCursor()
            box.exec_()
            return
        idx = self._mvlist.index( self._mv )
        max = len( self._mvlist ) - 1
        if next: # "next" geklickt
            if idx == 0:
                box = InfoBox( "Blättern in Mietverhältnissen", "Blättern nicht möglich.",
                               "Das jüngste Mietverhältnis wird angezeigt.", "OK" )
                box.moveToCursor()
                box.exec_()
                return
            self._mv = self._mvlist[idx-1]
            self._view.clear()
            self._view._setMietverhaeltnisData( self._mv )
        else: # "previous" geklickt
            if idx == max:
                box = InfoBox( "Blättern in Mietverhältnissen", "Blättern nicht möglich.",
                               "Das älteste Mietverhältnis wird angezeigt.", "OK" )
                box.moveToCursor()
                box.exec_()
                return
            self._mv = self._mvlist[idx+1]
            self._view.clear()
            self._view._setMietverhaeltnisData( self._mv )

    def validate( self, dlg:MietverhaeltnisDialog, isNewMv:bool ) -> bool:
        # Validierung sollte im ***Model*** sein, nicht im Controller.
        # siehe: https://stackoverflow.com/questions/5651175/mvc-question-should-i-put-form-validation-rules-in-the-controller-or-model
        # und https://stackoverflow.com/questions/5305854/best-place-for-validation-in-model-view-controller-model
        v = self._view
        title = "Validierung fehlgeschlagen"
        mvcopy = v.getMietverhaeltnisCopyWithChanges()
        if not mvcopy.von:
            dlg.showErrorMessage( title, "Mietbeginn fehlt" )
            return False
        if isNewMv:
            # zusätzliche Prüfungen, wenn es sich um die Neuanlage eines MV handelt
            vormieterBis = v.getVormieterMvBis()
            if not vormieterBis:
                dlg.showErrorMessage( title, "Für das vorige Mietverhältnis muss ein Kündigungsdatum angegeben werden." )
                return False
            if mvcopy.von < vormieterBis:
                dlg.showErrorMessage( title, "Das neue Mietverhältnis darf nicht beginnen, bevor das alte beendet ist." )
                return False
        msg = ""
        rc = True
        if mvcopy.bis and mvcopy.bis < mvcopy.von:
            msg = "Das Mietende darf nicht vor dem Mietbeginn liegen."
        elif not mvcopy.name:
            msg = "Der Nachname des ersten Mieters fehlt."
        elif not mvcopy.vorname:
            msg = "Der Vorname des ersten Mieters fehlt."
        elif mvcopy.name2 > " " and not mvcopy.vorname2:
            msg = "Vorname des zweiten Mieters fehlt."
        elif not mvcopy.anzahl_pers or mvcopy.anzahl_pers == 0:
            msg = "Anzahl Personen muss angegeben sein."
        elif not mvcopy.nettomiete or mvcopy.nettomiete == 0 or not mvcopy.nkv or mvcopy.nkv == 0:
            msg = "Nettomiete und Nebenkosten müssen angegeben werden."
        if msg > " ":
            dlg.showErrorMessage( title, msg )
            rc = False
        if not mvcopy.telefon and not mvcopy.mobil and not mvcopy.mailto:
            dlg.showWarningMessage( "Validierung kritisch", "Es ist keine Kontaktmöglichkeit angegeben!\n"
                                                             "Telefon, Mobilfunk und Mailadresse sind leer!" )
        return rc

    def getChanges( self ) -> Any:
        pass

    def getViewTitle( self ) -> str:
        title = "Mieterdaten von Mieter: " + self._mv.vorname + " " + self._mv.name
        if self._mv.name2: title += ( " und " + self._mv.vorname2 + " " + self._mv.vorname2 )
        return title

    def isChanged( self ) -> bool:
        xcopy = self._view.getMietverhaeltnisCopyWithChanges()
        return False if xcopy.equals( self._mv ) else True


#####################   MietverhaeltnisKuendigenController   #############
class MietverhaeltnisKuendigenController:
    def __init__( self ):
        self._view:MietverhaeltnisView = None
        self._mvlogic = MietverhaeltnisLogic()
        # self._mv: XMietverhaeltnis = None # das aktuell im View angezeigte Mietverhältnis

    def processKuendigung( self, mv_id:str=None ):
        if not mv_id:
            # zuerst über den Auswahldialog bestimmen, welche Daten für die View selektiert werden müssen
            mietobjektAuswahl = MietobjektAuswahl()
            xmo = mietobjektAuswahl.selectMietobjekt()
            if not xmo: return None
            mv_id = xmo.mv_id
        xmv:XMietverhaeltnis = self._mvlogic.getAktuellesMietverhaeltnis( mv_id )
        self.showDialog( xmv )

    def showDialog( self, xmv ):
        def validate():
            v = dlg.getDynamicAttributeView()
            xcopy:XMietverhaeltnis = v.getModifiedXBaseCopy()
            return self._mvlogic.validateKuendigungDaten( xcopy )
        xui = XBaseUI( xmv )
        vislist = (VisibleAttribute( "name_vorname", BaseEdit, "Mieter: ", editable=False, nextRow=True, columnspan=4 ),
                   VisibleAttribute( "nettomiete", FloatEdit, "Nettomiete (€): ", widgetWidth=80, editable=False, nextRow=False ),
                   VisibleAttribute( "nkv", FloatEdit, "NKV (€): ", widgetWidth=80, editable=False ),
                   VisibleAttribute( "kaution", IntEdit, "Kaution (€): ", editable=False, widgetWidth=50 ),
                   VisibleAttribute( "bis", SmartDateEdit, "Ende des Mietverhältnisses: ", widgetWidth=80 ) )
        xui.addVisibleAttributes( vislist )
        dlg = DynamicAttributeDialog( xui, "Kündigen eines Mietverhältnisses" )
        dlg.getApplyButton().setEnabled( False )
        dlg.setCallbacks( beforeAcceptCallback=validate )
        if dlg.exec_() == QDialog.Accepted:
            v = dlg.getDynamicAttributeView()
            v.updateData()  # Validierung war ok, also Übernahme der Änderungen ins XBase-Objekt
            try:
                self._mvlogic.kuendigeMietverhaeltnis( xmv )
            except Exception as ex:
                box = ErrorBox( "MietverhaeltnisKuendigenController.showDialog():\n"
                                "Fehler beim Speichern der Kündigung", str( ex ), xmv.toString( True ) )
                box.exec_()
                return
        else:
            # cancelled
            return


###################################################################################

def testKuendigen():
    app = QApplication()
    c = MietverhaeltnisKuendigenController()
    c.processKuendigung()

    app.exec_()

def test():
    app = QApplication()
    c = MietverhaeltnisController()
    #c.onMietverhaeltnisShow()
    c.onMietverhaeltnisNeu( "bueb" )
    app.exec_()
#
# if __name__ == "__main__":
#     test()
