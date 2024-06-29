import ftplib
import os
from typing import List

from mycrypt import EncryptDecrypt

class FtpIni:
    def __init__( self, ini_pathnfile:str ):
        """
        structure of ini file:
            server=nn.nn.nn.nnn
            remotepath=server path (not: file name) specifying the folder the local file is to be uploaded to
                        resp.the remote file to be downloaded is located
            localpath=local path (not: file name) specifying the folder the remote file is to be downloaded to
                        resp. the file to be uploaded is located
            key_file=path and name of the file containing the key (and only the key)
            enc_user_file=path and name of the file containing the encrypted user name (and only this item)
            enc_pwd_file=path and name of the file containing the encrypted password (and only that)
        :param ini_pathnfile: path and file to ftp ini file.
        """
        self._ini_pathnfile = ini_pathnfile  # path and name to ftp.ini file
        self._server: str = ""
        self._remotepath = ""
        self._localpath = ""
        self._key_file = ""
        self._enc_user_file = ""
        self._enc_pwd_file = ""
        self._readIniFile()

    def _readIniFile( self ):
        infos: dict = { }
        with open( self._ini_pathnfile ) as inifile:
            for line in inifile:
                parts = line.split( "=" )
                infos[parts[0]] = parts[1].rstrip()
        self._server = infos["server"]
        self._remotepath = infos["remotepath"]
        self._localpath = infos["localpath"]
        self._key_file = infos["key_file"]
        self._enc_user_file = infos["enc_user_file"]
        self._enc_pwd_file = infos["enc_pwd_file"]

    def getServer( self ) -> str:
        return self._server

    def getLocalPath( self ) -> str:
        return self._localpath

    def getRemotePath( self ) -> str:
        return self._remotepath

    def getUserAndPwd( self ) -> (str,str):
        crypt = EncryptDecrypt()
        key = crypt.getKey( self._key_file )
        user:bytes = crypt.getDecryptedFromFile( key, self._enc_user_file )
        pwd:bytes = crypt.getDecryptedFromFile( key, self._enc_pwd_file )
        return ( user.decode(), pwd.decode() )

