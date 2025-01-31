# DarkModePalette.PY    2023-04-27 1:14:44 PM
# 
# Complete application based on the "Dark Theme" setup code on pages 233-234 
#   of 'Create GUI Applications with Python Qt6 (PySide6 Edition) V2.0 2021, M. Fitzpatrick'
#   See code example 'palette_dark_widgets.py' in the 'themes' folder.
# Demonstrates an overall visual theme change.
# Note: Code "app.setStyle('Fusion')" is mandatory (on Windows) to produce dark text backgrounds.


from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt                   # Named colors.

import sys

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

#------------------------------------------------

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dark_Mode.PY Widgets App")

        layout = QVBoxLayout()
        widgets = [
            QCheckBox,
            QComboBox,
            QDateEdit,
            QDateTimeEdit,
            QDial,
            QDoubleSpinBox,
            QFontComboBox,
            QLCDNumber,
            QLabel,
            QLineEdit,
            QProgressBar,
            QPushButton,
            QRadioButton,
            QSlider,
            QSpinBox,
            QTimeEdit,
        ]
        
        for w in widgets:
            widget = w( self )
            widget.setAutoFillBackground( True )    # Doesn't appear to do anything (on MSW, anyway)!
            layout.addWidget( widget )
       
        widget = QWidget()
        widget.setLayout(layout)

        # Set the central widget of the Window to expand it 
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

#end MainWindow class

def get_darkModePalette( app=None ) :
    
    darkPalette = app.palette()
    darkPalette.setColor( QPalette.Window, QColor( 53, 53, 53 ) )
    darkPalette.setColor( QPalette.WindowText, Qt.white )
    darkPalette.setColor( QPalette.Disabled, QPalette.WindowText, QColor( 127, 127, 127 ) )
    darkPalette.setColor( QPalette.Base, QColor( 42, 42, 42 ) )
    darkPalette.setColor( QPalette.AlternateBase, QColor( 66, 66, 66 ) )
    darkPalette.setColor( QPalette.ToolTipBase, QColor( 53, 53, 53 ) )
    darkPalette.setColor( QPalette.ToolTipText, Qt.white )
    darkPalette.setColor( QPalette.Text, Qt.white )
    darkPalette.setColor( QPalette.Disabled, QPalette.Text, QColor( 127, 127, 127 ) )
    darkPalette.setColor( QPalette.Dark, QColor( 35, 35, 35 ) )
    darkPalette.setColor( QPalette.Shadow, QColor( 20, 20, 20 ) )
    darkPalette.setColor( QPalette.Button, QColor( 53, 53, 53 ) )
    darkPalette.setColor( QPalette.ButtonText, Qt.white )
    darkPalette.setColor( QPalette.Disabled, QPalette.ButtonText, QColor( 127, 127, 127 ) )
    darkPalette.setColor( QPalette.BrightText, Qt.red )
    darkPalette.setColor( QPalette.Link, QColor( 42, 130, 218 ) )
    darkPalette.setColor( QPalette.Highlight, QColor( 42, 130, 218 ) )
    darkPalette.setColor( QPalette.Disabled, QPalette.Highlight, QColor( 80, 80, 80 ) )
    darkPalette.setColor( QPalette.HighlightedText, Qt.white )
    darkPalette.setColor( QPalette.Disabled, QPalette.HighlightedText, QColor( 127, 127, 127 ), )
    
    return darkPalette
    
#end get_darkModePalette def

#================================================

app = QApplication( sys.argv + ['-platform', 'windows:darkmode=2'] )
app.setStyle( 'Fusion' )
app.setPalette( get_darkModePalette( app ) )

mainWindow = MainWindow()  # Replace with your custom mainwindow.
mainWindow.setGeometry(500, 100, 300, 625)
mainWindow.show()

sys.exit( app.exec() )
