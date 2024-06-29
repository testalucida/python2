
class XAnlageVKopfdaten:
    def __init__(self):
        self.stpfl_id: int = 0
        self.objekt_id: int = 0
        self.objekt_angeschafft_am: str = ""  # TTMMJJJJ
        self.stpfl_name: str = ""
        self.stpfl_vorname: str = ""
        self.stpfl_steuernummer: str = ""
        self.objekt_str_hnr: str = ""
        self.objekt_plz: str = ""
        self.objekt_ort: str = ""
        self.einh_wert_az: str = ""

class XErhaltungsaufwand:
    def __init__(self):
        self.voll_abziehbar:int = 0
        self.zu_verteilen_gesamt_neu:int = 0 #Gesamtsumme des zu verteilenden Aufwands, der im Veranl.jahr neu entstanden ist
        self.verteilen_auf_jahre:int = 0     #auf wieviele Jahre diese Gesamtsumme verteilt werden soll (max 5)
        self.abziehbar_veranljahr:int = 0    #wieviel davon im Veranl.jahr abgezogen werden soll
        self.abziehbar_veranljahr_minus_1:int = 0
        self.abziehbar_veranljahr_minus_2: int = 0
        self.abziehbar_veranljahr_minus_3: int = 0
        self.abziehbar_veranljahr_minus_4: int = 0


class XAnlageVData:
    def __init__(self):
        self.stpfl_id:int = 0
        self.objekt_id:int = 0
        self.objekt_angeschafft_am:str = ""  # TTMMJJJJ
        self.veranl_jahr = 0
        self.stpfl_name:str = ""
        self.stpfl_vorname:str = ""
        self.stpfl_steuernummer:str = ""
        self.objekt_str_hnr:str = ""
        self.objekt_plz:str = ""
        self.objekt_ort:str = ""
        self.qm:int = 0
        self.nettomiete_eg:int = 0
        self.nettomiete_og1:int = 0
        self.nettomiete_og2:int = 0
        self.nettomiete_wg:int = 0  #weitere geschosse
        self.nettomiete_gesamt:int = 0
        self.nk_voraus:int = 0      #NK: Jahressumme Vorauszahlungen
        self.nk_abrech_vj:int = 0   #NK: Abrechnung aus dem Vorjahr; kann pos. od. neg. sein
        self.grundsteuer:int = 0
        self.zurechng_ueberschuss_stpfl_prozent:float = 0.0 #zu wieviel Prozent der Überschuss auf den Stpfl entfällt; Rest auf Ehepartner
        self.afa_linear:bool = True # wenn False, wird "degressiv" angenommen
        self.afa_prozent:float = 2.5
        self.afa_wie_vj:bool = True
        self.afa:int  = 0           #AfA-Betrag
        self.geldbeschaff_kosten:int = 0 #Z. 38: Schätz-, Notar-, Grundbuchgebühren
        self.erhalt_aufw:XErhaltungsaufwand = XErhaltungsaufwand()
        self.hg_voraus_ohne_rueckl:int = 0 #Summe der Jahres-Hausgeld-Vorauszahlungen ohne Rücklagen
        self.hg_abrech_vj:int = 0 # Abrechnung aus dem Vorjahr; kann pos. od. neg. sein


