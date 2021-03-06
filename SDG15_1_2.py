#PyQGIS script for SDG15_1_2 Indicator
from qgis.core import *
import processing
from qgis.analysis import *
from processing.core.Processing import Processing
from qgis.PyQt.QtCore import QVariant,QSettings, QTranslator, qVersion, QCoreApplication

# Prepare the environment
qgs = QgsApplication([], False)
qgs.setPrefixPath("/usr", True)

# Inizialization
qgs.initQgis()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

## Processing init
#input_output
outputs = {}
g = QgsVectorLayer("KBA_Apulian_Region_Italy.zip","kba","ogr")
if not g.isValid():
  print ("Layer g failed to load!")

g1 = QgsVectorLayer("Protected_area_Murge.shp","PAonKBA","ogr" )
if not g1.isValid():
    print ("Layer g1 failed to load!")

gr= QgsRasterLayer("LC_GRASSLANDS_1990_30m_ProtectedAreaMurge.tif", "grasslands")
if not gr.isValid():
    print ("Raster layer failed to load!")

# Overlap analysis
alg_params = {
'INPUT': g,
'LAYERS': g1,
'OUTPUT': "PAonKBA.gpkg",
}

outputs['OverlapAnalysis'] = processing.run('native:calculatevectoroverlaps', alg_params)

# Statistiche zonali
alg_params = {
    'COLUMN_PREFIX': 'N_',
    'INPUT_RASTER': gr,
    'INPUT_VECTOR': g1,
    'RASTER_BAND': 1,
    'STATS': [1]
    }

outputs['StatisticheZonali'] = processing.run('qgis:zonalstatistics', alg_params)

#Intersezione
alg_params = {
    'INPUT': outputs['OverlapAnalysis']['OUTPUT'],
    'INPUT_FIELDS': None,
    'OVERLAY': g1,
    'OVERLAY_FIELDS': "N_sum",
    'OVERLAY_FIELDS_PREFIX': 'Ov',
    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
}
outputs['Intersezione'] = processing.run('native:intersection', alg_params)

#field calculator
Processing.initialize()
alg_params = {
    'FIELD_LENGTH': 10,
    'FIELD_NAME': 'PixArea100',
    'FIELD_PRECISION': 3,
    'FIELD_TYPE': 0,
    'FORMULA': gr.rasterUnitsPerPixelX()*gr.rasterUnitsPerPixelY()*100.0,
    'INPUT': outputs['Intersezione']['OUTPUT'],
    'NEW_FIELD': True,
    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
}
outputs['CalcolatoreCampi'] = processing.run('qgis:fieldcalculator', alg_params)


#field calculator
Processing.initialize()
alg_params = {
    'FIELD_LENGTH': 10,
    'FIELD_NAME': 'GRonPA',
    'FIELD_PRECISION': 3,
    'FIELD_TYPE': 0,
    'FORMULA':'"PixArea100"*"OvN_sum"/"PAonKBA_area"',
    'INPUT': outputs['CalcolatoreCampi']['OUTPUT'],
    'NEW_FIELD': True,
    'OUTPUT': "PrAreaonKBA.gpkg",
}
outputs['CalcolatoreCampi']= processing.run('qgis:fieldcalculator', alg_params)
## Processing end

#part2: textual output
a = {}
b = {}
c = {}

resultat = {}
resultat1 = {}

oo = QgsVectorLayer(outputs['CalcolatoreCampi']['OUTPUT'])

for feat in oo.getFeatures():
    a[feat['SitRecID']] = feat['Area_meter']
    b[feat['SitRecID']] = feat['PAonKBA_area']
    c[feat['SitRecID']] = feat['OvN_sum']*gr.rasterUnitsPerPixelX()*gr.rasterUnitsPerPixelY()

resultat = {key: (100*b.get(key, 0)/a[key]) for key in a.keys()}
resultat1 = {key: (100*c.get(key, 0)/b[key]) for key in b.keys()}

count = 0
mysum = 0
mysum1= 0

for i in resultat:
    count += 1
    mysum += resultat[i]
    mysum1 += resultat1[i]

print ("The mean percentage of area covered by protected area is ", mysum/count)
print ("The mean percentage of area covered by protected area by ecosystem type ",gr.name()," is ", mysum1/count)


# Finally, exitQgis() is called to remove the
# provider and layer registries from memory
# print ("success")
qgs.exitQgis()