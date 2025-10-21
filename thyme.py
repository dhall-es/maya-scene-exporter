import maya.cmds as cmds
from UIHelpers import *

# workspace layout with:
# source object
# list of clone objects
# option to save/load json(?)

# add icon = addCreateGeneric_100.png
# add icon = newLayerEmpty.png
# delete icon = deleteGeneric_100.png
# refresh icon = refresh.png
# select icon = highlightSelect.png
# select icon = IsolateSelected.png

# background color for toggles = #5285a6 or [0.32, 0.52, 0.65]

global clones
clones = []

global sourceObject
sourceObject = None

global settingsPane
settingsPane = None

global clonesPane
clonesPane = None

global syncSelectEnabled
syncSelectEnabled = False

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
    paneLayout = cmds.paneLayout(configuration = 'vertical2')

    global settingsPane
    global clonesPane

    settingsPane = settingsUI(paneLayout)
    clonesPane = clonesUI(paneLayout)

class settingsUI:
    def __init__(self, parent, lOffset = 2, rOffset = 0):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 600)
        self.title = cmds.frameLayout(p = self, label = "Source Object", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.setButton = cmds.button(p = self, label = "Use Selected Object", h = 25, w = 120,
                                    command = lambda _: self.setSourceToSelected(),
                                    annotation = "Set the source object to what is currently selected in the scene")
        self.nameField = cmds.textField(p = self, bgc = bgColor(-0.1), editable = False,
                                        text = "No object set", h = 25)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.nameField, 'left', lOffset),
                                    (self.setButton, 'right', rOffset)],
                        attachControl = [(self.nameField, 'top', 4, self.title),
                                        (self.setButton, 'top', 4, self.title),
                                        (self.nameField, 'right', 4, self.setButton)])
        
        self.exportButton = cmds.button(p = self, h = 30, label = "Export CSV",
                                        command = lambda _: exportCSV(self.exportDir()))
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.exportButton, 'left', lOffset),
                                      (self.exportButton, 'right', rOffset),
                                      (self.exportButton, 'bottom', 4)])

        self.filenameField = cmds.textField(p = self, bgc = bgColor(-0.1), placeholderText = "filename")
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.filenameField, 'left', lOffset),
                                      (self.filenameField, 'right', rOffset)],
                        attachControl = [(self.filenameField, 'bottom', 4, self.exportButton)])

        self.dirField = directoryField(self)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.dirField, 'left', lOffset),
                                      (self.dirField, 'right', rOffset)],
                        attachControl = [(self.dirField, 'bottom', 4, self.filenameField)])
    
    def exportDir(self):
        import re
        
        fullName = cmds.textField(self.filenameField, query = True, text = True)
        fileName = re.sub(r'[^a-zA-Z0-9]', '', fullName)

        return f"{self.dirField.directory}/{fileName}.csv"

    def setSourceToSelected(self):
        selection = cmds.ls(selection = True, type = 'transform')
        if (len(selection) != 1):
            print("Must have only one object selected to set the source object.")
            return

        global clones
        global sourceObject
        global clonesPane

        if (selection[0] in clones):
            print(f"New source object {selection[0]} found in clones list. Removing {selection[0]} from clones list.")
            sourceObject = clones[clones.index(selection[0])]

            clones.remove(sourceObject)
            clonesPane.updateClonesList()
        else:
            sourceObject = transform(selection[0])
        
        self.updateSourceObject(selection)

    def updateSourceObject(self, selection):
        cmds.textField(self.nameField, edit = True, text = selection[0])

    def __str__(self):
        return self.name
    
    def __eq__(self, value):
        if (type(value) == str):
            return self.name == value
        pass

class syncSelectButton:
    def __init__(self, parent, clonesList):
        self.name = cmds.iconTextButton(p = parent, style = 'iconOnly', bgc = [0.32, 0.52, 0.65], ebg = False,
                            i = 'highlightSelect.png', annotation = "Toggle sync selection." \
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

class clonesUI:
    def __init__(self, parent, lOffset = 0, rOffset = 2):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 600)
        
        self.title = cmds.frameLayout(p = self, label = "Clones", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.buttonLayout = horizontalFormLayout(self, ebg = False)

        self.clonesList = cmds.textScrollList(p = self, allowMultiSelection = True)
        
        self.deleteIcon = cmds.iconTextButton(p = self.buttonLayout, style = 'iconOnly',
                            i = 'deleteGeneric_100.png', annotation = "Delete clones selected in this list",
                            command = self.deleteSelection)
        self.addIcon = cmds.iconTextButton(p = self.buttonLayout, style = 'iconOnly',
                            i = 'addCreateGeneric_100.png', annotation = "Add/Update clones selected in the scene",
                            command = self.addSelection)
        
        self.refreshIcon = cmds.iconTextButton(p = self.buttonLayout, style = 'iconOnly',
                            i = 'refresh.png', annotation = "Update clones that have been moved/deleted",
                            command = self.refreshAll)
        self.syncIcon = syncSelectButton(parent = self.buttonLayout, clonesList = self.clonesList)

        self.buttonLayout.controls['right'] = [self.deleteIcon, self.addIcon]
        self.buttonLayout.controls['left'] = [self.refreshIcon, self.syncIcon]
        self.buttonLayout.updateLayout(0, 0)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.clonesList, 'left', lOffset),
                                    (self.clonesList, 'bottom', 2),
                                    (self.clonesList, 'right', rOffset)],
                        attachControl = [(self.clonesList, 'top', 2, self.buttonLayout)])

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttonLayout, 'left', lOffset),
                                    (self.buttonLayout, 'right', rOffset)],
                        attachControl = [(self.buttonLayout, 'top', 2, self.title)])

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

        global sourceObject
        global clones

        for item in selection:
            if (item == sourceObject):
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

        for clone in ([sourceObject] + clones):
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