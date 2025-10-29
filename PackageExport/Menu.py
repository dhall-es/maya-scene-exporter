import maya.cmds as cmds
from PackageExport import MainWindow

def Create(menuName = "PackageExportMenu"):
    if (cmds.menu(menuName, exists = True)):
        cmds.deleteUI(menuName, menu = True)

    menu = cmds.menu(menuName, label = "Package Exporter", parent = "MayaWindow", tearOff = True)
    cmds.menuItem(label = "Open Window", parent = menu,
                  command = lambda _: MainWindow.Create())