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

global currentPackage
currentPackage = None

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
                                    nd = 100, w = 10, h = 50)
        
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
        
        self.openIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly', bgc = [0.32, 0.52, 0.65], ebg = False,
                                            i = 'outArrow.png', annotation = "Move to package editor",
                                            command = self.open)
        self.selectIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                                              i = 'selectBackFacingUV.png', annotation = "Select objects from this package",
                                              command = self.select)
        self.deleteIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                                              i = 'deleteGeneric_100.png', annotation = "Delete this package",
                                              command = self.delete)
        
        self.buttons.controls['left'] = [self.deleteIcon]
        self.buttons.controls['right'] = [self.openIcon, self.selectIcon]
        self.buttons.updateLayout(0, 0)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttons, 'left', 2),
                                      (self.buttons, 'right', 2),
                                      (self.buttons, 'bottom', 2)])

    def select(self, modifiers = True):
        if (not modifiers):
            cmds.select(self.items, replace = True)
            return
        
        mods = getModifiers()
        shift = mods.__contains__('Shift')
        ctrl = mods.__contains__('Ctrl')

        if (shift and ctrl):
            cmds.select(self.items, add = True)
        elif(shift):
            cmds.select(self.items, toggle = True)
        elif(ctrl):
            cmds.select(self.items, deselect = True)
        else:
            cmds.select(self.items, replace = True)

    def delete(self):
        global packManagerPane
        packManagerPane.removePackage(self)

    def open(self):
        global currentPackage
        if (currentPackage == self):
            return
        
        global packManagerPane
        packManagerPane.setCurrentPackage(self)

    def updateUI(self, isCurrent):
        cmds.text(self.itemCount, edit = True, label = f"{len(self.items)} Item(s)")

        if (isCurrent):
            cmds.iconTextButton(self.openIcon, edit = True, ebg = True,
                                annotation = "Currently in package editor")
        else:
            cmds.iconTextButton(self.openIcon, edit = True, ebg = False,
                                annotation = "Move to package editor")

    def getFileName(self):
        return self.nameField.text

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
            'name' : self.name,
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
            translate = list(cmds.getAttr(f"{self}.translate")[0])
            pivot = list(cmds.getAttr(f"{self}.rotatePivot")[0])
            for i in range(len(translate)): translate[i] += pivot[i]

            self.attributes = {
                'name' : self.name,
                'translate' : translate,
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

class settingsUI:
    def __init__(self, parent, lOffset = 2, rOffset = 2):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 120)
        self.title = cmds.frameLayout(p = self, label = "Export Settings", collapsable = True, collapse = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.scroll = cmds.scrollLayout(p = self.title, childResizable = True, h = 1)
        self.collapse = cmds.formLayout(p = self.scroll, ebg = False, nd = 100, w = 100)
        
        extraOffset = 4
        
        # Export Toggles

        self.jsonToggle = cmds.checkBox(p = self.collapse, label = "Export JSON scene", value = True,
                                       changeCommand = lambda _: self.onJSONToggle())
        self.fbxToggle = cmds.checkBox(p = self.collapse, label = "Export FBX meshes", value = True,
                                       changeCommand = lambda _: self.onFBXToggle())

        cmds.formLayout(self.collapse, edit = True,
                        attachForm = [(self.jsonToggle, 'left', lOffset + extraOffset * 3),
                                      (self.fbxToggle, 'right', lOffset + extraOffset * 3),
                                      (self.fbxToggle, 'top', 2), (self.jsonToggle, 'top', 2)])

        # Root Transform field
        self.rootSetButton = cmds.button(p = self.collapse, label = "Use Selected Object", h = 25, w = 120,
                                    command = lambda _: self.setRootToSelected(),
                                    annotation = "Set the root transform to currently selected object")
        self.rootNameField = cmds.textField(p = self.collapse, bgc = bgColor(-0.1), editable = False,
                                        text = "No root transform set", h = 25)
        cmds.formLayout(self.collapse, edit = True,
                        attachForm = [(self.rootNameField, 'left', lOffset + extraOffset),
                                     (self.rootSetButton, 'right', rOffset + extraOffset)],
                        attachControl = [(self.rootNameField, 'right', 4, self.rootSetButton),
                                         (self.rootNameField, 'top', 4, self.fbxToggle),
                                         (self.rootSetButton, 'top', 4, self.fbxToggle)])

        # FBX Settings Frame
        self.fbxSettings = self.fbxSettingsLayout(self.collapse)
        cmds.formLayout(self.collapse, edit = True,
                        attachForm = [(self.fbxSettings, 'left', lOffset),
                                     (self.fbxSettings, 'right', rOffset)],
                        attachControl = [(self.fbxSettings, 'top', 4, self.rootNameField)])

        # Bottom Controls
        self.exportButton = cmds.button(p = self, h = 30, label = "Export FBX and JSON",
                                        command = lambda _: export())
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
                        attachControl = [(self.dirField, 'bottom', 4, self.fileName),
                                         (self.title, 'bottom', 4, self.dirField)])

    def onFBXToggle(self):
        v = cmds.checkBox(self.fbxToggle, query = True, value = True)

        cmds.frameLayout(self.fbxSettings, edit = True, enable = v)

        self.onToggle()

    def onJSONToggle(self):
        v = cmds.checkBox(self.jsonToggle, query = True, value = True)

        cmds.button(self.rootSetButton, edit = True, enable = v)
        cmds.textField(self.rootNameField, edit = True, enable = v,
                       bgc = bgColor(-0.1))
        
        self.onToggle()

    def onToggle(self):
        fbxEnabled = cmds.checkBox(self.fbxToggle, query = True, value = True)
        jsonEnabled = cmds.checkBox(self.jsonToggle, query = True, value = True)

        if (fbxEnabled and jsonEnabled):
            cmds.button(self.exportButton, edit = True, enable = True,
                        label = "Export FBX and JSON")
        elif(fbxEnabled):
            cmds.button(self.exportButton, edit = True, enable = True,
                        label = "Export FBX")
        elif(jsonEnabled):
            cmds.button(self.exportButton, edit = True, enable = True,
                        label = "Export JSON")
        else:
            cmds.button(self.exportButton, edit = True, enable = False,
                        label = "Export")

    def setRootToSelected(self):
        selection = cmds.ls(selection = True, type = 'transform')
        if (len(selection) != 1):
            cmds.confirmDialog(title = 'Root transform not set', button = ['Ok'], icon = 'critical', message = "" \
            "You must have only one object selected in the scene to set the root transform.")
            return

        global rootTransform
        global packEditorPane
        
        rootTransform = transform(selection[0])
        self.updateRootTransformUI(selection)

    def updateRootTransformUI(self, selection):
        cmds.textField(self.rootNameField, edit = True, text = selection[0])

    def __str__(self):
        return self.name
    
    def __eq__(self, value):
        if (type(value) == str):
            return self.name == value
        pass

    class fbxSettingsLayout():
        class fbxCheckbox:
            def __init__(self, parent, label, defaultValue, fbxproperty):
                self.name = cmds.checkBox(p = parent, l = label, v = defaultValue,
                                        changeCommand = lambda _: self.onUIChanged())
                self.fbxproperty = fbxproperty
                self.value = defaultValue
            
            def onUIChanged(self):
                self.value = cmds.checkBox(self, query = True, value = True)
            
            def sendProperty(self):
                cmds.FBXProperty(self.fbxproperty, '-v', int(self.value))

            def __str__(self):
                return self.name

        def __init__(self, parent):
            self.name = cmds.frameLayout(p = parent, label = "FBX Settings", collapsable = True, collapse = True)

            self.vForm = verticalFormLayout(parent = self, ebg = False)

            self.vForm.controls['top'] += [self.fbxCheckbox(self.vForm, "Smoothing Groups", True, 'Export|IncludeGrp|Geometry|SmoothingGroups')]
            self.vForm.controls['top'] += [self.fbxCheckbox(self.vForm, "Smooth Mesh", True, 'Export|IncludeGrp|Geometry|SmoothMesh')]
            self.vForm.controls['top'] += [self.fbxCheckbox(self.vForm, "Split Vertex Normals", False, 'Export|IncludeGrp|Geometry|expHardEdges')]
            self.vForm.controls['top'] += [self.fbxCheckbox(self.vForm, "Triangulate", False, 'Export|IncludeGrp|Geometry|Triangulate')]
            self.vForm.controls['top'] += [self.fbxCheckbox(self.vForm, "Tangents & Binormals", False, 'Export|IncludeGrp|Geometry|TangentsandBinormals')]

            self.vForm.controls['top'] += [self.fbxCheckbox(self.vForm, "Skinning", True, 'Export|IncludeGrp|Animation|Deformation|Skins')]
            self.vForm.controls['top'] += [self.fbxCheckbox(self.vForm, "Blendshapes", True, 'Export|IncludeGrp|Animation|Deformation|Shape')]

            self.vForm.updateLayout(xOffset = 12)

        def sendProperties(self):
            for checkbox in self.vForm.controls['top']:
                checkbox.sendProperty()
        
        def __str__(self):
            return self.name

