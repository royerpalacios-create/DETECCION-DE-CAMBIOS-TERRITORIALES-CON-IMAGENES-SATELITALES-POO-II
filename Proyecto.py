import ee
import geemap
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# ==========================================
# 1. INICIALIZAR GOOGLE EARTH ENGINE
# ==========================================

# Solo la primera vez:
# ee.Authenticate()

ee.Initialize(project='dctiis')

print("Conexión con Earth Engine exitosa.")

# ==========================================
# 2. DEFINIR ÁREA DE ESTUDIO (PUNO)
# ==========================================

roi = ee.Geometry.Point([-70.01, -15.84]).buffer(5000).bounds()

# ==========================================
# 3. FUNCIÓN PARA OBTENER MOSAICOS SENTINEL-2
# ==========================================

def get_mosaico(fecha_inicio, fecha_fin):
    return (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(roi)
        .filterDate(fecha_inicio, fecha_fin)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .median()
        .clip(roi)
    )

# Mosaico de 2018
mosaico_t1 = get_mosaico(
    '2018-01-01',
    '2018-12-31'
)

# Mosaico de 2023
mosaico_t2 = get_mosaico(
    '2023-01-01',
    '2023-12-31'
)

print("Mosaicos Sentinel-2 cargados correctamente.")

# ==========================================
# 4. DATOS DE ENTRENAMIENTO (SIMULADOS)
# ==========================================

data = {
    'B2': [0.1, 0.2, 0.5, 0.1],   # Azul
    'B3': [0.15, 0.25, 0.4, 0.12], # Verde
    'B4': [0.05, 0.3, 0.1, 0.08],  # Rojo
    'B8': [0.8, 0.1, 0.05, 0.7],   # NIR
    'clase': [1, 2, 3, 1]          # Vegetación, Urbano, Agua
}

df_train = pd.DataFrame(data)

# ==========================================
# 5. ENTRENAMIENTO RANDOM FOREST
# ==========================================

X = df_train[['B2', 'B3', 'B4', 'B8']]
y = df_train['clase']

clf = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

clf.fit(X, y)

print("Modelo Random Forest entrenado correctamente.")

# ==========================================
# 6. DETECCIÓN DE CAMBIOS
# ==========================================

def detectar_cambios(mapa_t1, mapa_t2):
    return mapa_t2.subtract(mapa_t1)

# Ejemplo simple usando banda B8
cambios = detectar_cambios(
    mosaico_t1.select('B8'),
    mosaico_t2.select('B8')
)

print("Comparación temporal realizada.")

# ==========================================
# 7. VISUALIZACIÓN EN GEEMAP
# ==========================================

Map = geemap.Map(center=[-15.84, -70.01], zoom=11)

Map.addLayer(
    mosaico_t1,
    {
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 3000
    },
    'Sentinel 2018'
)

Map.addLayer(
    mosaico_t2,
    {
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 3000
    },
    'Sentinel 2023'
)

Map.addLayer(
    cambios,
    {
        'min': -1000,
        'max': 1000
    },
    'Cambios'
)

Map.addLayerControl()

print("\n--- Sistema de Detección de Cambios Territoriales ---")
print("Modelo entrenado con éxito.")
print("Procesando comparación temporal entre 2018 y 2023...")
print("Proceso finalizado correctamente.")

# Mostrar mapa
Map

Map.to_html("mapa_cambios.html")

print("Mapa guardado correctamente.")
print("Abre mapa_cambios.html en tu navegador.")