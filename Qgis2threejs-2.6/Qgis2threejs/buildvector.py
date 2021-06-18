# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Qgis2threejs
                                 A QGIS plugin
 export terrain data, map canvas image and vector data to web browser
                              -------------------
        begin                : 2014-01-16
        copyright            : (C) 2014 Minoru Akagi
        email                : akaginch@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import json
import random
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor
from qgis.core import (QgsCoordinateTransform, QgsExpression, QgsExpressionContext, QgsExpressionContextUtils,
                       QgsFeatureRequest, QgsGeometry, QgsProject, QgsRenderContext, QgsWkbTypes)

from .conf import FEATURES_PER_BLOCK, DEBUG_MODE
from .buildlayer import LayerBuilder
from .datamanager import MaterialManager, ModelManager
from .geometry import VectorGeometry, PointGeometry, LineGeometry, PolygonGeometry, TINGeometry
from .qgis2threejstools import logMessage
from .stylewidget import StyleWidget, ColorWidgetFunc, OpacityWidgetFunc, OptionalColorWidgetFunc, ColorTextureWidgetFunc
from .vectorobject import ObjectType


GeomType2Class = {QgsWkbTypes.PointGeometry: PointGeometry,
                  QgsWkbTypes.LineGeometry: LineGeometry,
                  QgsWkbTypes.PolygonGeometry: PolygonGeometry}


def json_default(o):
    if isinstance(o, QVariant):
        return repr(o)
    raise TypeError(repr(o) + " is not JSON serializable")


class Feature:

    def __init__(self, vlayer, qGeom, altitude, propValues, attrs=None, labelHeight=None):
        self.geomType = vlayer.geomType
        self.objectType = vlayer.objectType

        self.geom = qGeom
        self.altitude = altitude
        self.values = propValues
        self.attributes = attrs
        self.labelHeight = labelHeight

        self.material = self.model = None

    def clipGeometry(self, extent):
        r = extent.rotation()
        if r:
            self.geom.rotate(r, extent.center())

        self.geom = self.geom.clipped(extent.unrotatedRect())
        if r:
            self.geom.rotate(-r, extent.center())
        return self.geom

    def geometry(self, z_func, mapTo3d, useZM=VectorGeometry.NotUseZM, baseExtent=None, grid=None):
        geom, alt = (self.geom, self.altitude)
        zf = lambda x, y: z_func(x, y) + alt
        transform_func = mapTo3d.transform

        if self.geomType != QgsWkbTypes.PolygonGeometry:
            return GeomType2Class[self.geomType].fromQgsGeometry(geom, zf, transform_func, useZM=useZM)

        if self.objectType == ObjectType.Polygon:
            return TINGeometry.fromQgsGeometry(geom, zf, transform_func,
                                               drop_z=(useZM == VectorGeometry.NotUseZM))

        if self.objectType == ObjectType.Extruded:
            return PolygonGeometry.fromQgsGeometry(geom, zf, transform_func,
                                                   useCentroidHeight=True,
                                                   centroidPerPolygon=True)

        # Overlay
        border = bool(len(self.values) > 2 and self.values[2] is not None)
        if grid is None:
            # absolute z coordinate
            g = TINGeometry.fromQgsGeometry(geom, zf, transform_func, drop_z=True)
            if border:
                g.bnds_list = PolygonGeometry.fromQgsGeometry(geom, zf, transform_func).toLineGeometryList()
            return g

        # relative to DEM
        transform_func = mapTo3d.transformRotated

        if baseExtent.rotation():
            geom.rotate(baseExtent.rotation(), baseExtent.center())

        polys = grid.splitPolygon(geom)
        g = TINGeometry.fromQgsGeometry(polys, zf, transform_func, use_earcut=True)

        if border:
            bnds = grid.segmentizeBoundaries(geom)
            g.bnds_list = [LineGeometry.fromQgsGeometry(bnd, zf, transform_func, useZM=VectorGeometry.UseZ) for bnd in bnds]
        return g