class packManagerUI:
    def __init__(self, parent, lOffset = 2, rOffset = 0):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 50)

        self.title = cmds.frameLayout(p = self, label = "Package Manager", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.buttons = horizontalFormLayout(self, ebg = False)
        self.addIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                                           i = 'addCreateGeneric_100.png', annotation = "Add empty package",
                                           command = self.addPackage)
        self.buttons.controls['left'] = [self.addIcon]
        self.buttons.updateLayout(0, 2)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttons, 'left', lOffset),
                                      (self.buttons, 'right', rOffset)],
                        attachControl = [(self.buttons, 'top', 0, self.title)])

        self.scrollLayout = cmds.scrollLayout(p = self, childResizable = True, bgc = bgColor(-0.1),
                                              w = 10, h = 1)
        self.packageList = verticalFormLayout(self.scrollLayout, False, w = 10, h = 600)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.scrollLayout, 'left', lOffset),
                                      (self.scrollLayout, 'right', rOffset),
                                      (self.scrollLayout, 'bottom', 2)],
                        attachControl = [(self.scrollLayout, 'top', 0, self.buttons)])
        
        self.setCurrentPackage(self.addPackage())

    def setCurrentPackage(self, pack):
        global currentPackage

        if (currentPackage):
            currentPackage.updateUI(False)
        
        currentPackage = pack
        currentPackage.updateUI(True)
        
        global packEditorPane
        if (packEditorPane):
            packEditorPane.updateItemsList()

    def removePackage(self, pack):
        self.packageList.controls['top'].remove(pack)
        self.packageList.updateLayout(yOffset = 4, h = 54 * len(self.packageList.controls['top']))

        if (len(self.packageList.controls['top']) <= 0):
            self.setCurrentPackage(self.addPackage())
        else:
            self.setCurrentPackage(self.packageList.controls['top'][0])

    def addPackage(self):
        new = package(self.packageList)

        self.packageList.controls['top'] += [new]
        self.packageList.updateLayout(yOffset = 4, h = 54 * len(self.packageList.controls['top']))

        return new

    def __str__(self):
        return self.name

