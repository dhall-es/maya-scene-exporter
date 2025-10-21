import maya.cmds as cmds
from UIHelpers import *

# add icon = addCreateGeneric_100.png
# add icon = newLayerEmpty.png
# delete icon = deleteGeneric_100.png
# refresh icon = refresh.png
# select icon = highlightSelect.png
# select icon = selectCycle.png
# select icon = selectBackFacingUV.png

# background color for toggles = #5285a6 or [0.32, 0.52, 0.65]

global clones
clones = []

global rootTransform
rootTransform = None

global settingsPane
settingsPane = None

global packManagerPane
settingsPane = None

global packEditorPane
packEditorPane = None

global syncSelectEnabled
syncSelectEnabled = False

class package:
    def __init__(self, parent):
        self.name = cmds.formLayout(p = parent, ebg = True, bgc = bgColor(),
                                    nd = 100, w = 100, h = 50)
        
        self.items = []

        self.nameField = fileNameField(self)
        self.itemCount = cmds.text(p = self, align = 'left', label = f"{len(self.items)} Item(s)")
        cmds.formLayout(self, edit = True, 
                        attachForm = [(self.nameField, 'top', 2),
                                      (self.nameField, 'left', 2),
                                      (self.itemCount, 'top', 4),
                                      (self.itemCount, 'right', 4)],
                        attachPosition = [(self.nameField, 'right', 0, 75),
                                          (self.itemCount, 'left', 4, 75)])
        
        self.buttons = horizontalFormLayout(self, False)
        
        self.openIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                                            i = 'outArrow.png', annotation = "Move to package editor")
        self.selectIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                                              i = 'selectBackFacingUV.png', annotation = "Select objects from this package")
        self.deleteIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                                              i = 'deleteGeneric_100.png', annotation = "Delete this package")
        
        self.buttons.controls['left'] = [self.deleteIcon]
        self.buttons.controls['right'] = [self.openIcon, self.selectIcon]
        self.buttons.updateLayout(0, 0)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttons, 'left', 2),
                                      (self.buttons, 'right', 2),
                                      (self.buttons, 'bottom', 2)])

    def __str__(self):
        return self.name

class transform:
    def __init__(self, name):
        self.name = name
        self.update()
    
    def getRelativeAttributes(self, other):
        
        translate = self.attributes['translate']
        
        for i, value in enumerate(other.attributes['translate']):
            translate[i] -= value

        rotate = self.attributes['rotate']
        for i, value in enumerate(other.attributes['rotate']):
            rotate[i] -= value

        scale = self.attributes['scale']
        for i, value in enumerate(other.attributes['scale']):
            scale[i] /= value

        return {
            'translate' : translate,
            'rotate' : rotate,
            'scale' : scale
        }

    def update(self, force = True):
        if (not cmds.objExists(self)):
            return False
        elif (cmds.objectType(self) != 'transform'):
            return False

        if (force):
            self.attributes = {
                'translate' : list(cmds.getAttr(f"{self}.translate")[0]),
                'rotate' : list(cmds.getAttr(f"{self}.rotate")[0]),
                'scale' : list(cmds.getAttr(f"{self}.scale")[0]),
            }

        return True

    def __str__(self):
        return self.name
    
    def __eq__(self, value):
        if (type(value) == str):
            return self.name == value
        pass

def cloneManagerUI():
    topBottomPanes = cmds.paneLayout(configuration = 'horizontal2')
    leftRightPanes = cmds.paneLayout(configuration = 'vertical2', p = topBottomPanes)

    global settingsPane
    global packManagerPane
    global packEditorPane

    settingsPane = settingsUI(topBottomPanes)
    packManagerPane = packManagerUI(leftRightPanes)
    packEditorPane = packEditorUI(leftRightPanes)

    cmds.paneLayout(topBottomPanes, edit = True, paneSize = [2, 100, 10])

