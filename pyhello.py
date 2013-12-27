from rv import rvtypes, commands

import sys
sys.path.append('/home/aberg/py26/lib/python2.6/site-packages')
from PyQt4 import QtGui
from PyQt4 import QtCore

prop_func_map = {
    1: commands.getFloatProperty,
    8: commands.getStringProperty,
    2: commands.getIntProperty
}


class BaseProperty(object):
    def __init__(self, name):
        self.name = name

    def get_info(self):
        return commands.propertyInfo(self.name)

    def get_type(self):
        return self.get_info()['type']

    def get_value(self):
        prop_func = prop_func_map.get(self.get_type())
        if not prop_func:
            raise RuntimeError('Property not found %s' % self.get_type())
        return prop_func(self.name, 0, 20000)


class Node(object):
    def __init__(self, name):
        self.name = name

    def get_properties(self):
        return [BaseProperty(prop) for prop in commands.properties(self.name)]

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

    def get_nodes(self):
        return [Node(node) for node in commands.nodesInGroup(self.name)]


class Model(object):
    def __init__(self):
        pass

    @staticmethod
    def get_sources(self):
        return [Source(source) for source in commands.sourcesAtFrame(commands.frame())]


class PropertyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(PropertyWidget, self).__init__(parent)

        self.tree = QtGui.QTreeWidget()
        self.tree.setHeaderLabels(['Node', 'Value'])

        update_button = QtGui.QPushButton('Update', self)
        update_button.pressed.connect(self.on_update)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(self.tree)
        main_layout.addWidget(update_button)

        self.setLayout(main_layout)

    def on_update(self, *args):
        self.tree.clear()
        self.update_tree()
        print 'update'


    def update_tree(self):

        sources = Model.get_sources()
        for source in sources:
            group = source.get_group()
            group_item = QtGui.QTreeWidgetItem([group.name])
            self.tree.addTopLevelItem(group_item)

            nodes = group.get_nodes()
            for node in nodes:
                node_item = QtGui.QTreeWidgetItem([node.name])
                group_item.addChild(node_item)
                print 'attrs:', node.get_attrs()
                properties = node.get_properties()
                for prop in properties:
                    prop_item = QtGui.QTreeWidgetItem([prop.name, str(prop.get_value())])
                    node_item.addChild(prop_item)


class DockWidget(QtGui.QDockWidget):
    def __init__(self, parent=None):
        super(DockWidget, self).__init__(parent)
        self.setWindowTitle('Properties')
        self.setWidget(PropertyWidget())


class PyHello(rvtypes.MinorMode):
    """
    property explorer
    """

    def show_properties(self, event):
        main_win = self.get_main_window()
        if not main_win:
            return
        dock_wid = DockWidget()
        main_win.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_wid)

    def source_info(self, event):
        sources = self.model.get_sources()
        for source in sources:
            group = source.get_group()
            nodes = group.get_nodes()
            for node in nodes:
                print 'attrs:', node.get_attrs()
                properties = node.get_properties()
                print 'props:', properties
                for prop in properties:
                    print 'prop info:', prop.get_info()
                    print prop.get_value()


    def get_main_window(self):
        widgets = QtGui.QApplication.topLevelWidgets()
        for wid in widgets:
            if not isinstance(wid, QtGui.QMainWindow):
                continue
            return wid


    def __init__(self):
        rvtypes.MinorMode.__init__(self)
        self.model = Model()




        self.init("pyhello",
                  [("key-down--z", self.show_properties, "z key")],
                  None)


def createMode():
    "Required to initialize the module. RV will call this function to create your mode."
    return PyHello()
