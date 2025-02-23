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


import os
import sys
import textwrap

from collections import OrderedDict

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from eddy import APPNAME, DIAG_HOME, GRAPHOL_HOME
from eddy import ORGANIZATION, VERSION, WORKSPACE
from eddy.core.clipboard import Clipboard
from eddy.core.commands.common import CommandComposeAxiom
from eddy.core.commands.common import CommandItemsRemove
from eddy.core.commands.common import CommandItemsTranslate
from eddy.core.commands.common import CommandSnapItemsToGrid
from eddy.core.commands.diagram import CommandDiagramAdd
from eddy.core.commands.diagram import CommandDiagramRemove
from eddy.core.commands.diagram import CommandDiagramRename
from eddy.core.commands.edges import CommandEdgeBreakpointRemove
from eddy.core.commands.edges import CommandEdgeSwap
from eddy.core.commands.labels import CommandLabelMove
from eddy.core.commands.labels import CommandLabelChange
from eddy.core.commands.nodes import CommandNodeSwitchTo
from eddy.core.commands.nodes import CommandNodeSetBrush
from eddy.core.commands.nodes import CommandNodeSetDepth
from eddy.core.commands.project import CommandProjectSetProfile
from eddy.core.common import HasActionSystem
from eddy.core.common import HasDiagramExportSystem
from eddy.core.common import HasDiagramLoadSystem
from eddy.core.common import HasMenuSystem
from eddy.core.common import HasNotificationSystem
from eddy.core.common import HasOntologyExportSystem
from eddy.core.common import HasOntologyLoadSystem
from eddy.core.common import HasPluginSystem
from eddy.core.common import HasProfileSystem
from eddy.core.common import HasProjectExportSystem
from eddy.core.common import HasProjectLoadSystem
from eddy.core.common import HasThreadingSystem
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.graphol import Identity, Item
from eddy.core.datatypes.graphol import Restriction, Special
from eddy.core.datatypes.misc import Color, DiagramMode
from eddy.core.datatypes.owl import Datatype, Facet
from eddy.core.datatypes.qt import BrushIcon, Font
from eddy.core.datatypes.system import Channel, File
from eddy.core.diagram import Diagram
from eddy.core.exporters.graphml import GraphMLDiagramExporter
from eddy.core.exporters.graphol import GrapholProjectExporter
from eddy.core.exporters.owl2 import OWLOntologyExporter
from eddy.core.exporters.pdf import PdfDiagramExporter
from eddy.core.exporters.printer import PrinterDiagramExporter
from eddy.core.factory import MenuFactory, PropertyFactory
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.misc import first, format_exception
from eddy.core.functions.misc import snap, snapF
from eddy.core.functions.path import expandPath
from eddy.core.functions.path import shortPath
from eddy.core.functions.signals import connect
from eddy.core.loaders.graphml import GraphMLOntologyLoader
from eddy.core.loaders.graphol import GrapholOntologyLoader_v2
from eddy.core.loaders.graphol import GrapholProjectLoader_v2
from eddy.core.output import getLogger
from eddy.core.plugin import PluginManager
from eddy.core.profiles.owl2 import OWL2Profile
from eddy.core.profiles.owl2ql import OWL2QLProfile
from eddy.core.profiles.owl2rl import OWL2RLProfile
from eddy.core.update import UpdateCheckWorker

from eddy.ui.about import AboutDialog
from eddy.ui.fields import ComboBox
from eddy.ui.forms import CardinalityRestrictionForm
from eddy.ui.forms import NewDiagramForm
from eddy.ui.forms import RefactorNameForm
from eddy.ui.forms import RenameDiagramForm
from eddy.ui.forms import ValueForm
from eddy.ui.log import LogDialog
from eddy.ui.mdi import MdiArea
from eddy.ui.mdi import MdiSubWindow
from eddy.ui.plugin import PluginInstallDialog
from eddy.ui.preferences import PreferencesDialog
from eddy.ui.progress import BusyProgressDialog
from eddy.ui.syntax import SyntaxValidationDialog
from eddy.ui.view import DiagramView


_LINUX = sys.platform.startswith('linux')
_MACOS = sys.platform.startswith('darwin')
_WIN32 = sys.platform.startswith('win32')


LOGGER = getLogger()


