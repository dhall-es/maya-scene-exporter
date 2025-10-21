import maya.cmds as cmds

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

def bgColor(offset = 0):
    return [0.27 + offset, 0.27 + offset, 0.27 + offset]

class fileNameField:
    def __init__(self, parent):
        self.name = cmds.textField(p = parent, bgc = bgColor(-0.1), placeholderText = "filename", tcc = self.changeCommand)
        self.text = ""
    
    def changeCommand(self, *args):
        import re

        raw = cmds.textField(self, query = True, text = True)
        self.text = re.sub(r'[\\/:*?"<>|]+', '', raw)

        cmds.textField(self, edit = True, text = self.text)

    def __str__(self):
        return self.name

class verticalFormLayout:
    def __init__(self, parent, ebg = True, bgc = [0.27, 0.27, 0.27], w = 25, h = 25):
        self.name = cmds.formLayout(parent = parent,
                                    enableBackground = ebg,
                                    backgroundColor = bgc,
                                    numberOfDivisions = 100,
                                    w = w,
                                    h = h)
        
        self.controls = {
            'top' : [],
            'bottom' : []
        }
    
    def updateLayout(self, xOffset = 4, yOffset = 4):
        attachControl = []
        attachForm = []

        for align in ['top', 'bottom']:
            if (len(self.controls[align]) <= 0):
                continue
            
            attachForm += [(self.controls[align][0], align, yOffset)]

            for control in self.controls[align]:
                attachForm += [(control, 'left', xOffset)]
                attachForm += [(control, 'right', xOffset)]
            
            for i in range(1, len(self.controls[align])):
                attachControl += [(self.controls[align][i], align, yOffset, self.controls[align][i - 1])]

        cmds.formLayout(self.name, edit = True,
                        attachForm = attachForm,
                        attachControl = attachControl)
    
    def __str__(self):
        return self.name

class horizontalFormLayout:
    def __init__(self, parent, ebg = True, bgc = [0.27, 0.27, 0.27], w = 25, h = 25):
        self.name = cmds.formLayout(parent = parent,
                                    enableBackground = ebg,
                                    backgroundColor = bgc,
                                    numberOfDivisions = 100,
                                    w = w,
                                    h = h)
        
        self.controls = {
            'left' : [],
            'right' : []
        }
    
    def updateLayout(self, xOffset = 4, yOffset = 4):
        attachControl = []
        attachForm = []

        for align in ['left', 'right']:
            if (len(self.controls[align]) <= 0):
                continue
            
            attachForm += [(self.controls[align][0], align, yOffset)]

            for control in self.controls[align]:
                attachForm += [(control, 'top', xOffset)]
                attachForm += [(control, 'bottom', xOffset)]
            
            for i in range(1, len(self.controls[align])):
                attachControl += [(self.controls[align][i], align, yOffset, self.controls[align][i - 1])]

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
