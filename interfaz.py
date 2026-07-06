# interfaz.py
# Versión Python de TERRA_INTEL - Detección de Cambios

import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter.filedialog as filedialog
from tkinter import messagebox
import os

# Configurar tema oscuro
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class TerraIntelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title("TERRA_INTEL | Change Analysis")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        
        # Colores personalizados (basados en tu HTML)
        self.colors = {
            "background": "#051424",
            "surface": "#122131",
            "surface_container": "#1c2b3c",
            "secondary": "#4edea3",
            "tertiary": "#ffb95f",
            "error": "#ffb4ab",
            "outline": "#909097",
            "outline_variant": "#45464d",
            "on_surface": "#d4e4fa",
            "on_secondary": "#003824",
            "on_error": "#690005"
        }
        
        # Variables de estado
        self.imagen_anterior = None
        self.imagen_actual = None
        self.porcentaje_slider = 50
        
        # Construir la interfaz
        self.setup_ui()
        
    def setup_ui(self):
        """Configura todos los elementos de la interfaz"""
        
        # Frame principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ========== PANEL LATERAL IZQUIERDO ==========
        self.panel = ctk.CTkFrame(
            self, 
            width=320, 
            corner_radius=0,
            fg_color=self.colors["surface_container"]
        )
        self.panel.grid(row=0, column=0, sticky="nsew")
        self.panel.grid_propagate(False)
        
        # Título del panel
        header_panel = ctk.CTkFrame(self.panel, fg_color="transparent")
        header_panel.pack(fill="x", padx=16, pady=16)
        
        ctk.CTkLabel(
            header_panel,
            text="DETECTION SUMMARY",
            font=("JetBrains Mono", 11, "bold"),
            text_color=self.colors["outline_variant"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_panel,
            text="Change Hotspots",
            font=("Inter", 24, "bold"),
            text_color=self.colors["on_surface"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_panel,
            text="Ranked by Magnitude",
            font=("JetBrains Mono", 12),
            text_color=self.colors["outline_variant"]
        ).pack(anchor="w")
        
        # Scrollable frame para hotspots
        self.hotspots_frame = ctk.CTkScrollableFrame(
            self.panel,
            fg_color="transparent",
            height=400
        )
        self.hotspots_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Hotspot 1 - Alto cambio
        self.crear_hotspot(
            "Illegal Logging #0092",
            "3.465, -62.210",
            "94.2%",
            "HIGH CHANGE",
            self.colors["error"],
            self.colors["on_error"],
            "+14% Growth / 48h"
        )
        
        # Hotspot 2 - Cambio medio
        self.crear_hotspot(
            "New Mining Activity",
            "2.112, -61.004",
            "42.8%",
            "MEDIUM CHANGE",
            self.colors["tertiary"],
            self.colors["on_secondary"],
            "Structure Detected"
        )
        
        # Hotspot 3 - Cambio medio
        self.crear_hotspot(
            "River Course Shift",
            "3.512, -62.404",
            "31.5%",
            "MEDIUM CHANGE",
            self.colors["tertiary"],
            self.colors["on_secondary"],
            "Sediment Increase"
        )
        
        # Botón Re-scan
        btn_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=16)
        
        self.btn_rescan = ctk.CTkButton(
            btn_frame,
            text="↻  RE-SCAN TARGET AREA",
            fg_color=self.colors["secondary"],
            text_color=self.colors["on_secondary"],
            hover_color="#3dbd88",
            font=("JetBrains Mono", 12, "bold"),
            height=50,
            corner_radius=12,
            command=self.rescan_area
        )
        self.btn_rescan.pack(fill="x")
        
        # ========== ÁREA PRINCIPAL (Comparación) ==========
        self.main_area = ctk.CTkFrame(
            self,
            fg_color=self.colors["background"],
            corner_radius=0
        )
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)
        
        # Frame para imágenes (contenedor)
        self.image_container = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent"
        )
        self.image_container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.image_container.grid_columnconfigure(0, weight=1)
        self.image_container.grid_rowconfigure(0, weight=1)
        
        # Canvas para mostrar imágenes lado a lado
        self.canvas = ctk.CTkCanvas(
            self.image_container,
            bg=self.colors["background"],
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Labels de información sobre las imágenes
        self.info_frame = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent",
            height=60
        )
        self.info_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_columnconfigure(1, weight=1)
        
        # Info imagen anterior
        self.label_anterior = ctk.CTkLabel(
            self.info_frame,
            text="EPOCH A: 2019 (BASELINE)",
            font=("Inter", 14, "bold"),
            text_color=self.colors["on_surface"]
        )
        self.label_anterior.grid(row=0, column=0, sticky="w")
        
        # Info imagen actual
        self.label_actual = ctk.CTkLabel(
            self.info_frame,
            text="EPOCH B: 2024 (LATEST)",
            font=("Inter", 14, "bold"),
            text_color=self.colors["tertiary"]
        )
        self.label_actual.grid(row=0, column=1, sticky="e")
        
        # ========== CONTROLES INFERIORES ==========
        control_frame = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent",
            height=80
        )
        control_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)
        
        # Botón cargar imagen anterior
        self.btn_cargar_anterior = ctk.CTkButton(
            control_frame,
            text="📂 Cargar Imagen Anterior",
            fg_color="#2a3a4e",
            hover_color="#3a4a5e",
            font=("Inter", 12),
            height=40,
            corner_radius=8,
            command=self.cargar_imagen_anterior
        )
        self.btn_cargar_anterior.grid(row=0, column=0, padx=5, sticky="ew")
        
        # Botón cargar imagen actual
        self.btn_cargar_actual = ctk.CTkButton(
            control_frame,
            text="📂 Cargar Imagen Actual",
            fg_color="#2a3a4e",
            hover_color="#3a4a5e",
            font=("Inter", 12),
            height=40,
            corner_radius=8,
            command=self.cargar_imagen_actual
        )
        self.btn_cargar_actual.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Botón detectar cambios
        self.btn_detectar = ctk.CTkButton(
            control_frame,
            text="🔍 DETECTAR CAMBIOS",
            fg_color=self.colors["error"],
            hover_color="#cc4444",
            font=("Inter", 14, "bold"),
            height=40,
            corner_radius=8,
            command=self.detectar_cambios
        )
        self.btn_detectar.grid(row=0, column=2, padx=5, sticky="ew")
        
        # Slider de comparación (en lugar del de JavaScript)
        slider_frame = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent",
            height=50
        )
        slider_frame.grid(row=3, column=0, sticky="ew", padx=40, pady=5)
        
        ctk.CTkLabel(
            slider_frame,
            text="2019",
            font=("Inter", 12),
            text_color=self.colors["outline_variant"]
        ).pack(side="left", padx=10)
        
        self.slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.actualizar_slider,
            progress_color=self.colors["secondary"],
            button_color=self.colors["secondary"]
        )
        self.slider.pack(side="left", fill="x", expand=True, padx=10)
        self.slider.set(50)
        
        ctk.CTkLabel(
            slider_frame,
            text="2024",
            font=("Inter", 12),
            text_color=self.colors["tertiary"]
        ).pack(side="left", padx=10)
        
        # Estado del sistema
        self.status_label = ctk.CTkLabel(
            self.main_area,
            text="● SAR-V2 Orbital Stream: Nominal",
            font=("JetBrains Mono", 10),
            text_color=self.colors["outline_variant"]
        )
        self.status_label.grid(row=4, column=0, sticky="w", padx=20, pady=10)
        
        # Vincular evento de redimensionamiento
        self.bind("<Configure>", self.on_resize)
        
        # Imágenes de ejemplo (placeholders)
        self.cargar_imagenes_ejemplo()
    
    def crear_hotspot(self, titulo, coords, porcentaje, nivel, color, text_color, detalle):
        """Crea un hotspot en el panel lateral - VERSIÓN CORREGIDA"""
        frame = ctk.CTkFrame(
            self.hotspots_frame,
            fg_color="transparent",
            corner_radius=12
        )
        frame.pack(fill="x", pady=4)
        
        # Contenedor con borde - SIN TRANSPARENCIA
        content = ctk.CTkFrame(
            frame,
            fg_color="transparent",
            border_width=1,
            border_color=color,  # Color sólido, sin sufijo "40"
            corner_radius=12
        )
        content.pack(fill="x", padx=4, pady=4)
        
        # Header del hotspot
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            header,
            text=nivel,
            font=("JetBrains Mono", 10, "bold"),
            text_color=text_color,
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
        
        # Info del hotspot
        info = ctk.CTkFrame(content, fg_color="transparent")
        info.pack(fill="x", padx=12, pady=(0, 8))
        
        ctk.CTkLabel(
            info,
            text=titulo,
            font=("Inter", 14, "bold"),
            text_color=self.colors["on_surface"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info,
            text=coords,
            font=("JetBrains Mono", 11),
            text_color=self.colors["outline_variant"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info,
            text=detalle,
            font=("Inter", 11),
            text_color=color
        ).pack(anchor="w")
    
    def cargar_imagen_anterior(self):
        """Carga la imagen 'anterior' desde el sistema de archivos"""
        archivo = filedialog.askopenfilename(
            title="Seleccionar Imagen Anterior (2019)",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.tif *.tiff")]
        )
        if archivo:
            self.imagen_anterior = archivo
            self.mostrar_imagenes()
            self.label_anterior.configure(text=f"EPOCH A: {os.path.basename(archivo)}")
    
    def cargar_imagen_actual(self):
        """Carga la imagen 'actual' desde el sistema de archivos"""
        archivo = filedialog.askopenfilename(
            title="Seleccionar Imagen Actual (2024)",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.tif *.tiff")]
        )
        if archivo:
            self.imagen_actual = archivo
            self.mostrar_imagenes()
            self.label_actual.configure(text=f"EPOCH B: {os.path.basename(archivo)}")
    
    def cargar_imagenes_ejemplo(self):
        """Carga imágenes de ejemplo (placeholders)"""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            text="Carga dos imágenes satelitales\npara iniciar la comparación",
            font=("Inter", 20),
            fill=self.colors["outline_variant"],
            justify="center"
        )
    
    def mostrar_imagenes(self):
        """Muestra las dos imágenes en el canvas con el slider"""
        if not self.imagen_anterior or not self.imagen_actual:
            return
        
        try:
            # Obtener tamaño del canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            # Cargar y redimensionar imágenes
            img1 = Image.open(self.imagen_anterior)
            img2 = Image.open(self.imagen_actual)
            
            # Redimensionar manteniendo aspecto
            img1.thumbnail((canvas_width//2, canvas_height))
            img2.thumbnail((canvas_width//2, canvas_height))
            
            # Convertir a PhotoImage
            self.photo1 = ImageTk.PhotoImage(img1)
            self.photo2 = ImageTk.PhotoImage(img2)
            
            # Limpiar canvas
            self.canvas.delete("all")
            
            # Posicionar imágenes lado a lado
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
                fill=self.colors["secondary"],
                width=2,
                dash=(5, 5)
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar las imágenes:\n{str(e)}")
    
    def actualizar_slider(self, valor):
        """Actualiza la visualización según el slider"""
        self.porcentaje_slider = float(valor)
    
    def detectar_cambios(self):
        """Función principal de detección de cambios (Parte 3)"""
        if not self.imagen_anterior or not self.imagen_actual:
            messagebox.showwarning(
                "Advertencia",
                "Por favor carga ambas imágenes satelitales primero."
            )
            return
        
        # Aquí va tu algoritmo de detección de cambios
        messagebox.showinfo(
            "Detección de Cambios",
            f"🔍 Analizando cambios entre:\n{self.imagen_anterior}\ny\n{self.imagen_actual}\n\n(Implementa aquí tu algoritmo)"
        )
    
    def rescan_area(self):
        """Re-escanea el área"""
        self.status_label.configure(
            text="● Escaneando área...",
            text_color=self.colors["tertiary"]
        )
        self.after(2000, lambda: self.status_label.configure(
            text="● SAR-V2 Orbital Stream: Nominal",
            text_color=self.colors["outline_variant"]
        ))
    
    def on_resize(self, event):
        """Maneja el redimensionamiento de la ventana"""
        if hasattr(self, 'imagen_anterior') and self.imagen_anterior:
            self.mostrar_imagenes()

# Punto de entrada
if __name__ == "__main__":
    app = TerraIntelApp()
    app.mainloop()