import maya.cmds as cmds

windowName = "beefWindow"

selectedList = []
listLayout = ""

# TODO:
# Change placeholder text for textfield
# Add max size for listLayout in exportItem

class exportItem:
    def __init__(self, parent, includedObjects):
        self.name = cmds.formLayout(parent = parent,
                                    enableBackground = True,
                                    backgroundColor = bgColor(),
                                    numberOfDivisions = 100)
        
        # Scrollable list of objects included
        self.includedObjects = includedObjects

        self.listLayout = cmds.scrollLayout(parent = self, childResizable = True, bgc = bgColor(-0.09))
        for item in includedObjects:
            cmds.text(item, parent = self.listLayout, align = 'left')

        # Select object(s) button
        self.selectButton = cmds.button(parent = self, w = 100, h = 30,
                                        label = "Select object(s)", annotation = "Selects objects included in this export.",
                                        bgc = bgColor(0.09))
        self.removeButton = cmds.button(parent = self, w = 100, h = 30,
                                        label = "Remove from list", annotation = "Removes this from the list of exports.",
                                        bgc = bgColor(0.09))
        
        # Filename text field
        self.textField = cmds.textField(parent = self, placeholderText = includedObjects[0])

        # Set up layout
        cmds.formLayout(self, edit = True, 
                        attachForm = [(self.listLayout, 'left', 4),
                                      (self.listLayout, 'top', 4),
                                      (self.listLayout, 'bottom', 4),
                                      (self.textField, 'top', 4),
                                      (self.textField, 'right', 4),
                                      (self.selectButton, 'top', 4),
                                      (self.removeButton, 'bottom', 4)],
                        attachPosition = [(self.listLayout, 'right', 2, 40),
                                          (self.selectButton, 'left', 2, 40),
                                          (self.removeButton, 'left', 2, 40),
                                          (self.selectButton, 'bottom', 2, 50),
                                          (self.removeButton, 'top', 2, 50),
                                          (self.selectButton, 'right', 2, 70),
                                          (self.removeButton, 'right', 2, 70),
                                          (self.textField, 'left', 2, 70)])
    
    def __str__(self):
        return self.name
        
        

def bgColor(offset = 0):
    return [0.27 + offset, 0.27 + offset, 0.27 + offset]

def addSelected(*args):
    selected = cmds.ls(selection = True, type = 'transform')

    global selectedList
    selectedList += [exportItem(listLayout, selected)]

def createWindow():
    if cmds.window(windowName, exists = True):
        cmds.deleteUI(windowName, window = True)

    window = cmds.window(windowName, title = "Beef Window", widthHeight = (500, 600))

    coreLayout = cmds.formLayout(parent = window, enableBackground = False, numberOfDivisions = 100)

    # "Add Selected" Button
    addButton = cmds.button(parent = coreLayout, w = 100, h = 30, 
                            label = "Add Selection", annotation = "Adds selected objects as a new list element.",
                            command = addSelected)
    
    cmds.formLayout(coreLayout, edit = True, attachForm = [(addButton, 'left', 5), (addButton, 'top', 5)], attachPosition = [(addButton, 'right', 5, 50)])

    # Scroll layout w/ list
    global listLayout
    listLayout = cmds.scrollLayout(parent = coreLayout, childResizable = True, bgc = bgColor(-0.06))

    cmds.formLayout(coreLayout, edit = True, attachForm = [(listLayout, 'right', 5), (listLayout, 'top', 5), (listLayout, 'bottom', 5)], attachPosition = [(listLayout, 'left', 0, 50)])

    # Show Window
    cmds.showWindow(windowName)

createWindow()