class VectorLayer:

    def __init__(self, settings, layer, materialManager, modelManager):
        """layer: Layer object"""
        self.settings = settings
        self.renderContext = QgsRenderContext.fromMapSettings(settings.mapSettings)

        self.mapLayer = layer.mapLayer
        self.name = self.mapLayer.name() if self.mapLayer else "no title"
        self.properties = layer.properties

        self.expressionContext = QgsExpressionContext()
        self.expressionContext.appendScope(QgsExpressionContextUtils.layerScope(self.mapLayer))

        self.objectType = ObjectType.typeByName(self.properties.get("comboBox_ObjectType"),
                                                self.mapLayer.geometryType())

        self.materialManager = materialManager
        self.modelManager = modelManager
        self.colorNames = []        # for random color

        self.transform = QgsCoordinateTransform(self.mapLayer.crs(), settings.crs, QgsProject.instance())
        self.geomType = self.mapLayer.geometryType()

        # attributes
        self.writeAttrs = self.properties.get("checkBox_ExportAttrs", False)
        self.labelAttrIndex = self.properties.get("comboBox_Label", None)
        self.fieldIndices = []
        self.fieldNames = []

        if self.writeAttrs:
            for index, field in enumerate(self.mapLayer.fields()):
                if field.editorWidgetSetup().type() != "Hidden":
                    self.fieldIndices.append(index)
                    self.fieldNames.append(field.displayName())

        # expressions
        self._exprs = {}
        self.exprAlt = QgsExpression(self.properties.get("fieldExpressionWidget_altitude") or "0")
        self.exprLabel = QgsExpression(self.properties.get("labelHeightWidget", {}).get("editText") or "0")

    def features(self, request=None):
        mapTo3d = self.settings.mapTo3d()
        be = self.settings.baseExtent()
        beGeom = be.geometry()
        rotation = be.rotation()
        fields = self.mapLayer.fields()

        # initialize symbol rendering, and then get features (geometry, attributes, color, etc.)
        self.renderer = self.mapLayer.renderer().clone()
        self.renderer.startRender(self.renderContext, self.mapLayer.fields())

        for f in self.mapLayer.getFeatures(request or QgsFeatureRequest()):
            geometry = f.geometry()
            if geometry is None:
                logMessage("null geometry skipped")
                continue

            # coordinate transformation - layer crs to project crs
            geom = QgsGeometry(geometry)
            if geom.transform(self.transform) != 0:
                logMessage("Failed to transform geometry")
                continue

            # check if geometry intersects with the base extent (rotated rect)
            if rotation and not beGeom.intersects(geom):
                continue

            # set feature to expression context
            self.expressionContext.setFeature(f)

            # evaluate expression
            altitude = float(self.exprAlt.evaluate(self.expressionContext) or 0)
            swVals = self.styleWidgetValues(f)

            attrs = labelHeight = None
            if self.writeAttrs:
                attrs = [fields[i].displayString(f.attribute(i)) for i in self.fieldIndices]

                if self.hasLabel():
                    labelHeight = float(self.exprLabel.evaluate(self.expressionContext) or 0) * mapTo3d.multiplierZ

            # create a feature object
            yield Feature(self, geom, altitude, swVals, attrs, labelHeight)

        self.renderer.stopRender(self.renderContext)

    def evaluateExpression(self, expr_str, f):
        if expr_str not in self._exprs:
            self._exprs[expr_str] = QgsExpression(expr_str)

        self.expressionContext.setFeature(f)
        return self._exprs[expr_str].evaluate(self.expressionContext)

    def readFillColor(self, vals, f):
        return self._readColor(vals, f)

    def readBorderColor(self, vals, f):
        return self._readColor(vals, f, isBorder=True)

    # read color from COLOR or OPTIONAL_COLOR widget
    def _readColor(self, widgetValues, f, isBorder=False):
        mode = widgetValues["comboData"]
        if mode == OptionalColorWidgetFunc.NONE:
            return None

        if mode == ColorWidgetFunc.EXPRESSION:
            val = self.evaluateExpression(widgetValues["editText"], f)
            try:
                if isinstance(val, str):
                    a = val.split(",")
                    if len(a) >= 3:
                        a = [max(0, min(int(c), 255)) for c in a[:3]]
                        return "0x{:02x}{:02x}{:02x}".format(a[0], a[1], a[2])
                    return val.replace("#", "0x")

                raise
            except:
                logMessage("Wrong color value: {}".format(val))
                return "0"

        if mode == ColorWidgetFunc.RANDOM or f is None:
            self.colorNames = self.colorNames or QColor.colorNames()
            color = random.choice(self.colorNames)
            self.colorNames.remove(color)
            return QColor(color).name().replace("#", "0x")

        # feature color
        symbols = self.renderer.symbolsForFeature(f, self.renderContext)
        if not symbols:
            logMessage("Symbol for feature not found. Please use a simple renderer for {0}.".format(self.name))
            return "0"

        symbol = symbols[0]
        if isBorder:
            sl = symbol.symbolLayer(0)
            if sl:
                return sl.strokeColor().name().replace("#", "0x")

        return symbol.color().name().replace("#", "0x")

    def readOpacity(self, widgetValues, f):
        vals = widgetValues

        if vals["comboData"] == OpacityWidgetFunc.EXPRESSION:
            try:
                val = self.evaluateExpression(widgetValues["editText"], f)
                return min(max(0, val), 100) / 100
            except:
                logMessage("Wrong opacity value: {}".format(val))
                return 1

        symbols = self.renderer.symbolsForFeature(f, self.renderContext)
        if not symbols:
            logMessage("Symbol for feature not found. Please use a simple renderer for {0}.".format(self.name))
            return 1

        symbol = symbols[0]
        return self.mapLayer.opacity() * symbol.opacity()

    @classmethod
    def toFloat(cls, val):
        try:
            return float(val)
        except Exception as e:
            logMessage('{0} (value: {1})'.format(e.message, str(val)))
            return 0

    # functions to read values from height widget (z coordinate)
    def useZ(self):
        return self.properties.get("radioButton_zValue", False)

    def useM(self):
        return self.properties.get("radioButton_mValue", False)

    def isHeightRelativeToDEM(self):
        return self.properties.get("comboBox_altitudeMode") is not None

    def hasLabel(self):
        return bool(self.labelAttrIndex is not None)

    # read values from style widgets
    def styleWidgetValues(self, f):
        vals = []
        for i in range(16):   # big number for style count
            widgetValues = self.properties.get("styleWidget" + str(i))
            if not widgetValues:
                break

            widgetType = widgetValues["type"]
            comboData = widgetValues.get("comboData")
            if widgetType == StyleWidget.COLOR:
                vals.append(self.readFillColor(widgetValues, f))

            elif widgetType == StyleWidget.OPACITY:
                vals.append(self.readOpacity(widgetValues, f))

            elif widgetType in (StyleWidget.EXPRESSION, StyleWidget.LABEL_HEIGHT):
                expr = widgetValues["editText"]
                val = self.evaluateExpression(expr, f)
                if val:
                    vals.append(val)
                else:
                    if val is None:
                        logMessage("Failed to evaluate expression: {} ({})".format(expr, self.name))
                    else:       # if val.isNull():
                        logMessage("NULL was treated as zero. ({})".format(self.name))
                    vals.append(0)

            elif widgetType == StyleWidget.OPTIONAL_COLOR:
                vals.append(self.readBorderColor(widgetValues, f))

            elif widgetType == StyleWidget.CHECKBOX:
                vals.append(widgetValues["checkBox"])

            elif widgetType == StyleWidget.COMBOBOX:
                vals.append(widgetValues["comboData"])

            elif widgetType == StyleWidget.FILEPATH:
                expr = widgetValues["editText"]
                val = self.evaluateExpression(expr, f)
                if val is None:
                    logMessage("Failed to evaluate expression: " + expr)
                vals.append(val or "")

            elif widgetType == StyleWidget.COLOR_TEXTURE:
                if comboData == ColorTextureWidgetFunc.MAP_CANVAS:
                    vals.append(comboData)
                elif comboData == ColorTextureWidgetFunc.LAYER:
                    vals.append(widgetValues.get("layerIds", []))
                else:
                    vals.append(self.readFillColor(widgetValues, f))

            else:
                logMessage("Widget type {} not found.".format(widgetType))
                vals.append(None)

        return vals


