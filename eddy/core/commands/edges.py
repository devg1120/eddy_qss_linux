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


from PySide6 import QtWidgets
from PySide6 import QtGui

from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import first


class CommandEdgeAdd(QtGui.QUndoCommand):
    """
    This command is used to add an edge to a diagram.
    """
    def __init__(self, diagram, edge):
        """
        Initialize the command.
        """
        super().__init__('add {0}'.format(edge.name))

        self.inputs = {'redo': [], 'undo': []}
        self.diagram = diagram
        self.edge = edge

        # IMPORTANT: do not remove the following since it's
        # needed by property assertion node and role chain node
        # to correctly generate an entry in their input lists.
        self.edge.source.addEdge(self.edge)
        self.edge.target.addEdge(self.edge)
        self.edge.updateEdge()

        if self.edge.type() is Item.InputEdge:
            # If we are adding an input edge targeting a role chain or a property
            # assertion node we need to save the new inputs order and compute the
            # old one by removing the current edge id from the input list.
            if self.edge.target.type() in {Item.RoleChainNode, Item.PropertyAssertionNode}:
                self.inputs['redo'] = self.edge.target.inputs[:]
                self.inputs['undo'] = self.edge.target.inputs[:]
                self.inputs['undo'].remove(self.edge.id)

    def redo(self):
        """redo the command"""
        # Map source/target over the edge.
        self.edge.source.addEdge(self.edge)
        self.edge.target.addEdge(self.edge)
        # Switch the inputs.
        if self.edge.target.type() in {Item.RoleChainNode, Item.PropertyAssertionNode}:
            self.edge.target.inputs = self.inputs['redo'][:]
        # Add the edge to the diagram.
        self.diagram.addItem(self.edge)
        # Update edge geometry.
        self.edge.updateEdge()
        # Emit diagram specific signals.
        self.diagram.sgnItemAdded.emit(self.diagram, self.edge)
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # Remove source/target from the edge.
        self.edge.source.removeEdge(self.edge)
        self.edge.target.removeEdge(self.edge)
        # Switch the inputs.
        if self.edge.target.type() in {Item.RoleChainNode, Item.PropertyAssertionNode}:
            self.edge.target.inputs = self.inputs['undo'][:]
        # Remove the edge from the diagram.
        self.diagram.removeItem(self.edge)
        self.diagram.sgnItemRemoved.emit(self.diagram, self.edge)
        self.diagram.sgnUpdated.emit()


class CommandEdgeBreakpointAdd(QtGui.QUndoCommand):
    """
    This command is used to add a breakpoint on the given edge.
    """
    def __init__(self, diagram, edge, index, point):
        """
        Initialize the command.
        :type diagram: Diagram
        :type edge: AbstractEdge
        :type index: int
        :type point: QPointF
        """
        super().__init__('add {0} breakpoint'.format(edge.name))
        self.edge = edge
        self.index = index
        self.point = point
        self.diagram = diagram

    def redo(self):
        """redo the command"""
        self.edge.breakpoints.insert(self.index, self.point)
        self.edge.updateEdge()
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints.pop(self.index)
        self.edge.updateEdge()
        self.diagram.sgnUpdated.emit()


class CommandEdgeAnchorMove(QtGui.QUndoCommand):
    """
    This command is used to move edge anchor points.
    """
    def __init__(self, diagram, edge, node, data):
        """
        Initialize the command.
        :type diagram: Diagram
        :type edge: AbstractEdge
        :type node: AbstractNode
        :type data: dict
        """
        super().__init__('move {0} anchor point'.format(edge.name))
        self.diagram = diagram
        self.edge = edge
        self.node = node
        self.data = data

    def redo(self):
        """redo the command"""
        self.node.setAnchor(self.edge, self.data['redo'])
        self.edge.updateEdge()
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.node.setAnchor(self.edge, self.data['undo'])
        self.edge.updateEdge()
        self.diagram.sgnUpdated.emit()


class CommandEdgeBreakpointMove(QtGui.QUndoCommand):
    """
    This command is used to move edge breakpoints.
    """
    def __init__(self, diagram, edge, index, data):
        """
        Initialize the command.
        :type diagram: Diagram
        :type edge: AbstractEdge
        :type index: int
        :type data: dict
        """
        super().__init__('move {0} breakpoint'.format(edge.name))
        self.diagram = diagram
        self.edge = edge
        self.index = index
        self.data = data

    def redo(self):
        """redo the command"""
        self.edge.breakpoints[self.index] = self.data['redo']
        self.edge.updateEdge()
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints[self.index] = self.data['undo']
        self.edge.updateEdge()
        self.diagram.sgnUpdated.emit()


class CommandEdgeBreakpointRemove(QtGui.QUndoCommand):
    """
    This command is used to delete edge breakpoints.
    """
    def __init__(self, diagram, edge, index):
        """
        Initialize the command.
        :type diagram: Diagram
        :type edge: AbstractEdge
        :type index: int
        """
        super().__init__('remove {0} breakpoint'.format(edge.name))
        self.diagram = diagram
        self.edge = edge
        self.index = index
        self.point = edge.breakpoints[self.index]

    def redo(self):
        """redo the command"""
        self.edge.breakpoints.pop(self.index)
        self.edge.updateEdge()
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.edge.breakpoints.insert(self.index, self.point)
        self.edge.updateEdge()
        self.diagram.sgnUpdated.emit()


class CommandEdgeSwap(QtGui.QUndoCommand):
    """
    This command is used to swap the endpoints of edges.
    """
    def __init__(self, diagram, edges):
        """
        Initialize the command.
        :type diagram: Diagram
        :type edges: T <= tuple|list|set
        """
        self.diagram = diagram
        self.edges = edges

        self.inputs = {n: {
            'undo': n.inputs[:],
            'redo': n.inputs[:],
        } for edge in self.edges \
            if edge.type() is Item.InputEdge \
                for n in {edge.source, edge.target} \
                    if n.type() in {Item.RoleChainNode, Item.PropertyAssertionNode}}

        for edge in self.edges:
            if edge.type() is Item.InputEdge and edge.target in self.inputs:
                self.inputs[edge.target]['redo'].doRemoveNode(edge.id)

        for edge in self.edges:
            if edge.type() is Item.InputEdge and edge.source in self.inputs:
                self.inputs[edge.source]['redo'].append(edge.id)

        if len(edges) == 1:
            name = 'swap {0}'.format(first(edges).name)
        else:
            name = 'swap {0} edges'.format(len(edges))

        super().__init__(name)

    def redo(self):
        """redo the command"""
        # Swap the edges.
        for edge in self.edges:
            edge.source, edge.target = edge.target, edge.source
            edge.breakpoints = edge.breakpoints[::-1]
            for node in {edge.source, edge.target}:
                if node in self.inputs:
                    node.inputs = self.inputs[node]['redo'][:]
            edge.updateEdge()
        # Identify all the endpoints.
        for edge in self.edges:
            for node in {edge.source, edge.target}:
                self.diagram.sgnNodeIdentification.emit(node)
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        # Swap the edges.
        for edge in self.edges:
            edge.source, edge.target = edge.target, edge.source
            edge.breakpoints = edge.breakpoints[::-1]
            for node in {edge.source, edge.target}:
                if node in self.inputs:
                    node.inputs = self.inputs[node]['undo'][:]
            edge.updateEdge()
        # Identify all the endpoints.
        for edge in self.edges:
            for node in {edge.source, edge.target}:
                self.diagram.sgnNodeIdentification.emit(node)
        # Emit updated signal.
        self.diagram.sgnUpdated.emit()
