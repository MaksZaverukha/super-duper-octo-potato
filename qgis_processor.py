#!/usr/bin/env python
import sys
import os
import json
import logging

# Вкажіть шлях до QGIS (коригуйте за потребою)
QGIS_PREFIX_PATH = "C:/Program Files/QGIS 3.40.5"

from qgis.core import (
    QgsApplication,
    QgsProcessingFeedback,
    QgsVectorLayer,
    QgsFeatureRequest
)
import processing
from processing.core.Processing import Processing

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

qgs = QgsApplication([], False)
QgsApplication.setPrefixPath(QGIS_PREFIX_PATH, True)
qgs.initQgis()
Processing.initialize()

# Файл з меж країн. Ми будемо використовувати поле ADMIN або NAME
BOUNDARIES_FILE = os.path.join("static", "country_boundaries.geojson")
COUNTRY_FIELDS = ["ADMIN", "NAME", "country"]  # перевіряти усі можливі варіанти

def get_boundary_country(feature):
    for field in COUNTRY_FIELDS:
        if feature.attributes() and feature[field]:
            return str(feature[field]).strip()
    return ""

def load_country_boundaries():
    if not os.path.exists(BOUNDARIES_FILE):
        logging.error(f"Country boundaries file {BOUNDARIES_FILE} not found!")
        return None
    layer = QgsVectorLayer(BOUNDARIES_FILE, "Country Boundaries", "ogr")
    if not layer.isValid():
        logging.error("Failed to load country boundaries layer!")
        return None
    logging.info("Country boundaries layer loaded successfully.")
    return layer

def add_geometry_from_boundaries(features, boundaries_layer):
    updated_features = []
    for feat in features:
        geom = feat.get("geometry")
        props = feat.get("properties", {})
        if not geom or not geom.get("coordinates"):
            country = props.get("country")
            if country:
                # Ми перевіряємо декілька альтернативних полів за допомогою ILIKE
                expr = ' OR '.join([f'"{field}" ILIKE \'{country}\''
                                     for field in COUNTRY_FIELDS])
                request = QgsFeatureRequest().setFilterExpression(expr)
                matching_feats = list(boundaries_layer.getFeatures(request))
                if matching_feats:
                    poly_geom = matching_feats[0].geometry()
                    feat["geometry"] = json.loads(poly_geom.asJson())
                    logging.debug(f"Geometry added for country: {country}")
                else:
                    logging.warning(f"No boundaries found for country: {country}")
        updated_features.append(feat)
    return updated_features

def process_geojson():
    input_geojson = os.path.join("data", "input.geojson")
    output_geojson = os.path.join("data", "result.geojson")
    if not os.path.exists(input_geojson):
        logging.error(f"Input file {input_geojson} not found!")
        return
    try:
        with open(input_geojson, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Error loading input GeoJSON: {e}")
        return

    features = data.get("features", [])
    boundaries_layer = load_country_boundaries()
    if boundaries_layer is not None:
        features = add_geometry_from_boundaries(features, boundaries_layer)
    else:
        logging.warning("Country boundaries layer not loaded; features remain without geometry.")

    result_fc = {"type": "FeatureCollection", "features": features}
    try:
        with open(output_geojson, "w", encoding="utf-8") as f:
            json.dump(result_fc, f, ensure_ascii=False, indent=2)
        logging.info(f"Result GeoJSON written to {output_geojson}")
    except Exception as e:
        logging.error(f"Error saving output GeoJSON: {e}")

if __name__ == "__main__":
    process_geojson()
    qgs.exitQgis()
