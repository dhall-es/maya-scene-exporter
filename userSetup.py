import maya.cmds as cmds

cmds.commandPort(name="localhost:5678", stp="python")
cmds.commandPort(name="localhost:7001", stp="mel")

import maya.utils
import PackageExport.Menu as Menu
import PackageExport.MainWindow as MainWindow

def LoadPackageExporter():
    Menu.Create()

maya.utils.executeDeferred(LoadPackageExporter)