import os
import sys

from PySide2.QtCore import QObject, QEvent, Qt, QPoint
from PySide2.QtGui import QPixmap, QIcon, QCursor, QGuiApplication, QScreen
from PySide2.QtWidgets import QApplication, QSplashScreen, QWidget

sys.path.append( "../" )
sys.path.append( "../common" )
print( "sys.path: ", sys.path )
from base.messagebox import ErrorBox
from ftp import FtpIni, Ftp
from controller.maincontroller import MainController

def showSplash( app:QApplication ):
    pixmap = QPixmap( "../images/bulle2.png" )
    splash = QSplashScreen( pixmap )
    # obsolete:
    # desktop = app.desktop()
    # scrn = desktop.screenNumber( QCursor.pos() )
    # currDesktopCenter = desktop.availableGeometry( scrn).center()
    # instead:
    #scrn = QGuiApplication.primaryScreen()
    point:QPoint = QCursor.pos()
    screen:QScreen = QGuiApplication.screenAt( point )
    currDesktopCenter = screen.availableGeometry().center()
    splash.move( currDesktopCenter - splash.rect().center() )
    splash.show()
    app.processEvents()
    return splash

def runningInDev() -> bool:
    scriptdir = os.path.dirname( os.path.realpath( __file__ ) )
    return True if "python" in scriptdir else False

def downloadDatabase():
    ftpIni = FtpIni( "./ftp.ini" )
    ftp = Ftp( ftpIni )
    ftp.connect()
    if ftp.existsFile( "db_in_use" ):
        if not runningInDev():
            ftp.quit()
            raise Exception( "Datenbank wird von einem anderen Prozess genutzt.\nSie kann nicht heruntergeladen werden.")
    ftp.download( "invest.db", "invest.db" )
    ftp.upload( "db_in_use", "db_in_use" )
    ftp.quit()

def uploadDatabase():
    ftpIni = FtpIni( "./ftp.ini" )
    ftp = Ftp( ftpIni )
    ftp.connect()
    ftp.upload( "invest.db", "invest.db" )
    ftp.deleteFile( "db_in_use" )
    ftp.quit()

class ShutDownFilter( QObject ):
    def __init__( self, win: QWidget, app: QApplication ):
        QObject.__init__( self )
        self._win = win
        self._app = app

    def eventFilter( self, obj, event ) -> bool:
        if obj is self._win and event.type() == QEvent.Close:
            self.quit_app()
            event.ignore()
            return True
        return super( ShutDownFilter, self ).eventFilter( obj, event )

    def quit_app( self ):
        try:
            uploadDatabase()
        except Exception as ex:
            print( "Upload der Datenbank gescheitert.\nAnwendung wird nicht gestartet." )
            box = ErrorBox( "Upload der Datenbank nicht möglich", str( ex ),
                            "Datenbank muss vor dem nächsten Start manuell hochgeladen werden!" )
            box.exec_()
            return -1
        self._win.removeEventFilter( self )
        self._app.quit()


def main():
    app = QApplication( sys.argv )
    splash = showSplash( app )
    splash.setCursor( Qt.WaitCursor )
    try:
        app.processEvents()
        downloadDatabase()
        app.processEvents()
    except Exception as ex:
        print( "Download der Datenbank gescheitert.\nAnwendung wird nicht gestartet." )
        box = ErrorBox( "Starten der Anwendung nicht möglich", str( ex ), "Anwendung wird  nicht gestartet." )
        box.exec_()
        return -1
    ctrl = MainController()
    app.processEvents()
    win = ctrl.createMainWindow()
    shutDownFilter = ShutDownFilter( win, app )
    win.installEventFilter( shutDownFilter )
    win.show()
    splash.finish( win )
    icon = QIcon( "../images/bulle2.png" )
    app.setWindowIcon( icon )
    app.exec_()

if __name__ == "__main__":
    main()

