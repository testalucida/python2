from tkinter import *
from anlagevframe import AnlageVFrame
from controller import Controller
from business import BusinessLogic

def main():
    root = Tk()
    root.title("Anlage V -- Dateneingabe und Erstellung")
    root.rowconfigure( 0, weight=1 )
    root.columnconfigure( 0, weight=1 )
    root.option_add('*Dialog.msg.font', 'Helvetica 11')
    frame:AnlageVFrame = AnlageVFrame( root )
    frame.grid( row=0, column=0, sticky="nswe", padx=3, pady=3 )

    busi:BusinessLogic = BusinessLogic()
    ctrl:Controller = Controller( frame, busi )
    ctrl.startWork()

    root.mainloop()

    busi.terminate()
    print( "Database closed successfully")

if __name__ == '__main__':
    main()
