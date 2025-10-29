import maya.cmds as cmds
from PackageExport.UIHelpers import *

# add icon = addCreateGeneric_100.png
# add icon = newLayerEmpty.png
# delete icon = deleteGeneric_100.png
# refresh icon = refresh.png
# select icon = highlightSelect.png
# select icon = selectCycle.png
# select icon = selectBackFacingUV.png

#  blue background color for toggles = #5285a6 or [0.32, 0.52, 0.65]
# green background color for toggles = #5FAD88 or [0.37, 0.68, 0.53]

global currentPackage
currentPackage = None

global rootTransform
rootTransform = None

global settingsPane
settingsPane = None

global packManagerPane
packManagerPane = None

global packEditorPane
packEditorPane = None

global syncSelectEnabled
syncSelectEnabled = False

def autoGeneratePackages(*args):
    '''
    Automatically generates packages by looking through the scene for similar shapes.
    \nNote that this process can easily mistake objects to be similar, especially those with applied transforms.
    '''
    
    global currentPackage
    global packManagerPane
    global packEditorPane

    # Turn off sync select
    packEditorPane.syncIcon.setSyncSelect(False)

    # Get all transforms
    allTransforms = cmds.ls(long = True, type = 'transform', visible = True)
    # convert to shapes, so there's 1 shape per transform (there can be more than 1, which leads to duplicates in the package list)
    allShapes = cmds.filterExpand(allTransforms, fullPath = True, selectionMask = 12)

    # Initialise progress bar. Progress is calculated based on the amount of shapes that have been checked in the scene.
    import maya.mel as mel
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    cmds.progressBar(gMainProgressBar, edit = True, beginProgress = True,
                     isInterruptable = True, status = 'Auto-generating packages...',
                     maxValue = len(allShapes))

    for _ in range(len(allShapes)):
        if (cmds.progressBar(gMainProgressBar, query = True, isCancelled = True)):
            break
        
        if (len(allShapes) <= 0):
            break
        # Add new package
        packManagerPane.setCurrentPackage(packManagerPane.addPackage())
        
        # Take a shape from the list to base the package off of
        packageShapes = [allShapes.pop()]

        # Update the progress bar since there's one less shape to iterate through
        cmds.progressBar(gMainProgressBar, edit = True, step = 1)

        # Iterate through the rest of the list
        i = 0
        for _ in range(len(allShapes)):
            if (cmds.progressBar(gMainProgressBar, query = True, isCancelled = True)):
                break
            if (i >= len(allShapes)):
                break

            # Check if they're similar based on 'Face Descriptions' (i.e. face topology, edge count) and based on UV sets
            similar = cmds.polyCompare(packageShapes[0], allShapes[i], faceDesc = True, uvSets = True) == 0

            # If the shape is similar, add it to the package and remove it from the list
            if (similar):
                shape = allShapes.pop(i)
                packageShapes.append(shape)

                # Update the progress bar since there's one less shape to iterate through
                cmds.progressBar(gMainProgressBar, edit = True, step = 1)
            else:
                # Only increment i when a shape doesn't match, so we don't skip past things accidentally when removing items
                i += 1
        
        # Get transforms for package shapes
        for shapeTransform in cmds.listRelatives(packageShapes, parent = True, fullPath = True):
            currentPackage.items.append(transform(shapeTransform))
        currentPackage.nameField.setName(str(currentPackage.items[0]))

    packManagerPane.setCurrentPackage(packManagerPane.packageList.controls['top'][0])
    cmds.progressBar(gMainProgressBar, edit = True, endProgress = True)

def getSelection():
    '''
    Gets selected mesh transforms in the scene.
    \nIf a group transform is selected, this function will return all of the child meshes of that group.

    :returns list[str]: The names of all selected transform objects.
    '''

    # Type 'Transform' can include meshes and groups, but we don't want to include groups
    root = cmds.ls(selection = True, type = 'transform', long = True)
    
    # Get all descendant meshes so groups (which have no attached mesh data) aren't included
    relativeMeshes = cmds.listRelatives(root, allDescendents = True, type = 'mesh', fullPath = True)

    # Get the transforms of descendant meshes
    transforms = cmds.listRelatives(relativeMeshes, parent = True, fullPath = True)

    # Return empty list rather than None to avoid 'NoneType is not iterable' errors
    if (transforms == None):
        transforms = []

    return transforms

