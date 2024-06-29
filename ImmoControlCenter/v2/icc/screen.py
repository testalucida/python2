from PySide2.QtWidgets import QApplication

screenwidth = 0
screenheight = 0

def setScreenSize( app:QApplication ):
    screen = app.primaryScreen()
    #size = screen.size()
    rect = screen.availableGeometry()
    global screenwidth
    screenwidth = rect.width()
    global screenheight
    screenheight = rect.height()

def getScreenWidth():
    global screenwidth
    return screenwidth



