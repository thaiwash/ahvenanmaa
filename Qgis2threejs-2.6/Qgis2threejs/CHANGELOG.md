## CHANGELOG

### Version 2.6
- Added navigation widget
- Added fixed base extent option and 1:1 aspect ratio option
- Added outline effect option
- DEM texture width is now specifiable with a numerical value
- Added edge option and quad wireframe option to DEM
- Added Ray Tracing Renderer template (experimental)
- Added view menu
- Fixed DEM edge processing between central block and surrounding blocks
- Some other bug fixes

### Version 2.5
- Potree data support
- Bug fixes

### Version 2.4.2
- Fixed scene export with glTF/COLLADA model file (fix #193)
- Fixed AR camera background in Mobile template (fix #196)

### Version 2.4.1
- Fixed clipping self-crossing lines (fix #117)
- Fixed retrieving a symbol for a feature
- Renamed DEM roughening option to roughness

### Version 2.4
- Build data to load into preview in background
- Added preserve current viewpoint option to web export
- Added side color option to DEM
- Added rotation order option to Model File
- Triangulate polygons using QgsTessellator for Polygon
- Triangulate polygons using earcut for Overlay
- Restored Overlay border option
- Fixed dat-gui panel for mobile device
- Renamed scene block size (width) option to base width
- Renamed Extruded border color option to edge color
- Renamed Profile type to Wall
- Renamed Triangular Mesh type to Polygon
- Updated three.js library to r108
- Bumped QGIS minimum version to 3.4

### Version 2.3.1
- Do not import Qt module from PyQt5.Qt (fix #162 and #134)
- Fixed initial camera target position (fix #163)

### Version 2.3
- Added export algorithms for Processing
- Added automatic z shift adjustment option
- Added Point type for point layer
- Fixed clipped DEM side building (fix #159)
- Fixed Overlay building
- Fixed model file load with Mobile template
- Fixed crash when continuously zooming map canvas with the exporter window open
- API and offscreen rendering

### Version 2.2
- Added Triangular Mesh type for polygon layer
- Added Plane type for point layer (width, height, orientation)
- Restored Icon type for point layer
- Added Model File type for point layer (COLLADA and glTF)
- Drag & drop model preview

### Version 2.1
- Added a new template for mobile device with experimental AR feature
- Added North arrow inset
- Accelerate building objects by caching last created geometry
- Added basic material type option to scene settings - Lambert/Phong/Toon shading
- Added visible on load option
- Added dashed option to Line type
- Added page load progress bar
- Restored GSI elevation tile DEM provider
- Use transform CSS property to position labels
- Fixed crash on closing exporter in Linux

### Version 2.0.1
- Bug fixes
- Improved DEM load performance

### Version 2.0

- Built for QGIS 3.x
- Improved GUI - new exporter with preview
- Save scene as glTF
- Using expression in vector layer properties
- Updated three.js library (r90)
- Disabled/removed these features: DEM advanced resampling mode, 3 object types (Icon, JSON/COLLADA Model), some object specific settings for Profile and Overlay, FileExporter (Save as STL, OBJ, COLLADA), GSIElevProvider.
    These features were available in version 1.4, but are not available in version 2.0.


### Version 1.4.2
- Fixed unicode decode error

### Version 1.4.1
- Rendering with antialias enabled
- Improved height range of custom plane (dat-gui, refs #53)
- Skip invalid polygons (fix #71)
- Fixed feature attribute writing (fix #73)

### Version 1.4

- Documentation improved and moved to readthedocs.org
- Activate DEM's shading by default to make it easy to create shaded 3D map
- Added menu commands for touch screen devices (dat-gui)
- Turn off scene.autoUpdate to reduce matrix calculation cost
- API for Python
- Added some basic test cases
- Fixed error while exporting with DEM's build frame option (fix #48)
- Fixed cone type object for point layer (fix #50)


### Version 1.3.1

- fixed error on applying plugin settings

### Version 1.3

#### General

- added object type for line: Box
- added clear settings command to settings menu
- automatically save settings near project file when exporting is done, and restore the settings next time
- added GSIElevTilePlugin (DEM provider. Optional feature)

#### DEM

- texture rendering with multiple selected layers
- added option to clip DEM with polygon layer
- added option to increase resolution of texture

#### Web page

- added "save image" dialog in which image size can be entered
- fixed bug of restoring view from URL parameters

#### Others

- added lower Z option (Profile)
- added texture option, side option and side lower Z option (Overlay)
- takes map rotation into account (Disk, JSON, COLLADA)


### Version 1.2

- map rotation support
- added object type for point: COLLADA model (experimental)
- added commands to save/load export settings
- fixed 2.5D geometry export bug
- fixed DEM layer export with FileExport template
- updated three.js library (r70)


### Version 1.1.1

- fixed bugs related to icon and attribute export

### Version 1.1

- updated the STLExporter to support other file formats (collada, obj) and is easier to extend (by Olivier Dalang)


### Version 1.0

### General

- added object types for point: Disk, Icon
- added object type for polygon: Overlay
- added base size option (World)
- added option to display coordinates in WGS84 lat/lon (World)
- added layer image option (DEM)
- added clip geometries option (Vector)
- code refactoring (more oo code)

#### Web page

- added layer opacity sliders in dat-gui panel
- added wireframe mode
- updated popup style


### Version 0.7.2

- added object type for line: Profile
- added shading option (DEM)
- 3D print compatible STL export
- bug fix for QGIS 2.5

### Version 0.7.1

- added template: STLExport
- added object types for line: Pipe, Cone
- added URL parameters

### Version 0.7

- export with no DEM and multiple DEMs
- added options for DEM: display type, transparency, sides, frame, surroundings and vertical shift
- added template: custom plane
- added controls: OrbitControls
- added object type for point: JSON model (experimental)
- integrated DEM and Vector tabs
- moved plugin items into web menu/toolbar

- attribute export and labeling
- queryable objects
- fixed texture loading


### Version 0.6

- fixed confusing GUI


### Version 0.5

- vector layer feature export
- added object types: Sphere, Cylinder, Cube, Cone, Line, (Extruded) Polygon


### Version 0.4

- added advanced resampling mode (quad tree)
- added vertical exaggeration option
- added settings dialog and browser path option in it
- DEM reprojection in memory
