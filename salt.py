import maya.cmds as cmds

# commandPort -n "localhost:7001" -stp "mel" -echoOutput;
# https://help.autodesk.com/cloudhelp/ENU/MayaCRE-Tech-Docs/CommandsPython/

def separateComponentString(componentString, groups = [1]):
    """
    separateComponentString takes in a maya component string (e.g. "pCube1.e[8]"), and separates the components using the specified groups.
    \nGroup 1 is the object name (e.g. "pCube1")
    \nGroup 2 is the type (e.g. "e")
    \nGroup 3 is the range (e.g. "8")
    \nNote that Group 3 returns an list of values, in case the component string uses a range (e.g. "[8:10]")

    :param str componentString: A maya component string.
    :param list groups: The groups to be separated.
    :returns list: The input 'groups' list with each element replaced with its specified group
    """

    import re
    separated = []

    match = re.match(r'([^\.]+)\.([^\[]+)\[([^\]]+)', componentString)
    if match:
        for i in range(len(groups)):
            if groups[i] != 3:
                group = match.group(groups[i])
                separated += [group]
                continue
            
            matchRange = re.match(r'(\d+):(\d+)', match.group(3))
            if (not matchRange):
                group = [int(match.group(3))]
                separated += [group]
                continue
            rangeStart = int(matchRange.group(1))
            rangeEnd = int(matchRange.group(2)) + 1

            group = list(range(rangeStart, rangeEnd))
            separated += [group]
    else:
        separated = [""]
    
    return separated

def facesToEdgePerimeter():
    objectsSelected = cmds.ls(selection = True, objectsOnly = True, an = True)

    if len(objectsSelected) <= 0:
        print("No objects selected.")
        return
    elif len(objectsSelected) > 1:
        print("More than 1 object selected.")
        return

    allSelected = cmds.ls(selection = True)
    objectName = separateComponentString(allSelected[0], [1])[0]

    for item in allSelected:
        if (separateComponentString(item, [2])[0] == "f"):
            break
    else:
        print("No faces selected.")
        return

    internalEdges = cmds.polyListComponentConversion(allSelected, fromFace = True, toEdge = True, internal = True)
    internalEdgeIndices = []

    if len(internalEdges) <= 0:
        pass    
    else:

        for edge in internalEdges:
            internalEdgeIndices += separateComponentString(edge, [3])[0]

    allEdges = cmds.polyListComponentConversion(allSelected, fromFace = True, toEdge = True, internal = False)

    externalEdges = []
    for edge in allEdges:

        indices = separateComponentString(edge, [3])[0]
        
        for index in indices:
            if (internalEdgeIndices.__contains__(index)):
                continue
            externalEdges += [f"{objectName}.e[{index}]"]

    cmds.select(clear = True)
    cmds.select(externalEdges)

# facesToEdgePerimeter()