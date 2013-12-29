import os
import sys

from rv import rvtypes, commands

sys.path.append('/home/aberg/py26/lib/python2.6/site-packages')

from PyQt4 import QtGui
from PyQt4 import QtCore

PROP_FUNC_MAP = {
    1: commands.getFloatProperty,
    2: commands.getIntProperty,
    8: commands.getStringProperty
}

PROP_FUNC_MAP_SET = {
    1: commands.setFloatProperty,
    2: commands.setIntProperty,
    8: commands.setStringProperty
}

class PropItemWidget(QtGui.QWidget):
    def __init__(self, name='', values=[]):
        super(PropItemWidget, self).__init__()
        layout = QtGui.QHBoxLayout()
        self.name = name
        self.setLayout(layout)
        self.values = values
        self.value_items = []

    def on_update(self, *value):
        print 'on update value:', self.name, value

class PropFloatWidget(PropItemWidget):
    def __init__(self, name, values):
        super(PropFloatWidget, self).__init__()
        self.name = name
        self.values = values
        self.add_widgets(values)

    def on_update(self, *value):
        values = []
        for item in self.value_items:
            values.append(item.value())
        PROP_FUNC_MAP_SET[1](self.name, values, False)

    def add_widgets(self, values):
        spin_rows_layout = QtGui.QVBoxLayout()
        current_row_layout = QtGui.QHBoxLayout()
        spin_rows_layout.addChildLayout(current_row_layout)

        for index, val in enumerate(values):
            if index % 4 == 0:
                current_row_layout = QtGui.QHBoxLayout()
                spin_rows_layout.addLayout(current_row_layout)

            spin_box = QtGui.QDoubleSpinBox()
            spin_box.setMaximum(999999)
            spin_box.setMinimum(-999999)
            self.value_items.append(spin_box)
            spin_box.setValue(val)
            spin_box.valueChanged.connect(self.on_update)
            current_row_layout.addWidget(spin_box)

        self.layout().addLayout((spin_rows_layout))


class PropIntWidget(PropItemWidget):
    def __init__(self, name, values):
        super(PropIntWidget, self).__init__()
        self.name = name
        self.values = values
        self.add_widgets(values)

    def on_update(self, *value):
        values = []
        for item in self.value_items:
            values.append(item.value())
        PROP_FUNC_MAP_SET[2](self.name, values, False)

    def add_widgets(self, values):
        for val in values:
            spin_box = QtGui.QSpinBox()
            self.value_items.append(spin_box)
            spin_box.valueChanged.connect(self.on_update)
            spin_box.setValue(val)
            self.layout().addWidget(spin_box)


class PropStringWidget(PropItemWidget):
    def __init__(self, name, values):
        super(PropStringWidget, self).__init__()
        self.name = name
        self.values = values
        self.add_widgets(values)

    def on_update(self, *value):
        values = []
        for item in self.value_items:
            values.append(str(item.text()))
        PROP_FUNC_MAP_SET[8](self.name, values, False)

    def add_widgets(self, values):
        for val in values:
            line_edit = QtGui.QLineEdit()
            self.value_items.append(line_edit)
            line_edit.returnPressed.connect(self.on_update)
            line_edit.setText(val)
            self.layout().addWidget(line_edit)


PROP_WIDGET_ITEM_MAP = {
    1: PropFloatWidget,
    2: PropIntWidget,
    8: PropStringWidget
}


class Property(object):
    def __init__(self, name):
        self.name = name

    def get_info(self):
        return commands.propertyInfo(self.name)

    def get_type(self):
        return self.get_info()['type']

    def get_value(self):
        prop_func = PROP_FUNC_MAP.get(self.get_type())
        if not prop_func:
            raise RuntimeError('Property not found %s' % self.get_type())
        return prop_func(self.name, 0, 20000)


class Node(object):
    def __init__(self, name):
        self.name = name

    def get_properties(self):
        return [Property(prop) for prop in commands.properties(self.name)]

    def get_property(self, prop_name):
        for prop in self.get_properties():
            if not prop.name.endswith(prop_name):
                continue
            return prop

    def get_type(self):
        return commands.nodeType(self.name)

    def get_attrs(self):
        return commands.sourceAttributes(self.name, None)