class packEditorUI:
    def __init__(self, parent, lOffset = 0, rOffset = 2):
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 50)
        
        self.title = cmds.frameLayout(p = self, label = "Package Editor", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        self.buttons = horizontalFormLayout(self, ebg = False)

        self.itemsList = cmds.textScrollList(p = self, allowMultiSelection = True,
                                             emptyLabel = "No items in the current package\n\nUse the buttons above to add/manage items")
        
        self.deleteIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'deleteGeneric_100.png', annotation = "Delete items selected in this list",
                            command = self.deleteSelection)
        self.addIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'addCreateGeneric_100.png', annotation = "Add/Update items selected in the scene",
                            command = self.addSelection)
        
        self.refreshIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'refresh.png', annotation = "Update items that have been moved/deleted",
                            command = self.refreshAll)
        self.syncIcon = self.syncSelectButton(parent = self.buttons, itemsList = self.itemsList)

        self.buttons.controls['right'] = [self.deleteIcon, self.addIcon]
        self.buttons.controls['left'] = [self.refreshIcon, self.syncIcon]
        self.buttons.updateLayout(0, 0)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.itemsList, 'left', lOffset),
                                    (self.itemsList, 'bottom', 2),
                                    (self.itemsList, 'right', rOffset)],
                        attachControl = [(self.itemsList, 'top', 2, self.buttons)])

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttons, 'left', lOffset),
                                    (self.buttons, 'right', rOffset)],
                        attachControl = [(self.buttons, 'top', 2, self.title)])

    def refreshAll(self):
        global currentPackage

        for item in currentPackage.items:
            if (not item.update()):
                currentPackage.items.remove(item)
        self.updateItemsList()

    def deleteSelection(self):
        selection = cmds.textScrollList(self.itemsList, query = True, selectItem = True)
        if (selection == None):
            print("No items in list selected.")
            return

        global currentPackage

        for item in selection:
            currentPackage.items.remove(item)

        self.updateItemsList()

    def addSelection(self):
        selection = cmds.ls(selection = True, type = 'transform')
        if (len(selection) <= 0):
            print("No objects selected.")
            return

        global rootTransform
        global currentPackage

        for item in selection:
            if (item == rootTransform):
                continue

            if (item in currentPackage.items):
                currentPackage.items[currentPackage.items.index(item)].update()
                continue
            
            currentPackage.items += [transform(item)]

        self.updateItemsList()

        if (syncSelectEnabled):
            cmds.textScrollList(self.itemsList, edit = True, selectItem = selection)

    def updateItemsList(self):
        cmds.textScrollList(self.itemsList, edit = True, removeAll = True)
        cmds.textScrollList(self.itemsList, edit = True, append = sorted(currentPackage.items, key = lambda t: t.name))
        currentPackage.updateUI(True)

    def __str__(self):
        return self.name

    class syncSelectButton:
        def __init__(self, parent, itemsList):
            self.name = cmds.iconTextButton(p = parent, style = 'iconOnly', bgc = [0.32, 0.52, 0.65], ebg = False,
                                i = 'selectCycle.png', annotation = "Toggle sync selection." \
                                "\nHold CTRL to transfer list selection to scene." \
                                "\nHold SHIFT to transfer scene selection to list.",
                                command = self.pressSyncSelect)
            
            self.syncSelectJob = -1

            cmds.textScrollList(itemsList, edit = True, selectCommand = self.listSelectionChanged)
            self.itemsList = itemsList
        
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
            listSelection = cmds.textScrollList(self.itemsList, query = True, selectItem = True)
            sceneSelection = cmds.ls(selection = True, type = 'transform')
            
            cmds.textScrollList(self.itemsList, edit = True, deselectAll = True)
            
            if (listSelection == None):
                listSelection = []

            for item in currentPackage.items:
                if (item in sceneSelection or item in listSelection):
                    cmds.textScrollList(self.itemsList, edit = True,selectItem = item)
                    cmds.select(item, add = True)
                else:
                    cmds.select(item, deselect = True)

        def sceneSelectionChanged(self, force = False):
            if (not syncSelectEnabled and not force):
                return

            selection = cmds.ls(selection = True, type = 'transform')
            cmds.textScrollList(self.itemsList, edit = True, deselectAll = True)

            if (len(selection) <= 0):
                return

            for item in currentPackage.items:
                if (item in selection):
                    cmds.textScrollList(self.itemsList, edit = True, selectItem = item)
        
        def listSelectionChanged(self, force = False):
            if (not syncSelectEnabled and not force):
                return
            
            selection = cmds.textScrollList(self.itemsList, query = True, selectItem = True)
            if (selection == None):
                selection = []

            for item in currentPackage.items:
                if (item in selection):
                    cmds.select(item, add = True)
                else:
                    cmds.select(item, deselect = True)
        
        def __str__(self):
            return self.name

