import os

ROOT_DIR = os.path.dirname( os.path.abspath( __file__ ) )
print( ROOT_DIR )
#ROOT_DIR = "/home/martin/Vermietung/ImmoControlCenter"  # gewaltsames Umstellen auf die Release-DB
DATABASE_DIR = ROOT_DIR
DATABASE = ROOT_DIR + "/immo.db"
ICON_DIR = ROOT_DIR + "/images/"
DATENUEBERNAHME_DIR = ROOT_DIR