class settingsUI:
    def __init__(self, parent, lOffset = 2, rOffset = 2):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 160)
        self.title = cmds.frameLayout(p = self, label = "Export Settings", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.setButton = cmds.button(p = self, label = "Use Selected Object", h = 25, w = 120,
                                    command = lambda _: self.setRootToSelected(),
                                    annotation = "Set the root transform to currently selected object")
        self.nameField = cmds.textField(p = self, bgc = bgColor(-0.1), editable = False,
                                        text = "No root transform set", h = 25)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.nameField, 'left', lOffset),
                                    (self.setButton, 'right', rOffset)],
                        attachControl = [(self.nameField, 'top', 4, self.title),
                                        (self.setButton, 'top', 4, self.title),
                                        (self.nameField, 'right', 4, self.setButton)])
        
        self.exportButton = cmds.button(p = self, h = 30, label = "Export CSV",
                                        command = lambda _: exportCSV(f"{self.dirField.directory}/{self.fileName.text}.csv"))
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.exportButton, 'left', lOffset),
                                      (self.exportButton, 'right', rOffset),
                                      (self.exportButton, 'bottom', 4)])

        self.fileName = fileNameField(self)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.fileName, 'left', lOffset),
                                      (self.fileName, 'right', rOffset)],
                        attachControl = [(self.fileName, 'bottom', 4, self.exportButton)])

        self.dirField = directoryField(self)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.dirField, 'left', lOffset),
                                      (self.dirField, 'right', rOffset)],
                        attachControl = [(self.dirField, 'bottom', 4, self.fileName)])

    def setRootToSelected(self):
        selection = cmds.ls(selection = True, type = 'transform')
        if (len(selection) != 1):
            print("Must have only one object selected to set the root transform.")
            return

        global clones
        global rootTransform
        global packEditorPane
        
        rootTransform = transform(selection[0])
        self.updateRootTransform(selection)

    def updateRootTransform(self, selection):
        cmds.textField(self.nameField, edit = True, text = selection[0])

    def __str__(self):
        return self.name
    
    def __eq__(self, value):
        if (type(value) == str):
            return self.name == value
        pass

class packManagerUI:
    def __init__(self, parent, lOffset = 2, rOffset = 0):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 80)

        self.title = cmds.frameLayout(p = self, label = "Package Manager", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.scrollLayout = cmds.scrollLayout(p = self, childResizable = True, bgc = bgColor(-0.1))
        self.packageList = verticalFormLayout(self.scrollLayout, False)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.scrollLayout, 'left', lOffset),
                                      (self.scrollLayout, 'right', rOffset),
                                      (self.scrollLayout, 'bottom', 2)],
                        attachControl = [(self.scrollLayout, 'top', 4, self.title)])
        
        self.addPackage()

    def addPackage(self):
        self.packageList.controls['top'] += [package(self.packageList)]
        self.packageList.updateLayout()

    def __str__(self):
        return self.name

