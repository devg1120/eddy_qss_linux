#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import platform
import os
import sys
#import jnius_config
from PySide6.QtWidgets import QStyleFactory
from eddy.core.functions.path import expandPath

_LINUX = sys.platform.startswith('linux')
_MACOS = sys.platform.startswith('darwin')
_WIN32 = sys.platform.startswith('win32')

#############################################
# BEGIN JVM SETUP
#################################

#if os.path.isdir(expandPath('@resources/java/')):
#    os.environ['JAVA_HOME'] = expandPath('@resources/java/')
#
#if _WIN32:
#    path = os.getenv('Path', '')
#    path = path.split(os.pathsep)
#    path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin', 'client'))
#    os.environ['Path'] = os.pathsep.join(path)
#
#classpath = []
#resources = expandPath('@resources/lib/')
#for name in os.listdir(resources):
#    path = os.path.join(resources, name)
#    if os.path.isfile(path):
#        classpath.append(path)

#jnius_config.add_options('-ea', '-Xmx512m')
#jnius_config.set_classpath(*classpath)

#############################################
# BEGIN ENVIRONMENT SPECIFIC SETUP
#################################

if _LINUX:
    os.environ['LD_LIBRARY_PATH'] = expandPath('@root/')

if hasattr(sys, 'frozen'):
    os.environ['REQUESTS_CA_BUNDLE'] = expandPath('@root/cacert.pem')


from PySide6.QtCore import Qt
from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets


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


from argparse import ArgumentParser
#from sip import SIP_VERSION_STR

from eddy import APPNAME, COPYRIGHT, VERSION, BUG_TRACKER
from eddy.core.application import Eddy
from eddy.core.functions.misc import format_exception
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger

from eddy.ui import fonts_rc
from eddy.ui import images_rc


app = None
msgbox = None


LOGGER = getLogger()


def base_except_hook(exc_type, exc_value, exc_traceback):
    """
    Used to handle all uncaught exceptions.
    :type exc_type: class
    :type exc_value: Exception
    :type exc_traceback: Traceback
    """
    if issubclass(exc_type, KeyboardInterrupt):
        app.quit()
    else:
        global msgbox
        if not msgbox:
            LOGGER.critical(format_exception(exc_value))
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QPixmap(':/images/eddy-sad'))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Fatal error!')
            msgbox.setText('This is embarrassing ...\n\n' \
            'A critical error has just occurred. {0} will continue to work, ' \
            'however a reboot is highly recommended.'.format(APPNAME))
            msgbox.setInformativeText('If the problem persists you can '
            '<a href="{0}">submit a bug report</a>.'.format(BUG_TRACKER))
            msgbox.setDetailedText(format_exception(exc_value))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Ok)
            buttonOk = msgbox.button(QtWidgets.QMessageBox.Ok)
            buttonOk.setText('Close')
            buttonQuit = msgbox.button(QtWidgets.QMessageBox.Close)
            buttonQuit.setText('Quit {0}'.format(APPNAME))
            connect(buttonOk.clicked, msgbox.close)
            connect(buttonQuit.clicked, app.quit)
            # noinspection PyArgumentList
            QtWidgets.QApplication.beep()
            msgbox.exec()
            msgbox = None


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

def main():
    """
    Application entry point.
    """
    parser = ArgumentParser()
    parser.add_argument('--nosplash', dest='nosplash', action='store_true')
    parser.add_argument('--tests', dest='tests', action='store_true')
    parser.add_argument('--open', dest='open', default=None)

    sys.excepthook = base_except_hook

    options, _ = parser.parse_known_args(args=sys.argv)

    global app
    app = Eddy(options, sys.argv)
    if app.isRunning():
        sys.exit(0)

    print(QStyleFactory.keys())
    #app.setStyle("windows11")
    #app.setStyle("windowsvista")
    #app.setStyle("Windows")
    app.setStyle("Fusion")
    #app.setPalette( get_darkModePalette( app ) )
    #app.setStyleSheet("QToolBar {background:#ffffff ; }")
    app.setStyleSheet("""
     QComboBox { background: pink; }
     QListView { background: red;  }

    """)


    LOGGER.separator(separator='-')
    LOGGER.frame('%s v%s', APPNAME, VERSION, separator='|')
    LOGGER.frame(COPYRIGHT, separator='|')
    LOGGER.separator(separator='-')
    LOGGER.frame('OS: %s %s', platform.system(), platform.release(), separator='|')
    LOGGER.frame('Python version: %s', platform.python_version(), separator='|')
    #LOGGER.frame('Qt version: %s', QtCore.QT_VERSION_STR, separator='|')
    #LOGGER.frame('PyQt version: %s', Qt.PYQT_VERSION_STR, separator='|')
    #LOGGER.frame('SIP version: %s', SIP_VERSION_STR, separator='|')
    LOGGER.separator(separator='-')

    app.configure(options)
    app.start(options)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
