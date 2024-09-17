import copy

from PySide2.QtCore import Signal, QSize
from PySide2.QtGui import Qt, QFont, QPalette
from PySide2.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QApplication, QTextEdit, QFrame, QVBoxLayout

from base.baseqtderivates import FatLabel, BaseBoldEdit, LabelTimesBold12, SmartDateEdit, MultiLineEdit, HLine, \
    LabelTimes12, BaseLabel, EditIconButton, LabelArial12, BaseBoldComboBox, BaseGridLayout, BaseWidget, BaseEdit, \
    BaseComboBox, BaseButton
from generictable_stuff.okcanceldialog import OkDialog, OkCancelDialog
from v2.icc.constants import ValueMapperHelper, Heizung
from v2.icc.iccwidgets import IccTableView
from v2.icc.interfaces import XMietobjektExt, XMietobjekt, XHausgeld, XMieter, XMasterMietobjektMieter, XMasterobjekt


# def createXMietobjektExt() -> XMietobjektExt:
#     x = XMietobjektExt()
#     x.master_id = 17
#     x.master_name = "NK-Kleist"
#     x.plz = "66538"
#     x.ort = "Neunkirchen"
#     x.strasse_hnr = "Klabautermannstraße 377"
#     x.anz_whg = 8
#     x.gesamt_wfl = 432
#     x.veraeussert_am = "2024-12-01"
#     x.heizung = "Gaszentralheizung"
#     x.energieeffz = "F"
#     x.verwalter = "Hausverwalter Kannundtunix, Neunkirchen"
#     x.verwalter_telefon = "06821 / 232333"
#     x.verwalter_mailto = "kannundtunix_hausverwaltung@kannundtunix.de"
#     x.hauswart = "Hans-Jürgen Müller-Westernhagen"
#     x.hauswart_telefon = "06821 / 123456"
#     x.hauswart_mailto = "mueller-hauswart@t-online.de"
#     x.bemerkung_masterobjekt = "Außen hui Innen pfui"
#     x.mobj_id = "kleist_11"
#     x.whg_bez = "1. OG links"
#     x.qm = 50
#     x.container_nr = "098765/11"
#     x.bemerkung_mietobjekt = "Wird unser HQ im Saarland"
#     x.mieter = "Graf von Strübel-Lakaiendorf, Christian-Eberhard"
#     x.telefon_mieter = "0171 / 11211345"
#     x.mailto_mieter = "grastruelakai@t-online.de"
#     x.nettomiete = 234.56
#     x.nkv = 87.69
#     x.weg_name = "WEG Beispielstraße 22, 55432 Mühlheim"
#     x.hgv_netto = 300.00
#     x.ruezufue = 67.89
#     x.hgv_brutto = 367.89
#     return x

# def createXHausgeld():
#     x = XHausgeld()
#     x.hgv_netto = 123.45
#     x.hgv_brutto = 232.45
#     x.ruezufue = 100.00
#     return x


