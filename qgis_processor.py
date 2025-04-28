#!/usr/bin/env python
import sys
import os
import json
import logging

QGIS_PREFIX_PATH = "C:/Program Files/QGIS 3.40.5"

from qgis.core import (
    QgsApplication,
    QgsProcessingFeedback,
    QgsVectorLayer
)
import processing
from processing.core.Processing import Processing

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

qgs = QgsApplication([], False)
QgsApplication.setPrefixPath(QGIS_PREFIX_PATH, True)
qgs.initQgis()
Processing.initialize()

def process_geojson():
    input_geojson = "data/input.geojson"
    output_geojson = "data/result.geojson"
    if not os.path.exists(input_geojson):
        logging.error(f"Input file {input_geojson} not found!")
        return
    layer = QgsVectorLayer(input_geojson, "Input Layer", "ogr")
    if not layer.isValid():
        logging.error("Failed to load layer from input_geojson!")
        return
    logging.info("Input layer loaded successfully.")
    params = {
        'INPUT': layer,
        'DISTANCE': 1000,
        'SEGMENTS': 5,
        'DISSOLVE': False,
        'OUTPUT': output_geojson
    }
    feedback = QgsProcessingFeedback()
    try:
        result = processing.run("native:buffer", params, feedback=feedback)
        logging.info(f"Buffer processing completed, result saved: {output_geojson}")
    except Exception as e:
        logging.error(f"Buffer processing error: {e}")

if __name__ == "__main__":
    process_geojson()
    qgs.exitQgis()
