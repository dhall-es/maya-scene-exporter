Maya export tool geared toward scenes with a small amount of unique meshes, but a large amount of those meshes duplicated around the scene.<br/><br/>
You to put those meshes into groups, or 'packages'. Each package has one mesh exported as an FBX, and the transforms of the duplicate meshes are stored in a separate JSON file.<br/><br/>
You may then import this JSON file into unreal using the companion tool: https://github.com/dhall-es/unreal-scene-importer
