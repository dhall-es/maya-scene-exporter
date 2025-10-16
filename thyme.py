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
# select icon = isolateSelected.png

# background color for toggles = #5285a6 or [0.32, 0.52, 0.65]

global clones
clones = []

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

    def update(self):
        self.attributes = {
            'translate' : list(cmds.getAttr(f"{self.name}.translate")[0]),
            'rotate' : list(cmds.getAttr(f"{self.name}.rotate")[0]),
            'scale' : list(cmds.getAttr(f"{self.name}.scale")[0]),
        }

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
    
    def setSourceToSelected(self):
        selection = cmds.ls(selection = True, type = 'transform')
        if (len(selection) != 1):
            print("Must have only one object selected to set the source object.")
            return

        global clones
        global sourceObject
        global clonesPane

        if (selection[0] in clones):
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
    
class clonesUI:
    def __init__(self, parent, lOffset = 0, rOffset = 2):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 600)
        
        self.title = cmds.frameLayout(p = self, label = "Clones", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.buttonLayout = horizontalFormLayout(self, ebg = False)
        
        self.delete = cmds.iconTextButton(p = self.buttonLayout, style = 'iconOnly',
                            i = 'deleteGeneric_100.png', annotation = "Delete clones selected in this list",
                            command = self.deleteSelection)
        self.add = cmds.iconTextButton(p = self.buttonLayout, style = 'iconOnly',
                            i = 'addCreateGeneric_100.png', annotation = "Add clones selected in the scene",
                            command = self.addSelection)
        
        self.refresh = cmds.iconTextButton(p = self.buttonLayout, style = 'iconOnly',
                            i = 'refresh.png', annotation = "Update clones that have been moved/deleted")

        self.buttonLayout.controls['right'] = [self.delete, self.add]
        self.buttonLayout.controls['left'] = [self.refresh]
        self.buttonLayout.updateLayout(0, 0)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttonLayout, 'left', lOffset),
                                    (self.buttonLayout, 'right', rOffset)],
                        attachControl = [(self.buttonLayout, 'top', 2, self.title)])

        self.clonesList = cmds.textScrollList(p = self, allowMultiSelection = True)
        
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.clonesList, 'left', lOffset),
                                    (self.clonesList, 'bottom', 2),
                                    (self.clonesList, 'right', rOffset)],
                        attachControl = [(self.clonesList, 'top', 2, self.buttonLayout)])
    
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

    def updateClonesList(self):
        cmds.textScrollList(self.clonesList, edit = True, removeAll = True)
        cmds.textScrollList(self.clonesList, edit = True, append = clones)

    def __str__(self):
        return self.name

def createWorkspaceControl(windowName):
    if (cmds.workspaceControl(windowName, exists = True)):
            cmds.workspaceControl(windowName, edit=True, close = True)

    cmds.workspaceControl(windowName, retain = False, floating = True, uiScript = "cloneManagerUI()",
                          mw = 500, mh = 600, label = "Clone Manager")

createWorkspaceControl("cloneManagerWindow")