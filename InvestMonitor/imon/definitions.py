import os

from imon.enums import Period, Interval, InfoPanelOrder

ROOT_DIR = os.path.dirname( os.path.abspath( __file__ ) )
print( ROOT_DIR )
DATABASE_DIR = ROOT_DIR
DATABASE = ROOT_DIR + "/invest.db"
ICON_DIR = ROOT_DIR + "/images/"

DEFAULT_PERIOD = Period.oneYear
DEFAULT_INTERVAL = Interval.fiveDays
DEFAULT_INFOPANEL_ORDER = InfoPanelOrder.DeltaKursAsc