class FeatureBlockBuilder:

    def __init__(self, settings, vlayer, jsLayerId, pathRoot=None, urlRoot=None, useZM=VectorGeometry.NotUseZM, z_func=None, grid=None):
        self.settings = settings
        self.vlayer = vlayer
        self.jsLayerId = jsLayerId
        self.pathRoot = pathRoot
        self.urlRoot = urlRoot
        self.useZM = useZM
        self.z_func = z_func
        self.grid = grid

        self.blockIndex = None
        self.features = []

    def clone(self):
        return FeatureBlockBuilder(self.settings, self.vlayer, self.jsLayerId,
                                   self.pathRoot, self.urlRoot,
                                   self.useZM, self.z_func, self.grid)

    def setBlockIndex(self, index):
        self.blockIndex = index

    def setFeatures(self, features):
        self.features = features

    def build(self):
        be = self.settings.baseExtent()
        obj_geom_func = self.vlayer.objectType.geometry
        mapTo3d = self.settings.mapTo3d()

        feats = []
        for f in self.features:
            d = {}
            d["geom"] = obj_geom_func(self.settings, self.vlayer, f,
                                      f.geometry(self.z_func, mapTo3d, self.useZM, be, self.grid))

            if f.material is not None:
                d["mtl"] = f.material
            elif f.model is not None:
                d["model"] = f.model

            if f.attributes is not None:
                d["prop"] = f.attributes

                if f.labelHeight is not None:
                    d["lh"] = f.labelHeight

            feats.append(d)

        data = {
            "type": "block",
            "layer": self.jsLayerId,
            "block": self.blockIndex,
            "features": feats,
            "featureCount": len(feats)
        }

        if self.pathRoot is not None:
            with open(self.pathRoot + "{0}.json".format(self.blockIndex), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2 if DEBUG_MODE else None, default=json_default)

            url = self.urlRoot + "{0}.json".format(self.blockIndex)
            return {"url": url, "featureCount": len(feats)}

        else:
            return data