#########################  MasterMietobjektMieterView  ############################
class MasterMietobjektMieterView( QFrame ):
    """
    MasterMietobjektMieterView ist ein Wrapper um
    a) eine MasterView, welche wiederum besteht aus
        aa) HeaderView
        ab) DataView
    b) eine MobjView
    c) MieterView
    """

    class MasterView(QFrame):
        show_verwalter = Signal(str)
        # show_hauswart = Signal( str )
        """
        Enthält die Masterobjekt-Daten.
        Besteht aus einer HeaderView im oberen Bereich und einer DataView im unteren Bereich.
        """

        ###########  MasterView.HeaderView  ################
        class HeaderView(QFrame):
            def __init__(self, master_id: int, master_name: str, strasse_hnr: str, plz: str, ort: str,
                         veraeussert_am: str = ""):
                QFrame.__init__(self)
                self._master_id = master_id
                self._master_name = master_name
                self._strasse_hnr = strasse_hnr
                self._plz = plz
                self._ort = ort
                self._veraeussert_am = veraeussert_am
                self._layout = BaseGridLayout()
                self.setLayout(self._layout)
                self._mleMasterHeader = MultiLineEdit()
                self._sdeVeraeussertAm = SmartDateEdit()
                self._createGui()
                self._dataToGui()

            def _createGui(self):
                self.setStyleSheet("HeaderView { background: lightgray; }")
                l = self._layout
                e = self._mleMasterHeader
                e.setStyleSheet("background: lightgray;")
                e.setReadOnly(True)
                e.setFrameStyle(QFrame.NoFrame)
                e.setMaximumHeight(70)
                r, c = 0, 0
                l.addWidget(e, r, c, 1, 2)
                r += 1
                vam = self._sdeVeraeussertAm
                vam.setStyleSheet("background: white;")
                vam.setMaximumWidth(100)
                l.addWidget(BaseLabel("veräußert am: "), r, c, 1, 1, alignment=Qt.AlignRight)
                c += 1
                l.addWidget(vam, r, c, 1, 1, alignment=Qt.AlignLeft)

            def _dataToGui(self):
                e = self._mleMasterHeader
                html = 'Master-ID: <font size="+2"><b>' + str(self._master_id) + '</font></b>' + \
                       '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Master-Name: <font size="+2"><b>' + \
                       self._master_name + '</font></b>'
                e.setHtml(html)
                e.setAlignment(Qt.AlignCenter)
                e.append(" ")
                e.append("<b>" + self._strasse_hnr + "&nbsp;&nbsp;&nbsp;" + self._plz + "&nbsp;" + self._ort + "</b>")
                e.setAlignment(Qt.AlignCenter)
                self._sdeVeraeussertAm.setValue(self._veraeussert_am)

            def getVeraeussertAm(self) -> str:
                """
                :return: den Wert aus dem GUI-Feld
                """
                return self._sdeVeraeussertAm.getValue()

        ############  MasterView.DataView  ##################
        class DataView(QFrame):
            show_verwalter = Signal()

            # show_hauswart = Signal()
            def __init__(self, x: XMasterobjekt):
                QFrame.__init__(self)
                self._x = x
                self._layout = BaseGridLayout()
                self.setLayout(self._layout)
                self._lblAnzWhg = BaseEdit()
                self._lblGesamtWfl = BaseEdit()
                self._cboHeizung = BaseComboBox()
                self._cboHeizung.addItems(ValueMapperHelper.getDisplayValues(Heizung, issorted=False))
                self._cboEnergieEffz = BaseComboBox()
                self._cboEnergieEffz.addItems(("", "A", "B", "C", "D", "E", "F", "G", "H"))
                self._mleVerwalter = MultiLineEdit()
                self._edVerwalterTelefon_1 = BaseEdit()
                self._edVerwalterTelefon_2 = BaseEdit()
                self._edVerwalterMailto = BaseEdit()
                self._edVerwalterAp = BaseEdit()
                self._btnVerwalterDetail = BaseButton("🔍")
                self._btnVerwalterDetail.clicked.connect(self.show_verwalter.emit)
                self._lblWegName = BaseEdit()
                self._mleHauswart = MultiLineEdit()
                self._edHauswartTelefon = BaseEdit()
                self._edHauswartMailto = BaseEdit()
                # self._btnHauswartDetail = BaseButton( "🔍" )
                # self._btnHauswartDetail.clicked.connect( self.show_hauswart.emit )
                self._mleBemerkung = MultiLineEdit()
                self._createGui()
                self._dataToGui()

            def _createGui(self):
                l = self._layout
                l.setHorizontalSpacing(20)
                anz_cols = 7
                for c in range(0, anz_cols - 1):
                    l.setColumnStretch(c, 0)
                l.setColumnStretch(1, 1)
                l.setColumnStretch(anz_cols - 1, 1)

                r, c = 0, 0
                ## Anzahl Wohnungen und Gesamt-Wfl.
                l.addWidget(BaseLabel("Anzahl Wohnungen:"), r, c)
                c += 1
                self._lblAnzWhg.setFixedWidth(50)
                self._lblAnzWhg.setReadOnly(True)
                self._lblAnzWhg.setStyleSheet("background: lightgray;")
                l.addWidget(self._lblAnzWhg, r, c, 1, 1, alignment=Qt.AlignLeft)
                c += 2
                l.addWidget(BaseLabel("Gesamt-Wfl.(qm):"), r, c)
                c += 1
                self._lblGesamtWfl.setFixedWidth(50)
                self._lblGesamtWfl.setReadOnly(True)
                self._lblGesamtWfl.setStyleSheet("background: lightgray;")
                l.addWidget(self._lblGesamtWfl, r, c, 1, 1)

                r += 1
                c = 0
                ## Heizung und Energie-Effizienzklasse
                l.addWidget(BaseLabel("Heizung:"), r, c)
                c += 1
                l.addWidget(self._cboHeizung, r, c, 1, 1)
                c += 2
                l.addWidget(BaseLabel("Energieeffz.klasse:"), r, c)
                c += 1
                self._cboEnergieEffz.setFixedWidth(50)
                l.addWidget(self._cboEnergieEffz, r, c, 1, 1)

                r += 1
                c = 0
                ## Verwalter
                l.addWidget(BaseLabel("Verwalter:"), r, c)
                c += 1
                self._mleVerwalter.setReadOnly(True)
                self._mleVerwalter.setMaximumHeight(70)
                self._mleVerwalter.setStyleSheet("background: lightgray;")
                l.addWidget(self._mleVerwalter, r, c, 1, 2)
                c += 2
                l.addWidget(BaseLabel("Telefon:"), r, c)
                c += 1
                wdg = QFrame()
                boxlay = QVBoxLayout()
                boxlay.setSpacing( 0 )
                boxlay.setMargin(0)
                boxlay.addWidget(self._edVerwalterTelefon_1 )
                boxlay.addWidget( self._edVerwalterTelefon_2)
                wdg.setLayout(boxlay)
                l.addWidget( wdg, r, c, 1, 1, alignment=Qt.AlignLeft )
                # l.addWidget(self._edVerwalterTelefon_1, r, c)
                c += 1
                l.addWidget(BaseLabel("mailto:"), r, c)
                c += 1
                l.addWidget(self._edVerwalterMailto, r, c, 1, 1)
                c += 1
                self._btnVerwalterDetail.setFixedSize(QSize(22, 22))
                self._btnVerwalterDetail.setToolTip("Details zum Verwalter anzeigen")
                l.addWidget(self._btnVerwalterDetail, r, c, 1, 1)
                r += 1
                c = 0
                l.addWidget(BaseLabel("Verw.-AP:"), r, c )
                c += 1
                l.addWidget(self._edVerwalterAp, r, c )
                r += 1
                c = 0
                ## WEG-Name
                l.addWidget(BaseLabel("WEG:"), r, c)
                c += 1
                self._lblWegName.setReadOnly(True)
                l.addWidget(self._lblWegName, r, c, 1, 4)

                r += 1
                c = 0
                ## Hauswart
                l.addWidget(BaseLabel("Hauswart:"), r, c)
                c += 1
                self._mleHauswart.setMaximumHeight(50)
                l.addWidget(self._mleHauswart, r, c, 1, 2)
                c += 2
                l.addWidget(BaseLabel("Telefon:"), r, c)
                c += 1
                l.addWidget(self._edHauswartTelefon, r, c, 1, 1)
                c += 1
                l.addWidget(BaseLabel("mailto:"), r, c)
                c += 1
                l.addWidget(self._edHauswartMailto, r, c, 1, 1)

                r += 1
                c = 0
                ## Bemerkung
                self._mleBemerkung.setMaximumHeight(60)
                self._mleBemerkung.setPlaceholderText("Bemerkungen zum Masterobjekt")
                l.addWidget(self._mleBemerkung, r, c, 1, anz_cols)

            # MasterView.DataView
            def _dataToGui(self):
                x = self._x
                self._lblAnzWhg.setValue(str(x.anz_whg))
                self._lblGesamtWfl.setValue(str(x.gesamt_wfl))
                items = [self._cboHeizung.itemText(i) for i in range(self._cboHeizung.count())]
                self._cboHeizung.setValue(x.heizung)
                self._cboEnergieEffz.setValue(x.energieeffz)
                self._mleVerwalter.setValue(x.verwalter)
                self._edVerwalterTelefon_1.setValue(x.verwalter_telefon_1)
                self._edVerwalterTelefon_2.setValue(x.verwalter_telefon_2)
                self._edVerwalterMailto.setValue(x.verwalter_mailto)
                self._edVerwalterAp.setValue( x.verwalter_ap )
                self._lblWegName.setValue(x.weg_name)
                self._mleHauswart.setValue(x.hauswart)
                self._edHauswartTelefon.setValue(x.hauswart_telefon)
                self._edHauswartMailto.setValue(x.hauswart_mailto)
                self._mleBemerkung.setValue(x.bemerkung)

            # MasterView.DataView
            def guiToData(self, x: XMasterobjekt):
                """
                Nur veränderbare Daten werden von der GUI in x geladen
                :param x:
                :return:
                """
                x.heizung = self._cboHeizung.currentText()
                x.energieeffz = self._cboEnergieEffz.currentText()
                x.verwalter_telefon_1 = self._edVerwalterTelefon_1.getValue()
                x.verwalter_telefon_2 = self._edVerwalterTelefon_2.getValue()
                x.verwalter_mailto = self._edVerwalterMailto.getValue()
                x.hauswart = self._mleHauswart.getValue()
                x.hauswart_telefon = self._edHauswartTelefon.getValue()
                x.hauswart_mailto = self._edHauswartMailto.getValue()
                x.verwalter_ap = self._edVerwalterAp.getValue()
                x.bemerkung = self._mleBemerkung.getValue()

            def getHeizung(self) -> str:
                """
                :return: die display-Version einer der Konstanten der class Heizung
                """
                return self._cboHeizung.currentText()

            def getEnergieEffz(self) -> str:
                return self._cboEnergieEffz.currentText()

            def getVerwalterTelefon(self) -> str:
                return self._edVerwalterTelefon_1

            def getVerwalterMailto(self) -> str:
                return self._edVerwalterMailto

            def getHauswart(self) -> str:
                return self._mleHauswart.getValue()

            def getHauswartTelefon(self) -> str:
                return self._edHauswartTelefon.getValue()

            def getHauswartMailto(self) -> str:
                return self._edHauswartMailto.getValue()

            def getBemerkung(self) -> str:
                return self._mleBemerkung.getValue()

        #####################################################
        # MasterView:
        def __init__(self, x: XMasterobjekt):
            QFrame.__init__(self)
            self._x = x
            self._layout = BaseGridLayout()
            self.setLayout(self._layout)
            self._headerView = MasterMietobjektMieterView.MasterView.HeaderView(x.master_id, x.master_name, x.strasse_hnr, x.plz, x.ort,
                                                     x.veraeussert_am)
            self._dataView = MasterMietobjektMieterView.MasterView.DataView(x)
            self._createGui()

        def _createGui(self):
            l = self._layout
            anz_cols = 1
            r, c = 0, 0
            l.addWidget(self._headerView, r, c, 1, anz_cols)
            r += 1
            l.addWidget(self._dataView, r, c, 1, anz_cols)

        # MasterView
        def guiToData(self, x:XMasterobjekt):
            x.veraeussert_am = self._headerView.getVeraeussertAm()
            self._dataView.guiToData(x)

        # def getMasterobjektCopyWithChanges(self) -> XMasterobjekt:
        #     xcopy = copy.copy(self._x)
        #     xcopy.veraeussert_am = self._headerView.getVeraeussertAm()
        #     self._dataView.guiToData(xcopy)
        #     return xcopy

        def applyChanges(self):
            self._x.veraeussert_am = self._headerView.getVeraeussertAm()
            self._dataView.guiToData( self._x )

    ###############  MobjView  #########################
    class MobjView(QFrame):
        def __init__(self, x: XMietobjekt):
            QFrame.__init__(self)
            self._x: XMietobjekt = x
            self._mleHeader = MultiLineEdit()
            self._lblQm = BaseEdit()
            self._eContainerNr = BaseEdit()
            self._lblHgvNetto = BaseEdit()
            self._lblRuezufue = BaseEdit()
            self._lblHgvBrutto = BaseEdit()
            self._mleBemerkung = MultiLineEdit()
            self._layout = BaseGridLayout()
            self.setLayout(self._layout)
            self._createGui()
            self._dataToGui()

        def _createGui(self):
            wBetrag = 60
            l = self._layout
            l.setHorizontalSpacing(25)
            anz_cols = 7
            for c in range(0, anz_cols - 1):
                l.setColumnStretch(c, 0)
            l.setColumnStretch(anz_cols - 1, 1)
            e = self._mleHeader
            e.setStyleSheet("background: lightgray;")
            e.setReadOnly(True)
            e.setFrameStyle(QFrame.NoFrame)
            e.setMaximumHeight(40)
            r, c = 0, 0
            l.addWidget(e, r, c, 1, anz_cols)

            r += 1
            c = 0
            l.addWidget(BaseLabel("qm:"), r, c)
            c += 1
            self._lblQm.setFixedWidth(wBetrag)
            self._lblQm.setReadOnly(True)
            l.addWidget(self._lblQm, r, c)
            c += 1
            l.addWidget(BaseLabel("Container-Nr.:"), r, c)
            c += 1
            l.addWidget(self._eContainerNr, r, c)

            r += 1
            c = 0
            l.addWidget(BaseLabel("HGV netto:"), r, c, 1, 1)
            c += 1
            self._lblHgvNetto.setFixedWidth(wBetrag)
            self._lblHgvNetto.setReadOnly(True)
            l.addWidget(self._lblHgvNetto, r, c, 1, 1, alignment=Qt.AlignLeft)
            c += 1
            l.addWidget(BaseLabel("RüZuFü:"), r, c, 1, 1)
            c += 1
            self._lblRuezufue.setFixedWidth(wBetrag)
            self._lblRuezufue.setReadOnly(True)
            l.addWidget(self._lblRuezufue, r, c, 1, 1, alignment=Qt.AlignLeft)
            c += 1
            l.addWidget(BaseLabel("HGV brutto:"), r, c, 1, 1)
            c += 1
            self._lblHgvBrutto.setFixedWidth(wBetrag)
            self._lblHgvBrutto.setReadOnly(True)
            l.addWidget(self._lblHgvBrutto, r, c, 1, 1, alignment=Qt.AlignLeft)

            r += 1
            c = 0
            self._mleBemerkung.setPlaceholderText("Bemerkungen zum Mietobjekt")
            self._mleBemerkung.setMaximumHeight(60)
            l.addWidget(self._mleBemerkung, r, c, 1, anz_cols)

        # MobjView
        def _dataToGui(self):
            x = self._x
            e = self._mleHeader
            if x.whg_bez is None: x.whg_bez = ""
            html = 'Mietobjekt: <font size="+2"><b>' + x.mobj_id + '</font></b>' + \
                   '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Bezeichnung: <font size="+2"><b>' + \
                   x.whg_bez + '</font></b>'
            e.setHtml(html)
            e.setAlignment(Qt.AlignCenter)
            self._lblQm.setValue(str(x.qm))
            self._eContainerNr.setValue(x.container_nr)
            self._mleBemerkung.setValue(x.bemerkung)
            self._lblHgvNetto.setValue("%.2f" % self._x.hgv.netto)
            self._lblRuezufue.setValue("%.2f" % self._x.hgv.ruezufue)
            self._lblHgvBrutto.setValue("%.2f" % self._x.hgv.brutto)

        def guiToData(self, x:XMietobjekt):
            x.container_nr = self._eContainerNr.getValue()
            x.bemerkung = self._mleBemerkung.getValue()

        def getMietobjektCopyWithChanges(self) -> XMietobjekt:
            xcopy = copy.deepcopy(self._x)
            self._guiToData(xcopy)
            return xcopy

        def applyChanges(self):
            self.guiToData(self._x)

        def getModel(self) -> XMietobjekt:
            return self._x


    ###############  MieterView  #######################
    class MieterView(QFrame):
        def __init__(self, x: XMieter):
            QFrame.__init__(self)
            self._x = x
            self._layout = BaseGridLayout()
            self.setLayout(self._layout)
            # self._mleHeader = MultiLineEdit()
            self._mleHeader = MultiLineEdit()
            self._eTelefon = BaseEdit()
            self._eMailto = BaseEdit()
            self._lblNettoMiete = BaseEdit()
            self._lblNkv = BaseEdit()
            self._lblBruttoMiete = BaseEdit()
            self._lblKaution = BaseEdit()
            self._mleBemerkung1 = MultiLineEdit()
            self._mleBemerkung2 = MultiLineEdit()
            self._createGui()
            self._dataToGui()

        def _createGui(self):
            wBetrag = 60
            l = self._layout
            l.setHorizontalSpacing(20)
            anz_cols = 10
            for c in range(0, anz_cols - 1):
                l.setColumnStretch(c, 0)
            l.setColumnStretch(anz_cols - 1, 1)

            r, c = 0, 0
            self._mleHeader.setReadOnly(True)
            self._mleHeader.setFrameStyle(QFrame.NoFrame)
            self._mleHeader.setStyleSheet("background: lightgray;")
            self._mleHeader.setFixedHeight(40)
            l.addWidget(self._mleHeader, r, c, 1, anz_cols)

            r += 1
            c = 0
            l.addWidget(BaseLabel("Telefon:"), r, c)
            c += 1
            self._eTelefon.setFixedWidth(150)
            l.addWidget(self._eTelefon, r, c, 1, 2)
            c += 2
            l.addWidget(BaseLabel("mailto:"), r, c)
            c += 1
            self._eMailto.setFixedWidth(260)
            l.addWidget(self._eMailto, r, c, 1, 3)

            r += 1
            c = 0
            l.addWidget(BaseLabel("Netto-Miete:"), r, c)
            c += 1
            self._lblNettoMiete.setReadOnly(True)
            self._lblNettoMiete.setFixedWidth(wBetrag)
            l.addWidget(self._lblNettoMiete, r, c)
            c += 2
            l.addWidget(BaseLabel("NKV:"), r, c)
            c += 1
            self._lblNkv.setReadOnly(True)
            self._lblNkv.setFixedWidth(wBetrag)
            l.addWidget(self._lblNkv, r, c)
            c += 1
            l.addWidget(BaseLabel("Brutto-Miete:"), r, c)
            c += 1
            self._lblBruttoMiete.setReadOnly(True)
            self._lblBruttoMiete.setFixedWidth(wBetrag)
            l.addWidget(self._lblBruttoMiete, r, c)
            c += 1
            l.addWidget(BaseLabel("Kaution:"), r, c)
            c += 1
            self._lblKaution.setFixedWidth(wBetrag)
            self._lblKaution.setReadOnly(True)
            l.addWidget(self._lblKaution, r, c)

            r += 1
            c = 0
            self._mleBemerkung1.setMaximumHeight(80)
            self._mleBemerkung1.setPlaceholderText("Bemerkungen zum Mieter")
            l.addWidget(self._mleBemerkung1, r, c, 1, 5)
            c += 5
            self._mleBemerkung2.setMaximumHeight(80)
            self._mleBemerkung2.setPlaceholderText("Weitere Bemerkungen zum Mieter")
            l.addWidget(self._mleBemerkung2, r, c, 1, 5)

        def _dataToGui(self):
            x = self._x
            e = self._mleHeader
            html = 'Mieter: <font size="+2"><b>' + x.mieter + '</font></b>'
            e.setHtml(html)
            e.setAlignment(Qt.AlignCenter)
            self._eTelefon.setValue(x.telefon)
            self._eMailto.setValue(x.mailto)
            self._lblNettoMiete.setValue("%.2f" % x.nettomiete)
            self._lblNkv.setValue("%.2f" % x.nkv)
            self._lblBruttoMiete.setValue("%.2f" % (x.nkv+x.nettomiete))
            self._lblKaution.setValue(str(x.kaution))
            self._mleBemerkung1.setValue(x.bemerkung1)
            self._mleBemerkung2.setValue(x.bemerkung2)

        # MieterView
        def guiToData(self, x:XMieter):
            """
            Schreibt den Inhalt der GUI-Felder in die korrespondierenden
            Datenfelder der übergebenen Schnittstelle <x>
            :param x:
            :return:
            """
            x.telefon = self._eTelefon.getValue()
            x.mailto = self._eMailto.getValue()
            x.bemerkung1 = self._mleBemerkung1.getValue()
            x.bemerkung2 = self._mleBemerkung2.getValue()

        def getMieterCopyWithChanges(self) -> XMieter:
            xcopy = copy.deepcopy(self._x)
            self._guiToData(xcopy)
            return xcopy

        def applyChanges(self):
            self.guiToData(self._x)

        def getModel(self) -> XMieter:
            return self._x

    ########################################################
    # MasterMietobjektMieterView
    def __init__( self, x: XMasterMietobjektMieter ):
        QFrame.__init__( self )
        self._layout = BaseGridLayout()
        self.setLayout( self._layout )
        self._mastermietobjektmieter = x
        self._masterView = MasterMietobjektMieterView.MasterView( x.xmaster )
        self._mobjView = MasterMietobjektMieterView.MobjView( x.xmobj )
        self._mieterView = MasterMietobjektMieterView.MieterView( x.xmieter )
        self._masterChanged = False
        self._mobjChanged = False
        self._mieterChanged = False
        self._createGui()

    def _createGui( self ):
        l = self._layout
        l.setVerticalSpacing( 15 )

        r, c = 0, 0
        l.addWidget( self._masterView, r, c )

        r += 1
        l.addWidget( self._mobjView, r, c )

        r += 1
        l.addWidget( self._mieterView, r, c)

    # MasterMietobjektMieterView
    def getMasterMietobjektMietertCopyWithChanges( self ) -> XMasterMietobjektMieter:
        xcopy: XMasterMietobjektMieter = copy.deepcopy(self._mastermietobjektmieter)
        self._guiToData(xcopy)
        return xcopy

    def _guiToData(self, x:XMasterMietobjektMieter):
        self._masterView.guiToData(x.xmaster)
        self._mobjView.guiToData(x.xmobj)
        self._mieterView.guiToData(x.xmieter)

    def applyChanges( self ):
        self._guiToData(self._mastermietobjektmieter)

    def getModel( self ):
        return self._mastermietobjektmieter

    @staticmethod
    def getPreferredWidth() -> int:
        return 1350

    @staticmethod
    def getPreferredSize() -> QSize:
        return QSize( MasterMietobjektMieterView.getPreferredWidth( ), 786 )