class package:
    '''
    A package represents a mesh, as well as all of the instances of it in the maya scene.
    This is to ease the process of exporting an FBX file and placing copies of it in an Unreal Engine level.
    \nIt stores:
    - A list of transforms.
    - A filename.
    - A path, where the corresponding FBX file will be exported. (This can be toggled on or off)
    \nInternally, the package class also refers to the UI element that appears in the 'Package Manager' panel.
    '''

    foldedHeight = 36
    expandedHeight = 72

    def __init__(self, parent):
        self.name = cmds.formLayout(p = parent, ebg = True, bgc = bgColor(),
                                    nd = 100, w = 10, h = package.foldedHeight)
        
        self.items = []
        self.customPathEnabled = False
        
        #region Top Layout
        # Top Layout containing the buttons and filename
        self.topLayout = horizontalFormLayout(self, False)
        
        self.deleteIcon = cmds.iconTextButton(p = self.topLayout, style = 'iconOnly',
                                              i = 'deleteGeneric_100.png', annotation = "Delete this package",
                                              command = self.delete, w = 28)
        
        self.nameField = fileNameField(self.topLayout)
        self.itemCount = cmds.text(p = self.topLayout, align = 'center', label = f"{len(self.items)} Item(s)", w = 50)

        self.selectIcon = cmds.iconTextButton(p = self.topLayout, style = 'iconOnly',
                                              i = 'selectBackFacingUV.png', annotation = "Select objects from this package",
                                              command = self.select)
        self.pathIcon = cmds.iconTextButton(p = self.topLayout, style = 'iconOnly', bgc = [0.37, 0.68, 0.53], ebg = False,
                                            i = 'folder-new.png', annotation = "Enable custom export path",
                                            command = self.toggleCustomPath)
        self.openIcon = cmds.iconTextButton(p = self.topLayout, style = 'iconOnly', bgc = [0.32, 0.52, 0.65], ebg = False,
                                            i = 'outArrow.png', annotation = "Move to package editor",
                                            command = self.open)
        
        self.topLayout.controls['left'] = [self.deleteIcon, self.nameField]
        self.topLayout.controls['right'] = [self.openIcon, self.pathIcon, self.selectIcon, self.itemCount, self.nameField]
        self.topLayout.updateLayout(2, 0)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.topLayout, 'left', 0),
                                      (self.topLayout, 'right', 0),
                                      (self.topLayout, 'top', 6)])
        #endregion Top Layout

        # Collapsable layout containing the package's custom export directory
        self.dirField = directoryField(self)
        cmds.formLayout(self.dirField, edit = True, visible = False)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.dirField, 'left', 4),
                                      (self.dirField, 'right', 2),
                                      (self.dirField, 'bottom', 6)])

    # self.pathIcon button command
    def toggleCustomPath(self):
        '''
        Toggle the packages' custom export path (for its corresponding FBX file) and expand its layout
        '''
        if (self.customPathEnabled):
            cmds.iconTextButton(self.pathIcon, edit = True, ebg = False,
                                annotation = "Enable custom export path")
            self.customPathEnabled = False

            cmds.formLayout(self, edit = True, h = package.foldedHeight)
            cmds.formLayout(self.dirField, edit = True, visible = False)
        else:
            cmds.iconTextButton(self.pathIcon, edit = True, ebg = True,
                                annotation = "Disable custom export path")
            self.customPathEnabled = True

            cmds.formLayout(self, edit = True, h = package.expandedHeight)
            cmds.formLayout(self.dirField, edit = True, visible = True)

    # self.selectIcon button command
    def select(self, modifiers = True):
        '''
        Select the packages' contents in the scene. Works with modifiers (Shift and Ctrl)
        '''
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

    # self.deleteIcon button command
    def delete(self):
        global packManagerPane
        packManagerPane.removePackage(self)
    
    # self.openIcon button command
    def open(self):
        global currentPackage
        if (currentPackage == self):
            return
        
        global packManagerPane
        packManagerPane.setCurrentPackage(self)

    def updateUI(self, isCurrent):
        '''
        Update the package's UI for item count and whether it's opened in the package editor.
        '''
        if (not cmds.formLayout(self, exists = True)):
            return
        
        cmds.text(self.itemCount, edit = True, label = f"{len(self.items)} Item(s)")

        if (isCurrent):
            cmds.iconTextButton(self.openIcon, edit = True, ebg = True,
                                annotation = "Currently in package editor")
        else:
            cmds.iconTextButton(self.openIcon, edit = True, ebg = False,
                                annotation = "Move to package editor")

    def getFileName(self):
        return self.nameField.text

    # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
    def __str__(self):
        return self.name

