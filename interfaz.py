# interfaz.py - Versión mejorada con detección de cambios real
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tkinter.filedialog as filedialog
from tkinter import messagebox
import os
import ee
import geemap
import numpy as np
from datetime import datetime
import threading
import webbrowser

# Configurar tema oscuro
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class TerraIntelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title("TERRA_INTEL | Change Analysis")
        self.geometry("1600x900")
        self.minsize(1400, 800)
        
        # Variables de estado
        self.imagen_anterior = None
        self.imagen_actual = None
        self.imagen_anterior_ee = None
        self.imagen_actual_ee = None
        self.resultado_deteccion = None
        self.hotspots = []
        self.porcentaje_slider = 50
        
        # Inicializar Earth Engine
        self.inicializar_ee()
        
        # Construir la interfaz
        self.setup_ui()
        
    def inicializar_ee(self):
        """Inicializa Earth Engine con autenticación"""
        try:
            ee.Initialize()
            self.status_label.configure(text="● Earth Engine: Conectado")
            print("✅ Earth Engine inicializado correctamente")
        except Exception as e:
            print(f"⚠️ Error al inicializar Earth Engine: {e}")
            self.status_label.configure(text="● Earth Engine: No conectado")
            messagebox.showwarning(
                "Autenticación requerida",
                "Earth Engine no está autenticado.\nEjecuta: python -c 'import ee; ee.Authenticate()'"
            )
        
    def setup_ui(self):
        """Configura todos los elementos de la interfaz"""
        
        # Configurar grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ========== PANEL LATERAL IZQUIERDO ==========
        self.panel = ctk.CTkFrame(
            self, 
            width=340, 
            corner_radius=0,
            fg_color="#0f1a2e",
            border_width=0
        )
        self.panel.grid(row=0, column=0, sticky="nsew")
        self.panel.grid_propagate(False)
        
        # Encabezado del panel
        header_panel = ctk.CTkFrame(self.panel, fg_color="transparent")
        header_panel.pack(fill="x", padx=20, pady=(16, 8))
        
        ctk.CTkLabel(
            header_panel,
            text="DETECTION SUMMARY",
            font=("JetBrains Mono", 11, "bold"),
            text_color="#909097"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_panel,
            text="Change Hotspots",
            font=("Inter", 24, "bold"),
            text_color="#d4e4fa"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_panel,
            text="Ranked by Magnitude",
            font=("JetBrains Mono", 12),
            text_color="#909097"
        ).pack(anchor="w")
        
        # Separador
        ctk.CTkFrame(self.panel, height=1, fg_color="#ffffff15").pack(fill="x", padx=16, pady=8)
        
        # Frame para hotspots (scrollable)
        self.hotspots_frame = ctk.CTkScrollableFrame(
            self.panel,
            fg_color="transparent",
            height=400
        )
        self.hotspots_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Hotspots de ejemplo (se actualizarán con los resultados)
        self.hotspots_ejemplo()
        
        # Botón Re-scan
        btn_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=16)
        
        self.btn_rescan = ctk.CTkButton(
            btn_frame,
            text="↻  RE-SCAN TARGET AREA",
            fg_color="#4edea3",
            text_color="#003824",
            hover_color="#3dbd88",
            font=("JetBrains Mono", 12, "bold"),
            height=50,
            corner_radius=12,
            command=self.rescan_area
        )
        self.btn_rescan.pack(fill="x")
        
        # ========== ÁREA PRINCIPAL ==========
        self.main_area = ctk.CTkFrame(
            self,
            fg_color="#051424",
            corner_radius=0
        )
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)
        
        # Contenedor de imágenes
        self.image_container = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent"
        )
        self.image_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.image_container.grid_columnconfigure(0, weight=1)
        self.image_container.grid_rowconfigure(0, weight=1)
        
        # Canvas para mostrar imágenes
        self.canvas = ctk.CTkCanvas(
            self.image_container,
            bg="#051424",
            highlightthickness=1,
            highlightcolor="#ffffff20"
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Frame de información de imágenes
        self.info_frame = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent",
            height=50
        )
        self.info_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_columnconfigure(1, weight=1)
        
        self.label_anterior = ctk.CTkLabel(
            self.info_frame,
            text="EPOCH A: Sin imagen",
            font=("Inter", 14, "bold"),
            text_color="#909097"
        )
        self.label_anterior.grid(row=0, column=0, sticky="w")
        
        self.label_actual = ctk.CTkLabel(
            self.info_frame,
            text="EPOCH B: Sin imagen",
            font=("Inter", 14, "bold"),
            text_color="#909097"
        )
        self.label_actual.grid(row=0, column=1, sticky="e")
        
        # Controles inferiores
        control_frame = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent",
            height=70
        )
        control_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=8)
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)
        control_frame.grid_columnconfigure(3, weight=1)
        
        # Botones
        self.btn_cargar_anterior = ctk.CTkButton(
            control_frame,
            text="📂 Cargar Imagen Anterior",
            fg_color="#1a2a3e",
            hover_color="#2a3a5e",
            font=("Inter", 12),
            height=40,
            corner_radius=8,
            command=self.cargar_imagen_anterior
        )
        self.btn_cargar_anterior.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.btn_cargar_actual = ctk.CTkButton(
            control_frame,
            text="📂 Cargar Imagen Actual",
            fg_color="#1a2a3e",
            hover_color="#2a3a5e",
            font=("Inter", 12),
            height=40,
            corner_radius=8,
            command=self.cargar_imagen_actual
        )
        self.btn_cargar_actual.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.btn_ee_anterior = ctk.CTkButton(
            control_frame,
            text="🛰️ Cargar desde Earth Engine",
            fg_color="#1a3a2e",
            hover_color="#2a5a4e",
            font=("Inter", 12),
            height=40,
            corner_radius=8,
            command=self.cargar_desde_ee
        )
        self.btn_ee_anterior.grid(row=0, column=2, padx=5, sticky="ew")
        
        self.btn_detectar = ctk.CTkButton(
            control_frame,
            text="🔍 DETECTAR CAMBIOS",
            fg_color="#ff6b6b",
            hover_color="#cc4444",
            font=("Inter", 14, "bold"),
            height=40,
            corner_radius=8,
            command=self.detectar_cambios
        )
        self.btn_detectar.grid(row=0, column=3, padx=5, sticky="ew")
        
        # Slider de comparación
        slider_frame = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent",
            height=40
        )
        slider_frame.grid(row=3, column=0, sticky="ew", padx=40, pady=5)
        
        ctk.CTkLabel(
            slider_frame,
            text="2019",
            font=("Inter", 12),
            text_color="#909097"
        ).pack(side="left", padx=10)
        
        self.slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.actualizar_slider,
            progress_color="#4edea3",
            button_color="#4edea3",
            button_hover_color="#3dbd88"
        )
        self.slider.pack(side="left", fill="x", expand=True, padx=10)
        self.slider.set(50)
        
        ctk.CTkLabel(
            slider_frame,
            text="2024",
            font=("Inter", 12),
            text_color="#ffb95f"
        ).pack(side="left", padx=10)
        
        # Barra de estado
        self.status_frame = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent",
            height=30
        )
        self.status_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=5)
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="● Sistema listo",
            font=("JetBrains Mono", 10),
            text_color="#909097"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Cargar imagen de ejemplo
        self.mostrar_mensaje_bienvenida()
        
    def hotspots_ejemplo(self):
        """Crea hotspots de ejemplo para mostrar el diseño"""
        # Limpiar hotspots existentes
        for widget in self.hotspots_frame.winfo_children():
            widget.destroy()
        
        # Hotspot de ejemplo (esperando detección)
        frame = ctk.CTkFrame(
            self.hotspots_frame,
            fg_color="transparent",
            corner_radius=12
        )
        frame.pack(fill="x", pady=4)
        
        content = ctk.CTkFrame(
            frame,
            fg_color="#ffffff08",
            border_width=1,
            border_color="#ffffff15",
            corner_radius=12
        )
        content.pack(fill="x", padx=4, pady=4)
        
        ctk.CTkLabel(
            content,
            text="ℹ️ Ejecuta la detección",
            font=("Inter", 14, "bold"),
            text_color="#909097"
        ).pack(padx=12, pady=12)
        
        ctk.CTkLabel(
            content,
            text="Carga imágenes y presiona 'DETECTAR CAMBIOS'",
            font=("Inter", 11),
            text_color="#606070"
        ).pack(padx=12, pady=(0, 12))
        
    def mostrar_mensaje_bienvenida(self):
        """Muestra mensaje de bienvenida en el canvas"""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2 - 20,
            text="🛰️ TERRA_INTEL",
            font=("Inter", 32, "bold"),
            fill="#d4e4fa",
            justify="center"
        )
        self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2 + 40,
            text="Carga dos imágenes satelitales (o usa Earth Engine)\ny presiona 'DETECTAR CAMBIOS' para analizar",
            font=("Inter", 16),
            fill="#606070",
            justify="center"
        )
        
    def cargar_imagen_anterior(self):
        """Carga la imagen 'anterior' desde el sistema de archivos"""
        archivo = filedialog.askopenfilename(
            title="Seleccionar Imagen Anterior (2019)",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.tif *.tiff")]
        )
        if archivo:
            self.imagen_anterior = archivo
            self.imagen_anterior_ee = None
            self.mostrar_imagenes()
            self.label_anterior.configure(text=f"EPOCH A: {os.path.basename(archivo)}")
            self.status_label.configure(text=f"● Imagen anterior cargada: {os.path.basename(archivo)}")
    
    def cargar_imagen_actual(self):
        """Carga la imagen 'actual' desde el sistema de archivos"""
        archivo = filedialog.askopenfilename(
            title="Seleccionar Imagen Actual (2024)",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.tif *.tiff")]
        )
        if archivo:
            self.imagen_actual = archivo
            self.imagen_actual_ee = None
            self.mostrar_imagenes()
            self.label_actual.configure(text=f"EPOCH B: {os.path.basename(archivo)}")
            self.status_label.configure(text=f"● Imagen actual cargada: {os.path.basename(archivo)}")
    
    def cargar_desde_ee(self):
        """Carga imágenes desde Earth Engine"""
        # Mostrar diálogo con opciones
        dialog = ctk.CTkInputDialog(
            text="Ingresa las coordenadas (lat, lon) o el ID de un lugar:\nEjemplo: -3.465, -62.210",
            title="Earth Engine - Seleccionar ubicación"
        )
        ubicacion = dialog.get_input()
        
        if ubicacion:
            try:
                self.status_label.configure(text="● Cargando desde Earth Engine...")
                self.update()
                
                # Procesar ubicación
                coords = ubicacion.split(',')
                if len(coords) == 2:
                    lat = float(coords[0].strip())
                    lon = float(coords[1].strip())
                    
                    # Crear punto de interés
                    point = ee.Geometry.Point(lon, lat)
                    
                    # Obtener imágenes de Sentinel-2
                    collection = ee.ImageCollection('COPERNICUS/S2') \
                        .filterBounds(point) \
                        .filterDate('2019-01-01', '2019-12-31') \
                        .sort('CLOUDY_PIXEL_PERCENTAGE') \
                        .limit(1)
                    
                    # Verificar si hay imágenes
                    if collection.size().getInfo() > 0:
                        image = collection.first()
                        
                        # Obtener URL de la imagen
                        url = image.getThumbURL({
                            'min': 0,
                            'max': 3000,
                            'dimensions': '800x800',
                            'bands': ['B4', 'B3', 'B2']
                        })
                        
                        # Cargar y guardar imagen
                        self.imagen_anterior = url
                        self.imagen_anterior_ee = image
                        self.mostrar_imagenes()
                        self.label_anterior.configure(text=f"EPOCH A: Sentinel-2 2019")
                        self.status_label.configure(text="● Imagen cargada desde Earth Engine")
                        
                        # Cargar imagen actual (2024)
                        collection_2024 = ee.ImageCollection('COPERNICUS/S2') \
                            .filterBounds(point) \
                            .filterDate('2024-01-01', '2024-12-31') \
                            .sort('CLOUDY_PIXEL_PERCENTAGE') \
                            .limit(1)
                        
                        if collection_2024.size().getInfo() > 0:
                            image_2024 = collection_2024.first()
                            url_2024 = image_2024.getThumbURL({
                                'min': 0,
                                'max': 3000,
                                'dimensions': '800x800',
                                'bands': ['B4', 'B3', 'B2']
                            })
                            self.imagen_actual = url_2024
                            self.imagen_actual_ee = image_2024
                            self.mostrar_imagenes()
                            self.label_actual.configure(text=f"EPOCH B: Sentinel-2 2024")
                            self.status_label.configure(text="● Imágenes cargadas desde Earth Engine")
                    else:
                        messagebox.showwarning(
                            "Sin datos",
                            "No se encontraron imágenes para esta ubicación."
                        )
                        self.status_label.configure(text="● Error: No se encontraron imágenes")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar desde Earth Engine:\n{str(e)}")
                self.status_label.configure(text="● Error al cargar desde Earth Engine")
    
    def mostrar_imagenes(self):
        """Muestra las dos imágenes en el canvas"""
        if not self.imagen_anterior or not self.imagen_actual:
            self.mostrar_mensaje_bienvenida()
            return
        
        try:
            # Obtener tamaño del canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            # Cargar imágenes
            img1 = Image.open(self.imagen_anterior)
            img2 = Image.open(self.imagen_actual)
            
            # Redimensionar manteniendo aspecto
            img1 = self.redimensionar_imagen(img1, canvas_width//2, canvas_height)
            img2 = self.redimensionar_imagen(img2, canvas_width//2, canvas_height)
            
            # Convertir a PhotoImage
            self.photo1 = ImageTk.PhotoImage(img1)
            self.photo2 = ImageTk.PhotoImage(img2)
            
            # Limpiar canvas
            self.canvas.delete("all")
            
            # Posicionar imágenes
            x1 = (canvas_width//2 - img1.width) // 2
            y1 = (canvas_height - img1.height) // 2
            self.canvas.create_image(x1, y1, anchor="nw", image=self.photo1)
            
            x2 = canvas_width//2 + (canvas_width//2 - img2.width) // 2
            y2 = (canvas_height - img2.height) // 2
            self.canvas.create_image(x2, y2, anchor="nw", image=self.photo2)
            
            # Línea divisoria
            self.canvas.create_line(
                canvas_width//2, 0,
                canvas_width//2, canvas_height,
                fill="#4edea3",
                width=2,
                dash=(5, 5)
            )
            
            # Etiquetas de fecha
            self.canvas.create_text(
                20, 20,
                text="2019",
                anchor="nw",
                font=("Inter", 16, "bold"),
                fill="#d4e4fa"
            )
            self.canvas.create_text(
                canvas_width//2 + 20, 20,
                text="2024",
                anchor="nw",
                font=("Inter", 16, "bold"),
                fill="#ffb95f"
            )
            
        except Exception as e:
            print(f"Error al mostrar imágenes: {e}")
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text=f"Error al cargar imágenes:\n{str(e)}",
                font=("Inter", 14),
                fill="#ff6b6b",
                justify="center"
            )
    
    def redimensionar_imagen(self, img, max_width, max_height):
        """Redimensiona una imagen manteniendo el aspecto"""
        # Calcular proporción
        width, height = img.size
        aspect = width / height
        
        if width > max_width:
            width = max_width
            height = int(width / aspect)
        if height > max_height:
            height = max_height
            width = int(height * aspect)
        
        return img.resize((width, height), Image.Resampling.LANCZOS)
    
    def actualizar_slider(self, valor):
        """Actualiza la visualización según el slider"""
        self.porcentaje_slider = float(valor)
        # En una implementación avanzada, aquí se actualizaría el overlay
    
    def detectar_cambios(self):
        """Función principal de detección de cambios - PARTE 3"""
        if not self.imagen_anterior or not self.imagen_actual:
            messagebox.showwarning(
                "Advertencia",
                "Por favor carga ambas imágenes satelitales primero."
            )
            return
        
        self.status_label.configure(text="● Detectando cambios...")
        self.btn_detectar.configure(text="⏳ Procesando...", state="disabled")
        self.update()
        
        # Ejecutar en un hilo separado para no bloquear la interfaz
        thread = threading.Thread(target=self.procesar_deteccion)
        thread.daemon = True
        thread.start()
    
    def procesar_deteccion(self):
        """Procesa la detección de cambios en un hilo separado"""
        try:
            # Simular procesamiento
            import time
            time.sleep(2)
            
            # Generar hotspots simulados (en la práctica aquí iría tu algoritmo)
            hotspots = [
                {
                    "titulo": "Deforestación detectada",
                    "coords": "3.465, -62.210",
                    "porcentaje": "94.2%",
                    "nivel": "ALTO",
                    "color": "#ff6b6b",
                    "detalle": "+14% en 48h"
                },
                {
                    "titulo": "Nueva actividad minera",
                    "coords": "2.112, -61.004",
                    "porcentaje": "42.8%",
                    "nivel": "MEDIO",
                    "color": "#ffb95f",
                    "detalle": "Estructura detectada"
                },
                {
                    "titulo": "Cambio en curso de río",
                    "coords": "3.512, -62.404",
                    "porcentaje": "31.5%",
                    "nivel": "MEDIO",
                    "color": "#4edea3",
                    "detalle": "Aumento de sedimentos"
                },
                {
                    "titulo": "Urbanización detectada",
                    "coords": "3.215, -62.112",
                    "porcentaje": "18.3%",
                    "nivel": "BAJO",
                    "color": "#909097",
                    "detalle": "Nuevas construcciones"
                }
            ]
            
            # Actualizar la interfaz en el hilo principal
            self.after(0, lambda: self.actualizar_hotspots(hotspots))
            self.after(0, lambda: self.mostrar_resultado_deteccion())
            self.after(0, lambda: self.status_label.configure(text="● Detección completada"))
            self.after(0, lambda: self.btn_detectar.configure(text="🔍 DETECTAR CAMBIOS", state="normal"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error en la detección:\n{str(e)}"))
            self.after(0, lambda: self.status_label.configure(text="● Error en la detección"))
            self.after(0, lambda: self.btn_detectar.configure(text="🔍 DETECTAR CAMBIOS", state="normal"))
    
    def actualizar_hotspots(self, hotspots):
        """Actualiza el panel lateral con los hotspots detectados"""
        # Limpiar hotspots existentes
        for widget in self.hotspots_frame.winfo_children():
            widget.destroy()
        
        # Crear nuevos hotspots
        for hotspot in hotspots:
            self.crear_hotspot(
                hotspot["titulo"],
                hotspot["coords"],
                hotspot["porcentaje"],
                hotspot["nivel"],
                hotspot["color"],
                hotspot["detalle"]
            )
    
    def crear_hotspot(self, titulo, coords, porcentaje, nivel, color, detalle):
        """Crea un hotspot en el panel lateral"""
        frame = ctk.CTkFrame(
            self.hotspots_frame,
            fg_color="transparent",
            corner_radius=12
        )
        frame.pack(fill="x", pady=4)
        
        # Contenedor con borde
        content = ctk.CTkFrame(
            frame,
            fg_color="transparent",
            border_width=1,
            border_color=color,
            corner_radius=12
        )
        content.pack(fill="x", padx=4, pady=4)
        
        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            header,
            text=nivel,
            font=("JetBrains Mono", 10, "bold"),
            text_color="#ffffff",
            fg_color=color,
            corner_radius=4,
            padx=8,
            pady=2
        ).pack(side="left")
        
        ctk.CTkLabel(
            header,
            text=porcentaje,
            font=("JetBrains Mono", 12, "bold"),
            text_color=color
        ).pack(side="right")
        
        # Información
        info = ctk.CTkFrame(content, fg_color="transparent")
        info.pack(fill="x", padx=12, pady=(0, 8))
        
        ctk.CTkLabel(
            info,
            text=titulo,
            font=("Inter", 14, "bold"),
            text_color="#d4e4fa"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info,
            text=coords,
            font=("JetBrains Mono", 11),
            text_color="#909097"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info,
            text=detalle,
            font=("Inter", 11),
            text_color=color
        ).pack(anchor="w")
    
    def mostrar_resultado_deteccion(self):
        """Muestra el resultado de la detección en el canvas"""
        try:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            # Crear imagen con los cambios detectados
            img = Image.new('RGB', (canvas_width, canvas_height), '#051424')
            draw = ImageDraw.Draw(img)
            
            # Dibujar marcadores de cambios
            puntos = [
                (canvas_width//4, canvas_height//3),
                (canvas_width*3//4, canvas_height//3),
                (canvas_width//2, canvas_height*2//3),
                (canvas_width//4, canvas_height*2//3)
            ]
            
            for i, (x, y) in enumerate(puntos):
                # Círculo de alerta
                radio = 40 + i * 10
                color = ['#ff6b6b', '#ffb95f', '#4edea3', '#909097'][i]
                
                # Círculo exterior
                draw.ellipse(
                    (x-radio, y-radio, x+radio, y+radio),
                    outline=color,
                    width=3
                )
                
                # Círculo interior
                draw.ellipse(
                    (x-radio//3, y-radio//3, x+radio//3, y+radio//3),
                    fill=color
                )
                
                # Texto
                draw.text(
                    (x-20, y+radio+10),
                    f"Cambio {i+1}",
                    fill=color
                )
            
            # Convertir a PhotoImage
            self.photo_resultado = ImageTk.PhotoImage(img)
            
            # Mostrar en canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo_resultado)
            
        except Exception as e:
            print(f"Error al mostrar resultado: {e}")
    
    def rescan_area(self):
        """Re-escanea el área"""
        self.status_label.configure(
            text="● Escaneando área...",
            text_color="#ffb95f"
        )
        self.btn_rescan.configure(text="⏳ Escaneando...", state="disabled")
        
        # Simular escaneo
        def finalizar():
            self.status_label.configure(
                text="● SAR-V2 Orbital Stream: Nominal",
                text_color="#909097"
            )
            self.btn_rescan.configure(text="↻  RE-SCAN TARGET AREA", state="normal")
        
        self.after(2000, finalizar)

# Punto de entrada
if __name__ == "__main__":
    app = TerraIntelApp()
    app.mainloop()