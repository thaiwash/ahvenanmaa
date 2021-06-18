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
from qgis.core import Qgis, QgsApplication

from .datamanager import ImageManager
from .builddem import DEMLayerBuilder
from .buildvector import VectorLayerBuilder
from .buildpointcloud import PointCloudLayerBuilder
from . import q3dconst


class ThreeJSBuilder:

    def __init__(self, settings, progress=None, logMessage=None):
        self.settings = settings
        self.progress = progress or dummyProgress
        self.logMessage = logMessage or dummyLogMessage
        self.imageManager = ImageManager(settings)

        self._canceled = False

    def buildScene(self, build_layers=True, cancelSignal=None):
        self.progress(5, "Building scene...")
        be = self.settings.baseExtent()
        mapTo3d = self.settings.mapTo3d()

        obj = {
            "type": "scene",
            "properties": {
                "width": mapTo3d.baseWidth,
                "height": mapTo3d.baseHeight,
                "baseExtent": {
                    "x": be.center().x(),
                    "y": be.center().y(),
                    "width": be.width(),
                    "height": be.height(),
                    "rotation": be.rotation()
                },
                "zExaggeration": mapTo3d.verticalExaggeration,
                "zShift": mapTo3d.verticalShift
            }
        }

        if self.settings.needsProjString():
            crs = self.settings.crs
            obj["properties"]["proj"] = crs.toProj4() if Qgis.QGIS_VERSION_INT < 31003 else crs.toProj()

        self.logMessage("Z exaggeration: {}".format(mapTo3d.verticalExaggeration))
        self.logMessage("Z shift: {}".format(mapTo3d.verticalShift))

        if build_layers:
            obj["layers"] = self.buildLayers(cancelSignal)

        return obj

    def buildLayers(self, cancelSignal=None):
        if cancelSignal:
            cancelSignal.connect(self.cancel)

        layers = []
        layer_list = [layer for layer in self.settings.getLayerList() if layer.visible]
        total = len(layer_list)
        for i, layer in enumerate(layer_list):
            self.progress(int(i / total * 80) + 10, "Building {} layer...".format(layer.name))

            if self.canceled:
                break

            obj = self.buildLayer(layer, cancelSignal)
            if obj:
                layers.append(obj)

        if cancelSignal:
            cancelSignal.disconnect(self.cancel)

        return layers

    def buildLayer(self, layer, cancelSignal=None):
        if layer.geomType == q3dconst.TYPE_DEM:
            builder = DEMLayerBuilder(self.settings, layer, self.imageManager)
        elif layer.geomType == q3dconst.TYPE_POINTCLOUD:
            builder = PointCloudLayerBuilder(self.settings, layer)
        else:
            builder = VectorLayerBuilder(self.settings, layer, self.imageManager)
        return builder.build(cancelSignal=cancelSignal)

    def builders(self, layer):
        if layer.geomType == q3dconst.TYPE_DEM:
            builder = DEMLayerBuilder(self.settings, layer, self.imageManager)
        elif layer.geomType == q3dconst.TYPE_POINTCLOUD:
            builder = PointCloudLayerBuilder(self.settings, layer)
        else:
            builder = VectorLayerBuilder(self.settings, layer, self.imageManager)
        yield builder

        for blockBuilder in builder.blocks():
            yield blockBuilder

    @property
    def canceled(self):
        if not self._canceled:
            QgsApplication.processEvents()
        return self._canceled

    @canceled.setter
    def canceled(self, value):
        self._canceled = value

    def cancel(self):
        self._canceled = True


def dummyProgress(percentage=None, msg=None):
    pass


def dummyLogMessage(msg, level=None):
    pass