class packEditorUI:
    def __init__(self, parent, lOffset = 0, rOffset = 2):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 80)
        
        self.title = cmds.frameLayout(p = self, label = "Package Editor", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.buttons = horizontalFormLayout(self, ebg = False)

        self.clonesList = cmds.textScrollList(p = self, allowMultiSelection = True)
        
        self.deleteIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'deleteGeneric_100.png', annotation = "Delete clones selected in this list",
                            command = self.deleteSelection)
        self.addIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'addCreateGeneric_100.png', annotation = "Add/Update clones selected in the scene",
                            command = self.addSelection)
        
        self.refreshIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'refresh.png', annotation = "Update clones that have been moved/deleted",
                            command = self.refreshAll)
        self.syncIcon = self.syncSelectButton(parent = self.buttons, clonesList = self.clonesList)

        self.buttons.controls['right'] = [self.deleteIcon, self.addIcon]
        self.buttons.controls['left'] = [self.refreshIcon, self.syncIcon]
        self.buttons.updateLayout(0, 0)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.clonesList, 'left', lOffset),
                                    (self.clonesList, 'bottom', 2),
                                    (self.clonesList, 'right', rOffset)],
                        attachControl = [(self.clonesList, 'top', 2, self.buttons)])

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttons, 'left', lOffset),
                                    (self.buttons, 'right', rOffset)],
                        attachControl = [(self.buttons, 'top', 2, self.title)])

    def refreshAll(self):
        global clones
        for clone in clones:
            if (not clone.update()):
                clones.remove(clone)
        self.updateClonesList()

    def deleteSelection(self):
        selection = cmds.textScrollList(self.clonesList, query = True, selectItem = True)
        if (selection == None):
            print("No items in list selected.")
            return

        global clones
        for item in selection:
            clones.remove(item)

        self.updateClonesList()

    def addSelection(self):
        selection = cmds.ls(selection = True, type = 'transform')
        if (len(selection) <= 0):
            print("No objects selected.")
            return

        global rootTransform
        global clones

        for item in selection:
            if (item == rootTransform):
                continue

            if (item in clones):
                clones[clones.index(item)].update()
                continue
            
            clones += [transform(item)]

        self.updateClonesList()

        if (syncSelectEnabled):
            cmds.textScrollList(self.clonesList, edit = True, selectItem = selection)

    def updateClonesList(self):
        cmds.textScrollList(self.clonesList, edit = True, removeAll = True)
        cmds.textScrollList(self.clonesList, edit = True, append = sorted(clones, key = lambda t: t.name))

    def __str__(self):
        return self.name

    class syncSelectButton:
        def __init__(self, parent, clonesList):
            self.name = cmds.iconTextButton(p = parent, style = 'iconOnly', bgc = [0.32, 0.52, 0.65], ebg = False,
                                i = 'selectCycle.png', annotation = "Toggle sync selection." \
                                "\nHold CTRL to transfer list selection to scene." \
                                "\nHold SHIFT to transfer scene selection to list.",
                                command = self.pressSyncSelect)
            
            self.syncSelectJob = -1

            cmds.textScrollList(clonesList, edit = True, selectCommand = self.listSelectionChanged)
            self.clonesList = clonesList
        
        def pressSyncSelect(self):
            modifiers = getModifiers()
            
            shift = 'Shift' in modifiers
            ctrl = 'Ctrl' in modifiers

            if (shift and ctrl):
                self.quickSyncSelection()
                return
            elif (shift):
                self.sceneSelectionChanged(force = True)
                return
            elif (ctrl):
                self.listSelectionChanged(force = True)
                return
            
            global syncSelectEnabled

            if (syncSelectEnabled):
                cmds.iconTextButton(self, edit = True, ebg = False)
                syncSelectEnabled = False
                cmds.scriptJob(kill = self.syncSelectJob)
                return
            
            cmds.iconTextButton(self, edit = True, ebg = True)
            syncSelectEnabled = True

            self.syncSelectJob = cmds.scriptJob(event = ["SelectionChanged", self.sceneSelectionChanged],
                                                parent = self, compressUndo = True)
            
            self.quickSyncSelection()
            
        def quickSyncSelection(self):
            listSelection = cmds.textScrollList(self.clonesList, query = True, selectItem = True)
            sceneSelection = cmds.ls(selection = True, type = 'transform')
            
            cmds.textScrollList(self.clonesList, edit = True, deselectAll = True)
            
            if (listSelection == None):
                listSelection = []

            for clone in clones:
                if (clone in sceneSelection or clone in listSelection):
                    cmds.textScrollList(self.clonesList, edit = True,selectItem = clone)
                    cmds.select(clone, add = True)
                else:
                    cmds.select(clone, deselect = True)

        def sceneSelectionChanged(self, force = False):
            if (not syncSelectEnabled and not force):
                return

            selection = cmds.ls(selection = True, type = 'transform')
            cmds.textScrollList(self.clonesList, edit = True, deselectAll = True)

            if (len(selection) <= 0):
                return

            for clone in clones:
                if (clone in selection):
                    cmds.textScrollList(self.clonesList, edit = True, selectItem = clone)
        
        def listSelectionChanged(self, force = False):
            if (not syncSelectEnabled and not force):
                return
            
            selection = cmds.textScrollList(self.clonesList, query = True, selectItem = True)
            if (selection == None):
                selection = []

            for clone in clones:
                if (clone in selection):
                    cmds.select(clone, add = True)
                else:
                    cmds.select(clone, deselect = True)
        
        def __str__(self):
            return self.name

def exportCSV(fullPath):
    import csv

    global clones

    columns = ['name']
    columns += ['translate']
    columns += ['rotate']
    columns += ['scale']

    # 'w' for writing
    with open(fullPath, 'w', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(columns)

        for clone in ([rootTransform] + clones):
            data = []
            data.append(clone.name)

            data.append(clone.attributes['translate'])
            data.append(clone.attributes['rotate'])
            data.append(clone.attributes['scale'])

            writer.writerow(data)
            del data

def createWorkspaceControl(windowName):
    if (cmds.workspaceControl(windowName, exists = True)):
            cmds.workspaceControl(windowName, edit=True, close = True)

    cmds.workspaceControl(windowName, retain = False, floating = True, uiScript = "cloneManagerUI()",
                          mw = 500, mh = 600, label = "Clone Manager")

createWorkspaceControl("cloneManagerWindow")