import os
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import QAbstractTableModel, Signal, QModelIndex, QPoint, Qt, QDate
from PySide2.QtGui import QMouseEvent, QFont, QIcon, QKeySequence
from PySide2.QtWidgets import QAbstractScrollArea, QTableView, QAbstractItemView, QHeaderView, QHBoxLayout, QVBoxLayout, QCalendarWidget
from PySide2.QtWidgets import QDialog, QGridLayout, QBoxLayout, QPushButton, QLineEdit, QLabel, QWidget, QAction, QSizePolicy, QComboBox
from PySide2.QtWidgets import QMessageBox
from iconfactory import IconFactory
# from customcalendar import SmartDateEdit  -- circular import!