class Ftp:
    def __init__( self, ftpIni:FtpIni ):
        self._ftpIni = ftpIni
        self._ftp: ftplib.FTP = None

    def connect( self ):
        """
        needs to be called before first up- or download
        :return:
        """
        self._ftp: ftplib.FTP = ftplib.FTP( self._ftpIni.getServer() )
        user_and_pwd = self._ftpIni.getUserAndPwd()
        self._ftp.login( user_and_pwd[0], user_and_pwd[1] )

    def quit( self ):
        """
        needs to be called after last up- or download
        :return:
        """
        self._ftp.quit()

    # def existsFile( self, remotefilename:str ) -> bool:
    #     """
    #     Checks if <remotefilenname> exists on the remote path set in self._ftpIni.
    #     Returns True if file exists else False
    #     :param remotefilename:
    #     :return:
    #     """
    #     path = self._ftpIni.getRemotePath()
    #     self._ftp.cwd( self._ftpIni.getRemotePath() )
    #     lst = self._ftp.nlst( )
    #     return remotefilename in lst

    def upload( self, localfilename:str, remotefilename:str ) -> None:
        """
        stores file <localfilename> from folder self._ftpIni.getLocalPath() as file <remotefilename> to
        folder self._ftpIni.getRemotePath()
        :param localfilename:
        :param remotefilename:
        :return:
        """
        io = open( self._ftpIni.getLocalPath() + localfilename, 'rb' )
        self._ftp.cwd( self._ftpIni.getRemotePath() )
        self._ftp.storbinary( 'STOR ' + remotefilename, io )

    def download( self, remotefilename:str, localfilename:str ) -> None:
        """
        Downloads file <remotefilename> in folder self._ftpIni.getRemotePath() as file <localfilename>
        to folder self._ftpIni.getLocalPath()
        Maybe the server file doesn't exist yet, that might be not an error but probably a first access problem.
        The downloaded file is named xxx.tmp and only if no error occurred it will be renamed.
        1.) download <remotefilename> and save it as <localfilename.tmp>
        2.) if exists <localfilename.sav>: delete it
        3.) if exists <localfilename>: rename it to <localfilename.sav>
        4.) rename <localfilename.tmp> to localfilename
        """
        remotepathnfile = self._ftpIni.getRemotePath() + remotefilename
        localpathnfile = self._ftpIni.getLocalPath() + localfilename
        try:
            tmpfile = localpathnfile + ".tmp"
            savfile = localpathnfile + ".sav"
            # step 1:
            try:
                tmpfileIO = open( tmpfile, 'wb' )
            except Exception as ex:
                msg = "Can't open or create " + tmpfile + " for writing:\n\t" + str(ex)
                raise Exception( msg ) from ex
            self._ftp.retrbinary( cmd="RETR " + remotepathnfile, callback=tmpfileIO.write )
            # still here - download ok. Save the old file, rename the downloaded one.
            try:
                # step 2:
                if os.path.exists( savfile ):
                    os.remove( savfile )
            except Exception as x:
                # no problem - there was no .sav file
                print( "ftp.download(): couldn't delete %s:\n%s\nProceeding." % (savfile, str( x ) ) )
            try:
                if os.path.exists( localpathnfile ):
                    os.rename( localpathnfile, savfile )
            except Exception as x:
                print( "ftp.download(): couldn't rename %s to %s:\n%s" % ( localpathnfile, savfile, str( x ) ) )
                raise x

            try:
                os.rename( tmpfile, localpathnfile )
            except Exception as x:
                print( "ftp.download(): couldn't rename %s to %s:\n%s" % (tmpfile, localpathnfile, str( x ) ) )
                raise x
        except Exception as x:
            # delete (empty) tmp file:
            os.remove( tmpfile )
            raise( x )
            #raise( Exception( "ftp.download(): Download %s to %s failed:\n%s" % ( remotepathnfile, localpathnfile, str( x ) ) ) )

    def existsFile(self, filename:str) -> bool:
        """
        checks if given filename exists in specified remotePath (see file ftpIni)
        :param filename: filename to check
        :return: true if filename exists on remotePath else False
        """
        # set remote path as current work directory
        def check(entry):
            nonlocal file_exists
            if entry.endswith(filename):
                file_exists = True
        pwd = self._ftp.pwd()
        self._ftp.cwd(self._ftpIni.getRemotePath())
        file_exists = False
        self._ftp.retrlines('LIST', check)
        self._ftp.cwd( pwd )
        return file_exists

    def deleteFile(self, filename:str) -> None:
        """
        deletes file <filename> from remotePath (see file ftpIni).
        Raises Exception if operation is not successful.
        :param filename: name of the file to delete
        :return: text of response
        """
        pathnfile = self._ftpIni.getRemotePath() + filename
        self._ftp.delete( pathnfile )

    def rename( self, from_name:str, to_name:str ) -> None:
        """
        renames a file on the server located on the specified remote path.
        Throws an exception if operation is not successful.
        :param from_name:
        :param to_name:
        :return: an empty string if successful, else an error message
        """
        from_pathnfile = self._ftpIni.getRemotePath() + from_name
        to_pathnfile = self._ftpIni.getRemotePath() + to_name
        self._ftp.rename( from_pathnfile, to_pathnfile )

    def getFilenames( self ) -> List[str]:
        """
        Returns a list of filenames in specified remotePath (see file ftpIni).
        No folder names are returned.
        :return:
        """
        file_list = list()
        pwd = self._ftp.pwd()
        self._ftp.cwd( self._ftpIni.getRemotePath( ) )
        gen_obj = self._ftp.mlsd( facts=["type"])
        for tpl in gen_obj:
            dic = tpl[1]
            if dic["type"] not in ( "dir", "pdir", "cdir" ):
                file_list.append( tpl[0] )
        self._ftp.cwd( pwd )
        return file_list

def testUpAndDownload():
    ftpIni = FtpIni( "../ImmoControlCenter/v2/icc/ftp.ini" )
    ftp = Ftp( ftpIni )
    ftp.connect()
    files = ftp.getFilenames()
    print( files )
    # try:
    #     ftp.delete("kannweg2")
    # except Exception as ex:
    #     print( str(ex) )
    # exists = ftp.exists( "immo.db" )
    # if exists:
    #     msg = ftp.rename( "immo.db", "immo.db.locked" )str
    # exists = ftp.exists( "immo.db.locked" )
    # if exists:
    #     msg = ftp.rename( "immo.db.locked", "immo.db"  )
    # print(exists)
    # # ftp.upload( "immokannweg", "immokannweg" )
    # msg = ftp.delete( "immokannweg" )
    # print( msg )
    # ftp.download( "immo.db", "immokannweg" )
    ftp.quit()

if __name__ == "__main__":
    testUpAndDownload()
