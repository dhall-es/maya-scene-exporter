import maya.cmds as cmds

def bgColor(offset = 0):
    return [0.27 + offset, 0.27 + offset, 0.27 + offset]

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