class transform:
    '''
    Class relating to the maya 'transform' type, for use in packages.
    \nStores 'name', 'translate', 'rotate' and 'scale'.
    '''
    def __init__(self, name):
        '''
        :param str name: The name of the corresponding transform in the maya scene.
        '''
        
        self.name = name
        self.update()
    
    def getRelativeAttributes(self, other):
        '''
        Returns the translate, rotate and scale relative to another transform.
        \n(i.e. changes that would be applied to the other transform in order to match this transform)

        :param transform other: The transform object to compare this to.
        '''

        translate = self.attributes['translate']
        
        for i, value in enumerate(other.attributes['translate']):
            translate[i] -= value

        rotate = self.attributes['rotate']
        for i, value in enumerate(other.attributes['rotate']):
            rotate[i] -= value

        scale = self.attributes['scale']
        for i, value in enumerate(other.attributes['scale']):
            scale[i] /= value

        # Name is stored as an attribute to making exporting to JSON easier
        return {
            'name' : self.name,
            'translate' : translate,
            'rotate' : rotate,
            'scale' : scale
        }

    def update(self, force = True):
        '''
        Checks and returns whether a maya transform exists in the scene under this transform's name.
        \nThis helps determine whether the corresponding maya transform has been deleted, renamed or moved, and to update this accordingly.
        \nIf 'force' is enabled, this transform's attributes will be updated to match those of the maya transform.

        :param bool force: Whether or not this transform's attributes should be updated.
        :returns bool: True if a maya transform exists in the scene under the same name as this.
        '''
        if (not cmds.objExists(self)):
            return False
        elif (cmds.objectType(self) != 'transform'):
            return False

        if (force):
            translate = list(cmds.getAttr(f"{self}.translate")[0])
            pivot = list(cmds.getAttr(f"{self}.rotatePivot")[0])
            for i in range(len(translate)): translate[i] += pivot[i]

            # Name is stored as an attribute to making exporting to JSON easier
            self.attributes = {
                'name' : self.name,
                'translate' : translate,
                'rotate' : list(cmds.getAttr(f"{self}.rotate")[0]),
                'scale' : list(cmds.getAttr(f"{self}.scale")[0]),
            }

        return True

    # Return the name of the maya transform for easy integration/display with UI objects.
    def __str__(self):
        return self.name
    
    # Allow equal (==) operator to be used with this so transforms can be checked via name
    # (e.g. with list.contains())
    def __eq__(self, value):
        if (type(value) == str):
            return self.name == value
        pass

