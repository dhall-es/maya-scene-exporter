import maya.cmds as cmds

windowName = "beefWindow"

exportsList = []
# exportsListLayout = ""

# exportsCountLabel = ""

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
        exportsListLayout.controls.remove(self)
        exportsListLayout.updateLayout()

        global exportsCountLabel
        cmds.text(exportsCountLabel, edit = True, label = f"Ready to export ({len(exportsList)}) files")

    def __str__(self):
        return self.name

class quickFormLayout:
    def __init__(self, parent, ebg = True, bgc = [0.27, 0.27, 0.27]):
        self.name = cmds.formLayout(parent = parent,
                                    enableBackground = ebg,
                                    backgroundColor = bgc,
                                    numberOfDivisions = 100)
        
        self.controls = []
    
    def updateLayout(self, horizontalOffset = 4, verticalOffset = 4):
        if (len(self.controls) <= 0):
            return
        
        attachForm = []
        attachForm += [(self.controls[0], 'top', verticalOffset)]

        for control in self.controls:
            attachForm += [(control, 'left', horizontalOffset)]
            attachForm += [(control, 'right', horizontalOffset)]
        
        attachControl = []
        for i in range(1, len(self.controls)):
            attachControl += [(self.controls[i], 'top', verticalOffset, self.controls[i - 1])]
        
        cmds.formLayout(self.name, edit = True,
                        attachForm = attachForm,
                        attachControl = attachControl)
    
    def __str__(self):
        return self.name

class directoryField:
    def __init__(self, parent):
        self.name = cmds.formLayout(parent = parent, ebg = False, nd = 100)

        self.label = cmds.text("Path:", parent = self, align = 'left')
        self.field = cmds.textField(parent = self, placeholderText = "Choose an export directory",
                                    annotation = "Path to where the file(s) will be saved")
        self.button = cmds.symbolButton(parent = self, image = 'browseFolder_100.png',
                                        annotation = "Browse directory",
                                        command = lambda _: self.browseDir())
        self.directory = ""
        
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.label, 'left', 0), (self.button, 'right', 0),
                                      (self.label, 'top', 0), (self.label, 'bottom', 0),
                                      (self.field, 'top', 0), (self.field, 'bottom', 0),
                                      (self.button, 'top', 0), (self.button, 'bottom', 0)],
                        attachControl = [(self.field, 'left', 2, self.label), (self.field, 'right', 2, self.button)])
        
    def browseDir(self):
        directory = cmds.fileDialog2(fileMode = 3)
        if (directory):
            self.directory = directory[0]
            cmds.textField(self.field, edit = True, text = self.directory)
        
    def __str__(self):
        return self.name

def bgColor(offset = 0):
    return [0.27 + offset, 0.27 + offset, 0.27 + offset]

def export(*args):
    if (len(exportsList) <= 0):
        print("Nothing to export.")
    
    for item in exportsList:
        item.selectThis()
        directory = f"{dirField.directory}/{item.filename}.fbx"
        print(f"exporting {item.filename} to {directory}")
        cmds.file(directory, exportSelected = True, force = True, type = "FBX export",
                  preserveReferences = True, options="v=0;")

def addSelectedSeparate(*args):
    selected = cmds.ls(selection = True)
    if (len(selected) <= 0):
        print("No objects selected.")
        return

    for obj in selected:
        item = exportItem(exportsListLayout, [obj])
    
        global exportsList
        exportsList += [item]
        exportsListLayout.controls += [item]
    
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
    exportsListLayout.controls += [item]
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
    exportsListLayout = quickFormLayout(scrollLayout, False)

    cmds.formLayout(exportsPane, edit = True,
                    attachForm = [(scrollLayout, 'left', 0), (scrollLayout, 'right', 5), (scrollLayout, 'bottom', 5)],
                    attachControl = [(scrollLayout, 'top', 5, addSeparateButton)])
                    
    return exportsPane

def createBeefUI():
    coreLayout = cmds.paneLayout(configuration = 'vertical2')

    settingsTab = createSettingsPane(coreLayout)
    exportsTab = createExportsPane(coreLayout)

def createWindow():
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

createWorkspaceControl(windowName)