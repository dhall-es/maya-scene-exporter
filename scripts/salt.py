import maya.cmds as cmds

# commandPort -n "localhost:7001" -stp "mel" -echoOutput;

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
                group = int(match.group(3))
                separated += [group]
                continue
            rangeStart = int(matchRange.group(1))
            rangeEnd = int(matchRange.group(2)) + 1

            group = list(range(rangeStart, rangeEnd))
            separated += group
    else:
        separated = [""]
    
    return separated

# selected = cmds.ls(selection = True)
# if (selected == [""]):
#     print("nothing selected")

# internalEdges = cmds.polyListComponentConversion(selected, fromFace = True, toEdge = True, internal = True)
# components = separateComponentString(internalEdges[0], [1, 2])
# print(internalEdges)

# internalEdgeIndices = []
# for edge in internalEdges:
#     internalEdgeIndices += separateComponentString(edge, [3])
# print(internalEdgeIndices)

# allEdges = cmds.polyListComponentConversion(selected, fromFace = True, toEdge = True, internal = False)

# externalEdges = []
# for edge in allEdges:

#     index = separateComponentString(edge, [3])
#     print(index)
    
#     for i in index:
#         if (internalEdgeIndices.__contains__(index)):
#             continue
#         externalEdges += [f"{components[0]}.{components[1]}[{i}]"]

# cmds.select(clear = True)
# print(externalEdges)
# cmds.select(externalEdges)