class settingsUI:
    '''
    The Export Settings pane in the UI. Stores various settings and the export button.
    '''
    def __init__(self, parent, lOffset = 2, rOffset = 2):
        '''
        :param str parent: The maya UI object set to be the parent of this.
        :param int lOffset: How offset the UI elements in this pane will be from the left side.
        :param int rOffset: How offset the UI elements in this pane will be from the right side.
        '''
        self.parent = parent
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 120)
        self.title = cmds.frameLayout(p = self, label = "Export Settings", collapsable = True, collapse = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        #region Collapsable Layout

        # Scroll layout so top collapsable area doesn't overlap path/filename/export button
        self.scroll = cmds.scrollLayout(p = self.title, childResizable = True, h = 1)
        self.collapse = cmds.formLayout(p = self.scroll, ebg = False, nd = 100, w = 100)
        
        extraOffset = 4
        
        # Export Toggles

        self.jsonToggle = cmds.checkBox(p = self.collapse, label = "Export JSON scene", value = True,
                                       changeCommand = lambda _: self.onToggleUpdateUI())
        self.fbxToggle = cmds.checkBox(p = self.collapse, label = "Export FBX meshes", value = True,
                                       changeCommand = lambda _: self.onToggleUpdateUI())

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

        #endregion Collapsable Layout

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

    # self.fbxToggle change command
    # self.jsonToggle change command
    def onToggleUpdateUI(self):
        '''
        Update UI for export button whenever JSON or FBX is enabled/disabled.
        \nUpdates include:
        - the FBX Settings layout
        - the Root Transform button and text field
        - the Export button
        '''
        fbxEnabled = cmds.checkBox(self.fbxToggle, query = True, value = True)
        jsonEnabled = cmds.checkBox(self.jsonToggle, query = True, value = True)

        # Disable/Enable FBX settings layout
        cmds.frameLayout(self.fbxSettings, edit = True, enable = fbxEnabled)

        # Disable/Enable root transform button (and text field)
        cmds.button(self.rootSetButton, edit = True, enable = jsonEnabled)
        cmds.textField(self.rootNameField, edit = True, enable = jsonEnabled, bgc = bgColor(-0.1))

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

    # self.rootSetButton button command
    def setRootToSelected(self):
        '''
        Sets the root transform to the selected transform in the maya scene.
        \nThe root transform is a way of making sure the scene's objects aren't out in the middle of nowhere when being imported to Unreal.
        \nInstead of storing transforms' attributes based on their absolute positions in the maya scene, we base it off of their posittions relative to the 'root transform'.
        \nThis way you can work in Maya without worrying about how far your objects are from [0, 0, 0].
        '''

        selection = getSelection()
        if (len(selection) != 1):
            cmds.confirmDialog(title = 'Root transform not set', button = ['Ok'], icon = 'critical', message = "" \
            "You must have only one object selected in the scene to set the root transform.")
            return

        global rootTransform
        global packEditorPane

        rootTransform = transform(selection[0])

        # Since root transform is for the positions of objects, reset the rotation and scale.
        rootTransform.attributes['rotate'] = [0, 0, 0]
        rootTransform.attributes['scale'] = [1, 1, 1]

        self.updateRootTransformUI(selection)

    def updateRootTransformUI(self, selection):
        cmds.textField(self.rootNameField, edit = True, text = selection[0])

    # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
    def __str__(self):
        return self.name

    class fbxSettingsLayout():
        '''
        The collapsable layout under 'Export Settings' which stores all of the FBX export settings/checkboxes.
        '''
        class fbxCheckbox:
            '''
            A checkbox that stores a maya FBX property, and can update that property before an FBX file is exported.
            '''
            def __init__(self, parent, label, defaultValue, fbxProperty):
                '''
                :param str parent: The maya UI object set to be the parent of this.
                :param str label: The label displayed next to this checkbox.
                :param bool defaultValue: The default value of this checkbox.
                :param str fbxProperty: The property accessed and updated by cmds.FBXProperty() before an FBX file is exported.
                '''
                self.name = cmds.checkBox(p = parent, l = label, v = defaultValue,
                                        changeCommand = lambda _: self.onUIChanged())
                self.fbxProperty = fbxProperty
                self.value = defaultValue
            
            # self.name change command
            def onUIChanged(self):
                self.value = cmds.checkBox(self, query = True, value = True)
            
            def sendProperty(self):
                '''
                Sends this fbxCheckbox's property via cmds.FBXProperty(). Should be called right before an FBX file is exported.
                '''
                cmds.FBXProperty(self.fbxProperty, '-v', int(self.value))

            # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
            def __str__(self):
                return self.name

        def __init__(self, parent):
            self.name = cmds.frameLayout(p = parent, label = "FBX Settings", collapsable = True, collapse = True)

            self.vForm = verticalFormLayout(parent = self, ebg = False)

            self.vForm.controls['top'].append(self.fbxCheckbox(self.vForm, "Smoothing Groups", True, 'Export|IncludeGrp|Geometry|SmoothingGroups'))
            self.vForm.controls['top'].append(self.fbxCheckbox(self.vForm, "Smooth Mesh", True, 'Export|IncludeGrp|Geometry|SmoothMesh'))
            self.vForm.controls['top'].append(self.fbxCheckbox(self.vForm, "Split Vertex Normals", False, 'Export|IncludeGrp|Geometry|expHardEdges'))
            self.vForm.controls['top'].append(self.fbxCheckbox(self.vForm, "Triangulate", False, 'Export|IncludeGrp|Geometry|Triangulate'))
            self.vForm.controls['top'].append(self.fbxCheckbox(self.vForm, "Tangents & Binormals", False, 'Export|IncludeGrp|Geometry|TangentsandBinormals'))

            self.vForm.controls['top'].append(self.fbxCheckbox(self.vForm, "Skinning", True, 'Export|IncludeGrp|Animation|Deformation|Skins'))
            self.vForm.controls['top'].append(self.fbxCheckbox(self.vForm, "Blendshapes", True, 'Export|IncludeGrp|Animation|Deformation|Shape'))

            self.vForm.updateLayout(xOffset = 12)

        def sendProperties(self):
            '''
            Sends all fbxCheckbox properties via cmds.FBXProperty(). Should be called right before an FBX file is exported.
            '''
            for checkbox in self.vForm.controls['top']:
                checkbox.sendProperty()
        
        # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
        def __str__(self):
            return self.name

class packManagerUI:
    '''
    The Package Manager pane in the UI. Stores the list of packages to be exported.
    '''
    def __init__(self, parent, lOffset = 2, rOffset = 2):
        '''
        :param str parent: The maya UI object set to be the parent of this.
        :param int lOffset: How offset the UI elements in this pane will be from the left side.
        :param int rOffset: How offset the UI elements in this pane will be from the right side.
        '''
        self.parent = parent
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 50)

        self.title = cmds.frameLayout(p = self, label = "Package Manager", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        #region Button Layout
        self.buttons = horizontalFormLayout(self, ebg = False)
        self.addIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                                           i = 'addCreateGeneric_100.png', annotation = "Add empty package",
                                           command = self.addPackage)
        self.autoPackageButton = cmds.button(p = self.buttons, label = "Auto-Generate packages", h = 25, w = 150,
                                             command = autoGeneratePackages)
        self.buttons.controls['left'] = [self.addIcon]
        self.buttons.controls['right'] = [self.autoPackageButton]
        self.buttons.updateLayout(0, 2)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttons, 'left', lOffset),
                                      (self.buttons, 'right', rOffset)],
                        attachControl = [(self.buttons, 'top', 0, self.title)])
        #endregion Button Layout

        #region Package Scroll List
        self.scrollLayout = cmds.scrollLayout(p = self, childResizable = True, bgc = bgColor(-0.1), w = 10, h = 1)
        self.packageList = verticalFormLayout(self.scrollLayout, False, w = 10)

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.scrollLayout, 'left', lOffset),
                                      (self.scrollLayout, 'right', rOffset),
                                      (self.scrollLayout, 'bottom', 2)],
                        attachControl = [(self.scrollLayout, 'top', 0, self.buttons)])
        #endregion Package Scroll List
        
        self.setCurrentPackage(self.addPackage())

    # package.openIcon button command
    def setCurrentPackage(self, pack):
        '''
        Sets the package being edited in the packEditorPane.
        \nThis means the user can add/remove items from the package through the UI.
        '''
        global currentPackage

        if (currentPackage):
            currentPackage.updateUI(False)

        currentPackage = pack
        currentPackage.updateUI(True)

        global packEditorPane
        if (packEditorPane):
            packEditorPane.updateItemsList()

    # package.deleteIcon button command
    def removePackage(self, pack):
        '''
        Removes a package from the list.
        \nNote that there must always be at least one package, so this immediately creates a new one if the list is empty.
        '''
        self.packageList.controls['top'].remove(pack)

        # fix packages lingering even when they're not in the list
        if (cmds.formLayout(pack, exists = True) and len(pack.items) > 0):
            cmds.deleteUI(pack)
        
        # select a new currentPackage so packEditor doesn't show information from the package we just deleted
        if (len(self.packageList.controls['top']) <= 0):
            self.setCurrentPackage(self.addPackage())
        else:
            self.packageList.updateLayout(yOffset = 4)
            self.setCurrentPackage(self.packageList.controls['top'][0])

    def addPackage(self):
        '''
        Adds a new empty package to the list.
        '''
        new = package(self.packageList)

        self.packageList.controls['top'].append(new)
        self.packageList.updateLayout(yOffset = 4)

        return new

    # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
    def __str__(self):
        return self.name

