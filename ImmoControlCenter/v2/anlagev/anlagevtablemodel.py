from typing import Dict, Any

from PySide2.QtCore import QModelIndex, Qt
from PySide2.QtGui import QBrush, QColor, QFont

from base.basetablemodel import BaseTableModel
from base.interfaces import XBase


class XAnlageV( XBase ):
    def __init__( self, valuedict:Dict=None ):
        XBase.__init__( self, valuedict )
        # Einnahmen
        self.vj = 0
        self.master_name = ""
        self.anzahlMonate = 0
        self.bruttoMiete = 0 # nur Info
        self.nettoMiete = 0
        self.nkv = 0
        self.nka = 0 # Jahr vor Vj
        # Werbungskosten
        self.afa = 0
        self.erhaltg_voll = 0
        self.verteil_aufwand_im_vj_angefallen = 0 # nur relevant, wenn eine zu verteilende Aufwendg. im Vj getätigt wurde
        self.erhaltg_anteil_vj = 0
        self.erhaltg_anteil_vjminus1 = 0
        self.erhaltg_anteil_vjminus2 = 0
        self.erhaltg_anteil_vjminus3 = 0
        self.erhaltg_anteil_vjminus4 = 0
        self.erhaltg_anteile_summe = 0
        self.entnahme_rue = 0
        self.grundsteuer = 0
        self.versicherungen = 0
        self.hgv_netto = 0  # nur bei ET-Wohnungen
        self.hga = 0 # Jahr vor Vj -- nur bei ET-Wohnungen
        self.divAllgHk = 0 # bei eig. Häusern: Str.reinigg., Niederschlagswasser, Wasser, Strom Gas, Schlotfeger...
        self.reisekosten = 0
        self.sonstige = 0
        if valuedict:
            self.setFromDict( valuedict )

    def getSummeEinnahmen( self ):
        return self.nettoMiete + self.nkv + self.nka

    def getSummeErhaltungsaufwendungen( self ):
        return self.erhaltg_voll + \
               self.erhaltg_anteil_vj + self.erhaltg_anteil_vjminus1 + \
               self.erhaltg_anteil_vjminus2 + self.erhaltg_anteil_vjminus3 + self.erhaltg_anteil_vjminus4 + \
               self.entnahme_rue

    def getSummeVollAbziehbarerErhaltAufwand( self ):
        return self.erhaltg_voll + self.entnahme_rue

    def getSummeNebenkosten( self ):
        return self.nkv + self.nka

    def getSummeAllgHauskosten( self ):
        return self.grundsteuer + self.versicherungen + self.divAllgHk + self.hgv_netto + self.hga

    def getSummeSonstige( self ):
        return self.reisekosten + self.sonstige

    def getSummeWerbungskosten( self ):
        return self.afa + self.getSummeErhaltungsaufwendungen() + self.getSummeAllgHauskosten() + self.getSummeSonstige()

    def getUeberschuss( self ):
        return self.getSummeEinnahmen() + self.getSummeWerbungskosten()