##################   MietobjektDialog   ######################
class MietobjektDialog( OkCancelDialog ):
    def __init__( self, view:MasterMietobjektMieterView, title:str= "" ):
        # OkDialog.__init__( self, title + " (nur Ansicht, Änderungen noch nicht möglich)" )
        OkCancelDialog.__init__( self, title  )
        self._view = view
        self.addWidget( view, 0 )
        # self.setOkButtonText( "Schließen (derzeit ohne Speichern)" )
        self.setOkButtonText( "OK" )

    ######################   MietobjektAuswahlView   #############################


class MietobjektAuswahlTableView(IccTableView):
    """
    Wird im MietobjektAuswahlDialog verwendet
    """

    def __init__(self):
        IccTableView.__init__(self)
        self.setAlternatingRowColors(True)
##################   TEST   TEST   TEST   #####################

def testMasterMietobjektMieterView():
    app = QApplication()
    x = XMasterMietobjektMieter()
    v = MasterMietobjektMieterView( x )
    v.show()
    # sz:QSize = v.size()
    # print( sz.width(), " ", sz.height() )
    # sz.setWidth(1350)
    v.resize( v.getPreferredSize() )
    app.exec_()

# def test():
#     def validate() -> bool:
#         print( "validate")
#         print( "mobj_id: ", x.mobj_id )
#         return True
#
#     x = createXMietobjektExt()
#     app = QApplication()
#     v = MasterMietobjektMieterView( x )
#     # v.save.connect( onSaveChanges )
#     # v.show()
#     dlg = MietobjektDialog( v, x.mobj_id )
#     dlg.setBeforeAcceptFunction( validate )
#     # dlg.exec_()
#     dlg.show()
#     app.exec_()

