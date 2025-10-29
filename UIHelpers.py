import maya.cmds as cmds

def getModifiers():
    '''
    Returns a list of 'modifier' keys held. (i.e. Shift, Ctrl, Alt, Win)\n
    :returns list[str]: The names of the modifier keys currently held.
    '''
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
    '''
    Returns the default grey maya background color.\n
    :param double offset: A flat value to add to each color channel, to make it brighter/darker.
    :returns list[double]: A grey color represented as a list of channel values.
    '''
    return [0.27 + offset, 0.27 + offset, 0.27 + offset]

class fileNameField:
    '''
    A maya UI text field that automatically excludes the characters \/:*?"<>|
    '''
    def __init__(self, parent):
        '''
        :param str parent: The maya UI object set to be the parent of this.
        '''
        self.name = cmds.textField(p = parent, bgc = bgColor(-0.1), placeholderText = "filename", tcc = self.changeCommand)
        self.text = ""
    
    def setName(self, value):
        '''
        Set the text of the field. Automatically excludes the characters \/:*?"<>|
        '''
        import re

        self.text = re.sub(r'[\\/:*?"<>|]+', '', value)

        cmds.textField(self, edit = True, text = self.text)

    # self.name textChangedCommand
    def changeCommand(self, *args):
        import re

        raw = cmds.textField(self, query = True, text = True)
        self.text = re.sub(r'[\\/:*?"<>|]+', '', raw)

        cmds.textField(self, edit = True, text = self.text)

    # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
    def __str__(self):
        return self.name

class verticalFormLayout:
    '''
    A maya UI formLayout that automatically lays out children vertically.
    \nPlace children under x.controls['top'] or x.controls['bottom']
    \nUpdate the layout by calling x.updateLayout()
    '''
    def __init__(self, parent, ebg = True, bgc = [0.27, 0.27, 0.27], w = None, h = None):
        '''
        :param str parent: The maya UI object set to be the parent of this.
        :param bool ebg: Whether to enable the background.
        :param list[double] bgc: The background color of this layout.
        :param int w: The maximum width of this layout. If this has not been set, the layout should stretch horizontally.
        :param int h: The maximum height of this layout. If this has not been set, the layout should stretch vertically.
        '''
        self.name = cmds.formLayout(parent = parent,
                                    enableBackground = ebg,
                                    backgroundColor = bgc,
                                    numberOfDivisions = 100)
        
        if (w):
            cmds.formLayout(self, edit = True, w = w)
        if (h):
            cmds.formLayout(self, edit = True, h = h)

        self.controls = {
            'top' : [],
            'bottom' : []
        }
    
    def updateLayout(self, xOffset = 4, yOffset = 4, w = None, h = None):
        '''
        Automatically attaches this layouts' controls.
        \n- All controls will be attached to the left and right.
        \n- The first top/bottom control will be attached to the form's top/bottom.
        \n- Consecutive top/bottom controls with be attached to the previous top/bottom control.
        :param int xOffset: The horizontal offset for controls in the layout. This acts as both the margin and the spacing between controls.
        :param int yOffset: The vertical offset for controls in the layout. This acts as both the margin and the spacing between controls.
        :param int w: The maximum width of this layout. If this has not been set, the layout should stretch horizontally.
        :param int h: The maximum height of this layout. If this has not been set, the layout should stretch vertically.
        '''
        attachControl = []
        attachForm = []

        for align in ['top', 'bottom']:
            if (len(self.controls[align]) <= 0):
                continue
            
            # Attach first control to form
            attachForm += [(self.controls[align][0], align, yOffset)]

            # Attach all controls to sides
            for control in self.controls[align]:
                attachForm += [(control, 'left', xOffset)]
                attachForm += [(control, 'right', xOffset)]
            
            # Attach consecutive controls to previous controls
            for i in range(1, len(self.controls[align])):
                attachControl += [(self.controls[align][i], align, yOffset, self.controls[align][i - 1])]

        cmds.formLayout(self.name, edit = True,
                        attachForm = attachForm,
                        attachControl = attachControl)
        
        if (w):
            cmds.formLayout(self, edit = True, w = w)
        if (h):
            cmds.formLayout(self, edit = True, h = h)
    
    # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
    def __str__(self):
        return self.name