####################################################################
class AnlageVTableModel( BaseTableModel ):
    headers = ("Abschnitt", "Unter-Abschnitt", "Position", "Betrag", "Form.-\nZeile", "Form.-\nEintrag" )
    lightGray = QBrush( Qt.lightGray )
    darkGray = QBrush( Qt.darkGray )
    green = QBrush( QColor( "#76CB4C" ) )
    abschnittNameFont = QFont( "Arial", 12, QFont.Bold )
    abschnittNameCells = ((0, 0), (9, 0), (35,0))
    summeFont = QFont( "Arial", 10, -1, True)
    summenCells = ((7, 0), (33,0), (6, 1),  (14, 1), (27, 1), (31, 1))
    colFormZeile = 4
    colFormEintrag = 5

    def __init__( self, x:XAnlageV ):
        BaseTableModel.__init__( self )
        self._x = x
        self._boldFont13 = QFont( "Arial", 13, QFont.Bold )
        self._cells = (
            #("Einnahmen\n(%d Monate - brutto: %d)" % (x.anzahlMonate, x.bruttoMiete), ),
            ("Einnahmen",),
            ("", "Brutto-ME (%d Monate)" % x.anzahlMonate, "", x.bruttoMiete ),
            ("", "Netto-ME", "", "", 9, x.nettoMiete, "", "", ""),
            ( "", "Nebenkosten" ),
            ("", "", "NKV", x.nkv ),
            ("", "", "NKA %d" % (x.vj - 1), x.nka ),
            ("", "Summe Nebenkosten", "", "", 13, x.getSummeNebenkosten() ),
            ( "Summe Einnahmen", "", "", "", 21, x.getSummeEinnahmen() ),
            ("",),
            ("Werbungskosten", ),
            ("", "kalkulatorisch", "AfA", "", 33, x.afa),
            ("", ),
            ("", "Erhalt.aufwand, voll abziehbar", "", x.erhaltg_voll ),
            ("", "Entnahme Rücklagen", "", x.entnahme_rue, "", ""),
            ("", "Summe voll abziehb. Erhalt.aufw.", "", "", 40, x.getSummeVollAbziehbarerErhaltAufwand() ),
            ("", "Erhalt.aufwand, zu verteilen",  "Gesamtaufwand %d" % x.vj, x.verteil_aufwand_im_vj_angefallen ),
            ("", "", "davon in %d abzuziehen" % x.vj, "", 42, x.erhaltg_anteil_vj ),
            ("", "", "aus %d" % (x.vj - 4), "", 43, x.erhaltg_anteil_vjminus4),
            ("", "", "aus %d" % (x.vj - 3), "", 44, x.erhaltg_anteil_vjminus3),
            ("", "", "aus %d" % (x.vj - 2), "", 45, x.erhaltg_anteil_vjminus2),
            ("", "", "aus %d" % (x.vj - 1), "", 46, x.erhaltg_anteil_vjminus1),
            ("",),
            ("", "Allg. Hauskosten", "Grundsteuer", x.grundsteuer),
            ("", "", "Versicherungen", x.versicherungen),
            ("", "", "Strom, Gas, Wasser, Öl etc.", x.divAllgHk),
            ("", "", "HGV ohne RüZuFü", x.hgv_netto),
            ("", "", "HGA %d" % (x.vj - 1), x.hga),
            ("", "Summe Allg. Hauskosten", "", "", 47, x.getSummeAllgHauskosten()),
            ("",),
            ("", "Sonstige Kosten", "Reisen", x.reisekosten),
            ("", "", "Sonstige", x.sonstige),
            ("", "Summe Sonstige Kosten", "", "", 50, x.getSummeSonstige()),
            ("",),
            ("Summe Werbungskosten", "", "", "", 51, x.getSummeWerbungskosten(), ""),
            ("",),
            ("Überschuss", "", "", "", 23, x.getUeberschuss()),
        )

    def getMasterName( self ) -> str:
        return self._x.master_name

    def getUeberschuss( self ) -> int:
        return self._x.getUeberschuss()

    def rowCount( self, parent:QModelIndex=None ) -> int:
        return len( self._cells )

    def columnCount( self, parent:QModelIndex=None ) -> int:
        return len( AnlageVTableModel.headers )

    def headerData(self, col, orientation, role=None):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return AnlageVTableModel.headers[col]
            if role == Qt.BackgroundRole:
                if self.headerBrush:
                    return self.headerBrush
        return None

    def getValue( self, indexrow: int, indexcolumn: int ) -> Any:
        try:
            return self._cells[indexrow][indexcolumn]
        except:
            return ""

    def getBackgroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        val = self.getValue( indexrow, indexcolumn )
        if not val:
            if indexrow < 7:
                return self.green
            elif indexrow == self.rowCount() - 1:
                return self.yellow
            else:
                return self.lightGray

    def getForegroundBrush( self, indexrow: int, indexcolumn: int ) -> QBrush or None:
        brush = super().getForegroundBrush( indexrow, indexcolumn )
        if not brush and indexcolumn == self.colFormZeile:
            return self.darkGreyBrush
        return brush

    def getFont( self, indexrow: int, indexcolumn: int ) -> QFont or None:
        if indexcolumn == self.colFormZeile:
            return self.boldFont
        if indexcolumn == self.colFormEintrag:
            val = self.getValue( indexrow, indexcolumn )
            if val != 0:
                return self.boldFont
        if (indexrow, indexcolumn ) in self.abschnittNameCells:
            return self.abschnittNameFont
        if (indexrow, indexcolumn) in self.summenCells:
            return self.summeFont
        return None

    def getAlignment( self, indexrow:int, indexcolumn:int ) -> Qt.Alignment or None:
        align = super().getAlignment( indexrow, indexcolumn )
        if (indexrow, indexcolumn) in self.summenCells:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return align
