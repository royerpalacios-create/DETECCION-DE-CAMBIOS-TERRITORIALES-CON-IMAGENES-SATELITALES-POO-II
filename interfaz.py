# interfaz.py - Versión completa con barra superior, 3 botones y hotspots con miniaturas
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import tkinter.filedialog as filedialog
from tkinter import messagebox
import os
import ee
import threading
import time
from datetime import datetime

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
        self.ubicacion_actual = None
        
        # Construir la interfaz
        self.setup_ui()
        
        # Inicializar Earth Engine después de que la interfaz esté lista
        self.after(100, self.inicializar_ee)
        
    def inicializar_ee(self):
        """Inicializa Earth Engine con tu proyecto"""
        try:
            # Especifica tu proyecto aquí - ¡CAMBIAME SI ES NECESARIO!
            ee.Initialize(project='dctiis-501815')
            print("✅ Earth Engine inicializado correctamente")
            self.status_label.configure(text="● Earth Engine: Conectado")
        except Exception as e:
            print(f"⚠️ Error al inicializar Earth Engine: {e}")
            self.status_label.configure(text="● Earth Engine: No conectado")
            print("ℹ️ Puedes usar la interfaz sin Earth Engine o verificar tu autenticación")
            
    def setup_ui(self):
        """Configura todos los elementos de la interfaz"""
        
        # Configurar grid principal
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Contenido principal
        self.grid_columnconfigure(1, weight=1)
        
        # ========== BARRA SUPERIOR (HEADER) ==========
        self.header = ctk.CTkFrame(
            self,
            height=60,
            fg_color="#0f1a2e",
            corner_radius=0,
            border_width=0
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header.grid_propagate(False)
        
        # Logo y título
        logo_label = ctk.CTkLabel(
            self.header,
            text="🛰️ TERRA_INTEL",
            font=("Inter", 20, "bold"),
            text_color="#d4e4fa"
        )
        logo_label.pack(side="left", padx=20)
        
        # Indicador de sesión
        session_label = ctk.CTkLabel(
            self.header,
            text="SESIÓN ACTIVA",
            font=("JetBrains Mono", 11),
            text_color="#4edea3"
        )
        session_label.pack(side="left", padx=20)
        
        # Botón de reporte (derecha)
        self.btn_report = ctk.CTkButton(
            self.header,
            text="📊 GENERAR REPORTE",
            fg_color="#4edea3",
            text_color="#003824",
            hover_color="#3dbd88",
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            width=150,
            corner_radius=8,
            command=self.generar_reporte
        )
        self.btn_report.pack(side="right", padx=20)
        
        # Separador entre header y contenido
        ctk.CTkFrame(self, height=1, fg_color="#333333").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(60, 0))
        
        # ========== CONTENIDO PRINCIPAL (ROW 1) ==========
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # ========== PANEL LATERAL IZQUIERDO ==========
        self.panel = ctk.CTkFrame(
            self.content_frame, 
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
            text="RESUMEN DE DETECCION",
            font=("JetBrains Mono", 11, "bold"),
            text_color="#909097"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_panel,
            text="Puntos de Cambio",
            font=("Inter", 24, "bold"),
            text_color="#d4e4fa"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_panel,
            text="Clasificados por Magnitud",
            font=("JetBrains Mono", 12),
            text_color="#909097"
        ).pack(anchor="w")
        
        # Separador
        ctk.CTkFrame(self.panel, height=1, fg_color="#333333").pack(fill="x", padx=16, pady=8)
        
        # Frame para hotspots (scrollable)
        self.hotspots_frame = ctk.CTkScrollableFrame(
            self.panel,
            fg_color="transparent",
            height=400
        )
        self.hotspots_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Hotspots de ejemplo
        self.hotspots_ejemplo()
        
        # Botón Re-scan
        btn_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=16)
        
        self.btn_rescan = ctk.CTkButton(
            btn_frame,
            text="↻  RE-ESCANEAR EL AREA",
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
            self.content_frame,
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
            highlightcolor="#333333"
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
        
        # ========== CONTROLES INFERIORES - 3 BOTONES PRINCIPALES ==========
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
        
        # 🛰️ Botón BUSCAR UBICACIÓN
        self.btn_buscar = ctk.CTkButton(
            control_frame,
            text="🛰️ Buscar Ubicación",
            fg_color="#1a3a2e",
            hover_color="#2a5a4e",
            font=("Inter", 12, "bold"),
            height=40,
            corner_radius=8,
            command=self.buscar_ubicacion_ee
        )
        self.btn_buscar.grid(row=0, column=0, padx=5, sticky="ew")
        
        # 📊 Botón OBTENER DATOS
        self.btn_obtener_datos = ctk.CTkButton(
            control_frame,
            text="📊 Obtener Datos",
            fg_color="#1a2a4e",
            hover_color="#2a3a6e",
            font=("Inter", 12, "bold"),
            height=40,
            corner_radius=8,
            command=self.obtener_datos_cambio
        )
        self.btn_obtener_datos.grid(row=0, column=1, padx=5, sticky="ew")
        
        # 🔍 Botón DETECTAR CAMBIOS
        self.btn_detectar = ctk.CTkButton(
            control_frame,
            text="🔍 Detectar Cambios",
            fg_color="#ff6b6b",
            hover_color="#cc4444",
            font=("Inter", 14, "bold"),
            height=40,
            corner_radius=8,
            command=self.detectar_cambios
        )
        self.btn_detectar.grid(row=0, column=2, padx=5, sticky="ew")
        
        # 📂 Botón Cargar Local (extra)
        self.btn_cargar_local = ctk.CTkButton(
            control_frame,
            text="📂 Cargar Local",
            fg_color="#2a2a3e",
            hover_color="#3a3a5e",
            font=("Inter", 12),
            height=40,
            corner_radius=8,
            command=self.cargar_local
        )
        self.btn_cargar_local.grid(row=0, column=3, padx=5, sticky="ew")
        
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
            text="● Inicializando...",
            font=("JetBrains Mono", 10),
            text_color="#909097"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Cargar mensaje de bienvenida
        self.mostrar_mensaje_bienvenida()
        
    def hotspots_ejemplo(self):
        """Crea hotspots de ejemplo para mostrar el diseño"""
        for widget in self.hotspots_frame.winfo_children():
            widget.destroy()
        
        frame = ctk.CTkFrame(
            self.hotspots_frame,
            fg_color="transparent",
            corner_radius=12
        )
        frame.pack(fill="x", pady=4)
        
        content = ctk.CTkFrame(
            frame,
            fg_color="#222222",
            border_width=1,
            border_color="#444444",
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
            text="Usa 'Buscar Ubicación' o 'Cargar Local'\ny presiona 'Detectar Cambios'",
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
            text="Busca una ubicación o carga imágenes locales\npara analizar cambios territoriales",
            font=("Inter", 16),
            fill="#606070",
            justify="center"
        )
        
    def buscar_ubicacion_ee(self):
        """Busca una ubicación en Earth Engine y carga imágenes"""
        dialog = ctk.CTkInputDialog(
            text="Ingresa coordenadas (lat, lon):\nEjemplo: -3.465, -62.210",
            title="🛰️ Buscar Ubicación"
        )
        ubicacion = dialog.get_input()
        
        if not ubicacion:
            return
        
        try:
            self.status_label.configure(text="● Buscando en Earth Engine...")
            self.update()
            
            coords = ubicacion.split(',')
            if len(coords) == 2:
                lat = float(coords[0].strip())
                lon = float(coords[1].strip())
                self.ubicacion_actual = (lat, lon)
                
                point = ee.Geometry.Point(lon, lat)
                
                # Buscar imagen 2019
                collection_2019 = ee.ImageCollection('COPERNICUS/S2') \
                    .filterBounds(point) \
                    .filterDate('2019-01-01', '2019-12-31') \
                    .sort('CLOUDY_PIXEL_PERCENTAGE') \
                    .limit(1)
                
                if collection_2019.size().getInfo() > 0:
                    image_2019 = collection_2019.first()
                    url_2019 = image_2019.getThumbURL({
                        'min': 0,
                        'max': 3000,
                        'dimensions': '800x800',
                        'bands': ['B4', 'B3', 'B2']
                    })
                    self.imagen_anterior = url_2019
                    self.imagen_anterior_ee = image_2019
                    self.label_anterior.configure(text=f"EPOCH A: Sentinel-2 2019")
                
                # Buscar imagen 2024
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
                    self.label_actual.configure(text=f"EPOCH B: Sentinel-2 2024")
                
                # Mostrar imágenes
                self.mostrar_imagenes()
                
                # Mostrar coordenadas en la interfaz
                self.status_label.configure(
                    text=f"● Ubicación cargada: {lat}°, {lon}°"
                )
                
                messagebox.showinfo(
                    "✅ Ubicación cargada",
                    f"Imágenes cargadas para:\nLat: {lat}°\nLon: {lon}°"
                )
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al buscar ubicación:\n{str(e)}"
            )
            self.status_label.configure(text="● Error en la búsqueda")
    
    def obtener_datos_cambio(self):
        """Obtiene datos de cambio usando Earth Engine"""
        if not self.imagen_anterior or not self.imagen_actual:
            messagebox.showwarning(
                "Advertencia",
                "Primero carga imágenes usando 'Buscar Ubicación' o 'Cargar Local'."
            )
            return
        
        self.status_label.configure(text="● Obteniendo datos de cambio...")
        self.update()
        
        try:
            # Simular obtención de datos
            time.sleep(2)
            
            # Generar datos de cambio
            datos = {
                "cambios": [
                    {"area": "Sector 7-B", "cambio": "+42%", "tipo": "Deforestación"},
                    {"area": "Sector 3-A", "cambio": "+28%", "tipo": "Urbanización"},
                    {"area": "Sector 5-C", "cambio": "-15%", "tipo": "Recuperación"}
                ],
                "resumen": "Se detectaron 3 áreas con cambios significativos."
            }
            
            # Mostrar en un mensaje
            mensaje = "📊 DATOS DE CAMBIO DETECTADOS\n"
            mensaje += "=" * 30 + "\n"
            for item in datos["cambios"]:
                mensaje += f"• {item['area']}: {item['cambio']} ({item['tipo']})\n"
            mensaje += "\n" + datos["resumen"]
            
            messagebox.showinfo("📊 Datos de Cambio", mensaje)
            self.status_label.configure(text="● Datos obtenidos correctamente")
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al obtener datos:\n{str(e)}"
            )
            self.status_label.configure(text="● Error al obtener datos")
    
    def cargar_local(self):
        """Abre diálogo para cargar imágenes locales"""
        # Cargar imagen anterior
        archivo1 = filedialog.askopenfilename(
            title="Seleccionar Imagen Anterior (2019)",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.tif *.tiff")]
        )
        if archivo1:
            self.imagen_anterior = archivo1
            self.imagen_anterior_ee = None
            self.label_anterior.configure(text=f"EPOCH A: {os.path.basename(archivo1)}")
        
        # Cargar imagen actual
        archivo2 = filedialog.askopenfilename(
            title="Seleccionar Imagen Actual (2024)",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.tif *.tiff")]
        )
        if archivo2:
            self.imagen_actual = archivo2
            self.imagen_actual_ee = None
            self.label_actual.configure(text=f"EPOCH B: {os.path.basename(archivo2)}")
        
        if archivo1 and archivo2:
            self.mostrar_imagenes()
            self.status_label.configure(text="● Imágenes locales cargadas")
    
    def mostrar_imagenes(self):
        """Muestra las dos imágenes en el canvas"""
        if not self.imagen_anterior or not self.imagen_actual:
            self.mostrar_mensaje_bienvenida()
            return
        
        try:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            img1 = Image.open(self.imagen_anterior)
            img2 = Image.open(self.imagen_actual)
            
            img1 = self.redimensionar_imagen(img1, canvas_width//2, canvas_height)
            img2 = self.redimensionar_imagen(img2, canvas_width//2, canvas_height)
            
            self.photo1 = ImageTk.PhotoImage(img1)
            self.photo2 = ImageTk.PhotoImage(img2)
            
            self.canvas.delete("all")
            
            x1 = (canvas_width//2 - img1.width) // 2
            y1 = (canvas_height - img1.height) // 2
            self.canvas.create_image(x1, y1, anchor="nw", image=self.photo1)
            
            x2 = canvas_width//2 + (canvas_width//2 - img2.width) // 2
            y2 = (canvas_height - img2.height) // 2
            self.canvas.create_image(x2, y2, anchor="nw", image=self.photo2)
            
            self.canvas.create_line(
                canvas_width//2, 0,
                canvas_width//2, canvas_height,
                fill="#4edea3",
                width=2,
                dash=(5, 5)
            )
            
            self.canvas.create_text(
                20, 20,
                text="EPOCH A: 2019",
                anchor="nw",
                font=("Inter", 16, "bold"),
                fill="#d4e4fa"
            )
            self.canvas.create_text(
                canvas_width//2 + 20, 20,
                text="EPOCH B: 2024",
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
        self.porcentaje_slider = float(valor)
    
    def detectar_cambios(self):
        """Función principal de detección de cambios"""
        if not self.imagen_anterior or not self.imagen_actual:
            messagebox.showwarning(
                "Advertencia",
                "Primero carga imágenes usando 'Buscar Ubicación' o 'Cargar Local'."
            )
            return
        
        self.status_label.configure(text="● Detectando cambios...")
        self.btn_detectar.configure(text="⏳ Procesando...", state="disabled")
        self.update()
        
        thread = threading.Thread(target=self.procesar_deteccion)
        thread.daemon = True
        thread.start()
    
    def procesar_deteccion(self):
        """Procesa la detección de cambios con imágenes"""
        try:
            time.sleep(2)
            
            # Usar las imágenes cargadas como miniaturas
            img_url_anterior = self.imagen_anterior if self.imagen_anterior else None
            img_url_actual = self.imagen_actual if self.imagen_actual else None
            
            hotspots = [
                {
                    "titulo": "Deforestación detectada",
                    "coords": "3.465, -62.210",
                    "porcentaje": "94.2%",
                    "nivel": "ALTO",
                    "color": "#ff6b6b",
                    "detalle": "+14% en 48h",
                    "imagen": img_url_anterior
                },
                {
                    "titulo": "Nueva actividad minera",
                    "coords": "2.112, -61.004",
                    "porcentaje": "42.8%",
                    "nivel": "MEDIO",
                    "color": "#ffb95f",
                    "detalle": "Estructura detectada",
                    "imagen": img_url_actual
                },
                {
                    "titulo": "Cambio en curso de río",
                    "coords": "3.512, -62.404",
                    "porcentaje": "31.5%",
                    "nivel": "MEDIO",
                    "color": "#4edea3",
                    "detalle": "Aumento de sedimentos",
                    "imagen": None
                },
                {
                    "titulo": "Urbanización detectada",
                    "coords": "3.215, -62.112",
                    "porcentaje": "18.3%",
                    "nivel": "BAJO",
                    "color": "#909097",
                    "detalle": "Nuevas construcciones",
                    "imagen": None
                }
            ]
            
            self.hotspots = hotspots
            self.after(0, lambda: self.actualizar_hotspots(hotspots))
            self.after(0, lambda: self.mostrar_resultado_deteccion())
            self.after(0, lambda: self.status_label.configure(text="● Detección completada"))
            self.after(0, lambda: self.btn_detectar.configure(text="🔍 Detectar Cambios", state="normal"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error en detección:\n{str(e)}"))
            self.after(0, lambda: self.status_label.configure(text="● Error en detección"))
            self.after(0, lambda: self.btn_detectar.configure(text="🔍 Detectar Cambios", state="normal"))
    
    def actualizar_hotspots(self, hotspots):
        """Actualiza el panel lateral con los hotspots detectados"""
        for widget in self.hotspots_frame.winfo_children():
            widget.destroy()
        
        for hotspot in hotspots:
            self.crear_hotspot(
                hotspot["titulo"],
                hotspot["coords"],
                hotspot["porcentaje"],
                hotspot["nivel"],
                hotspot["color"],
                hotspot["detalle"],
                hotspot.get("imagen")
            )
    
    def crear_hotspot(self, titulo, coords, porcentaje, nivel, color, detalle, imagen_url=None):
        """Crea un hotspot en el panel lateral con miniatura"""
        frame = ctk.CTkFrame(
            self.hotspots_frame,
            fg_color="transparent",
            corner_radius=12
        )
        frame.pack(fill="x", pady=4)
        
        # Contenedor principal
        content = ctk.CTkFrame(
            frame,
            fg_color="#ffffff08",
            border_width=1,
            border_color=color,
            corner_radius=12
        )
        content.pack(fill="x", padx=4, pady=4)
        
        # Header con nivel y porcentaje
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
        
        # Cuerpo con miniatura
        body = ctk.CTkFrame(content, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=(0, 8))
        
        # Contenedor flexible para imagen y texto
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        
        # Miniatura (si hay URL)
        if imagen_url:
            try:
                img = Image.open(imagen_url)
                img.thumbnail((60, 60))
                photo = ImageTk.PhotoImage(img)
                img_label = ctk.CTkLabel(row, image=photo, text="")
                img_label.image = photo
                img_label.pack(side="left", padx=(0, 10))
            except:
                pass
        
        # Texto
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text=titulo,
            font=("Inter", 14, "bold"),
            text_color="#d4e4fa"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text=coords,
            font=("JetBrains Mono", 11),
            text_color="#909097"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
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
            
            img = Image.new('RGB', (canvas_width, canvas_height), '#051424')
            draw = ImageDraw.Draw(img)
            
            puntos = [
                (canvas_width//4, canvas_height//3),
                (canvas_width*3//4, canvas_height//3),
                (canvas_width//2, canvas_height*2//3),
                (canvas_width//4, canvas_height*2//3)
            ]
            
            colores = ['#ff6b6b', '#ffb95f', '#4edea3', '#909097']
            textos = ["Alto", "Medio", "Medio", "Bajo"]
            
            for i, (x, y) in enumerate(puntos):
                radio = 40 + i * 10
                color = colores[i]
                
                draw.ellipse(
                    (x-radio, y-radio, x+radio, y+radio),
                    outline=color,
                    width=3
                )
                
                draw.ellipse(
                    (x-radio//3, y-radio//3, x+radio//3, y+radio//3),
                    fill=color
                )
                
                draw.text(
                    (x-25, y+radio+15),
                    f"Cambio {textos[i]}",
                    fill=color
                )
            
            self.photo_resultado = ImageTk.PhotoImage(img)
            
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo_resultado)
            
            self.label_anterior.configure(text="EPOCH A: Análisis completado")
            self.label_actual.configure(text="EPOCH B: Cambios detectados")
            
        except Exception as e:
            print(f"Error al mostrar resultado: {e}")
    
    def rescan_area(self):
        """Re-escanea el área"""
        self.status_label.configure(
            text="● Escaneando área...",
            text_color="#ffb95f"
        )
        self.btn_rescan.configure(text="⏳ Escaneando...", state="disabled")
        
        def finalizar():
            self.status_label.configure(
                text="● Sistema listo",
                text_color="#909097"
            )
            self.btn_rescan.configure(text="↻  RE-SCAN TARGET AREA", state="normal")
        
        self.after(2000, finalizar)
    
    def generar_reporte(self):
        """Genera un reporte de los cambios detectados"""
        if not self.hotspots:
            messagebox.showinfo(
                "ℹ️ Sin datos",
                "Primero ejecuta 'Detectar Cambios' para generar datos."
            )
            return
        
        # Construir el reporte
        reporte = "📊 REPORTE DE CAMBIOS TERRITORIALES\n"
        reporte += "=" * 50 + "\n\n"
        reporte += f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        reporte += f"Ubicación: {self.ubicacion_actual if self.ubicacion_actual else 'No especificada'}\n\n"
        reporte += "=" * 50 + "\n"
        reporte += "HOTSPOTS DETECTADOS\n"
        reporte += "=" * 50 + "\n\n"
        
        for i, hotspot in enumerate(self.hotspots, 1):
            reporte += f"{i}. {hotspot['titulo']}\n"
            reporte += f"   Coordenadas: {hotspot['coords']}\n"
            reporte += f"   Cambio: {hotspot['porcentaje']}\n"
            reporte += f"   Nivel: {hotspot['nivel']}\n"
            reporte += f"   Detalle: {hotspot['detalle']}\n\n"
        
        reporte += "=" * 50 + "\n"
        reporte += f"Total de cambios detectados: {len(self.hotspots)}\n"
        reporte += "=" * 50 + "\n"
        reporte += "Reporte generado por TERRA_INTEL\n"
        
        # Guardar en archivo
        nombre_archivo = f"reporte_cambios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(reporte)
        
        # Mostrar en pantalla
        messagebox.showinfo(
            "✅ Reporte generado",
            f"Reporte guardado en:\n{nombre_archivo}\n\n{reporte}"
        )
if __name__ == "__main__":
    app = TerraIntelApp()
    app.mainloop()
