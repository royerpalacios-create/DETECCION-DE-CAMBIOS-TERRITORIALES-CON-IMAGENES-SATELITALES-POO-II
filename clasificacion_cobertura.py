"""Modulo RS-2: clasificacion de cobertura terrestre con Google Earth Engine.

Este modulo concentra la logica de entrenamiento y aplicacion del clasificador
para que el script principal solo orqueste el flujo del proyecto.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List

import ee


BANDAS_CLASIFICACION: List[str] = ["B2", "B3", "B4", "B8", "B11", "B12"]
PROPIEDAD_CLASE = "clase"


@dataclass(frozen=True)
class ClaseCobertura:
    """Representa una clase de cobertura terrestre del proyecto."""

    id: int
    nombre: str
    color: str


CLASES_COBERTURA: Dict[str, ClaseCobertura] = {
    "agua": ClaseCobertura(1, "Agua", "1f78b4"),
    "vegetacion": ClaseCobertura(2, "Vegetacion", "33a02c"),
    "urbano": ClaseCobertura(3, "Urbano", "e31a1c"),
    "suelo_desnudo": ClaseCobertura(4, "Suelo desnudo", "b15928"),
}


def crear_punto_entrenamiento(longitud: float, latitud: float, clase: int) -> ee.Feature:
    """Crea un punto de entrenamiento con la clase asignada."""
    return ee.Feature(ee.Geometry.Point([longitud, latitud]), {PROPIEDAD_CLASE: clase})


def obtener_muestras_entrenamiento() -> ee.FeatureCollection:
    """Devuelve muestras iniciales para entrenar cobertura terrestre en Puno.

    Las muestras son puntos semilla dentro del area de estudio. En una etapa
    posterior pueden reemplazarse por muestras validadas en campo o poligonos
    etiquetados sin cambiar el resto del flujo de clasificacion.
    """
    clases = CLASES_COBERTURA
    puntos = [
        crear_punto_entrenamiento(-69.9820, -15.8320, clases["agua"].id),
        crear_punto_entrenamiento(-69.9745, -15.8240, clases["agua"].id),
        crear_punto_entrenamiento(-70.0280, -15.8730, clases["vegetacion"].id),
        crear_punto_entrenamiento(-70.0450, -15.8590, clases["vegetacion"].id),
        crear_punto_entrenamiento(-70.0200, -15.8400, clases["urbano"].id),
        crear_punto_entrenamiento(-70.0110, -15.8350, clases["urbano"].id),
        crear_punto_entrenamiento(-70.0450, -15.8120, clases["suelo_desnudo"].id),
        crear_punto_entrenamiento(-70.0500, -15.8040, clases["suelo_desnudo"].id),
    ]
    return ee.FeatureCollection(puntos)


def validar_bandas(bandas: Iterable[str]) -> None:
    """Valida que existan bandas disponibles para entrenar el clasificador."""
    if not list(bandas):
        raise ValueError("Se requiere al menos una banda para clasificar cobertura terrestre.")


def preparar_imagen_clasificacion(
    imagen: ee.Image,
    bandas: Iterable[str] = BANDAS_CLASIFICACION,
) -> ee.Image:
    """Selecciona las bandas usadas por el modelo de cobertura terrestre."""
    bandas_seleccionadas = list(bandas)
    validar_bandas(bandas_seleccionadas)
    return imagen.select(bandas_seleccionadas)


def extraer_datos_entrenamiento(
    imagen: ee.Image,
    muestras: ee.FeatureCollection,
    escala: int = 10,
    bandas: Iterable[str] = BANDAS_CLASIFICACION,
) -> ee.FeatureCollection:
    """Extrae valores espectrales de la imagen sobre las muestras etiquetadas."""
    imagen_entrenamiento = preparar_imagen_clasificacion(imagen, bandas)
    return imagen_entrenamiento.sampleRegions(
        collection=muestras,
        properties=[PROPIEDAD_CLASE],
        scale=escala,
        geometries=True,
    )


def entrenar_clasificador_cobertura(
    imagen: ee.Image,
    muestras: ee.FeatureCollection,
    numero_arboles: int = 100,
    escala: int = 10,
    bandas: Iterable[str] = BANDAS_CLASIFICACION,
) -> ee.Classifier:
    """Entrena un Random Forest de Earth Engine para cobertura terrestre."""
    if numero_arboles <= 0:
        raise ValueError("El numero de arboles debe ser mayor que cero.")

    bandas_entrenamiento = list(bandas)
    datos_entrenamiento = extraer_datos_entrenamiento(
        imagen=imagen,
        muestras=muestras,
        escala=escala,
        bandas=bandas_entrenamiento,
    )

    return ee.Classifier.smileRandomForest(numberOfTrees=numero_arboles).train(
        features=datos_entrenamiento,
        classProperty=PROPIEDAD_CLASE,
        inputProperties=bandas_entrenamiento,
    )


def clasificar_cobertura(
    imagen: ee.Image,
    clasificador: ee.Classifier,
    bandas: Iterable[str] = BANDAS_CLASIFICACION,
) -> ee.Image:
    """Aplica el clasificador entrenado y devuelve una imagen de cobertura."""
    imagen_clasificacion = preparar_imagen_clasificacion(imagen, bandas)
    return imagen_clasificacion.classify(clasificador).rename("cobertura")


def clasificar_mosaicos_temporales(
    mosaico_t1: ee.Image,
    mosaico_t2: ee.Image,
    muestras: ee.FeatureCollection | None = None,
) -> Dict[str, ee.Image]:
    """Clasifica dos mosaicos temporales con un mismo modelo de cobertura."""
    muestras_entrenamiento = muestras if muestras is not None else obtener_muestras_entrenamiento()
    clasificador = entrenar_clasificador_cobertura(mosaico_t2, muestras_entrenamiento)

    return {
        "clasificacion_t1": clasificar_cobertura(mosaico_t1, clasificador),
        "clasificacion_t2": clasificar_cobertura(mosaico_t2, clasificador),
    }


def obtener_parametros_visualizacion() -> Dict[str, object]:
    """Devuelve parametros de visualizacion para el mapa de cobertura."""
    clases_ordenadas = sorted(CLASES_COBERTURA.values(), key=lambda clase: clase.id)
    return {
        "min": 1,
        "max": len(clases_ordenadas),
        "palette": [clase.color for clase in clases_ordenadas],
    }
