import ee
import geemap

from clasificacion_cobertura import (
    clasificar_mosaicos_temporales,
    obtener_parametros_visualizacion,
)

# ==========================================
# 1. INICIALIZAR GOOGLE EARTH ENGINE
# ==========================================

# Solo la primera vez:
# ee.Authenticate()

ee.Initialize(project="dctiis")

print("Conexion con Earth Engine exitosa.")

# ==========================================
# 2. DEFINIR AREA DE ESTUDIO (PUNO)
# ==========================================

roi = ee.Geometry.Point([-70.01, -15.84]).buffer(5000).bounds()

# ==========================================
# 3. FUNCION PARA OBTENER MOSAICOS SENTINEL-2
# ==========================================


def get_mosaico(fecha_inicio, fecha_fin):
    """Obtiene un mosaico Sentinel-2 filtrado por fecha, nube y area."""
    return (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filterDate(fecha_inicio, fecha_fin)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .median()
        .clip(roi)
    )


# Mosaico de 2018
mosaico_t1 = get_mosaico(
    "2018-01-01",
    "2018-12-31",
)

# Mosaico de 2023
mosaico_t2 = get_mosaico(
    "2023-01-01",
    "2023-12-31",
)

print("Mosaicos Sentinel-2 cargados correctamente.")

# ==========================================
# 4. CLASIFICACION DE COBERTURA TERRESTRE (RS-2)
# ==========================================

clasificaciones = clasificar_mosaicos_temporales(
    mosaico_t1,
    mosaico_t2,
)

mapa_cobertura_t1 = clasificaciones["clasificacion_t1"]
mapa_cobertura_t2 = clasificaciones["clasificacion_t2"]

print("Clasificacion de cobertura terrestre RS-2 generada correctamente.")

# ==========================================
# 5. DETECCION DE CAMBIOS
# ==========================================


def detectar_cambios(mapa_t1, mapa_t2):
    """Calcula cambios entre dos mapas clasificados."""
    return mapa_t2.subtract(mapa_t1)


cambios = detectar_cambios(
    mapa_cobertura_t1,
    mapa_cobertura_t2,
)

print("Comparacion temporal realizada.")

# ==========================================
# 6. VISUALIZACION EN GEEMAP
# ==========================================

Map = geemap.Map(center=[-15.84, -70.01], zoom=11)

Map.addLayer(
    mosaico_t1,
    {
        "bands": ["B4", "B3", "B2"],
        "min": 0,
        "max": 3000,
    },
    "Sentinel 2018",
)

Map.addLayer(
    mosaico_t2,
    {
        "bands": ["B4", "B3", "B2"],
        "min": 0,
        "max": 3000,
    },
    "Sentinel 2023",
)

parametros_cobertura = obtener_parametros_visualizacion()

Map.addLayer(
    mapa_cobertura_t1,
    parametros_cobertura,
    "Cobertura terrestre 2018",
)

Map.addLayer(
    mapa_cobertura_t2,
    parametros_cobertura,
    "Cobertura terrestre 2023",
)

Map.addLayer(
    cambios,
    {
        "min": -3,
        "max": 3,
        "palette": ["8c510a", "f6e8c3", "ffffff", "c7eae5", "01665e"],
    },
    "Cambios de cobertura",
)

Map.addLayerControl()

print("\n--- Sistema de Deteccion de Cambios Territoriales ---")
print("Modulo RS-2 ejecutado con exito.")
print("Procesando comparacion temporal entre 2018 y 2023...")
print("Proceso finalizado correctamente.")

# Mostrar mapa en entornos interactivos y guardarlo como HTML.
Map

Map.to_html("mapa_cambios.html")

print("Mapa guardado correctamente.")
print("Abre mapa_cambios.html en tu navegador.")