def testBackground():
    app = QApplication()
    v = QWidget()
    l = BaseGridLayout()
    v.setLayout( l )

    w = QWidget()
    hbl = QHBoxLayout()
    w.setLayout( hbl )
    w.setStyleSheet( "background: green;" )
    lbl = BaseLabel( "Ich bin ein Label" )
    hbl.addWidget( lbl, alignment=Qt.AlignLeft )
    lbl2 = FatLabel( "123" )
    hbl.addWidget( lbl2, alignment=Qt.AlignLeft )

    l.addWidget( w, 0, 0 )

    v.show()
    app.exec_()

def testHeader():
    app = QApplication()

    x = XMietobjektExt()
    x.master_id = 17
    x.master_name = "NK-Kleist"
    x.plz = "66538"
    x.ort = "Neunkirchen"
    x.strasse_hnr = "Klabautermannstraße 377"

    w = QWidget()
    l = BaseGridLayout()
    w.setLayout( l )
    mle = MultiLineEdit()
    mle.setReadOnly( True )
    mle.setStyleSheet( "background: green;" )
    txt = "Master-ID: " + str(x.master_id) + "\t" + "Master-Name: " + x.master_name
    mle.append( txt )
    mle.setAlignment( Qt.AlignCenter )
    mle.append( " " )
    txt = x.strasse_hnr + ", " + x.plz + " " + x.ort
    mle.append( txt )
    mle.setAlignment( Qt.AlignCenter )
    l.addWidget( mle, 0, 0, 1, 1 )  #, alignment=Qt.AlignCenter )

    mle2 = MultiLineEdit()
    html = "<html>Eine <b>Testzeile</b></html>"
    mle2.setHtml( html )
    mle2.setAlignment( Qt.AlignCenter )
    l.addWidget( mle2, 1, 0, 1, 1 )
    w.show()

    app.exec_()

if __name__ == "__main__":
    testMasterMietobjektMieterView()