class Source(object):
    def __init__(self, name):
        self.name = name

    def get_group(self):
        return Group(commands.nodeGroup(self.name))


class Group(object):
    def __init__(self, name):
        self.name = name

    def get_media_name(self):
        node = self.get_node('_source')
        if not node:
            return
        prop = node.get_property('media.movie')
        if not prop:
            return
        movie = prop.get_value()
        return os.path.basename(movie[0])

    def get_node(self, node_name):
        for node in self.get_nodes():
            if not node.name.endswith(node_name):
                continue
            return node

    def get_nodes(self):
        return [Node(node) for node in commands.nodesInGroup(self.name)]


class Model(object):
    def __init__(self):
        pass

    @staticmethod
    def get_sources():
        return [Source(source) for source in commands.sourcesAtFrame(commands.frame())]


class PropertyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(PropertyWidget, self).__init__(parent)

        self.tree = QtGui.QTreeWidget()
        self.tree.setHeaderLabels(['Node', 'Value'])
        self.tree.setAlternatingRowColors(True)

        update_button = QtGui.QPushButton('Update')

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(self.tree)
        main_layout.addWidget(update_button)

        self.setLayout(main_layout)

        update_button.clicked.connect(self.on_update)

        commands.bind("PropertyWidget", "global", "graph-node-inputs-changed", self.graph_event, "Doc String")

        self.on_update()

    def graph_event(self, event):
        self.on_update()

    def on_update(self):
        self.tree.clear()
        self.update_tree()
        for index in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(index)


    def update_tree(self):

        sources = Model.get_sources()
        for source in sources:
            group = source.get_group()
            group_item = QtGui.QTreeWidgetItem([group.get_media_name()])
            self.tree.addTopLevelItem(group_item)
            group_item.setExpanded(True)

            nodes = group.get_nodes()
            for node in nodes:
                node_item = QtGui.QTreeWidgetItem([node.name])
                group_item.addChild(node_item)
                attrs = node.get_attrs()
                if attrs:
                    attrs_item = QtGui.QTreeWidgetItem(['Source Attributes'])
                    for attr in attrs:
                        attr_item = QtGui.QTreeWidgetItem([attr[0], ', '.join(attr[1:])])
                        attrs_item.addChild(attr_item)
                    node_item.addChild(attrs_item)
                properties = node.get_properties()
                for prop in properties:
                    item_class = PROP_WIDGET_ITEM_MAP[prop.get_type()]
                    prop_item = QtGui.QTreeWidgetItem([prop.name, ''])
                    prop_item_widget = item_class(prop.name, prop.get_value())
                    node_item.addChild(prop_item)
                    self.tree.setItemWidget(prop_item, 1, prop_item_widget)


class DockWidget(QtGui.QDockWidget):
    def __init__(self, parent=None):
        super(DockWidget, self).__init__(parent)
        self.setWindowTitle('Properties')
        self.setWidget(PropertyWidget())


class PropertyMode(rvtypes.MinorMode):
    """
    property explorer
    """

    def show_properties(self, event):

        # odd, need to keep a reference to the widget here or the
        # signals wouldn't come through
        if self.dock_wid is None:
            self.dock_wid = DockWidget()
        self.dock_wid.show()

        main_win = self.get_main_window()
        if not main_win:
            return
        main_win.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_wid)


    def get_main_window(self):
        widgets = QtGui.QApplication.topLevelWidgets()
        for wid in widgets:
            if not isinstance(wid, QtGui.QMainWindow):
                continue
            return wid


    def __init__(self):
        rvtypes.MinorMode.__init__(self)
        self.dock_wid = None
        self.init("PropertyWidget",
                  None,
                  None,
                  [
                      ("Tools",
                       [("Properties Panel", self.show_properties, None, None)]
                      )
                  ]
        )


def createMode():
    "Required to initialize the module. RV will call this function to create your mode."
    return PropertyMode()
