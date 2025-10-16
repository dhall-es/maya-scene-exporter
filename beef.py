import maya.cmds as cmds
from UIHelpers import *

# https://polycount.com/discussion/232359/example-of-using-fbxproperties-mel-command-to-query-all-properties

# Smoothing Groups | cmds.FBXProperty('Export|IncludeGrp|Geometry|SmoothingGroups', '-v', 1)
# Smooth Mesh | cmds.FBXProperty('Export|IncludeGrp|Geometry|SmoothMesh', '-v', 1)
# Split Vertex Normals | cmds.FBXProperty('Export|IncludeGrp|Geometry|expHardEdges', '-v', 0)
# Triangulate | cmds.FBXProperty('Export|IncludeGrp|Geometry|Triangulate', '-v', 0)
# Tangents & Binormals | cmds.FBXProperty('Export|IncludeGrp|Geometry|TangentsandBinormals', '-v', 0)

# Skinning | cmds.FBXProperty('Export|IncludeGrp|Animation|Deformation|Skins', '-v', 1)
# Blendshapes | cmds.FBXProperty('Export|IncludeGrp|Animation|Deformation|Shape', '-v', 1)

def getModifiers():
    output = []
    mods = cmds.getModifiers()

    if (mods & 1) > 0:
        output += ['Shift']
    if (mods & 4) > 0:
        output += ['Ctrl']
    if (mods & 8) > 0:
        output += ['Alt']
    if (mods & 16):
        output += ['Win']
    
    return output

class exportItem:
    def __init__(self, parent, includedObjects):
        self.name = cmds.formLayout(parent = parent,
                                    enableBackground = True,
                                    backgroundColor = bgColor(),
                                    numberOfDivisions = 100,
                                    w = 100, h = 100)
        
        # Scrollable list of objects included
        self.includedObjects = includedObjects

        self.scrollLayout = cmds.scrollLayout(parent = self, childResizable = True, bgc = bgColor(-0.12),
                                              annotation = "Objects included in this export")
        for item in includedObjects:
            cmds.text(item, parent = self.scrollLayout, align = 'left')

        # Select object(s) button
        self.selectButton = cmds.button(parent = self, w = 100, h = 30,
                                        label = "Select object(s)", annotation = "Selects objects included in this export. Works with Shift/Ctrl",
                                        bgc = bgColor(0.09), command = lambda _: self.selectThis(True))
        
        # Remove from list button
        self.removeButton = cmds.button(parent = self, w = 100, h = 30,
                                        label = "Remove from list", annotation = "Removes this from the list of exports",
                                        bgc = bgColor(0.09), command = lambda _: self.removeThis())
        
        # Filename text field
        self.textField = cmds.textField(parent = self, text = includedObjects[0], placeholderText = "filename",
                                        annotation = "filename", w = 150, bgc = bgColor(-0.12),
                                        textChangedCommand = self.textChanged)
        self.filename = str(includedObjects[0])

        # Set up layout
        cmds.formLayout(self, edit = True, 
                        attachForm = [(self.scrollLayout, 'right', 4),
                                      (self.scrollLayout, 'top', 4),
                                      (self.scrollLayout, 'bottom', 4),
                                      (self.textField, 'top', 4),
                                      (self.textField, 'left', 4),
                                      (self.selectButton, 'top', 4),
                                      (self.removeButton, 'bottom', 4)],
                        attachControl = [(self.selectButton, 'left', 4, self.textField),
                                         (self.removeButton, 'left', 4, self.textField),
                                         (self.scrollLayout, 'left', 4, self.selectButton)],
                        attachPosition = [(self.selectButton, 'bottom', 2, 50),
                                          (self.removeButton, 'top', 2, 50)])
    
    def textChanged(self, *args):
        self.filename = args[0]

    def selectThis(self, modifiers = False):
        if (not modifiers):
            cmds.select(self.includedObjects, replace = True)
            return
        
        mods = getModifiers()
        shift = mods.__contains__('Shift')
        ctrl = mods.__contains__('Ctrl')

        if (shift and ctrl):
            cmds.select(self.includedObjects, add = True)
        elif(shift):
            cmds.select(self.includedObjects, toggle = True)
        elif(ctrl):
            cmds.select(self.includedObjects, deselect = True)
        else:
            cmds.select(self.includedObjects, replace = True)

    def removeThis(self):
        cmds.deleteUI(self, layout = True)

        global exportsList
        exportsList.remove(self)
        exportsListLayout.controls['top'].remove(self)
        exportsListLayout.updateLayout()

        global exportsCountLabel
        cmds.text(exportsCountLabel, edit = True, label = f"Ready to export ({len(exportsList)}) files")

    def __str__(self):
        return self.name

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

