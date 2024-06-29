from datetime import datetime
import os
from typing import List

from ftp import Ftp, FtpIni

class DatabaseTransfer:
    """
    Die Klasse behandelt die von einer Anwendung benutzte Datenbank
    bei Anwendungsstart und -ende.
    Speicherort der Datenbank ist das in der ftpini-Datei spezifizierte Server-Laufwerk.
    Bei Anwendungsstart wird die Datenbank per FTP heruntergeladen
    und in einem spezifizierten lokalen Verzeichnis gespeichert.
    Bei Anwendungsende wird die Datenbank wieder auf den Server
    hochgeladen.
    Nach dem Download wird die serverseitige Datenbank umbenannt (es wird
    der Download-Timestamp angehöngt),
    was verhindert, dass sie versehentlich auf einen anderen Rechner
    heruntergeladen werden kann.
    Nach dem Upload bleibt die alte, umbenannte Datenbank bestehen.
    Es gibt dann also serverseitig die gerade benutzte hochgeladene Datenbank mit dem
    Originalnamen und 1-CNT_BACKUPS alte Datenbanken mit Umbenennungen.
    Sollten mehr als CNT_BACKUPS alte Versionen existieren, werden die CNT_BACKUPS+1. bis n-te gelöscht.
    Die bis gerade benutzte lokale Datenbank bleibt bestehen, wird aber nach dem gleichen
    Muster umbenannt wie serverseitig.
    Auch lokal werden nur CNT_BACKUPS Sicherungsversionen gehalten, die übrigen werden gelöscht.
    """
    CNT_BACKUPS = 5

    def __init__( self, remote_db_name:str, local_db_name:str,  ftp_ini_pathnfile:str ):
        self._remote_db_name = remote_db_name
        self._local_db_name = local_db_name
        self._ftp_ini = FtpIni( ftp_ini_pathnfile )
        self._ftp = Ftp( self._ftp_ini )
        self._ftp.connect()

    def download_db( self ):
        """
        Downloads the specified database from server and renames the serverside original file.
        :return:
        """
        self._ftp.download( self._remote_db_name, self._local_db_name )
        self._ftp.rename( self._remote_db_name, self._remote_db_name + self._getEnding( ) )

    def upload_db( self ):
        """
        Uploads the specified database from local path to remote path and deletes both
        serverside and local copies, as far as they exceed the maximal number (CNT_BACKUPS)
        :return:
        """
        self._ftp.upload( self._local_db_name, self._remote_db_name )
        # delete serverside backup files if there are more than 5:
        self._check_delete_serverside_backups( )
        # rename local database
        local_pathnfile = self._ftp_ini.getLocalPath() + self._local_db_name
        os.rename( local_pathnfile, local_pathnfile + self._getEnding() )
        # delete local backup files if there are more than CNT_BACKUPS:
        self._check_delete_local_backups()

    def _check_delete_serverside_backups( self ):
        """
        Gets all files from remotePath, filters for files with database names
        (original one and backup copies) and deletes oldest copies if there are
        more than CNT_BACKUPS
        :return:
        """
        files:List[str] = self._ftp.getFilenames()
        backups = self._get_sorted_backups_from_files( self._remote_db_name, files )
        to_delete = len( backups ) - self.CNT_BACKUPS
        # delete oldest backups in backups from remote folder:
        for n in range( 0, to_delete ):
            self._ftp.delete( backups[n] )

    def _check_delete_local_backups( self ):
        """
        Gets all files from localPath, filters for files with database names
        (original one and backup copies) and deletes oldest copies if there are
        more than CNT_BACKUPS
        :return:
        """
        files:List[str] = os.listdir( path=self._ftp_ini.getLocalPath() )
        backups = self._get_sorted_backups_from_files( self._local_db_name, files )
        to_delete = len( backups ) - self.CNT_BACKUPS
        localpath = self._ftp_ini.getLocalPath()
        for n in range( 0, to_delete ):
            pathnfile = localpath + backups[n]
            if os.path.isfile( pathnfile ):
                os.remove( pathnfile )

    def _get_sorted_backups_from_files( self, db_name:str, files:List[str] ) -> List[str]:
        backups = list( )
        for f in files:
            if f.startswith( db_name ) and not f.endswith( ".db" ):
                backups.append( f )
        backups.sort( )
        return backups

    @staticmethod
    def _getEnding() -> str:
        return "." + datetime.now().strftime( "%Y-%m-%d:%H.%M.%S.%f" )

###########################################################
def test1():
    dbt = DatabaseTransfer( "immo.db", "immo.db", "../ImmoControlCenter/v2/icc/ftp.ini" )
    #msg = dbt.download_db()
    dbt._check_delete_local_backups()

if __name__ == "__main__":
    test1()