class packEditorUI:
    '''
    The Package Editor pane in the UI. Allows the user to add/remove transforms in the current package.
    '''
    def __init__(self, parent, lOffset = 2, rOffset = 2):
        '''
        :param str parent: The maya UI object set to be the parent of this.
        :param int lOffset: How offset the UI elements in this pane will be from the left side.
        :param int rOffset: How offset the UI elements in this pane will be from the right side.
        '''
        self.parent = parent
        self.name = cmds.formLayout(p = parent, ebg = False, nd = 100, w = 100, h = 50)
        
        self.title = cmds.frameLayout(p = self, label = "Package Editor", collapsable = False)
        cmds.formLayout(self, edit = True,
                        attachForm = [(self.title, 'left', lOffset),
                                    (self.title, 'top', 2),
                                    (self.title, 'right', rOffset)])
        
        #region Buttons Layout
        self.buttons = horizontalFormLayout(self, ebg = False)
        
        self.deleteIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'deleteGeneric_100.png', annotation = "Delete items selected in this list",
                            command = self.deleteSelection)
        
        self.addIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'addCreateGeneric_100.png', annotation = "Add/Update items selected in the scene",
                            command = self.addSelection)
        
        self.refreshIcon = cmds.iconTextButton(p = self.buttons, style = 'iconOnly',
                            i = 'refresh.png', annotation = "Update items that have been moved/deleted",
                            command = self.refreshAll)
        
        # Create Items list (which is below the buttons) before the syncIcon so it can be referenced
        self.itemsList = cmds.textScrollList(p = self, allowMultiSelection = True,
                                             emptyLabel = "No items in the current package\n\nUse the buttons above to add/manage items")
        self.syncIcon = self.syncSelectButton(parent = self.buttons, itemsList = self.itemsList)

        self.buttons.controls['right'] = [self.deleteIcon, self.addIcon]
        self.buttons.controls['left'] = [self.refreshIcon, self.syncIcon]
        self.buttons.updateLayout(0, 0)
        #endregion Buttons Layout

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.itemsList, 'left', lOffset),
                                    (self.itemsList, 'bottom', 2),
                                    (self.itemsList, 'right', rOffset)],
                        attachControl = [(self.itemsList, 'top', 2, self.buttons)])

        cmds.formLayout(self, edit = True,
                        attachForm = [(self.buttons, 'left', lOffset),
                                    (self.buttons, 'right', rOffset)],
                        attachControl = [(self.buttons, 'top', 2, self.title)])

    # self.refreshIcon button command
    def refreshAll(self):
        global currentPackage

        for item in currentPackage.items:
            if (not item.update()):
                currentPackage.items.remove(item)
        self.updateItemsList()

    # self.deleteIcon button command
    def deleteSelection(self):
        selection = cmds.textScrollList(self.itemsList, query = True, selectItem = True)
        if (selection == None):
            print("No items in list selected.")
            return

        global currentPackage

        for item in selection:
            currentPackage.items.remove(item)

        self.updateItemsList()

    # self.addIcon button command
    def addSelection(self):
        selection = getSelection()
        if (len(selection) <= 0):
            print("No objects selected.")
            return

        global currentPackage

        for item in selection:
            if (item in currentPackage.items):
                currentPackage.items[currentPackage.items.index(item)].update()
                continue
            
            currentPackage.items.append(transform(item))

        self.updateItemsList()

        # Select new items in the list if sync select is on
        if (syncSelectEnabled):
            cmds.textScrollList(self.itemsList, edit = True, selectItem = selection)

    def updateItemsList(self):
        cmds.textScrollList(self.itemsList, edit = True, removeAll = True)
        cmds.textScrollList(self.itemsList, edit = True, append = currentPackage.items)
        currentPackage.updateUI(True)

    # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
    def __str__(self):
        return self.name

    class syncSelectButton:
        '''
        The Sync Select button. Handles all sync select functionality.
        '''
        def __init__(self, parent, itemsList):
            self.name = cmds.iconTextButton(p = parent, style = 'iconOnly', bgc = [0.32, 0.52, 0.65], ebg = False,
                                i = 'selectCycle.png', annotation = "Toggle sync selection." \
                                "\nHold CTRL to transfer list selection to scene." \
                                "\nHold SHIFT to transfer scene selection to list.",
                                command = self.pressSyncSelect)
            
            self.syncSelectJob = -1

            cmds.textScrollList(itemsList, edit = True, selectCommand = self.listSelectionChanged)
            self.itemsList = itemsList
        
        # self.name button command
        def pressSyncSelect(self):
            modifiers = getModifiers()
            
            shift = 'Shift' in modifiers
            ctrl = 'Ctrl' in modifiers

            if (shift and ctrl):
                # Hold SHIFT and CTRL to quick-sync scene and list selection
                self.quickSyncSelection()
                return
            elif (shift):
                # Hold SHIFT to transfer scene selection to list.
                self.sceneSelectionChanged(force = True)
                return
            elif (ctrl):
                # Hold CTRL to transfer list selection to scene.
                self.listSelectionChanged(force = True)
                return
            
            # Toggle sync selection if no modifiers held
            global syncSelectEnabled
            self.setSyncSelect(not syncSelectEnabled)
        
        def setSyncSelect(self, value):
            # No change is sync select is already at the set value
            global syncSelectEnabled
            if (syncSelectEnabled == value):
                return

            # If setting to false
            if (syncSelectEnabled):
                cmds.iconTextButton(self, edit = True, ebg = False)
                syncSelectEnabled = False

                # Remove script job
                cmds.scriptJob(kill = self.syncSelectJob)
                return
            
            # Else if setting to true
            cmds.iconTextButton(self, edit = True, ebg = True)
            syncSelectEnabled = True

            # Create script job
            self.syncSelectJob = cmds.scriptJob(event = ["SelectionChanged", self.sceneSelectionChanged],
                                                parent = self, compressUndo = True)
            
            self.quickSyncSelection()

        def quickSyncSelection(self):
            # Store current list selection
            listSelection = cmds.textScrollList(self.itemsList, query = True, selectItem = True)
            sceneSelection = getSelection()
            
            # Deselect everything in the list since we'll re-select them all later
            cmds.textScrollList(self.itemsList, edit = True, deselectAll = True)
            
            # Use empty list rather than None to avoid 'NoneType is not iterable' errors
            if (listSelection == None):
                listSelection = []

            for item in currentPackage.items:
                if (item in sceneSelection or item in listSelection):
                    # If it's selected in the list or the scene, make it selected in both.
                    cmds.textScrollList(self.itemsList, edit = True, selectItem = item)
                    cmds.select(item, add = True)
                else:
                    # If it exists in the list but isn't selected, deselect it. 
                    # This way the user doesn't lose their scene selection when they quick-sync or turn on sync selection.
                    cmds.select(item, deselect = True)

        def sceneSelectionChanged(self, force = False):
            '''
            self.syncSelectJob script job function. Triggers when selection is changed in the scene.
            \nUpdates list selection to match scene selection.
            :param bool force: Use this param to force functionality even when Sync Select is off.
            '''
            
            if (not syncSelectEnabled and not force):
                return

            selection = getSelection()
            cmds.textScrollList(self.itemsList, edit = True, deselectAll = True)

            if (len(selection) <= 0):
                return

            for item in currentPackage.items:
                if (item in selection):
                    cmds.textScrollList(self.itemsList, edit = True, selectItem = item)
        
        # packEditorUI.itemsList select command
        def listSelectionChanged(self, force = False):
            '''
            packEditorUI.itemsList selectCommand. Triggers when selection is changed in the items list.
            \nUpdates scene selection to match list selection.
            :param bool force: Use this param to force functionality even when Sync Select is off.
            '''
            if (not syncSelectEnabled and not force):
                return
            
            selection = cmds.textScrollList(self.itemsList, query = True, selectItem = True)
            
            # Use empty list rather than None to avoid 'NoneType is not iterable' errors
            if (selection == None):
                selection = []

            for item in currentPackage.items:
                if (item in selection):
                    cmds.select(item, add = True)
                else:
                    # If it exists in the list but isn't selected, deselect it.
                    # This way the user doesn't lose their scene selection when they quick-sync or turn on sync selection.
                    cmds.select(item, deselect = True)
        
        # Return self.name so this class can be interacted with in the same way as maya.cmds UI objects
        def __str__(self):
            return self.name