class fbxSettingsLayout (verticalFormLayout):
    def __init__(self, parent):
        super().__init__(parent = parent, ebg = False)

        self.controls['top'] += [fbxCheckbox(self, "Smoothing Groups", True, 'Export|IncludeGrp|Geometry|SmoothingGroups')]
        self.controls['top'] += [fbxCheckbox(self, "Smooth Mesh", True, 'Export|IncludeGrp|Geometry|SmoothMesh')]
        self.controls['top'] += [fbxCheckbox(self, "Split Vertex Normals", False, 'Export|IncludeGrp|Geometry|expHardEdges')]
        self.controls['top'] += [fbxCheckbox(self, "Triangulate", False, 'Export|IncludeGrp|Geometry|Triangulate')]
        self.controls['top'] += [fbxCheckbox(self, "Tangents & Binormals", False, 'Export|IncludeGrp|Geometry|TangentsandBinormals')]

        self.controls['top'] += [fbxCheckbox(self, "Skinning", True, 'Export|IncludeGrp|Animation|Deformation|Skins')]
        self.controls['top'] += [fbxCheckbox(self, "Blendshapes", True, 'Export|IncludeGrp|Animation|Deformation|Shape')]

        self.updateLayout()

    def sendProperties(self):
        for checkbox in self.controls['top']:
            checkbox.sendProperty()

def export(*args):
    if (len(exportsList) <= 0):
        print("Nothing to export.")
    
    global fbxSettings
    fbxSettings.sendProperties()

    for item in exportsList:
        item.selectThis()
        if (item.filename == ""):
            print("Skipped export due to empty filename")
            continue

        directory = f"{dirField.directory}/{item.filename}.fbx"
        print(f"exporting {item.filename} to {directory}")

        # -s makes it export selected instead of export all
        cmds.FBXExport("-file", directory, "-s")

def addSelectedSeparate(*args):
    selected = cmds.ls(selection = True)
    if (len(selected) <= 0):
        print("No objects selected.")
        return

    for obj in selected:
        item = exportItem(exportsListLayout, [obj])
    
        global exportsList
        exportsList += [item]
        exportsListLayout.controls['top'] += [item]
    
    exportsListLayout.updateLayout()

    global exportsCountLabel
    cmds.text(exportsCountLabel, edit = True, label = f"Ready to export ({len(exportsList)}) files")

def addSelectedSingle(*args):
    selected = cmds.ls(selection = True)
    if (len(selected) <= 0):
        print("No objects selected.")
        return

    item = exportItem(exportsListLayout, selected)
    
    global exportsList
    exportsList += [item]
    exportsListLayout.controls['top'] += [item]
    exportsListLayout.updateLayout()

    global exportsCountLabel
    cmds.text(exportsCountLabel, edit = True, label = f"Ready to export ({len(exportsList)}) files")