def packageExporterUI():
    topBottomPanes = cmds.paneLayout(configuration = 'horizontal2')
    leftRightPanes = cmds.paneLayout(configuration = 'vertical2', p = topBottomPanes)

    global settingsPane
    global packManagerPane
    global packEditorPane

    settingsPane = settingsUI(topBottomPanes)
    packManagerPane = packManagerUI(leftRightPanes)
    packEditorPane = packEditorUI(leftRightPanes)

    cmds.paneLayout(topBottomPanes, edit = True, paneSize = [2, 100, 10])

def export():
    global settingsPane
    fbxEnabled = cmds.checkBox(settingsPane.fbxToggle, query = True, value = True)
    jsonEnabled = cmds.checkBox(settingsPane.jsonToggle, query = True, value = True)

    if (not fbxEnabled and not jsonEnabled):
        return
    
    global packManagerPane
    namesList = []
    hasEmptyNames = False
    hasEmptyPackages = False

    for pack in packManagerPane.packageList.controls['top']:
        fileName = pack.getFileName()

        if (fileName == ""):
            hasEmptyNames = True
        
        if (len(pack.items) <= 0):
            hasEmptyPackages = True

        namesList += [fileName]

    if (settingsPane.fileName.text == ""):
        cmds.confirmDialog(title = 'Invalid filename', button = ['Ok'], icon = 'critical',
                           message = 'Please enter a valid filename.')
        return

    import os
    if (not os.path.isdir(settingsPane.dirField.directory)):
        cmds.confirmDialog(title = 'Invalid export directory', button = ['Ok'], icon = 'critical',
                           message = f"Path \"{settingsPane.dirField.directory}\"" \
        "\nis invalid or does not exist.\n\nPlease enter a valid path.")
        return

    if (len(namesList) != len(set(namesList))):
        cmds.confirmDialog(title = 'Error', button = ['Ok'], icon = 'critical', message = "" \
        "You have one or more packages with the same name.\n\nPlease rename the packages and try again.")
        return

    if (hasEmptyPackages):
        response = cmds.confirmDialog(title = 'Warning', button = ['Continue','Cancel'],
                           defaultButton = 'Cancel', cancelButton = 'Cancel',
                           dismissString = 'Cancel', icon = 'warning', message = "" \
        "You have one or more packages with no items.\n\nThese will not be exported.")

        if (response == 'Cancel'):
            return

    if (hasEmptyNames):
        response = cmds.confirmDialog(title = 'Warning', button = ['Continue','Cancel'],
                           defaultButton = 'Cancel', cancelButton = 'Cancel',
                           dismissString = 'Cancel', icon = 'warning', message = "" \
        "You have one or more packages with no filename." \
        "\n\nThese will not be exported.")

        if (response == 'Cancel'):
            return

    global rootTransform
    if (jsonEnabled and rootTransform == None):
        response = cmds.confirmDialog(title = 'Warning', button = ['Continue','Cancel'],
                           defaultButton = 'Cancel', cancelButton = 'Cancel',
                           dismissString = 'Cancel', icon = 'warning', message = "" \
        "The root transform has not been set." \
        "\n\nThis may cause issues when loading the JSON scene somewhere else.")

        if (response == 'Cancel'):
            return

    if (fbxEnabled):
        exportFBX()
    if (jsonEnabled):
        exportJSON()