class horizontalFormLayout:
    '''
    A maya UI formLayout that automatically lays out children horizontally.
    \nPlace children under x.controls['left'] or x.controls['right']
    \nUpdate the layout by calling x.updateLayout()
    '''
    def __init__(self, parent, ebg = True, bgc = [0.27, 0.27, 0.27], w = None, h = None):
        '''
        :param str parent: The maya UI object set to be the parent of this.
        :param bool ebg: Whether to enable the background.
        :param list[double] bgc: The background color of this layout.
        :param int w: The maximum width of this layout. If this has not been set, the layout should stretch horizontally.
        :param int h: The maximum height of this layout. If this has not been set, the layout should stretch vertically.
        '''
        self.name = cmds.formLayout(parent = parent,
                                    enableBackground = ebg,
                                    backgroundColor = bgc,
                                    numberOfDivisions = 100)
        
        if (w):
            cmds.formLayout(self, edit = True, w = w)
        if (h):
            cmds.formLayout(self, edit = True, h = h)

        self.controls = {
            'left' : [],
            'right' : []
        }
    
    def updateLayout(self, xOffset = 4, yOffset = 4, w = None, h = None):
        '''
        Automatically attaches this layouts' controls.
        \n- All controls will be attached to the top and bottom.
        \n- The first left/right control will be attached to the form's left/right.
        \n- Consecutive left/right controls with be attached to the previous left/right control.
        :param int xOffset: The horizontal offset for controls in the layout. This acts as both the margin and the spacing between controls.
        :param int yOffset: The vertical offset for controls in the layout. This acts as both the margin and the spacing between controls.
        :param int w: The maximum width of this layout. If this has not been set, the layout should stretch horizontally.
        :param int h: The maximum height of this layout. If this has not been set, the layout should stretch vertically.
        '''
        attachControl = []
        attachForm = []

        for align in ['left', 'right']:
            if (len(self.controls[align]) <= 0):
                continue
            
            # Attach first control to form
            attachForm += [(self.controls[align][0], align, xOffset)]

            # Attach all controls to top/bottom
            for control in self.controls[align]:
                attachForm += [(control, 'top', yOffset)]
                attachForm += [(control, 'bottom', yOffset)]

            # Attach consecutive controls to previous controls
            for i in range(1, len(self.controls[align])):
                attachControl += [(self.controls[align][i], align, xOffset, self.controls[align][i - 1])]

        cmds.formLayout(self.name, edit = True,
                        attachForm = attachForm,
                        attachControl = attachControl)
        
        if (w):
            cmds.formLayout(self, edit = True, w = w)
        if (h):
            cmds.formLayout(self, edit = True, h = h)

    # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
    def __str__(self):
        return self.name

class directoryField:
    '''
    A field in the maya UI where the user can enter a directory. Includes a label, a text field and a browse button.
    '''
    def __init__(self, parent):
        '''
        :param str parent: The maya UI object set to be the parent of this.
        '''
        self.name = cmds.formLayout(parent = parent, ebg = False, nd = 100)

        self.label = cmds.text("Path:", parent = self, align = 'left')
        self.field = cmds.textField(parent = self, placeholderText = "Choose an export directory",
                                    annotation = "Path to where the file(s) will be saved",
                                    tcc = self.changeCommand, bgc = bgColor(-0.1))
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
    
    # self.field text changed command
    def changeCommand(self, *args):
        import re

        raw = cmds.textField(self.field, query = True, text = True)
        self.directory = re.sub(r'[*?"<>|]+', '', raw)

        cmds.textField(self.field, edit = True, text = self.directory)

    # self.button button command
    def browseDir(self):
        '''
        Browse to set a directory in this field.
        \nIf the field has a valid directory already, browsing will start there.
        '''
        start = None

        import os
        if (os.path.isdir(self.directory)):
            start = self.directory
        directory = cmds.fileDialog2(fileMode = 3, startingDirectory = start)

        if (directory):
            self.directory = directory[0]
            cmds.textField(self.field, edit = True, text = self.directory)
    
    # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
    def __str__(self):
        return self.name