def createSettingsPane(coreLayout):
    settingsPane = cmds.formLayout(parent = coreLayout, ebg = False, nd = 100, w = 150, h = 100)
    
    # Export button
    exportButton = cmds.button(parent = settingsPane, h = 30, command = export, label = "Export")
    cmds.formLayout(settingsPane, edit = True,
                    attachForm = [(exportButton, 'left', 5), (exportButton, 'right', 0), (exportButton, 'bottom', 5)])
    
    # File directory field
    global dirField
    dirField = directoryField(parent = settingsPane)
    
    cmds.formLayout(settingsPane, edit = True,
                    attachForm = [(dirField, 'left', 5), (dirField, 'right', 0)],
                    attachControl = [(dirField, 'bottom', 5, exportButton)])
    
    global fbxSettings
    fbxSettings = fbxSettingsLayout(settingsPane)

    cmds.formLayout(settingsPane, edit = True,
                    attachForm = [(fbxSettings, 'left', 5),
                                  (fbxSettings, 'right', 0),
                                  (fbxSettings, 'top', 5)])

    return settingsPane

def createExportsPane(coreLayout):
    exportsPane = cmds.formLayout(parent = coreLayout, ebg = False, nd = 100, w = 150, h = 100)

    # Exports count label
    global exportsCountLabel
    exportsCountLabel = cmds.text(parent = exportsPane, align = 'left', label = f"Ready to export ({len(exportsList)}) files")
    
    cmds.formLayout(exportsPane, edit = True, attachForm = [(exportsCountLabel, 'top', 55), (exportsCountLabel, 'left', 5)])    

    # "Add Selected (single)" Button
    addSingleButton = cmds.button(parent = exportsPane, w = 150, h = 30, command = addSelectedSingle,
                            label = "Add Selection (single)", annotation = "Adds selected objects to be exported as one file")
    
    cmds.formLayout(exportsPane, edit = True,
                    attachForm = [(addSingleButton, 'top', 5), (addSingleButton, 'right', 5)])
    
    # "Add Selected (separate)" Button
    addSeparateButton = cmds.button(parent = exportsPane, w = 150, h = 30, command = addSelectedSeparate,
                            label = "Add Selection (separate)", annotation = "Adds selected objects to be exported as multiple files")
    
    cmds.formLayout(exportsPane, edit = True, attachForm = [(addSeparateButton, 'right', 5)],
                    attachControl = [(addSeparateButton, 'top', 5, addSingleButton)])
    
    # Scroll area and list of exports
    scrollLayout = cmds.scrollLayout(parent = exportsPane, childResizable = True, bgc = bgColor(-0.06))

    global exportsListLayout
    exportsListLayout = verticalFormLayout(scrollLayout, False)

    cmds.formLayout(exportsPane, edit = True,
                    attachForm = [(scrollLayout, 'left', 0), (scrollLayout, 'right', 5), (scrollLayout, 'bottom', 5)],
                    attachControl = [(scrollLayout, 'top', 5, addSeparateButton)])
                    
    return exportsPane

def createBeefUI():
    global exportsList
    exportsList = []

    coreLayout = cmds.paneLayout(configuration = 'vertical2')

    settingsTab = createSettingsPane(coreLayout)
    exportsTab = createExportsPane(coreLayout)

def createWindow(windowName):
    """
    Backup function for creating the window. Ideally you would use workspaceControl since it docks to the UI,
    but sometimes they can be a little finnicky.
    """
    if (cmds.window(windowName, exists = True)):
        cmds.deleteUI(windowName, window = True)

    window = cmds.window(windowName, title = "Beef Window", widthHeight = (500, 600), resizeToFitChildren = True)
    createBeefUI(window)
    cmds.showWindow(windowName)

def createWorkspaceControl(windowName):
    if (cmds.workspaceControl(windowName, exists = True)):
            cmds.workspaceControl(windowName, edit=True, close = True)

    cmds.workspaceControl(windowName, retain = False, floating = True, uiScript = "createBeefUI()",
                          mw = 500, mh = 600, label = "Exporter")

createWorkspaceControl("beefWindow")