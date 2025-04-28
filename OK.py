from qgis.core import QgsApplication
import sys
import processing


QgsApplication.setPrefixPath(r"C:\Program Files\QGIS 3.40.5\apps\qgis-ltr", True)
qgs = QgsApplication([], False)
qgs.initQgis()

print("✅ QGIS успішно ініціалізовано!")
qgs.exitQgis()