def packageExporterUI():
    '''
    Main UI function for the Package Exporter. Can be used on a Window or WorkspaceControl.
    '''
    topBottomPanes = cmds.paneLayout(configuration = 'horizontal2')
    leftRightPanes = cmds.paneLayout(configuration = 'vertical2', p = topBottomPanes)

    global settingsPane
    global packManagerPane
    global packEditorPane

    # Export settings pane on the bottom, margins on both sides
    settingsPane = settingsUI(topBottomPanes, lOffset = 2, rOffset = 2)

    # Package manager pane on the top left, margin on the left
    packManagerPane = packManagerUI(leftRightPanes, lOffset = 2, rOffset = 0)

    # Package editor pane on the top right, margin on the right
    packEditorPane = packEditorUI(leftRightPanes, lOffset = 0, rOffset = 2)

    # Set size of the pane 2 (the bottom pane, the Export Settings) to take up 100% width, 10% height
    cmds.paneLayout(topBottomPanes, edit = True, paneSize = [2, 100, 10])

# settingsPane.exportButton button command
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

    #region Error/Warning Dialogs
    import os

    # Check for empty/duplicate package filenames, empty packages and invalid package paths
    for pack in packManagerPane.packageList.controls['top']:
        fileName = pack.getFileName()

        if (fileName == ""):
            hasEmptyNames = True
        
        if (len(pack.items) <= 0):
            hasEmptyPackages = True

        if (pack.customPathEnabled):
            if (not os.path.isdir(pack.dirField.directory)):
                cmds.confirmDialog(title = 'Invalid export directory', button = ['Ok'], icon = 'critical',
                           message = f"Path \"{pack.dirField.directory}\" on package \"{fileName}\"" \
                "\nis invalid or does not exist.\n\nPlease enter a valid path and try again.")
                return

        namesList.append(fileName)

    if (settingsPane.fileName.text == ""):
        cmds.confirmDialog(title = 'Invalid filename', button = ['Ok'], icon = 'critical',
                           message = 'Please enter a valid filename and try again.')
        return

    if (not os.path.isdir(settingsPane.dirField.directory)):
        cmds.confirmDialog(title = 'Invalid export directory', button = ['Ok'], icon = 'critical',
                           message = f"Path \"{settingsPane.dirField.directory}\"" \
        "\nis invalid or does not exist.\n\nPlease enter a valid path and try again.")
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

    #endregion Error/Warning Dialogs

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

        # Duplicate object and reset transforms so offsets/rotation arent baked into the mesh
        # This helps for instancing later
        dupe = cmds.duplicate(pack.items[0])[0]
        cmds.setAttr(f"{dupe}.translate", 0, 0, 0, type = 'double3')
        cmds.setAttr(f"{dupe}.rotate", 0, 0, 0, type = 'double3')
        cmds.setAttr(f"{dupe}.scale", 1, 1, 1, type = 'double3')
        cmds.select(dupe, replace = True)

        if (fileName == ""):
            print("Skipped exporting package due to empty filename")
            continue

        if (pack.customPathEnabled):
            directory = f"{pack.dirField.directory}/{fileName}.fbx"
        else:
            directory = f"{settingsPane.dirField.directory}/{fileName}.fbx"

        print(f"Exporting {fileName} package to {directory}")
        # -s makes it export selected instead of export all
        cmds.FBXExport("-file", directory, "-s")
        
        # Delete duplicated object so the scene is as it was
        cmds.delete(dupe)

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

        filePath = f"{settingsPane.dirField.directory}/{fileName}"
        if (pack.customPathEnabled):
            filePath = f"{pack.dirField.directory}/{fileName}"

        packageData += [{
            "fileName" : fileName,
            "transforms" : transformData,
            "path" : filePath
        }]

    scene = {
        "rootTransform" : rootTransform.attributes,
        "packages" : packageData
    }

    sceneJson = json.dumps(scene, indent = 4)
    # 'w' for write
    with open(fullPath, 'w') as f:
        f.write(sceneJson)

    print(f"Finished JSON Export to {fullPath}...")

def Create(windowName = "packageExporterWindow"):
    global currentPackage
    currentPackage = None

    global rootTransform
    rootTransform = None

    global settingsPane
    settingsPane = None

    global packManagerPane
    packManagerPane = None

    global packEditorPane
    packEditorPane = None

    global syncSelectEnabled
    syncSelectEnabled = False
    if (cmds.workspaceControl(windowName, exists = True)):
            cmds.workspaceControl(windowName, edit=True, close = True)

    cmds.workspaceControl(windowName, retain = False, floating = True,
                          mw = 290, mh = 250, label = "Package Exporter")
    packageExporterUI()