class Session(HasActionSystem, HasMenuSystem, HasPluginSystem, HasWidgetSystem,
    HasDiagramExportSystem, HasOntologyExportSystem, HasProjectExportSystem,
    HasDiagramLoadSystem, HasOntologyLoadSystem, HasProjectLoadSystem,
    HasProfileSystem, HasThreadingSystem, HasNotificationSystem, QtWidgets.QMainWindow):
    """
    Extends QtWidgets.QMainWindow and implements Eddy main working session.
    Additionally to built-in signals, this class emits:

    * sgnClosed: whenever the current session is closed.
    * sgnFocusDiagram: whenever a diagram is to be focused.
    * sgnFocusItem: whenever an item is to be focused.
    * sgnPluginDisposed: to notify that a plugin has been destroyed.
    * sgnPluginStarted: to notify that a plugin startup sequence has been completed.
    * sgnProjectSaved: to notify that the current project has been saved.
    * sgnQuit: whenever the application is to be terminated.
    * sgnReady: after the session startup sequence completes.
    * sgnSaveProject: whenever the current project is to be saved.
    * sgnUpdateState: to notify that something in the session state changed.
    """
    sgnClosed = QtCore.Signal()
    sgnCheckForUpdate = QtCore.Signal()
    sgnDiagramFocused = QtCore.Signal('QGraphicsScene')
    sgnFocusDiagram = QtCore.Signal('QGraphicsScene')
    sgnFocusItem = QtCore.Signal('QGraphicsItem')
    sgnPluginDisposed = QtCore.Signal(str)
    sgnPluginStarted = QtCore.Signal(str)
    sgnProjectSaved = QtCore.Signal()
    sgnQuit = QtCore.Signal()
    sgnReady = QtCore.Signal()
    sgnSaveProject = QtCore.Signal()
    sgnUpdateState = QtCore.Signal()

    def __init__(self, application, path, **kwargs):
        """
        Initialize the application main working session.
        :type application: QApplication
        :type path: str
        :type kwargs: dict
        """
        super().__init__(**kwargs)

        #############################################
        # INITIALIZE MAIN STUFF
        #################################

        self.app = application
        self.clipboard = Clipboard(self)
        self.undostack = QtGui.QUndoStack(self)
        self.mdi = MdiArea(self)

        #self.mdi.setBackground(QtGui.QBrush(QtGui.QColor("olive")))  #GSCOLOR
        #self.mdi.setBackground(QtGui.QBrush(QtGui.QColor("lavender")))  #GSCOLOR
        self.mdi.setBackground(QtGui.QBrush(QtGui.QColor("whitesmoke")))  #GSCOLOR

        self.mf = MenuFactory(self)
        self.pf = PropertyFactory(self)
        self.pmanager = PluginManager(self)
        self.project = None
        #GUSA COLOR
        #self.setStyleSheet("Session {background: green ; }")   #GSCOLOR

        #############################################
        # CONFIGURE SESSION
        #################################

        self.initPre()
        self.initActions()
        self.initMenus()
        self.initProfiles()
        self.initWidgets()
        self.initExporters()
        self.initLoaders()
        self.initSignals()
        self.initStatusBar()
        self.initToolBars()
        self.initPlugins()
        self.initState()

        #############################################
        # LOAD THE GIVEN PROJECT
        #################################

        worker = self.createProjectLoader(File.Graphol, path, self)
        worker.run()

        #############################################
        # COMPLETE SESSION SETUP
        #################################

        self.setAcceptDrops(False)
        self.setCentralWidget(self.mdi)
        self.setDockOptions(Session.AnimatedDocks | Session.AllowTabbedDocks)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle(self.project)

        self.sgnReady.emit()

        #cssfile = "eddy.css"
        cssfile = "eddy-light.css"
        css = self.readCssFile(cssfile)
        self.setStyleSheet(css)
        LOGGER.info('Session CSSFile setStyle: %s ', cssfile)

        LOGGER.info('Session startup completed: %s v%s [%s]', APPNAME, VERSION, self.project.name)

    #############################################
    #   SESSION CONFIGURATION
    #################################
    def readCssFile(self, filepath):
        #print("readCssFile:", filepath)
        try:
            f = open(filepath)
            css = f.read()
            return css
        except Exception as e:
            return ""

    def initActions(self):
        """
        Configure application built-in actions.
        """
        #############################################
        # APPLICATION GENERIC
        #################################

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_black'), 'Preferences', self,
            objectName='open_preferences', shortcut=QtGui.QKeySequence.Preferences,
            statusTip='Open application preferences', triggered=self.doOpenDialog)
        action.setData(PreferencesDialog)
        self.addAction(action)

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_power_settings_new_black'), 'Quit', self,
            objectName='quit', shortcut=QtGui.QKeySequence.Quit,
            statusTip='Quit {0}'.format(APPNAME), triggered=self.doQuit))

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_help_outline_black'), 'About {0}'.format(APPNAME),
            self, objectName='about', shortcut=QtGui.QKeySequence.HelpContents,
            statusTip='About {0}'.format(APPNAME), triggered=self.doOpenDialog)
        action.setData(AboutDialog)
        self.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'), 'Visit DIAG website', self,
            objectName='diag_web', statusTip='Visit DIAG website',
            triggered=self.doOpenURL)
        action.setData(DIAG_HOME)
        self.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_link_black'), 'Visit Graphol website', self,
            objectName='graphol_web', statusTip='Visit Graphol website',
            triggered=self.doOpenURL)
        action.setData(GRAPHOL_HOME)
        self.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_message_black'), 'System log...',
            self, objectName='system_log', statusTip='Show application system log',
            triggered=self.doOpenDialog)
        action.setData(LogDialog)
        self.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_extension_black'), 'Install Plugin...',
            self, objectName='install_plugin', statusTip='Install a plugin',
            triggered=self.doOpenDialog)
        action.setData(PluginInstallDialog)
        self.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_system_update'), 'Check for Updates...',
            self, objectName='check_for_updates', statusTip='Checks for available updates.',
            triggered=self.doCheckForUpdate)
        self.addAction(action)

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        collection = settings.value('project/recent', None, str) or []
        collection = collection[:5]
        #group = QtGui.QActionGroup(self, objectName='recent_projects')
        group = QtGui.QActionGroup(self)
        group.setObjectName('recent_projects')
        for i, path in enumerate(collection, start=1):
            action = QtGui.QAction('{0}. {1}'.format(i, os.path.basename(path)), group, triggered=self.doOpenRecent)
            action.setData(path)
            group.addAction(action)
        self.addAction(group)

        if _MACOS:
            self.action('about').setIcon(QtGui.QIcon())
            self.action('open_preferences').setIcon(QtGui.QIcon())
            self.action('quit').setIcon(QtGui.QIcon())

        #############################################
        # PROJECT / DIAGRAM MANAGEMENT
        #################################

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_add_document_black'), 'New diagram...',
            self, objectName='new_diagram', shortcut=QtGui.QKeySequence.New,
            statusTip='Create a new diagram', triggered=self.doNewDiagram))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'), 'Rename...',
            self, objectName='rename_diagram', statusTip='Rename a diagram',
            triggered=self.doRenameDiagram))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_black'), 'Delete...',
            self, objectName='remove_diagram', statusTip='Delete a diagram',
            triggered=self.doRemoveDiagram))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_folder_open_black'), 'Open...',
            self, objectName='open', shortcut=QtGui.QKeySequence.Open,
            statusTip='Open a diagram and add it to the current project',
            triggered=self.doOpen))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_close_black'), 'Close', self,
            objectName='close_project', shortcut=QtGui.QKeySequence.Close,
            statusTip='Close the current project', triggered=self.doClose))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_save_black'), 'Save', self,
            objectName='save', shortcut=QtGui.QKeySequence.Save,
            statusTip='Save the current project', enabled=False,
            triggered=self.doSave))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_save_black'), 'Save As...', self,
            objectName='save_as', shortcut=QtGui.QKeySequence.SaveAs,
            statusTip='Create a copy of the active diagram',
            enabled=False, triggered=self.doSaveAs))

        self.addAction(QtGui.QAction(
            'Import...', self, objectName='import', triggered=self.doImport,
            statusTip='Import a document in the current project'))

        self.addAction(QtGui.QAction(
            'Export...', self, objectName='export', triggered=self.doExport,
            statusTip='Export the current project in a different format',
            enabled=False))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_print_black'), 'Print...', self,
            objectName='print', shortcut=QtGui.QKeySequence.Print,
            statusTip='Print the active diagram', enabled=False,
            triggered=self.doPrint))

        #############################################
        # PROJECT SPECIFIC
        #################################

        action = self.undostack.createUndoAction(self)
        action.setIcon(QtGui.QIcon(':/icons/24/ic_undo_black'))
        action.setObjectName('undo')
        action.setShortcut(QtGui.QKeySequence.Undo)
        self.addAction(action)

        action = self.undostack.createRedoAction(self)
        action.setIcon(QtGui.QIcon(':/icons/24/ic_redo_black'))
        action.setObjectName('redo')
        action.setShortcut(QtGui.QKeySequence.Redo)
        self.addAction(action)

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_spellcheck_black'), 'Run syntax check',
            self, objectName='syntax_check', triggered=self.doSyntaxCheck,
            statusTip='Run syntax validation according to the selected profile'))

        ### GUSA APPEND ###
        self.addAction(QtGui.QAction(
            #QtGui.QIcon(':/icons/24/ic_spellcheck_black'), 'Css Load',
            #QtGui.QIcon(':/icons/24/ic_flip_to_back_black'), 'Css Load',
            QtGui.QIcon(':/icons/24/ic_visibility_back_black'), 'cssLoad',
            self, objectName='css_load', triggered=self.doCssLoad,
            statusTip='external css file load and set'))
        #############################################
        # DIAGRAM SPECIFIC
        #################################

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_center_focus_strong_black'), 'Center diagram', self,
            objectName='center_diagram', statusTip='Center the active diagram',
            enabled=False, triggered=self.doCenterDiagram))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_black'), 'Properties...',
            self, objectName='diagram_properties',
            statusTip='Open current diagram properties',
            triggered=self.doOpenDiagramProperties))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_healing_black'), 'Snap to grid',
            self, objectName='snap_to_grid', enabled=False,
            statusTip='Align the elements in the active diagram to the grid',
            triggered=self.doSnapTopGrid))

        icon = QtGui.QIcon()
        icon.addFile(':/icons/24/ic_grid_on_black', QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.On)
        icon.addFile(':/icons/24/ic_grid_off_black', QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.addAction(QtGui.QAction(
            icon, 'Toggle the grid', self, objectName='toggle_grid', enabled=False,
            checkable=True, statusTip='Activate or deactivate the diagram grid',
            triggered=self.doToggleGrid))

        #############################################
        # ITEM GENERICS
        #################################

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_content_cut_black'), 'Cut', self,
            objectName='cut', enabled=False, shortcut=QtGui.QKeySequence.Cut,
            statusTip='Cut selected items', triggered=self.doCut))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_content_copy_black'), 'Copy', self,
            objectName='copy', enabled=False, shortcut=QtGui.QKeySequence.Copy,
            statusTip='Copy selected items', triggered=self.doCopy))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_content_paste_black'), 'Paste', self,
            objectName='paste', enabled=False, shortcut=QtGui.QKeySequence.Paste,
            statusTip='Paste previously copied items', triggered=self.doPaste))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_black'), 'Delete', self,
            objectName='delete', enabled=False, shortcut=QtGui.QKeySequence.Delete,
            statusTip='Delete selected items', triggered=self.doDelete))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_forever_black'), 'Purge', self,
            objectName='purge', enabled=False, triggered=self.doPurge,
            statusTip='Delete selected items by also removing no more necessary elements'))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_flip_to_front_black'), 'Bring to front',
            self, objectName='bring_to_front', enabled=False,
            statusTip='Bring selected items to front',
            triggered=self.doBringToFront))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_flip_to_back_black'), 'Send to back',
            self, objectName='send_to_back', enabled=False,
            statusTip='Send selected items to back',
            triggered=self.doSendToBack))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_select_all_black'), 'Select all',
            self, objectName='select_all', enabled=False,
            statusTip='Select all items in the active diagram',
            shortcut=QtGui.QKeySequence.SelectAll, triggered=self.doSelectAll))

        #############################################
        # EDGE RELATED
        #################################

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_delete_black'), 'Remove breakpoint', self,
            objectName='remove_breakpoint', statusTip='Remove the selected edge breakpoint',
            triggered=self.doRemoveBreakpoint))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_swap_horiz_black'), 'Swap edge', self,
            objectName='swap_edge', shortcut='ALT+S', enabled=False,
            statusTip='Swap the direction of all the selected edges',
            triggered=self.doSwapEdge))

        #############################################
        # NODE RELATED
        #################################

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_settings_black'), 'Properties...',
            self, objectName='node_properties',
            triggered=self.doOpenNodeProperties))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_label_outline_black'), 'Rename...',
            self, objectName='refactor_name',
            triggered=self.doRefactorName))

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_refresh_black'), 'Relocate label',
            self, objectName='relocate_label',
            triggered=self.doRelocateLabel))

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_top_black'), Special.Top.value,
            self, objectName='special_top',
            triggered=self.doSetNodeSpecial)
        action.setData(Special.Top)
        self.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_bottom_black'), Special.Bottom.value,
            self, objectName='special_bottom',
            triggered=self.doSetNodeSpecial)
        action.setData(Special.Bottom)
        self.addAction(action)

        style = self.style()
        isize = style.pixelMetric(QtWidgets.QStyle.PM_ToolBarIconSize)
        for name, trigger in (('brush', self.doSetNodeBrush), ('refactor_brush', self.doRefactorBrush)):
            #GUSA group = QtGui.QActionGroup(self, objectName=name)
            group = QtGui.QActionGroup(self)
            group.setObjectName(name)
            for color in Color:
                action = QtGui.QAction(
                    BrushIcon(isize, isize, color.value), color.name,
                    self, checkable=False, triggered=trigger)
                action.setData(color)
                group.addAction(action)
            self.addAction(group)

        #############################################
        # ROLE SPECIFIC
        #################################

        self.addAction(QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_square_pair_black'), 'Invert Role', self,
            objectName='invert_role', triggered=self.doInvertRole,
            statusTip='Invert the selected role in all its occurrences'))

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_square_outline_black'), 'Domain',
            self, objectName='property_domain', shortcut='CTRL+D',
            triggered=self.doComposePropertyExpression)
        action.setData((Item.DomainRestrictionNode,))
        self.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_square_black'), 'Range',
            self, objectName='property_range', shortcut='CTRL+R',
            triggered=self.doComposePropertyExpression)
        action.setData((Item.RangeRestrictionNode,))
        self.addAction(action)

        action = QtGui.QAction(
            QtGui.QIcon(':/icons/24/ic_square_half_black'), 'Domain/Range',
            self, objectName='property_domain_range',
            triggered=self.doComposePropertyExpression)
        action.setData((Item.DomainRestrictionNode, Item.RangeRestrictionNode))
        self.addAction(action)

        #############################################
        # PROPERTY DOMAIN / RANGE SPECIFIC
        #################################

        #group = QtGui.QActionGroup(self, objectName='restriction')
        group = QtGui.QActionGroup(self)
        group.setObjectName('restriction')
        for restriction in Restriction:
            action = QtGui.QAction(restriction.value, group,
                objectName=restriction.name, checkable=True,
                triggered=self.doSetPropertyRestriction)
            action.setData(restriction)
            group.addAction(action)
        self.addAction(group)

        data = OrderedDict()
        data[Item.DomainRestrictionNode] = 'Domain'
        data[Item.RangeRestrictionNode] = 'Range'

        #group = QtGui.QActionGroup(self, objectName='switch_restriction')
        group = QtGui.QActionGroup(self )
        group.setObjectName('switch_restriction')
        for k, v in data.items():
            action = QtGui.QAction(v, group,
                objectName=k.name, checkable=True,
                triggered=self.doSwitchRestrictionNode)
            action.setData(k)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # VALUE-DOMAIN SPECIFIC
        #################################

        #group = QtGui.QActionGroup(self, objectName='datatype')
        group = QtGui.QActionGroup(self)
        group.setObjectName('datatype')
        for datatype in Datatype:
            action = QtGui.QAction(datatype.value, group,
                objectName=datatype.name, checkable=True,
                triggered=self.doSetDatatype)
            action.setData(datatype)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        #group = QtGui.QActionGroup(self, objectName='switch_individual')
        group = QtGui.QActionGroup(self)
        group.setObjectName('switch_individual')

        for identity in (Identity.Individual, Identity.Value):
            action = QtGui.QAction(identity.value, group,
                objectName=identity.name, checkable=True,
                triggered=self.doSetIndividualAs)
            action.setData(identity)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # FACET SPECIFIC
        #################################

        #group = QtGui.QActionGroup(self, objectName='facet')
        group = QtGui.QActionGroup(self)
        group.setObjectName('facet')
        for facet in Facet:
            action = QtGui.QAction(facet.value, group,
                objectName=facet.name, checkable=True,
                triggered=self.doSetFacet)
            action.setData(facet)
            group.addAction(action)
        self.addAction(group)

        #############################################
        # OPERATORS SPECIFIC
        #################################

        data = OrderedDict()
        data[Item.ComplementNode] = 'Complement'
        data[Item.DisjointUnionNode] = 'Disjoint union'
        data[Item.DatatypeRestrictionNode] = 'Datatype restriction'
        data[Item.EnumerationNode] = 'Enumeration'
        data[Item.IntersectionNode] = 'Intersection'
        data[Item.RoleChainNode] = 'Role chain'
        data[Item.RoleInverseNode] = 'Role inverse'
        data[Item.UnionNode] = 'Union'

        #group = QtGui.QActionGroup(self, objectName='switch_operator')
        group = QtGui.QActionGroup(self )
        group.setObjectName('switch_operator')
        for k, v in data.items():
            action = QtGui.QAction(v, group,
                objectName=k.name, checkable=True,
                triggered=self.doSwitchOperatorNode)
            action.setData(k)
            group.addAction(action)
        self.addAction(group)

    def initExporters(self):
        """
        Initialize diagram and project exporters.
        """
        self.addDiagramExporter(GraphMLDiagramExporter)
        self.addDiagramExporter(PdfDiagramExporter)
        self.addOntologyExporter(OWLOntologyExporter)
        self.addProjectExporter(GrapholProjectExporter)

    def initLoaders(self):
        """
        Initialize diagram and project loaders.
        """
        self.addOntologyLoader(GraphMLOntologyLoader)
        self.addOntologyLoader(GrapholOntologyLoader_v2)
        self.addProjectLoader(GrapholProjectLoader_v2)

    def initMenus(self):
        """
        Configure application built-in menus.
        """
        #############################################
        # MENU BAR RELATED
        #################################

        menu = QtWidgets.QMenu('File', objectName='file')
        menu.addAction(self.action('new_diagram'))
        menu.addAction(self.action('open'))
        menu.addSeparator()
        menu.addAction(self.action('save'))
        menu.addAction(self.action('save_as'))
        menu.addAction(self.action('close_project'))
        menu.addSeparator()
        menu.addAction(self.action('import'))
        menu.addAction(self.action('export'))
        menu.addSeparator()
        if self.action('recent_projects'):
            for action in self.action('recent_projects').actions():
                menu.addAction(action)
        menu.addSeparator()
        menu.addAction(self.action('print'))
        menu.addSeparator()
        menu.addAction(self.action('quit'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('\u200CEdit', objectName='edit')
        menu.addAction(self.action('undo'))
        menu.addAction(self.action('redo'))
        menu.addSeparator()
        menu.addAction(self.action('cut'))
        menu.addAction(self.action('copy'))
        menu.addAction(self.action('paste'))
        menu.addAction(self.action('delete'))
        menu.addSeparator()
        menu.addAction(self.action('bring_to_front'))
        menu.addAction(self.action('send_to_back'))
        menu.addSeparator()
        menu.addAction(self.action('swap_edge'))
        menu.addSeparator()
        menu.addAction(self.action('select_all'))
        menu.addAction(self.action('snap_to_grid'))
        menu.addAction(self.action('center_diagram'))
        menu.addSeparator()
        menu.addAction(self.action('open_preferences'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Compose', objectName='compose')
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        menu.addAction(self.action('property_domain_range'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Toolbars', objectName='toolbars')
        menu.addAction(self.widget('document_toolbar').toggleViewAction())
        menu.addAction(self.widget('editor_toolbar').toggleViewAction())
        menu.addAction(self.widget('graphol_toolbar').toggleViewAction())
        menu.addAction(self.widget('view_toolbar').toggleViewAction())
        menu.addAction(self.widget('window_toolbar').toggleViewAction())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('\u200CView', objectName='view')
        menu.addAction(self.action('toggle_grid'))
        menu.addSeparator()
        menu.addMenu(self.menu('toolbars'))
        menu.addSeparator()
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Ontology', objectName='ontology')
        menu.addAction(self.action('syntax_check'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Tools', objectName='tools')
        menu.addAction(self.action('install_plugin'))
        menu.addSeparator()
        menu.addAction(self.action('system_log'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Help', objectName='help')
        menu.addAction(self.action('about'))
        if not _MACOS:
            menu.addSeparator()
        menu.addAction(self.action('check_for_updates'))
        menu.addSeparator()
        menu.addAction(self.action('diag_web'))
        menu.addAction(self.action('graphol_web'))
        self.addMenu(menu)

        #############################################
        # NODE GENERIC
        #################################

        menu = QtWidgets.QMenu('Select color', objectName='brush')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('brush').actions())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Special type', objectName='special')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_star_black'))
        menu.addAction(self.action('special_top'))
        menu.addAction(self.action('special_bottom'))
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Select color', objectName='refactor_brush')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        menu.addActions(self.action('refactor_brush').actions())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Refactor', objectName='refactor')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_format_shapes_black'))
        menu.addAction(self.action('refactor_name'))
        menu.addMenu(self.menu('refactor_brush'))
        self.addMenu(menu)

        #############################################
        # ROLE / ATTRIBUTE SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Compose', objectName='compose_domain_range')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        menu.addAction(self.action('property_domain'))
        menu.addAction(self.action('property_range'))
        menu.addSeparator()
        menu.addAction(self.action('property_domain_range'))
        self.addMenu(menu)

        #############################################
        # VALUE-DOMAIN SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Select type', objectName='datatype')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('datatype').actions())
        self.addMenu(menu)

        #############################################
        # FACET SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Select facet', objectName='facet')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('facet').actions())
        self.addMenu(menu)

        #############################################
        # PROPERTY DOMAIN / RANGE SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Select restriction', objectName='property_restriction')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_settings_ethernet'))
        menu.addActions(self.action('restriction').actions())
        self.addMenu(menu)

        menu = QtWidgets.QMenu('Switch to', objectName='switch_restriction')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('switch_restriction').actions())
        self.addMenu(menu)

        #############################################
        # INDIVIDUAL SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Switch to', objectName='switch_individual')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('switch_individual').actions())
        self.addMenu(menu)

        #############################################
        # OPERATORS SPECIFIC
        #################################

        menu = QtWidgets.QMenu('Switch to', objectName='switch_operator')
        menu.setIcon(QtGui.QIcon(':/icons/24/ic_transform_black'))
        menu.addActions(self.action('switch_operator').actions())
        self.addMenu(menu)

        #############################################
        # CONFIGURE MENUBAR
        #################################

        menuBar = self.menuBar()
        menuBar.addMenu(self.menu('file'))
        menuBar.addMenu(self.menu('edit'))
        menuBar.addMenu(self.menu('compose'))
        menuBar.addMenu(self.menu('view'))
        menuBar.addMenu(self.menu('ontology'))
        menuBar.addMenu(self.menu('tools'))
        menuBar.addMenu(self.menu('help'))

    def initPre(self):
        """
        Initialize stuff that are shared by actions, menus, widgets etc.
        """
        #self.addWidget(QtWidgets.QToolBar('Document', objectName='document_toolbar'))
        #self.addWidget(QtWidgets.QToolBar('Editor', objectName='editor_toolbar'))
        #self.addWidget(QtWidgets.QToolBar('View', objectName='view_toolbar'))
        #self.addWidget(QtWidgets.QToolBar('Graphol', objectName='graphol_toolbar'))

        #GUSA COLOR   GSCOLOR
        document = QtWidgets.QToolBar('Document', objectName='document_toolbar')
        #document.setStyleSheet("QToolBar {background: #1e90ff ; }")   #GSCOLOR
        self.addWidget(document)

        editor = QtWidgets.QToolBar('Editor', objectName='editor_toolbar')
        #editor.setStyleSheet("QToolBar {background: #1e90ff ; }")   #GSCOLOR
        self.addWidget(editor)

        view  = QtWidgets.QToolBar('View', objectName='view_toolbar')
        #view.setStyleSheet("QToolBar {background: #1e90ff ; }")     #GSCOLOR
        self.addWidget(view)

        grap  = QtWidgets.QToolBar('Graphol', objectName='graphol_toolbar')
        #grap.setStyleSheet("QToolBar {background: #1e90ff ; }")    #GSCOLOR
        self.addWidget(grap)

        grap  = QtWidgets.QToolBar('Window', objectName='window_toolbar')
        #grap.setStyleSheet("QToolBar {background: #1e90ff ; }")    #GSCOLOR
        self.addWidget(grap)

    def initPlugins(self):
        """
        Load and initialize application plugins.
        """
        self.addPlugins(self.pmanager.init())
        pass

    def initProfiles(self):
        """
        Initialize the ontology profiles.
        """
        self.addProfile(OWL2Profile)
        self.addProfile(OWL2QLProfile)
        self.addProfile(OWL2RLProfile)

    def initSignals(self):
        """
        Connect session specific signals to their slots.
        """
        connect(self.undostack.cleanChanged, self.doUpdateState)
        connect(self.sgnCheckForUpdate, self.doCheckForUpdate)
        connect(self.sgnFocusDiagram, self.doFocusDiagram)
        connect(self.sgnFocusItem, self.doFocusItem)
        connect(self.sgnReady, self.doUpdateState)
        connect(self.sgnReady, self.onSessionReady)
        connect(self.sgnSaveProject, self.doSave)
        connect(self.sgnUpdateState, self.doUpdateState)

    def initState(self):
        """
        Configure application state by reading the preferences file.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        self.restoreGeometry(settings.value('session/geometry', QtCore.QByteArray(), QtCore.QByteArray))
        self.restoreState(settings.value('session/state', QtCore.QByteArray(), QtCore.QByteArray))
        self.action('toggle_grid').setChecked(settings.value('diagram/grid', False, bool))

    def initStatusBar(self):
        """
        Configure the status bar.
        """
        statusbar = QtWidgets.QStatusBar(self)
        statusbar.addPermanentWidget(self.widget('progress_bar'))
        statusbar.addPermanentWidget(QtWidgets.QWidget())
        statusbar.setSizeGripEnabled(False)
        #statusbar.setStyleSheet("QStatusBar {background: yellow ; }")   #GSCOLOR
        self.setStatusBar(statusbar)

    def initToolBars(self):
        """
        Configure application built-in toolbars.
        """
        toolbar = self.widget('document_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addAction(self.action('new_diagram'))
        toolbar.addAction(self.action('open'))
        toolbar.addAction(self.action('save'))
        toolbar.addAction(self.action('print'))

        toolbar = self.widget('editor_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addAction(self.action('undo'))
        toolbar.addAction(self.action('redo'))
        toolbar.addSeparator()
        toolbar.addAction(self.action('cut'))
        toolbar.addAction(self.action('copy'))
        toolbar.addAction(self.action('paste'))
        toolbar.addAction(self.action('delete'))
        toolbar.addAction(self.action('purge'))
        toolbar.addSeparator()
        toolbar.addAction(self.action('bring_to_front'))
        toolbar.addAction(self.action('send_to_back'))
        toolbar.addSeparator()
        toolbar.addAction(self.action('swap_edge'))
        toolbar.addWidget(self.widget('button_set_brush'))

        toolbar = self.widget('view_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addAction(self.action('toggle_grid'))
        toolbar.addAction(self.action('snap_to_grid'))
        toolbar.addAction(self.action('center_diagram'))

        toolbar = self.widget('graphol_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addWidget(self.widget('profile_switch'))
        toolbar.addAction(self.action('syntax_check'))

        toolbar = self.widget('window_toolbar')
        toolbar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        toolbar.addAction(self.action('css_load'))

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('document_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('editor_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('view_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('graphol_toolbar'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.widget('window_toolbar'))

    def initWidgets(self):
        """
        Configure application built-in widgets.
        """
        button = QtWidgets.QToolButton(objectName='button_set_brush')
        button.setIcon(QtGui.QIcon(':/icons/24/ic_format_color_fill_black'))
        button.setMenu(self.menu('brush'))
        button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        button.setStatusTip('Change the background color of the selected predicate nodes')
        button.setEnabled(False)
        self.addWidget(button)

        combobox = ComboBox(objectName='profile_switch')
        #css = """
        # QComboBox { background: pink; }
        # QListView { background: red;  }
        #"""
        #combobox.setStyleSheet(css)   #GSCOLOR
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.setStatusTip('Change the profile of the active project')
        combobox.addItems(self.profileNames())
        connect(combobox.activated, self.doSetProfile)
        self.addWidget(combobox)

        progressBar = QtWidgets.QProgressBar(objectName='progress_bar')
        progressBar.setContentsMargins(0, 0, 0, 0)
        progressBar.setFixedSize(222, 14)
        progressBar.setRange(0, 0)
        progressBar.setVisible(False)
        self.addWidget(progressBar)

    #############################################
    #   SLOTS
    #################################

    @QtCore.Slot()
    def doBringToFront(self):
        """
        Bring the selected item to the top of the diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            commands = []
            diagram.setMode(DiagramMode.Idle)
            for node in diagram.selectedNodes():
                zValue = 0
                for item in [x for x in node.collidingItems() if x.type() is not Item.Label]:
                    if item.zValue() >= zValue:
                        zValue = item.zValue() + 0.2
                if zValue != node.zValue():
                    commands.append(CommandNodeSetDepth(diagram, node, zValue))
            if commands:
                if len(commands) > 1:
                    self.undostack.beginMacro('change the depth of {0} nodes'.format(len(commands)))
                    for command in commands:
                        self.undostack.push(command)
                    self.undostack.endMacro()
                else:
                    self.undostack.push(first(commands))

    @QtCore.Slot()
    def doCenterDiagram(self):
        """
        Center the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            items = diagram.items()
            if items:
                R1 = diagram.sceneRect()
                R2 = diagram.visibleRect(margin=0)
                moveX = snapF(((R1.right() - R2.right()) - (R2.left() - R1.left())) / 2, Diagram.GridSize)
                moveY = snapF(((R1.bottom() - R2.bottom()) - (R2.top() - R1.top())) / 2, Diagram.GridSize)
                if moveX or moveY:
                    items = [x for x in items if x.isNode() or x.isEdge()]
                    command = CommandItemsTranslate(diagram, items, moveX, moveY, 'center diagram')
                    self.undostack.push(command)
                    self.mdi.activeView().centerOn(0, 0)

    @QtCore.Slot()
    def doCheckForUpdate(self):
        """
        Execute the update check routine.
        """
        channel = Channel.Beta
        # SHOW PROGRESS BAR
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('Checking for updates...')
        progressBar.setVisible(True)
        # RUN THE UPDATE CHECK WORKER IN A THREAD
        try:
            settings = QtCore.QSettings(ORGANIZATION, APPNAME)
            channel = Channel.valueOf(settings.value('update/channel', channel, str))
        except TypeError:
            pass
        finally:
            worker = UpdateCheckWorker(channel, VERSION)
            connect(worker.sgnNoUpdateAvailable, self.onNoUpdateAvailable)
            connect(worker.sgnNoUpdateDataAvailable, self.onNoUpdateDataAvailable)
            connect(worker.sgnUpdateAvailable, self.onUpdateAvailable)
            self.startThread('updateCheck', worker)

    @QtCore.Slot()
    def doClose(self):
        """
        Close the currently active subwindow.
        """
        self.close()
        self.sgnClosed.emit()

    @QtCore.Slot()
    def doComposePropertyExpression(self):
        """
        Compose a property domain using the selected role/attribute node.
        """
        positions = []

        def compose(scene, source, items):
            """
            Returns a collection of items to be added to the given source node to compose a property expression.
            :type scene: Diagram
            :type source: AbstractNode
            :type items: tuple
            :rtype: set
            """
            collection = set()
            for item in items:
                restriction = scene.factory.create(item)
                edge = scene.factory.create(Item.InputEdge, source=source, target=restriction)
                size = Diagram.GridSize
                offsets = (
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size), 0),
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size), 0),
                    QtCore.QPointF(0, snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(0, snapF(+source.height() / 2 + 70, size)),
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size), snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size), snapF(-source.height() / 2 - 70, size)),
                    QtCore.QPointF(snapF(+source.width() / 2 + 70, size), snapF(+source.height() / 2 + 70, size)),
                    QtCore.QPointF(snapF(-source.width() / 2 - 70, size), snapF(+source.height() / 2 + 70, size)),
                )
                pos = source.pos() + offsets[0]
                num = sys.maxsize
                rad = QtCore.QPointF(restriction.width() / 2, restriction.height() / 2)
                for o in offsets:
                    if source.pos() + o not in positions:
                        count = len(scene.items(QtCore.QRectF(source.pos() + o - rad, source.pos() + o + rad)))
                        if count < num:
                            num = count
                            pos = source.pos() + o
                restriction.setPos(pos)
                collection.update({restriction, edge})
                positions.append(pos)
            return collection

        diagram = self.mdi.activeDiagram()
        if diagram:
            commands = []
            action = self.sender()
            elements = action.data()
            diagram.setMode(DiagramMode.Idle)
            supported = {Item.RoleNode, Item.AttributeNode}
            for node in diagram.selectedNodes(lambda x: x.type() in supported):
                name = 'compose {0} restriction(s)'.format(node.shortName)
                addons = compose(diagram, node, elements)
                nodes = {x for x in addons if x.isNode()}
                edges = {x for x in addons if x.isEdge()}
                commands.append(CommandComposeAxiom(name, diagram, node, nodes, edges))
            if commands:
                if len(commands) > 1:
                    self.undostack.beginMacro('compose attribute/role restriction(s)')
                    for command in commands:
                        self.undostack.push(command)
                    self.undostack.endMacro()
                else:
                    self.undostack.push(first(commands))

    @QtCore.Slot()
    def doCopy(self):
        """
        Make a copy of selected items.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            diagram.pasteX = Clipboard.PasteOffsetX
            diagram.pasteY = Clipboard.PasteOffsetY
            self.clipboard.update(diagram)
            self.sgnUpdateState.emit()

    @QtCore.Slot()
    def doCut(self):
        """
        Cut selected items from the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            diagram.pasteX = 0
            diagram.pasteY = 0
            self.clipboard.update(diagram)
            self.sgnUpdateState.emit()
            items = diagram.selectedItems()
            if items:
                items.extend([x for item in items if item.isNode() for x in item.edges if x not in items])
                self.undostack.push(CommandItemsRemove(diagram, items))

    @QtCore.Slot()
    def doDelete(self):
        """
        Delete the currently selected items from the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            items = diagram.selectedItems()
            if items:
                items.extend([x for item in items if item.isNode() for x in item.edges if x not in items])
                self.undostack.push(CommandItemsRemove(diagram, items))

    @QtCore.Slot()
    def doExport(self):
        """
        Export the current project.
        """
        if not self.project.isEmpty():
            dialog = QtWidgets.QFileDialog(self)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setDirectory(expandPath('~/'))
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setNameFilters(sorted(self.ontologyExporterNameFilters() + self.projectExporterNameFilters({File.Graphol})))
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.selectFile(self.project.name)
            dialog.selectNameFilter(File.Owl.value)
            if dialog.exec_():
                filetype = File.valueOf(dialog.selectedNameFilter())
                try:
                    worker = self.createOntologyExporter(filetype, self.project, self)
                except ValueError:
                    worker = self.createProjectExporter(filetype, self.project, self)
                worker.run(expandPath(first(dialog.selectedFiles())))

    @QtCore.Slot('QGraphicsScene')
    def doFocusDiagram(self, diagram):
        """
        Focus the given diagram in the MDI area.
        :type diagram: Diagram
        """
        subwindow = self.mdi.subWindowForDiagram(diagram)
        if not subwindow:
            view = self.createDiagramView(diagram)
            subwindow = self.createMdiSubWindow(view)
            subwindow.showMaximized()
        self.mdi.setActiveSubWindow(subwindow)
        self.mdi.update()
        self.sgnDiagramFocused.emit(diagram)

    @QtCore.Slot('QGraphicsItem')
    def doFocusItem(self, item):
        """
        Focus an item in its diagram.
        :type item: AbstractItem
        """
        self.sgnFocusDiagram.emit(item.diagram)
        self.mdi.activeDiagram().clearSelection()
        self.mdi.activeView().centerOn(item)
        item.setSelected(True)

    @QtCore.Slot()
    def doImport(self):
        """
        Import an ontology into the currently active Project.
        """
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath('~'))
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setNameFilters(self.ontologyLoaderNameFilters())
        if dialog.exec_():
            filetype = File.valueOf(dialog.selectedNameFilter())
            selected = [x for x in dialog.selectedFiles() if File.forPath(x) is filetype and fexists(x)]
            if selected:
                try:
                    with BusyProgressDialog(parent=self) as progress:
                        for path in selected:
                            progress.setWindowTitle('Importing {0}...'.format(os.path.basename(path)))
                            worker = self.createOntologyLoader(filetype, path, self.project, self)
                            worker.run()
                except Exception as e:
                    msgbox = QtWidgets.QMessageBox(self)
                    msgbox.setDetailedText(format_exception(e))
                    msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
                    msgbox.setText('Eddy could not import all the selected files!')
                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle('Import failed!')
                    msgbox.exec_()

    @QtCore.Slot()
    def doInvertRole(self):
        """
        Swap the direction of all the occurrences of the selected role.
        """
        def invert(item):
            """
            Invert the type of a node.
            :type item: Item
            :rtype: Item
            """
            if item is Item.DomainRestrictionNode:
                return Item.RangeRestrictionNode
            return Item.DomainRestrictionNode

        f0 = lambda x: x.type() is Item.RoleNode
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
        f3 = lambda x: x.type() is Item.RoleInverseNode

        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(x for x in diagram.selectedNodes(filter_on_nodes=f0))
            if node:
                swappable = set()
                collection = dict()
                predicates = self.project.predicates(node.type(), node.text())
                for predicate in predicates:
                    swappable = set.union(swappable, predicate.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                    for inv in predicate.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f3):
                        swappable = set.union(swappable, inv.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
                for xnode in swappable:
                    ynode = xnode.diagram.factory.create(invert(xnode.type()))
                    ynode.setPos(xnode.pos())
                    ynode.setText(xnode.text())
                    ynode.setTextPos(xnode.textPos())
                    collection[xnode] = ynode
                if collection:
                    self.undostack.beginMacro("swap '{0}' domain and range".format(node.text()))
                    for xnode, ynode in collection.items():
                        self.undostack.push(CommandNodeSwitchTo(xnode.diagram, xnode, ynode))
                    self.undostack.endMacro()

    @QtCore.Slot()
    def doLookupOccurrence(self):
        """
        Focus the item which is being held by the supplying QAction.
        """
        self.sgnFocusItem.emit(self.sender().data())

    @QtCore.Slot()
    def doNewDiagram(self):
        """
        Create a new diagram.
        """
        form = NewDiagramForm(self.project, self)
        if form.exec_() == NewDiagramForm.Accepted:
            settings = QtCore.QSettings(ORGANIZATION, APPNAME)
            size = settings.value('diagram/size', 5000, int)
            name = form.nameField.value()
            diagram = Diagram.create(name, size, self.project)
            connect(diagram.sgnItemAdded, self.project.doAddItem)
            connect(diagram.sgnItemRemoved, self.project.doRemoveItem)
            connect(diagram.selectionChanged, self.doUpdateState)
            self.undostack.push(CommandDiagramAdd(diagram, self.project))
            self.sgnFocusDiagram.emit(diagram)

    @QtCore.Slot()
    def doOpen(self):
        """
        Open a project in a new session.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        workspace = settings.value('workspace/home', WORKSPACE, str)
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath(workspace))
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.app.sgnCreateSession.emit(expandPath(first(dialog.selectedFiles())))

    @QtCore.Slot()
    def doOpenRecent(self):
        """
        Open a recent project in a new session.
        """
        action = self.sender()
        path = expandPath(action.data())
        if path != expandPath(self.project.path):
            self.app.sgnCreateSession.emit(expandPath(action.data()))

    @QtCore.Slot()
    def doOpenDialog(self):
        """
        Open a dialog window by initializing it using the class stored in action data.
        """
        action = self.sender()
        dialog = action.data()
        window = dialog(self)
        window.exec_()

    @QtCore.Slot()
    def doOpenURL(self):
        """
        Open a URL using the operating system default browser.
        """
        action = self.sender()
        weburl = action.data()
        if weburl:
            # noinspection PyTypeChecker,PyCallByClass,PyCallByClass
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(weburl))

    @QtCore.Slot()
    def doOpenDiagramProperties(self):
        """
        Executed when scene properties needs to be displayed.
        """
        diagram = self.sender().data() or self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            properties = self.pf.create(diagram)
            properties.exec_()

    @QtCore.Slot()
    def doOpenNodeProperties(self):
        """
        Executed when node properties needs to be displayed.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            node = first(diagram.selectedNodes())
            if node:
                properties = self.pf.create(diagram, node)
                properties.exec_()

    @QtCore.Slot()
    def doPaste(self):
        """
        Paste previously copied items.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            if not self.clipboard.empty():
                self.clipboard.paste(diagram, diagram.mp_Pos)

    @QtCore.Slot()
    def doPrint(self):
        """
        Print the active diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            worker = PrinterDiagramExporter(diagram, self)
            worker.run()

    @QtCore.Slot()
    def doPurge(self):
        """
        Delete the currently selected items by also removing no more necessary elements.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            items = set(diagram.selectedItems())
            purge = set()
            for item in items:
                if item.isNode():
                    for node in item.definition():
                        if item.isConstructor():
                            if node not in items:
                                # Here we examine a node which is included in the definition of a node
                                # in the original selection, but it's not included in the selection itself.
                                # If the node contribute only to the definition on this node and has no
                                # relation with any other node in the diagram, which is not in the original
                                # item selection, we will remove it.
                                if node.adjacentNodes(filter_on_nodes=lambda x: x not in items):
                                    continue
                        purge.add(node)
            collection = list(items|purge)
            if collection:
                collection.extend([x for item in collection if item.isNode() for x in item.edges if x not in collection])
                self.undostack.push(CommandItemsRemove(diagram, collection))

    @QtCore.Slot()
    def doQuit(self):
        """
        Quit Eddy.
        """
        self.close()
        self.sgnQuit.emit()

    @QtCore.Slot()
    def doRefactorBrush(self):
        """
        Change the node brush for all the predicate nodes matching the selected predicate.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                color = action.data()
                nodes = self.project.predicates(node.type(), node.text())
                self.undostack.push(CommandNodeSetBrush(diagram, nodes, QtGui.QBrush(QtGui.QColor(color.value))))

    @QtCore.Slot()
    def doRefactorName(self):
        """
        Rename all the instance of the selected predicate node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                 dialog = RefactorNameForm(node, self)
                 dialog.exec_()

    @QtCore.Slot()
    def doRelocateLabel(self):
        """
        Reset the selected node label to its default position.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.label is not None
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node and node.label.isMovable():
                undo = node.label.pos()
                redo = node.label.defaultPos()
                self.undostack.push(CommandLabelMove(diagram, node, undo, redo))

    @QtCore.Slot()
    def doRemoveBreakpoint(self):
        """
        Remove the edge breakpoint specified in the action triggering this slot.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            edge, breakpoint = action.data()
            if 0 <= breakpoint < len(edge.breakpoints):
                self.undostack.push(CommandEdgeBreakpointRemove(diagram, edge, breakpoint))

    @QtCore.Slot()
    def doRemoveDiagram(self):
        """
        Removes a diagram from the current project.
        """
        action = self.sender()
        diagram = action.data()
        if diagram:
            self.undostack.push(CommandDiagramRemove(diagram, self.project))

    @QtCore.Slot()
    def doRenameDiagram(self):
        """
        Renames a diagram.
        """
        action = self.sender()
        diagram = action.data()
        if diagram:
            form = RenameDiagramForm(self.project, diagram, self)
            if form.exec_() == RenameDiagramForm.Accepted:
                name = form.nameField.value()
                self.undostack.push(CommandDiagramRename(diagram.name, name, diagram, self.project))

    @QtCore.Slot()
    def doSave(self):
        """
        Save the current project.
        """
        try:
            worker = self.createProjectExporter(File.Graphol, self.project, self)
            worker.run()
        except Exception as e:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setDetailedText(format_exception(e))
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
            msgbox.setText('Eddy could not save the current project!')
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Save failed!')
            msgbox.exec_()
        else:
            self.undostack.setClean()
            self.sgnProjectSaved.emit()

    @QtCore.Slot()
    def doSaveAs(self):
        """
        Creates a copy of the currently open diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            dialog = QtWidgets.QFileDialog(self)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setDirectory(expandPath('~/'))
            dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            dialog.setNameFilters(self.diagramExporterNameFilters())
            dialog.setViewMode(QtWidgets.QFileDialog.Detail)
            dialog.selectFile(diagram.name)
            dialog.selectNameFilter(File.Pdf.value)
            if dialog.exec_():
                filetype = File.valueOf(dialog.selectedNameFilter())
                worker = self.createDiagramExporter(filetype, diagram, self)
                worker.run(expandPath(first(dialog.selectedFiles())))

    @QtCore.Slot()
    def doSelectAll(self):
        """
        Select all the items in the active diagrsm.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            path = QtGui.QPainterPath()
            path.addRect(diagram.sceneRect())
            diagram.setSelectionArea(path)
            diagram.setMode(DiagramMode.Idle)

    @QtCore.Slot()
    def doSendToBack(self):
        """
        Send the selected item to the back of the diagram.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            commands = []
            diagram.setMode(DiagramMode.Idle)
            for node in diagram.selectedNodes():
                zValue = 0
                for item in [x for x in node.collidingItems() if x.type() is not Item.Label]:
                    if item.zValue() <= zValue:
                        zValue = item.zValue() - 0.2
                if zValue != node.zValue():
                    commands.append(CommandNodeSetDepth(diagram, node, zValue))
            if commands:
                if len(commands) > 1:
                    self.undostack.beginMacro('change the depth of {0} nodes'.format(len(commands)))
                    for command in commands:
                        self.undostack.push(command)
                    self.undostack.endMacro()
                else:
                    self.undostack.push(first(commands))
            
    @QtCore.Slot()
    def doSetNodeBrush(self):
        """
        Set the brush of selected nodes.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            color = action.data()
            brush = QtGui.QBrush(QtGui.QColor(color.value))
            supported = {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}
            fn = lambda x: x.type() in supported and x.brush() != brush
            selected = diagram.selectedNodes(filter_on_nodes=fn)
            if selected:
                self.undostack.push(CommandNodeSetBrush(diagram, selected, brush))

    @QtCore.Slot()
    def doSetPropertyRestriction(self):
        """
        Set a property domain / range restriction.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                data = None
                action = self.sender()
                restriction = action.data()
                if restriction is not Restriction.Cardinality:
                    data = restriction.toString()
                else:
                    form = CardinalityRestrictionForm(self)
                    if form.exec_() == CardinalityRestrictionForm.Accepted:
                        data = restriction.toString(form.min(), form.max())
                if data and node.text() != data:
                    name = 'change {0} to {1}'.format(node.shortName, data)
                    self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.Slot()
    def doSetIndividualAs(self):
        """
        Set an invididual node either to Individual or Value.
        Will bring up the Value Form if needed.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() is Item.IndividualNode
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                if action.data() is Identity.Individual:
                    if node.identity() is Identity.Value:
                        data = node.label.template
                        name = 'change {0} to {1}'.format(node.text(), data)
                        self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))
                elif action.data() is Identity.Value:
                    form = ValueForm(node, self)
                    form.exec_()

    @QtCore.Slot()
    def doSetNodeSpecial(self):
        """
        Set the special type of the selected node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            action = self.sender()
            fn = lambda x: x.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode}
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                special = action.data()
                data = special.value
                if node.text() != data:
                    name = 'change {0} to {1}'.format(node.shortName, data)
                    self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.Slot()
    def doSetDatatype(self):
        """
        Set the datatype of the selected value-domain node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() is Item.ValueDomainNode
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                datatype = action.data()
                data = datatype.value
                if node.text() != data:
                    name = 'change {0} to {1}'.format(node.shortName, data)
                    self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.Slot()
    def doSetFacet(self):
        """
        Set the facet of a Facet node.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() is Item.FacetNode
            node = first(diagram.selectedNodes(filter_on_nodes=fn))
            if node:
                action = self.sender()
                facet = action.data()
                if facet != node.facet:
                    data = node.compose(facet, node.value)
                    name = 'change {0} to {1}'.format(node.facet.value, facet.value)
                    self.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))

    @QtCore.Slot()
    def doSetProfile(self):
        """
        Set the currently used project profile.
        """
        widget = self.widget('profile_switch')
        profile = widget.currentText()
        if self.project.profile.name() != profile:
            self.undostack.push(CommandProjectSetProfile(self.project, self.project.profile.name(), profile))
        widget.clearFocus()

    @QtCore.Slot()
    def doSnapTopGrid(self):
        """
        Snap all the element in the active diagram to the grid.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            data = {'redo': {'nodes': {}, 'edges': {}}, 'undo': {'nodes': {}, 'edges': {}}}
            for item in diagram.items():
                if item.isNode():
                    undoPos = item.pos()
                    redoPos = snap(undoPos, Diagram.GridSize)
                    if undoPos != redoPos:
                        data['undo']['nodes'][item] = {
                            'pos': undoPos,
                            'anchors': {k: v for k, v in item.anchors.items()}
                        }
                        data['redo']['nodes'][item] = {
                            'pos': redoPos,
                            'anchors': {k: v + redoPos - undoPos for k, v in item.anchors.items()}
                        }
                elif item.isEdge():
                    undoPts = item.breakpoints
                    redoPts = [snap(x, Diagram.GridSize) for x in undoPts]
                    if undoPts != redoPts:
                        data['undo']['edges'][item] = {'breakpoints': undoPts}
                        data['redo']['edges'][item] = {'breakpoints': redoPts}

            if data['undo']['nodes'] or data['undo']['edges']:
                self.undostack.push(CommandSnapItemsToGrid(diagram, data))

    @QtCore.Slot()
    def doSwapEdge(self):
        """
        Swap the selected edges by inverting source/target points.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fe = lambda x: x.isSwapAllowed()
            selected = diagram.selectedEdges(filter_on_edges=fe)
            if selected:
                self.undostack.push(CommandEdgeSwap(diagram, selected))

    @QtCore.Slot()
    def doSwitchOperatorNode(self):
        """
        Switch the selected operator node to a different type.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: Item.UnionNode <= x.type() <= Item.DisjointUnionNode
            node = first([x for x in diagram.selectedNodes(filter_on_nodes=fn)])
            if node:
                action = self.sender()
                if node.type() is not action.data():
                    xnode = diagram.factory.create(action.data())
                    xnode.setPos(node.pos())
                    self.undostack.push(CommandNodeSwitchTo(diagram, node, xnode))

    @QtCore.Slot()
    def doSwitchRestrictionNode(self):
        """
        Switch the selected restriction node to a different type.
        """
        diagram = self.mdi.activeDiagram()
        if diagram:
            diagram.setMode(DiagramMode.Idle)
            fn = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
            node = first([x for x in diagram.selectedNodes(filter_on_nodes=fn)])
            if node:
                action = self.sender()
                if node.type() is not action.data():
                    xnode = diagram.factory.create(action.data())
                    xnode.setPos(node.pos())
                    xnode.setText(node.text())
                    xnode.setTextPos(node.textPos())
                    self.undostack.push(CommandNodeSwitchTo(diagram, node, xnode))

    @QtCore.Slot()
    def doSyntaxCheck(self):
        """
        Perform syntax checking on the active diagram.
        """
        dialog = SyntaxValidationDialog(self.project, self)
        dialog.exec_()

    @QtCore.Slot()
    def doCssLoad(self):
        print("doCssLoad")

        cssfile = "eddy-light.css"
        css = self.readCssFile(cssfile)
        self.setStyleSheet(css)
        LOGGER.info('Session CSSFile setStyle: %s ', cssfile)

    @QtCore.Slot()
    def doToggleGrid(self):
        """
        Toggle snap to grid setting and viewport display.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('diagram/grid', self.action('toggle_grid').isChecked())
        settings.sync()
        for subwindow in self.mdi.subWindowList():
            subwindow.view.setGridSize(Diagram.GridSize)
            viewport = subwindow.view.viewport()
            viewport.update()

    @QtCore.Slot()
    def doUpdateState(self):
        """
        Update built-in actions according to the application state.
        """
        isDomainRangeUsable = False
        isDiagramActive = False
        isClipboardEmpty = True
        isEdgeSelected = False
        isEdgeSwapEnabled = False
        isNodeSelected = False
        isPredicateSelected = False
        isProjectEmpty = self.project.isEmpty()
        isUndoStackClean = self.undostack.isClean()

        if self.mdi.subWindowList():
            diagram = self.mdi.activeDiagram()
            restrictables = {Item.AttributeNode, Item.RoleNode}
            predicates = {Item.ConceptNode, Item.AttributeNode, Item.RoleNode, Item.IndividualNode}
            if diagram:
                nodes = diagram.selectedNodes()
                edges = diagram.selectedEdges()
                isDiagramActive = True
                isClipboardEmpty = self.clipboard.empty()
                isEdgeSelected = first(edges) is not None
                isNodeSelected = first(nodes) is not None
                isDomainRangeUsable = any([x.type() in restrictables for x in nodes])
                isPredicateSelected = any([x.type() in predicates for x in nodes])
                if isEdgeSelected:
                    for edge in edges:
                        isEdgeSwapEnabled = edge.isSwapAllowed()
                        if isEdgeSwapEnabled:
                            break

        self.action('bring_to_front').setEnabled(isNodeSelected)
        self.action('center_diagram').setEnabled(isDiagramActive)
        self.action('cut').setEnabled(isNodeSelected)
        self.action('copy').setEnabled(isNodeSelected)
        self.action('delete').setEnabled(isNodeSelected or isEdgeSelected)
        self.action('purge').setEnabled(isNodeSelected)
        self.action('export').setEnabled(not isProjectEmpty)
        self.action('paste').setEnabled(not isClipboardEmpty)
        self.action('property_domain').setEnabled(isDomainRangeUsable)
        self.action('property_domain_range').setEnabled(isDomainRangeUsable)
        self.action('property_range').setEnabled(isDomainRangeUsable)
        self.action('save').setEnabled(not isUndoStackClean)
        self.action('save_as').setEnabled(isDiagramActive)
        self.action('select_all').setEnabled(isDiagramActive)
        self.action('send_to_back').setEnabled(isNodeSelected)
        self.action('snap_to_grid').setEnabled(isDiagramActive)
        self.action('syntax_check').setEnabled(not isProjectEmpty)
        self.action('swap_edge').setEnabled(isEdgeSelected and isEdgeSwapEnabled)
        self.action('toggle_grid').setEnabled(isDiagramActive)
        self.widget('button_set_brush').setEnabled(isPredicateSelected)
        self.widget('profile_switch').setCurrentText(self.project.profile.name())

    @QtCore.Slot()
    def onNoUpdateAvailable(self):
        """
        Executed when the update worker thread terminates and no software update is available.
        """
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('')
        progressBar.setVisible(False)
        self.addNotification('No update available.')

    @QtCore.Slot()
    def onNoUpdateDataAvailable(self):
        """
        Executed when the update worker thread terminates abnormally.
        """
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('')
        progressBar.setVisible(False)
        #GUSA self.addNotification(textwrap.dedent("""
        #    <b><font color="#7E0B17">ERROR</font></b>: Could not connect to update site:
        #    unable to get update information.
        #    """))

    @QtCore.Slot()
    def onSessionReady(self):
        """
        Executed when the session is initialized.
        """
        ## CONNECT PROJECT SPECIFIC SIGNALS
        connect(self.project.sgnDiagramRemoved, self.mdi.onDiagramRemoved)
        ## CHECK FOR UPDATES ON STARTUP
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        if settings.value('update/check_on_startup', True, bool):
            action = self.action('check_for_updates')
            action.trigger()

    @QtCore.Slot(str, str)
    def onUpdateAvailable(self, name, url):
        """
        Executed when the update worker thread terminates and a new software update is available.
        :type name: str
        :type url: str
        """
        progressBar = self.widget('progress_bar')
        progressBar.setToolTip('')
        progressBar.setVisible(False)
        self.addNotification(textwrap.dedent("""
            A new version of {} is available for download: <a href="{}"><b>{}</b></a>""".format(APPNAME, url, name)))

    #############################################
    #   EVENTS
    #################################

    def closeEvent(self, closeEvent):
        """
        Executed when the main window is closed.
        :type closeEvent: QCloseEvent
        """
        close = True
        save = False
        if not self.undostack.isClean():
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_question_outline_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Save changes?')
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Cancel|QtWidgets.QMessageBox.No|QtWidgets.QMessageBox.Yes)
            msgbox.setText('Your project contains unsaved changes. Do you want to save?')
            msgbox.exec_()
            if msgbox.result() == QtWidgets.QMessageBox.Cancel:
                close = False
            elif msgbox.result() == QtWidgets.QMessageBox.No:
                save = False
            elif msgbox.result() == QtWidgets.QMessageBox.Yes:
                save = True

        if not close:
            closeEvent.ignore()
        else:
            ## SAVE THE CURRENT PROJECT IF NEEDED
            if save:
                self.sgnSaveProject.emit()
            ## DISPOSE ALL THE PLUGINS
            for plugin in self.plugins():
                self.pmanager.dispose(plugin)
            self.pmanager.clear()
            ## DISPOSE ALL THE RUNNING THREADS
            self.stopRunningThreads()
            ## HIDE ALL THE NOTIFICATION POPUPS
            self.hideNotifications()
            ## SHUTDOWN THE ACTIVE SESSION
            self.sgnClosed.emit()
            closeEvent.accept()

            LOGGER.info('Session shutdown completed: %s v%s [%s]', APPNAME, VERSION, self.project.name)

    def keyPressEvent(self, keyEvent):
        """
        Executed when a keyboard button is pressed
        :type keyEvent: QKeyEvent
        """
        if _MACOS:
            if keyEvent.key() == QtCore.Qt.Key_Backspace:
                action = self.action('delete')
                action.trigger()
        super().keyPressEvent(keyEvent)

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released.
        :type keyEvent: QKeyEvent
        """
        if keyEvent.key() == QtCore.Qt.Key_Control:
            diagram = self.mdi.activeDiagram()
            if diagram and not diagram.isEdgeAdd():
                diagram.setMode(DiagramMode.Idle)
        super().keyReleaseEvent(keyEvent)

    def showEvent(self, showEvent):
        """
        Executed when the window is shown.
        :type showEvent: QShowEvent
        """
        self.setWindowState((self.windowState() & ~QtCore.Qt.WindowMinimized) | QtCore.Qt.WindowActive)
        self.activateWindow()
        self.raise_()

    #############################################
    #   INTERFACE
    #################################

    def createDiagramView(self, diagram):
        """
        Create a new diagram view displaying the given diagram.
        :type diagram: Diagram
        :rtype: DigramView
        """
        view = DiagramView(diagram, self)
        view.centerOn(0, 0)
        return view

    def createMdiSubWindow(self, widget):
        """
        Create a subwindow in the MDI area that displays the given widget.
        :type widget: QWidget
        :rtype: MdiSubWindow
        """
        subwindow = MdiSubWindow(widget)
        subwindow = self.mdi.addSubWindow(subwindow)
        subwindow.showMaximized()
        return subwindow

    def save(self):
        """
        Save the current session state.
        """
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('session/geometry', self.saveGeometry())
        settings.setValue('session/state', self.saveState())
        settings.sync()

    def setWindowTitle(self, project, diagram=None):
        """
        Set the main window title.
        :type project: Project
        :type diagram: Diagram
        """
        title = '{0} - [{1}]'.format(project.name, shortPath(project.path))
        if diagram:
            title = '{0} - {1}'.format(diagram.name, title)
        super().setWindowTitle(title)