def exportFBX():
    global settingsPane
    settingsPane.fbxSettings.sendProperties()

    print(f"Starting FBX Export to {settingsPane.dirField.directory}...")

    global packManagerPane
    for pack in packManagerPane.packageList.controls['top']:
        fileName = pack.getFileName()

        if (len(pack.items) <= 0):
            print(f"No items in {fileName} package, skipping...")
            continue

        pack.select(False) # Select w/o modifiers so holding Shift + export doesn't break things

        if (fileName == ""):
            print("Skipped exporting package due to empty filename")
            continue

        directory = f"{settingsPane.dirField.directory}/{fileName}.fbx"

        print(f"Exporting {fileName} package to {directory}")
        # -s makes it export selected instead of export all
        cmds.FBXExport("-file", directory, "-s")

    print(f"Finished FBX Export to {settingsPane.dirField.directory}.")

def exportJSON():
    global settingsPane
    fullPath = f"{settingsPane.dirField.directory}/{settingsPane.fileName.text}.json"

    print(f"Starting JSON Export to {fullPath}...")

    import json
    packageData = []

    global packManagerPane
    for pack in packManagerPane.packageList.controls['top']:
        transformData = []
        fileName = pack.getFileName()

        if (len(pack.items) <= 0):
            print(f"No items in {fileName} package. It will be left out of the scene JSON.")
            continue

        if (fileName == ""):
            print(f"Package is missing a filename. It will be left out of the scene JSON.")
            continue

        for item in pack.items:
            transformData += [item.getRelativeAttributes(rootTransform)]

        packageData += [{
            "fileName" : fileName,
            "transforms" : transformData
        }]

    scene = {
        "rootTransform" : rootTransform.attributes,
        "packages" : packageData
    }

    sceneJson = json.dumps(scene, indent = 4)
    with open(fullPath, 'w') as f:
        f.write(sceneJson)

    print(f"Finished JSON Export to {fullPath}...")

def createWorkspaceControl(windowName):
    if (cmds.workspaceControl(windowName, exists = True)):
            cmds.workspaceControl(windowName, edit=True, close = True)

    cmds.workspaceControl(windowName, retain = False, floating = True, uiScript = "packageExporterUI()",
                          mw = 290, mh = 250, label = "Package Exporter")

createWorkspaceControl("packageExporterWindow")