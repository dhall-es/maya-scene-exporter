import maya.cmds as cmds

windowName = "beefWindow"

exportsList = []
exportsListLayout = ""

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

        self.scrollLayout = cmds.scrollLayout(parent = self, childResizable = True, bgc = bgColor(-0.09))
        for item in includedObjects:
            cmds.text(item, parent = self.scrollLayout, align = 'left')

        # Select object(s) button
        self.selectButton = cmds.button(parent = self, w = 100, h = 30,
                                        label = "Select object(s)", annotation = "Selects objects included in this export. Works with Shift/Ctrl.",
                                        bgc = bgColor(0.09), command = lambda _: self.selectThis())
        
        # Remove from list button
        self.removeButton = cmds.button(parent = self, w = 100, h = 30,
                                        label = "Remove from list", annotation = "Removes this from the list of exports.",
                                        bgc = bgColor(0.09), command = lambda _: self.removeThis())
        
        # Filename text field
        self.textField = cmds.textField(parent = self, text = includedObjects[0], placeholderText = "filename")

        # Set up layout
        cmds.formLayout(self, edit = True, 
                        attachForm = [(self.scrollLayout, 'left', 4),
                                      (self.scrollLayout, 'top', 4),
                                      (self.scrollLayout, 'bottom', 4),
                                      (self.textField, 'top', 4),
                                      (self.textField, 'right', 4),
                                      (self.selectButton, 'top', 4),
                                      (self.removeButton, 'bottom', 4)],
                        attachPosition = [(self.scrollLayout, 'right', 2, 40),
                                          (self.selectButton, 'left', 2, 40),
                                          (self.removeButton, 'left', 2, 40),
                                          (self.selectButton, 'bottom', 2, 50),
                                          (self.removeButton, 'top', 2, 50),
                                          (self.selectButton, 'right', 2, 70),
                                          (self.removeButton, 'right', 2, 70),
                                          (self.textField, 'left', 2, 70)])
    
    def selectThis(self):
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
        exportsList.remove(self)
        exportsListLayout.controls.remove(self)
        exportsListLayout.updateLayout()

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
                                    annotation = "Path to where the file(s) will be saved.")
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
        self.directory = cmds.fileDialog2(fileMode = 3)[0]
        cmds.textField(self.field, edit = True, text = self.directory)
        
    def __str__(self):
        return self.name

def bgColor(offset = 0):
    return [0.27 + offset, 0.27 + offset, 0.27 + offset]

def addSelected(*args):
    selected = cmds.ls(selection = True)
    if (len(selected) <= 0):
        print("No objects selected.")
        return

    item = exportItem(exportsListLayout, selected)
    
    global exportsList
    exportsList += [item]
    exportsListLayout.controls += [item]
    exportsListLayout.updateLayout()

def createWindow():
    if (cmds.window(windowName, exists = True)):
        cmds.deleteUI(windowName, window = True)

    window = cmds.window(windowName, title = "Beef Window", widthHeight = (500, 600), resizeToFitChildren = True)

    coreLayout = cmds.formLayout(parent = window, enableBackground = False, numberOfDivisions = 100, w = 300, h = 200)

    #region Settings layout (left side)
    settingsLayout = cmds.formLayout(parent = coreLayout, ebg = False, nd = 100, w = 150, h = 100)
    cmds.formLayout(coreLayout, edit = True, 
                    attachForm = [(settingsLayout, 'left', 0), (settingsLayout, 'top', 0), (settingsLayout, 'bottom', 0)],
                    attachPosition = [(settingsLayout, 'right', 0, 50)])

    # "Add Selected" Button
    addButton = cmds.button(parent = settingsLayout, w = 50, h = 30, 
                            label = "Add Selection", annotation = "Adds selected objects as a new list element.",
                            command = addSelected)
    
    cmds.formLayout(settingsLayout, edit = True,
                    attachForm = [(addButton, 'left', 5), (addButton, 'top', 5), (addButton, 'right', 5)])

    # File directory field
    dirField = directoryField(parent = settingsLayout)
    
    cmds.formLayout(settingsLayout, edit = True,
                    attachForm = [(dirField, 'left', 5), (dirField, 'right', 5), (dirField, 'bottom', 5)])

    #endregion

    # Scroll layout w/ list
    global exportsListLayout
    scrollLayout = cmds.scrollLayout(parent = coreLayout, childResizable = True, bgc = bgColor(-0.06))
    exportsListLayout = quickFormLayout(scrollLayout, False)

    cmds.formLayout(coreLayout, edit = True, 
                    attachForm = [(scrollLayout, 'right', 5),
                                  (scrollLayout, 'top', 5),
                                  (scrollLayout, 'bottom', 5)],
                    attachPosition = [(scrollLayout, 'left', 0, 50)])

    # Show Window
    cmds.showWindow(windowName)

createWindow()