class VectorLayerBuilder(LayerBuilder):

    gt2str = {QgsWkbTypes.PointGeometry: "point",
              QgsWkbTypes.LineGeometry: "line",
              QgsWkbTypes.PolygonGeometry: "polygon"}

    def __init__(self, settings, layer, imageManager, pathRoot=None, urlRoot=None, progress=None, logMessage=None):
        LayerBuilder.__init__(self, settings, layer, imageManager, pathRoot, urlRoot, progress, logMessage)

        self.materialManager = MaterialManager(imageManager, settings.materialType())
        self.modelManager = ModelManager(settings)

        self.geomType = self.layer.mapLayer.geometryType()
        self.clipExtent = None

    def build(self, build_blocks=False, cancelSignal=None):
        if self.layer.mapLayer is None:
            return

        vlayer = VectorLayer(self.settings, self.layer, self.materialManager, self.modelManager)
        if vlayer.objectType is None:
            logMessage("Object type not found")
            return

        self.logMessage("Object type is {}.".format(vlayer.objectType.name))

        self.vlayer = vlayer

        be = self.settings.baseExtent()
        p = self.layer.properties

        # feature request
        request = QgsFeatureRequest()
        if p.get("radioButton_IntersectingFeatures", False):
            request.setFilterRect(vlayer.transform.transformBoundingBox(be.boundingBox(),
                                                                        QgsCoordinateTransform.ReverseTransform))

            # geometry for clipping
            if p.get("checkBox_Clip") and vlayer.objectType != ObjectType.Polygon:
                self.clipExtent = be.clone().scale(0.9999)    # clip to slightly smaller extent than map canvas extent
        self.features = []
        data = {}

        # materials/models
        if vlayer.objectType != ObjectType.ModelFile:
            for feat in vlayer.features(request):
                feat.material = vlayer.objectType.material(self.settings, vlayer, feat)
                self.features.append(feat)
            data["materials"] = self.materialManager.buildAll(self.pathRoot, self.urlRoot,
                                                              base64=self.settings.base64)
        else:
            for feat in vlayer.features(request):
                feat.model = vlayer.objectType.model(self.settings, vlayer, feat)
                self.features.append(feat)

            data["models"] = self.modelManager.build(self.pathRoot is not None,
                                                     base64=self.settings.base64)

            self.logMessage("This layer has reference to 3D model file(s). If there are relevant files, you need to copy them to data directory for this export.")

        if build_blocks:
            self._startBuildBlocks(cancelSignal)

            nf = 0
            blocks = []
            for block in self.blocks():
                if self.canceled:
                    break
                b = block.build()
                nf += b["featureCount"]

                blocks.append(b)

            self._endBuildBlocks(cancelSignal)

            nb = len(blocks)
            if nb > 1:
                self.logMessage("{} features were splitted into {} parts.".format(nf, nb))
            else:
                self.logMessage("{} feature{}.".format(nf, "s" if nf > 1 else ""))

            data["blocks"] = blocks

        d = {
            "type": "layer",
            "id": self.layer.jsLayerId,
            "properties": self.layerProperties(),
            "data": data
        }

        if self.canceled:
            return None

        if DEBUG_MODE:
            d["PROPERTIES"] = p

        return d

    def layerProperties(self):
        p = LayerBuilder.layerProperties(self)
        p["type"] = self.gt2str.get(self.layer.mapLayer.geometryType())
        p["objType"] = self.vlayer.objectType.name

        if self.vlayer.writeAttrs:
            p["propertyNames"] = self.vlayer.fieldNames

            if self.vlayer.labelAttrIndex is not None:
                p["label"] = {"index": self.vlayer.labelAttrIndex,
                              "relative": self.properties.get("labelHeightWidget", {}).get("comboData", 0) == 1}

        # object-type-specific properties
        # p.update(self.vlayer.objectType.layerProperties(self.settings, self))
        return p

    def blocks(self):
        z_func = lambda x, y: 0
        grid = None

        p = self.vlayer.properties
        if p.get("radioButton_zValue"):
            useZM = VectorGeometry.UseZ
        elif p.get("radioButton_mValue"):
            useZM = VectorGeometry.UseM
        else:
            useZM = VectorGeometry.NotUseZM

        if self.vlayer.isHeightRelativeToDEM():
            demLayerId = p.get("comboBox_altitudeMode")
            demProvider = self.settings.demProviderByLayerId(demLayerId)

            if self.vlayer.objectType == ObjectType.Overlay:
                # get the grid segments of the DEM layer which polygons overlay
                dem_seg = self.settings.demGridSegments(demLayerId)

                # prepare a grid geometry
                grid = demProvider.readAsGridGeometry(dem_seg.width() + 1, dem_seg.height() + 1, self.settings.baseExtent())

            else:
                z_func = demProvider.readValue      # readValue(x, y)

        builder = FeatureBlockBuilder(self.settings, self.vlayer, self.layer.jsLayerId, self.pathRoot, self.urlRoot,
                                      useZM, z_func, grid)

        one_per_block = (self.vlayer.objectType == ObjectType.Overlay
                         and self.vlayer.isHeightRelativeToDEM()
                         and self.settings.isPreview)
        index = 0
        feats = []
        for f in self.features or []:
            if self.clipExtent and self.geomType != QgsWkbTypes.PointGeometry:
                if f.clipGeometry(self.clipExtent) is None:
                    continue

            # skip if geometry is empty or null
            if f.geom.isEmpty() or f.geom.isNull():
                if not self.clipExtent:
                    logMessage("empty/null geometry skipped")
                continue

            feats.append(f)

            if len(feats) == FEATURES_PER_BLOCK or one_per_block:
                b = builder.clone()
                b.setBlockIndex(index)
                b.setFeatures(feats)
                yield b
                index += 1
                feats = []

        if len(feats) or index == 0:
            builder.setBlockIndex(index)
            builder.setFeatures(feats)
            yield builder
