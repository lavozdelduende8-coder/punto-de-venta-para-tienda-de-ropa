import tkinter as tk	
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
import shutil
import os 
import sys 
 

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "pos.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA database_list;")
print("DB EN USO:", cur.fetchall())

class LoginWindow:
	def __init__(self, master):
		self.master = master
		self.master.title("Inicio de sesión")

		# ---------------- CENTRAR LA VENTANA ----------------
		ancho = 350
		alto = 200
		screen_w = master.winfo_screenwidth()
		screen_h = master.winfo_screenheight()
		x = (screen_w // 2) - (ancho // 2)
		y = (screen_h // 2) - (alto // 2)
		master.geometry(f"{ancho}x{alto}+{x}+{y}")

		# ---------------- ESTILOS ----------------
		master.config(bg="#000000")   # Fondo negro
		font_lbl = ("Segoe UI", 12, "bold")
		font_entry = ("Segoe UI", 12)

		# ---------------- INTERFAZ ----------------
		tk.Label(master, text="Usuario:", bg="#000000", fg="white",
				font=font_lbl).pack(pady=5)

		self.entry_user = tk.Entry(master, font=font_entry, width=25)
		self.entry_user.pack(pady=3)

		tk.Label(master, text="Contraseña:", bg="#000000", fg="white",
				font=font_lbl).pack(pady=5)

		self.entry_pass = tk.Entry(master, show="*", font=font_entry, width=25)
		self.entry_pass.pack(pady=3)

		tk.Button(master,
				text="Ingresar",
				font=("Segoe UI", 12, "bold"),
				bg="#1e90ff",
				fg="white",
				width=12,
				command=self.verificar).pack(pady=12)

	def verificar(self):
		usuario = self.entry_user.get()
		contrasena = self.entry_pass.get()

		import sqlite3
		conn = sqlite3.connect("pos.db")
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND contrasena=?", (usuario, contrasena))
		data = cursor.fetchone()
		conn.close()

		if data:
			self.master.destroy()
			self.abrir_pos()
		else:
			from tkinter import messagebox
			messagebox.showerror("Error", "Usuario o contraseña incorrectos")

	def abrir_pos(self):
		root = tk.Tk()
		app = POSApp(root)  # tu clase principal
		root.mainloop()


class POSApp:
	def __init__(self, root):
		import sqlite3

		self.root = root

		# 🔑 OBLIGATORIO: referencia del menú
		self.menu_win = None

		# ❌ ELIMINAMOS conexión global
		# self.conn = sqlite3.connect("pos.db")

		# ✔️ Crear tablas usando conexión controlada
		self.crear_tablas()

		# ✔️ Inicializar UI
		self.crear_interfaz()

		# ✔️ Cierre limpio del programa
		self.root.protocol("WM_DELETE_WINDOW", self.salir_programa)

	def get_db_connection(self):
		import sqlite3, os, sys

		if getattr(sys, 'frozen', False):
			base_dir = os.path.dirname(sys.executable)
		else:
			base_dir = os.path.dirname(os.path.abspath(__file__))

		db_path = os.path.join(base_dir, "pos.db")

		return sqlite3.connect(
			db_path,
			timeout=10,
			check_same_thread=False
		)

	 # ---------------- Función para crear todas las tablas ----------------
   

	def crear_tablas(self):
		import sqlite3

		with self.get_db_connection() as conn:
			cur = conn.cursor()

			cur.execute("""
			CREATE TABLE IF NOT EXISTS productos (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				nombre TEXT NOT NULL,
				precio REAL NOT NULL,
				stock INTEGER DEFAULT 0
			)
			""")

			cur.execute("""
			CREATE TABLE IF NOT EXISTS ventas (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				fecha TEXT,
				total REAL
			)
			""")

			cur.execute("""
			CREATE TABLE IF NOT EXISTS detalle_ventas (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				venta_id INTEGER,
				producto TEXT,
				cantidad INTEGER,
				precio REAL
			)
			""")

			# NO commit manual
			# with se encarga de cerrar y guardar

	def crear_interfaz(self):
		import sqlite3
		from tkinter import ttk
		import tkinter as tk

		# ------------------ PANTALLA COMPLETA ------------------
		self.root.state('zoomed')  # Maximiza la ventana al abrir
		# self.root.attributes('-fullscreen', True)  # Pantalla completa real (opcional)

		# ---------------- PANEL IZQUIERDO (BUSCADOR) ----------------
		left_panel = tk.Frame(self.root, bg="#2b2b2b", width=260)
		left_panel.pack(side="left", fill="y")

		# Botón de menú
		menu_btn = tk.Button(
			left_panel, text="☰", bg="#2b2b2b", fg="white",
			font=("Segoe UI", 16, "bold"), relief="flat",
			command=self.abrir_menu_lateral
		)
		menu_btn.pack(pady=15)

		tk.Label(left_panel, text="🔍 Buscar producto:", bg="#2b2b2b", fg="white",
				font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=15)

		self.search_var = tk.StringVar()
		search_entry = tk.Entry(left_panel, textvariable=self.search_var,
								font=("Segoe UI", 11), width=25)
		search_entry.pack(pady=5, padx=15)

		self.sugerencias = tk.Listbox(left_panel, font=("Consolas", 10),
									bg="white", fg="black", height=8, width=40)
		self.sugerencias.pack(pady=5, padx=15, fill="both", expand=True)

		search_entry.bind("<KeyRelease>", self.mostrar_sugerencias)
		self.sugerencias.bind("<<ListboxSelect>>", self.seleccionar_sugerencia)
		self.sugerencias.bind("<Motion>", self.hover_sugerencias)
		self.sugerencias.bind("<Leave>", lambda e: self.sugerencias.selection_clear(0, tk.END))

		btn_buscar = tk.Button(left_panel, text="Buscar", command=self.buscar_producto,
			bg="#0078D7", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", width=20)
		btn_buscar.pack(pady=10)

		# Hover
		self.agregar_hover(btn_buscar, "#0078D7", "#005fa3")


		# ---------------- PANEL CENTRAL (CARRITO) ----------------
		center_frame = tk.Frame(self.root, bg="#1e1e1e")
		center_frame.pack(side="left", fill="both", expand=True)

		tk.Label(center_frame, text="🛒 Carrito de compras", bg="#1e1e1e", fg="white",
				font=("Segoe UI", 14, "bold")).pack(pady=10)

		# ==== COLUMNAS CORRECTAS ====
		columns = ("ID_Producto", "Producto", "Cantidad", "Precio", "Subtotal", "descuento")
	

		self.tree = ttk.Treeview(center_frame, columns=columns, show="headings", height=15)

		self.tree.heading("ID_Producto", text="ID")
		self.tree.heading("Producto", text="Producto")
		self.tree.heading("Cantidad", text="Cantidad")
		self.tree.heading("Precio", text="Precio")
		self.tree.heading("Subtotal", text="Subtotal")
		self.tree.heading("descuento", text="descuento")

		self.tree.column("ID_Producto", width=60, anchor="center")
		self.tree.column("Producto", width=160, anchor="w")
		self.tree.column("Cantidad", width=80, anchor="center")
		self.tree.column("Precio", width=90, anchor="e")
		self.tree.column("Subtotal", width=100, anchor="e")
		self.tree.column("descuento", width=90, anchor="e")
		self.tree.tag_configure("descuento", foreground="#28a745")

		self.tree.pack(pady=10, padx=20, fill="y", expand=True)

		# ===== CONTROLES DE AUMENTAR / REDUCIR =====
		control_frame = tk.Frame(center_frame, bg="#1e1e1e")
		control_frame.pack(pady=10)

		btn_aumentar = tk.Button(
			control_frame,
			text="➕ Aumentar",
			bg="#4CAF50",
			fg="white",
			font=("Segoe UI", 14, "bold"),
			relief="flat",
			width=18,
			height=2,
			command=self.aumentar_cantidad
		)
		btn_aumentar.pack(side="left", padx=10)
		self.agregar_hover(btn_aumentar, "#4CAF50", "#3e8e41")

		btn_reducir = tk.Button(
			control_frame,
			text="➖ Reducir",
			bg="#F44336",
			fg="white",
			font=("Segoe UI", 14, "bold"),
			relief="flat",
			width=18,
			height=2,
			command=self.reducir_cantidad
		)
		btn_reducir.pack(side="left", padx=10)
		self.agregar_hover(btn_reducir, "#F44336", "#c62828")

		# ===== TOTAL ====
		# Efecto hover
		self.agregar_hover(btn_reducir, "#F44336", "#c62828")

		tk.Label(center_frame, text="TOTAL:", bg="#1e1e1e", fg="#00FF7F",
				font=("Segoe UI", 24, "bold")).pack()
		self.label_total = tk.Label(center_frame, text="0.00", bg="#1e1e1e",
									fg="#00FF7F", font=("Segoe UI", 30, "bold"))
		self.label_total.pack()

		# ---------------- PANEL DERECHO (LOGO + BOTONES) ----------------
		right_frame = tk.Frame(self.root, bg="#2b2b2b", width=250)
		right_frame.pack(side="right", fill="y")

		logo_frame = tk.Frame(right_frame, bg="#2b2b2b")
		logo_frame.pack(side="top", fill="x")

		# --- BOTÓN DE CERRAR SESIÓN ABAJO DEL LOGO ---
		btn_cerrar = tk.Button(
			right_frame,
			text="🔒 Cerrar sesión",
			bg="#e74c3c",
			fg="white",
			font=("Segoe UI", 11, "bold"),
			relief="flat",
			width=20,
			height=2,
			command=lambda: self.cerrar_sesion()
		)
		btn_cerrar.pack(side="bottom", pady=20)

		# Hover
		self.agregar_hover(btn_cerrar, "#e74c3c", "#c0392b")


		try:
			from PIL import Image, ImageTk
			logo_img = Image.open("logoo coloR.jpeg")
			logo_img = logo_img.resize((180, 100))
			self.logo_tk = ImageTk.PhotoImage(logo_img)
			tk.Label(logo_frame, image=self.logo_tk, bg="#2b2b2b").pack(pady=20)
		except Exception as e:
			tk.Label(logo_frame, text="Logo no encontrado", bg="#2b2b2b", fg="gray").pack(pady=20)
			print("Error cargando logo:", e)

		botones_frame = tk.Frame(right_frame, bg="#2b2b2b")
		botones_frame.pack(side="top", fill="both", expand=True)

		botones = [
			("F3 Reimprimir ticket", self.reimprimir_ultimo_ticket, "#0078D7"),
			("F10 Pagar", self.finalizar_venta, "#4CAF50"),
			("💸 Gastos", self.abrir_gastos, "#231AA8"),
			("💰 Salarios", self.pagar_salario, "#928121"),
			("F2 Descuento", self.aplicar_descuento, "#6A1B9A"),
			("💳 Devoluciones", self.devolucion_simple, "#FF5722"),
		]


		for txt, cmd, color in botones:
			btn = tk.Button(
				botones_frame,
				text=txt,
				bg=color,
				fg="white",
				font=("Segoe UI", 11, "bold"),
				relief="flat",
				height=2,
				width=20,
				command=cmd
			)
			btn.pack(pady=10)

			# Hover automático para cada botón
			self.agregar_hover(btn, color, "#1b1b1b")


		self.pedir_fondo()

	def hover_sugerencias(self, event):
		index = self.sugerencias.nearest(event.y)
		self.sugerencias.selection_clear(0, tk.END)
		self.sugerencias.selection_set(index)

	def agregar_hover(self, widget, color_normal, color_hover):
		widget.bind("<Enter>", lambda e: widget.config(bg=color_hover))
		widget.bind("<Leave>", lambda e: widget.config(bg=color_normal))

	def mostrar_sugerencias(self, event):
		texto = self.search_var.get().strip().lower()
		self.sugerencias.delete(0, tk.END)

		# Si no hay texto, solo limpia la lista
		if not texto:
			return

		import sqlite3
		conn = sqlite3.connect(DB_PATH)
		cursor = conn.cursor()

		try:
			cursor.execute("""
				SELECT nombre_producto, precio_venta
				FROM productos
				WHERE stock IS NOT NULL
				AND nombre_producto LIKE ?
				LIMIT 20
			""", ('%' + texto + '%',))
			resultados = cursor.fetchall()
		except sqlite3.Error:
			conn.close()
			return

		conn.close()

		if not resultados:
			return

		for nombre, precio in resultados:
			self.sugerencias.insert(
				tk.END,
				f"{nombre.ljust(28)} ${precio:>7.2f}"
			)

	
	def seleccionar_sugerencia(self, event):
		if not self.sugerencias.curselection():
			return

		seleccion = self.sugerencias.get(self.sugerencias.curselection())
		nombre = seleccion.split("$")[0].strip()

		import sqlite3
		conn = sqlite3.connect(DB_PATH)
		cursor = conn.cursor()

		cursor.execute("""
			SELECT id_producto, nombre_producto, precio_venta, stock
			FROM productos
			WHERE nombre_producto = ?
			LIMIT 1
		""", (nombre,))

		fila = cursor.fetchone()
		conn.close()

		if not fila:
			return

		id_producto, nombre, precio, stock = fila

		if stock <= 0:
			from tkinter import messagebox
			messagebox.showwarning(
				"Sin stock",
				f"El producto '{nombre}' no tiene stock disponible."
			)
			return

		# Agrega al carrito
		self.agregar_producto(id_producto, nombre, 1, precio, stock)

		# Limpia SOLO el Entry (la lista se queda)
		self.search_var.set("")

	
	# --- Estas funciones deben estar fuera del confirmar_pago, en la clase POSApp ---
	def nueva_venta(self):
		"""Limpia el carrito después de una venta."""
		for item in self.tree.get_children():
			self.tree.delete(item)
		self.total = 0
		self.actualizar_totales()

	
	# --- Estas funciones deben estar fuera del confirmar_pago, en la clase POSApp ---
	def nueva_venta(self):
		"""Limpia el carrito después de una venta."""
		for item in self.tree.get_children():
			self.tree.delete(item)
		self.total = 0
		self.actualizar_totales()

	def anular_orden(self):
		"""Permite anular toda la venta actual."""
		if messagebox.askyesno("Anular orden", "¿Seguro que quieres anular esta orden?"):
			self.nueva_venta()

	def obtener_datos_venta(self, id_venta):
		import sqlite3

		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()

		# ===== ENCABEZADO DE LA VENTA =====
		cur.execute("""
			SELECT fecha, total, tipo_pago
			FROM ventas
			WHERE id_venta = ?
		""", (id_venta,))
		venta = cur.fetchone()

		if not venta:
			conn.close()
			return None

		fecha, total_venta, tipo_pago = venta

		# ===== PRODUCTOS =====
		# Usamos 0 como descuento si la columna no existe
		try:
			cur.execute("""
				SELECT
					p.nombre_producto,
					vd.cantidad,
					vd.precio_unitario,
					vd.subtotal,
					vd.descuento
				FROM ventas_detalle vd
				JOIN productos p ON vd.id_producto = p.id_producto
				WHERE vd.id_venta = ?
			""", (id_venta,))
		except sqlite3.OperationalError:
			cur.execute("""
				SELECT
					p.nombre_producto,
					vd.cantidad,
					vd.precio_unitario,
					vd.subtotal,
					0 AS descuento
				FROM ventas_detalle vd
				JOIN productos p ON vd.id_producto = p.id_producto
				WHERE vd.id_venta = ?
			""", (id_venta,))

		productos = cur.fetchall()

		total_productos = sum(p[1] for p in productos)

		# ===== PAGOS (FUENTE REAL) =====
		cur.execute("""
			SELECT metodo, monto
			FROM ventas_pagos
			WHERE id_venta = ?
		""", (id_venta,))
		pagos = cur.fetchall()


		# Calcular recibido y cambio
		recibido = sum(p[1] for p in pagos) if pagos else total_venta
		cambio = recibido - total_venta

		conn.close()

		# ===== ARMAR DICT FINAL =====
		datos_venta = {
			"fecha": fecha,
			"id_venta": id_venta,
			"productos": productos,
			"total_productos": total_productos,
			"total_venta": total_venta,
			"pagos": pagos,
			"recibido": recibido,
			"cambio": cambio
		}

		return datos_venta

	def actualizar_totales(self):
		"""Refresca los totales en pantalla."""
		self.label_subtotal.config(text=f"Subtotal: ${self.total:.2f}")
		self.label_total.config(text=f"TOTAL: ${self.total:.2f}")


	# 🧭 Menú lateral (VERSIÓN CORREGIDA)
	def abrir_menu_lateral(self):
		import tkinter as tk
		from tkinter import ttk

		# 🔒 EVITAR DOBLE INSTANCIA
		if self.menu_win and self.menu_win.winfo_exists():
			self.menu_win.lift()
			self.menu_win.focus_force()
			return

		# === VENTANA MENÚ LATERAL ===
		self.menu_win = tk.Toplevel(self.root)
		self.menu_win.title("Menú principal")
		self.menu_win.geometry("400x800+0+0")
		self.menu_win.config(bg="#2b2b2b")
		self.menu_win.resizable(False, False)

		# ❌ QUITAMOS toolwindow (causa bloqueos en Windows)
		# self.menu_win.attributes("-toolwindow", True)

		# 🔑 CIERRE CONTROLADO
		self.menu_win.protocol("WM_DELETE_WINDOW", self._cerrar_menu_lateral)

		# === SCROLL ===
		contenedor = tk.Frame(self.menu_win, bg="#2b2b2b")
		contenedor.pack(fill="both", expand=True)

		canvas = tk.Canvas(contenedor, bg="#2b2b2b", highlightthickness=0)
		scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
		frame_botones = tk.Frame(canvas, bg="#2b2b2b")

		frame_botones.bind(
			"<Configure>",
			lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
		)

		canvas.create_window((200, 30), window=frame_botones, anchor="n")
		canvas.configure(yscrollcommand=scrollbar.set)

		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		# === TÍTULO ===
		tk.Label(
			frame_botones,
			text="⚙️ Panel de Administración",
			bg="#2b2b2b",
			fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(pady=15)

		# === COLORES ===
		COLORS = {
			"📊 Tablero / Reportes": ("#0078D7", "#005BB5"),
			"🛒 Productos": ("#27ae60", "#1e8449"),
			"👥 Mayoristas / Clientes": ("#8e44ad", "#6c3483"),
			"💳 Historial Ventas": ("#f39c12", "#d68910"),
			"🧾 Configuración de Ticket": ("#16a085", "#117864"),
			"👤 Usuarios": ("#c0392b", "#922b21"),
			"ℹ️ Información del Programa": ("#34495e", "#2c3e50"),
		}

		# === EFECTOS ===
		def add_shadow(widget):
			sombra = tk.Frame(frame_botones, bg="#1e1e1e")
			sombra.place(in_=widget, x=3, y=3, relwidth=1, relheight=1)
			widget.lift()

		def make_hover(btn, normal, hover):
			btn.bind("<Enter>", lambda e: btn.config(bg=hover))
			btn.bind("<Leave>", lambda e: btn.config(bg=normal))

		# === SECCIONES ===
		secciones = [
			("📊 Tablero / Reportes", self.abrir_reportes),
			("🛒 Productos", self.abrir_productos),
			("👥 Mayoristas / Clientes", self.abrir_mayoristas),
			("💳 Historial Ventas", self.abrir_historial_ventas),
			("🧾 Configuración de Ticket", self.abrir_configuracion_ticket),
			("👤 Usuarios", self.abrir_usuarios),
			("ℹ️ Información del Programa", self.informacion_programa),
		]

		# ✅ EJECUCIÓN SEGURA
		def ejecutar_y_cerrar(fn):
			def _accion():
				self._cerrar_menu_lateral()
				self.root.after(50, fn)  # deja respirar el mainloop
			return _accion

		for txt, cmd in secciones:
			bg, hover = COLORS.get(txt, ("#0078D7", "#005BB5"))

			btn = tk.Button(
				frame_botones,
				text=txt,
				font=("Segoe UI", 12, "bold"),
				bg=bg,
				fg="white",
				relief="flat",
				width=30,
				height=2,
				command=ejecutar_y_cerrar(cmd)
			)

			btn.pack(pady=12)
			add_shadow(btn)
			make_hover(btn, bg, hover)

		# === BOTÓN CERRAR ===
		btn_close = tk.Button(
			frame_botones,
			text="❌ Cerrar",
			font=("Segoe UI", 11, "bold"),
			bg="#e74c3c",
			fg="white",
			relief="flat",
			width=30,
			height=2,
			command=self._cerrar_menu_lateral
		)
		btn_close.pack(pady=20)

		add_shadow(btn_close)
		btn_close.bind("<Enter>", lambda e: btn_close.config(bg="#c0392b"))
		btn_close.bind("<Leave>", lambda e: btn_close.config(bg="#e74c3c"))


	def _cerrar_menu_lateral(self):
		if self.menu_win and self.menu_win.winfo_exists():
			self.menu_win.destroy()
		self.menu_win = None

	def ejecutar_y_cerrar(fn):
			def _accion():
				# 1️⃣ Ejecutar la función PRIMERO
				self.root.after(10, fn)

				# 2️⃣ Cerrar el menú DESPUÉS
				self.root.after(30, self._cerrar_menu_lateral)
			return _accion

	# --- FUNCIONES DE SECCIONES ---
	# --- reportes ---
	def abrir_reportes(self):
		import tkinter as tk

		ventana = tk.Toplevel(self.root)
		ventana.title("📊 Reportes")
		ventana.geometry("800x600")
		ventana.config(bg="#1e1e1e")
		ventana.transient(self.root)
		ventana.focus_force()

		tk.Label(
			ventana,
			text="📊 Reportes del Sistema",
			bg="#1e1e1e",
			fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(pady=10)

		BOTONES = [
			("📉 Reporte de Gastos", self.reporte_gastos, "#2ecc71"),
			("📊 Reporte de Ventas", self.reporte_ventas, "#3498db"),
			("💰 Reporte de Salarios", self.reporte_salarios, "#9b59b6"),
			("📦 Reporte de Productos", self.reporte_productos, "#f39c12"),
			("🏬 Productos por Departamento", self.reporte_productos_por_departamento, "#16a085"),
			("🛒 Reporte de Mayoristas", self.reporte_mayoristas, "#e67e22"),
		]

		for texto, comando, color in BOTONES:
			tk.Button(
				ventana,
				text=texto,
				bg=color,
				fg="white",
				font=("Segoe UI", 11, "bold"),
				width=35,
				height=2,
				command=comando
			).pack(pady=6)

		tk.Button(
			ventana,
			text="❌ Cerrar",
			bg="#e74c3c",
			fg="white",
			font=("Segoe UI", 11, "bold"),
			width=20,
			command=ventana.destroy
		).pack(pady=20)

	def reporte_gastos(self):
		import sqlite3
		from tkinter import ttk
		import tkinter as tk
		from tkinter import messagebox, filedialog
		from datetime import datetime
		from tkcalendar import DateEntry
		import csv

		ventana = tk.Toplevel(self.root)
		ventana.title("📉 Reporte de Gastos")
		ventana.geometry("900x520")  # ← más baja
		ventana.config(bg="#1e1e1e")

			# === HACER VENTANA MODAL ===
		ventana.transient(self.root)
		ventana.grab_set()
		ventana.focus_force()

		tk.Label(ventana, text="📉 Reporte de Gastos con Filtros", bg="#1e1e1e", fg="white",
				font=("Segoe UI", 13, "bold")).pack(pady=6)

		# --- Frame de filtros ---
		frame_filtros = tk.Frame(ventana, bg="#1e1e1e")
		frame_filtros.pack(pady=4)

		# Categoría
		tk.Label(frame_filtros, text="Categoría:", bg="#1e1e1e", fg="white",
				font=("Segoe UI", 10)).grid(row=0, column=0, padx=4)
		categoria_var = tk.StringVar()
		combo_categoria = ttk.Combobox(frame_filtros, textvariable=categoria_var,
									state="readonly", width=20)
		combo_categoria["values"] = ["Todas", "Papelería", "Limpieza", "Insumos", "Devolución", "Pasajes", "Otros"]
		combo_categoria.current(0)
		combo_categoria.grid(row=0, column=1, padx=4)

		# Fecha inicio
		tk.Label(frame_filtros, text="Desde:", bg="#1e1e1e", fg="white",
				font=("Segoe UI", 10)).grid(row=0, column=2, padx=4)
		fecha_inicio = DateEntry(frame_filtros, width=12, background='darkblue',
								foreground='white', borderwidth=2, date_pattern='yyyy-MM-dd')
		fecha_inicio.grid(row=0, column=3, padx=4)

		# Fecha fin
		tk.Label(frame_filtros, text="Hasta:", bg="#1e1e1e", fg="white",
				font=("Segoe UI", 10)).grid(row=0, column=4, padx=4)
		fecha_fin = DateEntry(frame_filtros, width=12, background='darkblue',
							foreground='white', borderwidth=2, date_pattern='yyyy-MM-dd')
		fecha_fin.grid(row=0, column=5, padx=4)

		# --- Tabla ---
		columnas = ("Fecha", "Categoría", "Descripción", "Monto")
		tree = ttk.Treeview(ventana, columns=columnas, show="headings", height=10)
		for col in columnas:
			tree.heading(col, text=col)
			tree.column(col, width=180 if col != "Descripción" else 280, anchor="center")
		tree.pack(expand=True, fill="both", padx=10, pady=5)

		# Total de gastos filtrados
		total_label = tk.Label(ventana, text="Total: $0.00", bg="#1e1e1e",
							fg="#2ecc71", font=("Segoe UI", 11, "bold"))
		total_label.pack(pady=3)

		# --- Función para cargar datos ---
		resultados_actuales = []

		def cargar_datos():
			nonlocal resultados_actuales
			for item in tree.get_children():
				tree.delete(item)

			categoria = categoria_var.get()
			f_ini = fecha_inicio.get_date().strftime("%Y-%m-%d")
			f_fin = fecha_fin.get_date().strftime("%Y-%m-%d")

			query = "SELECT fecha, categoria, descripcion, monto FROM gastos WHERE 1=1"
			params = []

			if categoria != "Todas":
				query += " AND categoria = ?"
				params.append(categoria)

			if f_ini:
				query += " AND date(fecha) >= date(?)"
				params.append(f_ini)

			if f_fin:
				query += " AND date(fecha) <= date(?)"
				params.append(f_fin)

			query += " ORDER BY fecha DESC"

			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()
			cur.execute("""
				CREATE TABLE IF NOT EXISTS gastos (
					id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
					fecha TEXT,
					categoria TEXT,
					descripcion TEXT,
					monto REAL
				)
			""")
			cur.execute(query, params)
			resultados_actuales = cur.fetchall()
			conn.close()

			total = 0
			for row in resultados_actuales:
				monto_formateado = f"${row[3]:,.2f}"
				tree.insert("", "end", values=(row[0], row[1], row[2], monto_formateado))

				total += row[3]

			total_label.config(text=f"Total: ${total:,.2f}")

			if not resultados_actuales:
				messagebox.showinfo("Sin resultados", "No se encontraron gastos con esos filtros.")

		# --- Exportar a CSV ---
		def exportar_csv():
			if not resultados_actuales:
				messagebox.showwarning("Sin datos", "No hay datos para exportar. Aplica un filtro primero.")
				return

			archivo = filedialog.asksaveasfilename(
				defaultextension=".csv",
				filetypes=[("Archivo CSV", "*.csv")],
				title="Guardar reporte como"
			)
			if not archivo:
				return

			try:
				with open(archivo, "w", newline='', encoding="utf-8") as f:
					writer = csv.writer(f)
					writer.writerow(["Fecha", "Categoría", "Descripción", "Monto"])
					for row in resultados_actuales:
						writer.writerow(row)
				messagebox.showinfo("Éxito", f"Reporte exportado correctamente:\n{archivo}")
			except Exception as e:
				messagebox.showerror("Error", f"No se pudo exportar el archivo:\n{e}")

		# --- Botones ---
		frame_botones = tk.Frame(ventana, bg="#1e1e1e")
		frame_botones.pack(pady=6)

		# Botón Aplicar Filtros
		btn_aplicar = tk.Button(
			frame_botones,
			text="🔍 Aplicar Filtros",
			bg="#27ae60",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			width=18,
			command=cargar_datos
		)
		btn_aplicar.grid(row=0, column=0, padx=8)
		self.agregar_hover(btn_aplicar, "#27ae60", "#1f8b4c")


		# Botón Exportar CSV
		btn_exportar = tk.Button(
			frame_botones,
			text="💾 Exportar CSV",
			bg="#f39c12",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			width=18,
			command=exportar_csv
		)
		btn_exportar.grid(row=0, column=1, padx=8)
		self.agregar_hover(btn_exportar, "#f39c12", "#d68910")


		# Botón Cerrar
		btn_cerrar = tk.Button(
			frame_botones,
			text="❌ Cerrar",
			bg="#e74c3c",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			width=15,
			command=ventana.destroy
		)
		btn_cerrar.grid(row=0, column=2, padx=8)
		self.agregar_hover(btn_cerrar, "#e74c3c", "#c0392b")

		cargar_datos()

	def reporte_ventas(self):
		import tkinter as tk
		from tkinter import ttk, messagebox
		import sqlite3
		from datetime import datetime

		win = tk.Toplevel(self.root)
		win.title("📊 Reporte de Ventas por Fecha")
		win.geometry("850x650")
		win.config(bg="#1e1e1e")
		win.transient(self.root)
		win.grab_set()

		tk.Label(
			win,
			text="📊 Reporte de Ventas por Fecha",
			bg="#1e1e1e",
			fg="white",
			font=("Segoe UI", 16, "bold")
		).pack(pady=10)

		# --- Selección de rango de fechas ---
		frame_sel = tk.Frame(win, bg="#1e1e1e")
		frame_sel.pack(pady=10)

		tk.Label(frame_sel, text="Desde (YYYY-MM-DD):", bg="#1e1e1e", fg="white", font=("Segoe UI", 12)).grid(row=0, column=0, padx=5)
		tk.Label(frame_sel, text="Hasta (YYYY-MM-DD):", bg="#1e1e1e", fg="white", font=("Segoe UI", 12)).grid(row=0, column=2, padx=5)

		hoy = datetime.now().strftime("%Y-%m-%d")
		desde_var = tk.StringVar(value=hoy)
		hasta_var = tk.StringVar(value=hoy)

		entry_desde = tk.Entry(frame_sel, textvariable=desde_var, font=("Segoe UI", 12), width=12)
		entry_desde.grid(row=0, column=1, padx=5)

		entry_hasta = tk.Entry(frame_sel, textvariable=hasta_var, font=("Segoe UI", 12), width=12)
		entry_hasta.grid(row=0, column=3, padx=5)

		# === TABLA 1: TOTALES POR DÍA ===
		frame_tabla = tk.Frame(win, bg="#1e1e1e")
		frame_tabla.pack(fill="both", expand=True, padx=20)

		columnas = ("Fecha", "Total del Día")
		tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=12)
		tree.heading("Fecha", text="Fecha")
		tree.heading("Total del Día", text="Total del Día ($)")
		tree.column("Fecha", width=150, anchor="center")
		tree.column("Total del Día", width=200, anchor="center")
		tree.pack(fill="both", expand=True)

		# --- Tabla 2: Totales por tipo de pago ---
		tk.Label(win, text="Totales por Tipo de Pago:", bg="#1e1e1e", fg="white", font=("Segoe UI", 14, "bold")).pack(pady=10)
		tree_totales = ttk.Treeview(win, columns=("Tipo", "Total"), show="headings", height=5)
		tree_totales.heading("Tipo", text="Método de Pago")
		tree_totales.heading("Total", text="Total ($)")
		tree_totales.column("Tipo", width=200, anchor="center")
		tree_totales.column("Total", width=150, anchor="center")
		tree_totales.pack(pady=5)

		# --- Total general ---
		lbl_total = tk.Label(win, text="TOTAL: $0.00", bg="#1e1e1e", fg="#00ff7f", font=("Segoe UI", 20, "bold"))
		lbl_total.pack(pady=10)

		# === FUNCIÓN CONSULTAR ===
		def consultar():
			desde = desde_var.get().strip()
			hasta = hasta_var.get().strip()

			# Validar formato de fecha
			try:
				datetime.strptime(desde, "%Y-%m-%d")
				datetime.strptime(hasta, "%Y-%m-%d")
			except ValueError:
				messagebox.showwarning(
					"Formato incorrecto",
					"Usa el formato YYYY-MM-DD (ej. 2025-11-29)"
				)
				return

			try:
				with sqlite3.connect("pos.db") as conn:
					cur = conn.cursor()

					# ========= TOTALES POR DÍA (YA CON DESCUENTO) =========
					cur.execute("""
						SELECT date(v.fecha), SUM(vp.monto)
						FROM ventas v
						JOIN ventas_pagos vp ON v.id_venta = vp.id_venta
						WHERE date(v.fecha) BETWEEN ? AND ?
						GROUP BY date(v.fecha)
						ORDER BY date(v.fecha) ASC
					""", (desde, hasta))
					rows = cur.fetchall()

					# Limpiar tabla por día
					for item in tree.get_children():
						tree.delete(item)

					for fecha, total_dia in rows:
						tree.insert(
							"",
							"end",
							values=(fecha, f"{total_dia:,.2f}" if total_dia else "0.00")
						)

					# ========= TOTALES POR MÉTODO DE PAGO =========
					cur.execute("""
						SELECT vp.metodo, SUM(vp.monto)
						FROM ventas_pagos vp
						JOIN ventas v ON v.id_venta = vp.id_venta
						WHERE date(v.fecha) BETWEEN ? AND ?
						GROUP BY vp.metodo
						ORDER BY SUM(vp.monto) DESC
					""", (desde, hasta))
					totales = cur.fetchall()

					# Limpiar tabla métodos
					for item in tree_totales.get_children():
						tree_totales.delete(item)

					total_general = 0
					for metodo, total in totales:
						total_general += total if total else 0
						tree_totales.insert(
							"",
							"end",
							values=(metodo, f"{total:,.2f}" if total else "0.00")
						)

					# ========= TOTAL GENERAL REAL =========
					lbl_total.config(text=f"TOTAL: ${total_general:,.2f}")

			except Exception as e:
				messagebox.showerror("Error", str(e))

		# Botón consultar
		tk.Button(frame_sel, text="Consultar", bg="#4CAF50", fg="white", font=("Segoe UI", 11, "bold"), width=12, command=consultar).grid(row=0, column=4, padx=10)

		# Consultar automáticamente al abrir para mostrar hoy
		consultar()
				 
	def reporte_salarios(self):
		import tkinter as tk
		from tkinter import ttk, messagebox, filedialog
		import sqlite3
		import csv
		from datetime import datetime

		# ======= Ventana principal modal =======
		win = tk.Toplevel(self.root)
		win.title("💰 Reporte de Salarios")
		win.geometry("1000x700")
		win.grab_set()
		win.focus_force()
		win.config(bg="#2b2b2b")

		# ======= Frames principales =======
		frame_superior = tk.Frame(win, bg="#2b2b2b")
		frame_superior.pack(side="top", fill="x", padx=10, pady=5)

		frame_empleados = tk.Frame(win, bg="#1e1e1e")
		frame_empleados.pack(side="top", fill="both", expand=True, padx=10, pady=5)

		frame_salarios = tk.Frame(win, bg="#1e1e1e")
		frame_salarios.pack(side="top", fill="both", expand=True, padx=10, pady=5)

		frame_total_csv = tk.Frame(frame_salarios, bg="#1e1e1e")
		frame_total_csv.pack(side="right", fill="y", padx=5, pady=5)

		# ======= Función para refrescar empleados =======
		def refrescar_empleados():
			for i in tree_emp.get_children():
				tree_emp.delete(i)
			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()
			cur.execute("SELECT * FROM empleados")
			empleados = cur.fetchall()
			for emp in empleados:
				tree_emp.insert("", tk.END, values=emp)
			conn.close()

		# ======= Función para nuevo empleado =======
		def nuevo_empleado():
			win_emp = tk.Toplevel(win)
			win_emp.title("Nuevo Empleado")
			win_emp.geometry("400x600")
			win_emp.grab_set()
			win_emp.focus_force()
			win_emp.config(bg="#2b2b2b")

			labels = ["Nombre", "Apellido", "Teléfono", "Dirección", "Puesto", "Usuario", "Estado", "Salario"]
			entries = {}

			for i, text in enumerate(labels):
				tk.Label(win_emp, text=text, bg="#2b2b2b", fg="white").pack(pady=5)
				entry = tk.Entry(win_emp, bg="#3b3b3b", fg="white")
				entry.pack(pady=5, fill="x", padx=10)
				entries[text.lower()] = entry

			def guardar():
				try:
					salario_str = entries["salario"].get()
					try:
						salario = float(salario_str)
					except ValueError:
						messagebox.showerror("Error", "El salario debe ser un número válido", parent=win_emp)
						return

					conn = sqlite3.connect("pos.db")
					cur = conn.cursor()
					cur.execute("""
						INSERT INTO empleados(nombre, apellido, telefono, direccion, puesto, usuario, estado, salario, fecha_registro)
						VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
					""", (
						entries["nombre"].get() or "",
						entries["apellido"].get() or "",
						entries["teléfono"].get() or "",
						entries["dirección"].get() or "",
						entries["puesto"].get() or "",
						entries["usuario"].get() or "",
						entries["estado"].get() or "",
						salario
					))
					conn.commit()
					conn.close()
					messagebox.showinfo("Éxito", "Empleado agregado correctamente.", parent=win_emp)
					win_emp.destroy()
					refrescar_empleados()
				except Exception as e:
					messagebox.showerror("Error", str(e), parent=win_emp)

			tk.Button(win_emp, text="Guardar", command=guardar, bg="red", fg="white",
					font=("Segoe UI", 12, "bold")).pack(pady=20)

		# ======= Función para modificar empleado =======
		def modificar_empleado():
			selected = tree_emp.selection()
			if not selected:
				messagebox.showwarning("Seleccione", "Seleccione un empleado para modificar", parent=win)
				return
			item = tree_emp.item(selected)
			emp = item["values"]

			win_emp = tk.Toplevel(win)
			win_emp.title("Modificar Empleado")
			win_emp.geometry("400x600")
			win_emp.grab_set()
			win_emp.focus_force()
			win_emp.config(bg="#2b2b2b")

			labels = ["Nombre", "Apellido", "Teléfono", "Dirección", "Puesto", "Usuario", "Estado", "Salario"]
			entries = {}

			for i, text in enumerate(labels):
				tk.Label(win_emp, text=text, bg="#2b2b2b", fg="white").pack(pady=5)
				entry = tk.Entry(win_emp, bg="#3b3b3b", fg="white")
				if text.lower() == "salario":
					entry.insert(0, "" if emp[10] is None else str(emp[10]))
				else:
					entry.insert(0, "" if emp[i+1] is None else str(emp[i+1]))
				entry.pack(pady=5, fill="x", padx=10)
				entries[text.lower()] = entry

			def guardar_mod():
				try:
					salario_str = entries["salario"].get()
					try:
						salario = float(salario_str)
					except ValueError:
						messagebox.showerror("Error", "El salario debe ser un número válido", parent=win_emp)
						return

					conn = sqlite3.connect("pos.db")
					cur = conn.cursor()
					cur.execute("""
						UPDATE empleados
						SET nombre=?, apellido=?, telefono=?, direccion=?, puesto=?, usuario=?, estado=?, salario=?
						WHERE id=?
					""", (
						entries["nombre"].get() or "",
						entries["apellido"].get() or "",
						entries["teléfono"].get() or "",
						entries["dirección"].get() or "",
						entries["puesto"].get() or "",
						entries["usuario"].get() or "",
						entries["estado"].get() or "",
						salario,
						emp[0]
					))
					conn.commit()
					conn.close()
					messagebox.showinfo("Éxito", "Empleado modificado correctamente.", parent=win_emp)
					win_emp.destroy()
					refrescar_empleados()
				except Exception as e:
					messagebox.showerror("Error", str(e), parent=win_emp)

			tk.Button(win_emp, text="Guardar cambios", command=guardar_mod, bg="red", fg="white",
					font=("Segoe UI", 12, "bold")).pack(pady=20)

		# ======= Botones arriba =======
		tk.Button(frame_superior, text="Nuevo Empleado", command=nuevo_empleado, bg="#444444", fg="white").pack(side="left", padx=5)
		tk.Button(frame_superior, text="Modificar Empleado", command=modificar_empleado, bg="#444444", fg="white").pack(side="left", padx=5)

		# ======= Tabla empleados arriba =======
		tree_emp = ttk.Treeview(frame_empleados, columns=("ID","Nombre","Apellido","Teléfono","Dirección","Puesto","Usuario","Estado","Fecha Registro","Fecha Baja","Salario"), show="headings")
		tree_emp.pack(fill="both", expand=True)

		scroll_y_emp = ttk.Scrollbar(frame_empleados, orient="vertical", command=tree_emp.yview)
		scroll_y_emp.pack(side="right", fill="y")
		tree_emp.configure(yscrollcommand=scroll_y_emp.set)

		scroll_x_emp = ttk.Scrollbar(frame_empleados, orient="horizontal", command=tree_emp.xview)
		scroll_x_emp.pack(side="bottom", fill="x")
		tree_emp.configure(xscrollcommand=scroll_x_emp.set)

		for col in tree_emp["columns"]:
			tree_emp.heading(col, text=col)
			tree_emp.column(col, width=120)

		# ======= Tabla salarios abajo =======
		tree_sal = ttk.Treeview(frame_salarios, columns=("ID Salario","Empleado","Fecha","Monto"), show="headings")
		tree_sal.pack(side="left", fill="both", expand=True)

		scroll_y_sal = ttk.Scrollbar(frame_salarios, orient="vertical", command=tree_sal.yview)
		scroll_y_sal.pack(side="left", fill="y")
		tree_sal.configure(yscrollcommand=scroll_y_sal.set)

		scroll_x_sal = ttk.Scrollbar(frame_salarios, orient="horizontal", command=tree_sal.xview)
		scroll_x_sal.pack(side="bottom", fill="x")
		tree_sal.configure(xscrollcommand=scroll_x_sal.set)

		for col in tree_sal["columns"]:
			tree_sal.heading(col, text=col)
			tree_sal.column(col, width=150)

		# ======= Total a la derecha =======
		lbl_total = tk.Label(frame_total_csv, text="Total: $0.00", bg="#1e1e1e", fg="green", font=("Segoe UI", 14, "bold"))
		lbl_total.pack(pady=10)

		# ======= Botón Exportar CSV debajo =======
		def export_csv():
			file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
			if not file_path:
				return
			with open(file_path, mode="w", newline="", encoding="utf-8") as f:
				writer = csv.writer(f)
				# Encabezados
				writer.writerow(["ID Salario","Empleado","Fecha","Monto"])
				for row in tree_sal.get_children():
					writer.writerow(tree_sal.item(row)["values"])
			messagebox.showinfo("Exportado", f"Archivo exportado correctamente a:\n{file_path}", parent=win)

		tk.Button(frame_total_csv, text="Exportar CSV", command=export_csv, bg="#444444", fg="white").pack(pady=5)

		# ======= Cargar datos =======
		conn = sqlite3.connect("pos.db")
		cur = conn.cursor()

		# Empleados
		cur.execute("SELECT * FROM empleados")
		empleados = cur.fetchall()
		for emp in empleados:
			tree_emp.insert("", tk.END, values=emp)

		# Salarios del mes
		mes_actual = datetime.now().strftime("%Y-%m")
		cur.execute("""
			SELECT s.id_salario, e.nombre || ' ' || e.apellido, s.fecha, s.monto
			FROM salarios s
			JOIN empleados e ON s.empleado_id = e.id
			WHERE strftime('%Y-%m', s.fecha) = ?
		""", (mes_actual,))
		salarios = cur.fetchall()

		total = 0
		for sal in salarios:
			monto_formateado = f"${sal[3]:,.2f}"
			tree_sal.insert("", tk.END, values=(sal[0], sal[1], sal[2], monto_formateado))
			total += sal[3]

		lbl_total.config(text=f"Total: ${total:,.2f}")

		conn.close()

	def reporte_productos(self):
		import sqlite3
		from tkinter import ttk
		import tkinter as tk
		from tkinter import filedialog, messagebox
		from datetime import datetime, timedelta
		import csv

		ventana = tk.Toplevel(self.root)
		ventana.title("📦 Reporte de Productos Más Vendidos")
		ventana.geometry("1100x630")
		ventana.config(bg="#1e1e1e")

		# === Ventana modal ===
		ventana.transient(self.root)
		ventana.grab_set()
		ventana.focus_force()

		tk.Label(
			ventana,
			text="📦 Reporte de Productos Más Vendidos",
			bg="#1e1e1e", fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(pady=10)

		# ===================== CONTENEDOR PRINCIPAL =====================
		contenedor = tk.Frame(ventana, bg="#1e1e1e")
		contenedor.pack(fill="both", expand=True, padx=10, pady=10)

		# ===================== IZQUIERDA: DEPARTAMENTOS (AHORA MÁS ANCHA) =====================
		left_frame = tk.Frame(contenedor, bg="#2b2b2b", width=700)
		left_frame.pack(side="left", fill="both", expand=True, padx=10)

		tk.Label(
			left_frame,
			text="🏬 Top 10 por Departamento",
			bg="#2b2b2b",
			fg="white",
			font=("Segoe UI", 13, "bold")
		).pack(pady=10)

		tk.Label(
			left_frame,
			text="Seleccionar Departamento:",
			bg="#2b2b2b",
			fg="white",
			font=("Segoe UI", 10, "bold")
		).pack()

		# Obtener departamentos
		conn = sqlite3.connect("pos.db")
		cur = conn.cursor()
		cur.execute("SELECT DISTINCT departamento FROM productos WHERE departamento IS NOT NULL")
		departamentos = [d[0] for d in cur.fetchall()]
		conn.close()

		depto_var = tk.StringVar()
		combo_deptos = ttk.Combobox(left_frame, textvariable=depto_var,
									values=departamentos, state="readonly")
		combo_deptos.pack(pady=(6, 6))

		# --- función buscar (debe estar definida antes del botón) ---
		# Fechas base
		hoy = datetime.now().strftime("%Y-%m-%d")
		semana = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
		mes = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

		# crear tablas de departamento primero (referencias usadas en la función)
		tabs_depto = ttk.Notebook(left_frame)
		# no lo empaquetamos aún — lo haremos después del botón para asegurar orden visual

		tab_d_hoy = tk.Frame(tabs_depto, bg="#2b2b2b")
		tab_d_semana = tk.Frame(tabs_depto, bg="#2b2b2b")
		tab_d_mes = tk.Frame(tabs_depto, bg="#2b2b2b")

		tabs_depto.add(tab_d_hoy, text="Hoy")
		tabs_depto.add(tab_d_semana, text="Semana")
		tabs_depto.add(tab_d_mes, text="Mes")

		def crear_tabla_depto(frame):
			tree = ttk.Treeview(
				frame,
				columns=("Producto", "Cantidad"),
				show="headings",
				height=12
			)
			tree.heading("Producto", text="Producto")
			tree.heading("Cantidad", text="Cantidad")
			# columna más ancha para departamento (tabla más grande)
			tree.column("Producto", width=360, anchor="w")
			tree.column("Cantidad", width=120, anchor="center")
			tree.pack(expand=True, fill="both", pady=6, padx=6)
			return tree

		tabla_depto_hoy = crear_tabla_depto(tab_d_hoy)
		tabla_depto_semana = crear_tabla_depto(tab_d_semana)
		tabla_depto_mes = crear_tabla_depto(tab_d_mes)

		# ahora sí colocamos el botón entre el combo y las tablas (medio)
		tk.Button(
			left_frame, text="🔍 Buscar", bg="#3498db", fg="white",
			font=("Segoe UI", 11, "bold"), width=20,
			command=lambda: buscar_departamento()
		).pack(pady=(4, 12))

		# empaquetar los tabs de departamento justo debajo del botón
		tabs_depto.pack(expand=True, fill="both", pady=(0, 6))

		# función buscar_departamento (usa las tablas creadas arriba)
		def buscar_departamento():
			depto = depto_var.get()
			if not depto:
				messagebox.showwarning("Aviso", "Seleccione un departamento.")
				return

			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()

			fechas = {
				"hoy": (hoy, hoy),
				"semana": (semana, hoy),
				"mes": (mes, hoy)
			}

			tablas = {
				"hoy": tabla_depto_hoy,
				"semana": tabla_depto_semana,
				"mes": tabla_depto_mes
			}

			# limpiar listas previas
			for periodo in tablas:
				for item in tablas[periodo].get_children():
					tablas[periodo].delete(item)

			datos_exportar_local = []

			for periodo, (f1, f2) in fechas.items():

				query = """
				SELECT p.nombre_producto, SUM(d.cantidad) AS total_vendido
				FROM ventas_detalle d
				JOIN productos p ON p.id_producto = d.id_producto
				JOIN ventas v ON v.id_venta = d.id_venta
				WHERE p.departamento = ?
				AND date(v.fecha) BETWEEN date(?) AND date(?)
				GROUP BY d.id_producto
				ORDER BY total_vendido DESC
				LIMIT 10;
				"""

				cur.execute(query, (depto, f1, f2))
				datos = cur.fetchall()

				tabla = tablas[periodo]

				if datos:
					for row in datos:
						tabla.insert("", "end", values=row)
						datos_exportar_local.append((periodo, ) + row)
				else:
					tabla.insert("", "end", values=("Sin ventas", 0))

			conn.close()

			# actualizar el dict global de exportación (manteniendo otros periodos)
			nonlocal_datos = datos_exportar  # usar closure var definida abajo
			nonlocal_datos["departamento"] = datos_exportar_local

		# ====================== DERECHA: TABLA GENERAL (AHORA MÁS COMPACTA) ======================
		right_frame = tk.Frame(contenedor, bg="#1e1e1e", width=380)
		right_frame.pack(side="right", fill="y", padx=10)

		tabs = ttk.Notebook(right_frame)
		tabs.pack(expand=True, fill="both")

		tab_hoy = tk.Frame(tabs, bg="#1e1e1e")
		tab_semana = tk.Frame(tabs, bg="#1e1e1e")
		tab_mes = tk.Frame(tabs, bg="#1e1e1e")

		tabs.add(tab_hoy, text="Hoy")
		tabs.add(tab_semana, text="Semana")
		tabs.add(tab_mes, text="Mes")

		def crear_tabla_compacta(frame):
			columnas = ("Producto", "Cantidad")
			tree = ttk.Treeview(frame, columns=columnas, show="headings", height=10)
			for col in columnas:
				tree.heading(col, text=col)
				# columnas más estrechas (tabla más pequeña)
				tree.column(col, anchor="center", width=220 if col == "Producto" else 80)
			tree.pack(expand=True, fill="both", pady=6, padx=6)
			return tree

		tabla_hoy = crear_tabla_compacta(tab_hoy)
		tabla_semana = crear_tabla_compacta(tab_semana)
		tabla_mes = crear_tabla_compacta(tab_mes)

		# Consulta general (similar a antes pero llenando tablas compactas)
		def cargar_top_general(fecha_inicio, fecha_fin, tabla):
			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()
			query = """
			SELECT p.nombre_producto, SUM(d.cantidad) AS total_vendido
			FROM ventas_detalle d
			JOIN productos p ON p.id_producto = d.id_producto
			JOIN ventas v ON v.id_venta = d.id_venta
			WHERE date(v.fecha) BETWEEN date(?) AND date(?)
			GROUP BY d.id_producto
			ORDER BY total_vendido DESC
			LIMIT 10;
			"""
			cur.execute(query, (fecha_inicio, fecha_fin))
			datos = cur.fetchall()
			conn.close()

			for i in tabla.get_children():
				tabla.delete(i)

			if datos:
				for row in datos:
					tabla.insert("", "end", values=row)
			else:
				tabla.insert("", "end", values=("Sin ventas", 0))

		# Cargar datos iniciales (fechas calculadas arriba)
		cargar_top_general(hoy, hoy, tabla_hoy)
		cargar_top_general(semana, hoy, tabla_semana)
		cargar_top_general(mes, hoy, tabla_mes)

		# ===================== BOTONES FINALES =====================
		datos_exportar = {"hoy": [], "semana": [], "mes": [], "departamento": []}

		botones = tk.Frame(ventana, bg="#1e1e1e")
		botones.pack(pady=10)

		tk.Button(
			botones, text="💾 Exportar CSV",
			bg="#f39c12", fg="white",
			font=("Segoe UI", 11, "bold"),
			width=20,
			command=lambda: exportar_csv()
		).grid(row=0, column=0, padx=10)

		tk.Button(
			botones, text="❌ Cerrar",
			bg="#e74c3c", fg="white",
			font=("Segoe UI", 11, "bold"),
			width=15,
			command=ventana.destroy
		).grid(row=0, column=1, padx=10)

		# función exportar CSV (usa datos_exportar)
		def exportar_csv():
			archivo = filedialog.asksaveasfilename(
				defaultextension=".csv",
				filetypes=[("Archivo CSV", "*.csv")],
				title="Guardar Reporte"
			)
			if not archivo:
				return
			try:
				with open(archivo, "w", newline="", encoding="utf-8") as f:
					writer = csv.writer(f)
					writer.writerow(["Periodo/Depto", "Producto", "Cantidad"])
					for row in datos_exportar.get("hoy", []):
						writer.writerow(["Hoy"] + list(row))
					for row in datos_exportar.get("semana", []):
						writer.writerow(["Semana"] + list(row))
					for row in datos_exportar.get("mes", []):
						writer.writerow(["Mes"] + list(row))
					for row in datos_exportar.get("departamento", []):
						# departamento entries are tuples (periodo, producto, cantidad)
						writer.writerow([row[0], row[1], row[2]])
				messagebox.showinfo("Éxito", "Reporte exportado correctamente.")
			except Exception as e:
				messagebox.showerror("Error", str(e))

	def reporte_productos_por_departamento(self):
		import sqlite3
		from tkinter import ttk
		import tkinter as tk
		from tkinter import messagebox

		# --- Ventana de selección ---
		win = tk.Toplevel(self.root)
		win.title("🔎 Top 10 por Departamento")
		win.geometry("420x260")
		win.config(bg="#1e1e1e")
		win.transient(self.root)
		win.grab_set()
		win.focus_force()

		tk.Label(
			win, text="🔎 Reporte por Departamento",
			bg="#1e1e1e", fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(pady=10)

		frame = tk.Frame(win, bg="#1e1e1e")
		frame.pack(pady=10)

		# Obtener departamentos desde DB
		conn = sqlite3.connect("pos.db")
		cur = conn.cursor()
		cur.execute("SELECT DISTINCT departamento FROM productos ORDER BY departamento ASC")
		departamentos = [d[0] for d in cur.fetchall()]
		conn.close()

		tk.Label(frame, text="Departamento:", bg="#1e1e1e", fg="white",
				font=("Segoe UI", 11)).grid(row=0, column=0, padx=5)

		combo = ttk.Combobox(frame, values=departamentos, width=28, state="readonly")
		combo.grid(row=0, column=1, padx=5, pady=5)

		# === Función para reporte por 1 departamento ===
		def ver_un_departamento():
			depto = combo.get().strip()
			if not depto:
				messagebox.showwarning("Atención", "Seleccione un departamento.")
				return

			win.destroy()
			self._mostrar_reporte_departamento(depto)

		# === Función para reporte de TODOS ===
		def ver_todos_departamentos():
			win.destroy()
			self._mostrar_reporte_departamento(None)   # None = todos

		# --- Botones ---
		tk.Button(
			win, text="🔍 Ver Solo Este", bg="#27ae60", fg="white",
			font=("Segoe UI", 11, "bold"), width=18,
			command=ver_un_departamento
		).pack(pady=5)

		tk.Button(
			win, text="📦 Ver Todos", bg="#2980b9", fg="white",
			font=("Segoe UI", 11, "bold"), width=18,
			command=ver_todos_departamentos
		).pack(pady=5)

		tk.Button(
			win, text="❌ Cancelar", bg="#e74c3c", fg="white",
			font=("Segoe UI", 11, "bold"), width=14,
			command=win.destroy
		).pack(pady=10)

	def _mostrar_reporte_departamento(self, departamento):
		import sqlite3
		import tkinter as tk
		from tkinter import ttk

		ventana = tk.Toplevel(self.root)
		ventana.title("📦 Top 10 por Departamento")
		ventana.geometry("950x600")
		ventana.config(bg="#1e1e1e")

		ventana.transient(self.root)
		ventana.grab_set()
		ventana.focus_force()

		# Layout: tabla izquierda / botones derecha
		contenedor = tk.Frame(ventana, bg="#1e1e1e")
		contenedor.pack(fill="both", expand=True, padx=10, pady=10)

		frame_tabla = tk.Frame(contenedor, bg="#1e1e1e")
		frame_tabla.pack(side="left", fill="both", expand=True)

		frame_botones = tk.Frame(contenedor, bg="#1e1e1e")
		frame_botones.pack(side="right", fill="y", padx=10)

		# Título
		titulo = "📦 Top 10 de Todos los Departamentos" if departamento is None else f"📦 Top 10 en {departamento}"
		tk.Label(frame_tabla, text=titulo, bg="#1e1e1e", fg="white",
				font=("Segoe UI", 14, "bold")).pack(pady=10)

		# Tabla
		columnas = ("Producto", "Departamento", "Cantidad Vendida")
		tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=18)

		for col in columnas:
			tree.heading(col, text=col)
			ancho = 290 if col == "Producto" else 150
			tree.column(col, width=ancho, anchor="center")

		tree.pack(fill="both", expand=True, pady=10)

		# --- CONSULTA ---
		conn = sqlite3.connect("pos.db")
		cur = conn.cursor()

		query = """
			SELECT p.nombre_producto, p.departamento, SUM(d.cantidad) AS total_vendido
			FROM ventas_detalle d
			JOIN productos p ON p.id_producto = d.id_producto
			JOIN ventas v ON v.id_venta = d.id_venta
		"""

		params = []

		if departamento is not None:
			query += " WHERE p.departamento = ? "
			params.append(departamento)

		query += """
			GROUP BY p.id_producto
			ORDER BY total_vendido DESC
			LIMIT 10;
		"""

		cur.execute(query, params)
		datos = cur.fetchall()
		conn.close()

		# Insertar datos
		if datos:
			for row in datos:
				tree.insert("", "end", values=row)
		else:
			tree.insert("", "end", values=("Sin ventas", "", 0))

		# --- Botones a la derecha ---
		tk.Button(
			frame_botones, text="🔁 Volver a Filtros", bg="#2980b9", fg="white",
			font=("Segoe UI", 11, "bold"), width=20,
			command=lambda: (ventana.destroy(), self.reporte_productos_por_departamento())
		).pack(pady=10)

		tk.Button(
			frame_botones, text="❌ Cerrar", bg="#e74c3c", fg="white",
			font=("Segoe UI", 11, "bold"), width=20,
			command=ventana.destroy
		).pack(pady=10)

	def reporte_mayoristas(self):
		import sqlite3
		import tkinter as tk
		from tkinter import ttk, filedialog, messagebox
		from datetime import datetime, timedelta
		import csv

		ventana = tk.Toplevel(self.root)
		ventana.title("🛒 Reporte de Mayoristas")
		ventana.geometry("750x650")
		ventana.config(bg="#1e1e1e")
		ventana.transient(self.root)
		ventana.grab_set()
		ventana.focus_force()

		tk.Label(
			ventana,
			text="🛒 Top Mayoristas que Más Compran",
			bg="#1e1e1e",
			fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(pady=10)

		# --------------------- TABS -----------------------
		tabs = ttk.Notebook(ventana)
		tabs.pack(expand=True, fill="both", padx=10, pady=10)

		tab_hoy = tk.Frame(tabs, bg="#1e1e1e")
		tab_semana = tk.Frame(tabs, bg="#1e1e1e")
		tab_mes = tk.Frame(tabs, bg="#1e1e1e")

		tabs.add(tab_hoy, text="Hoy")
		tabs.add(tab_semana, text="Semana")
		tabs.add(tab_mes, text="Mes")

		# -------- Crear tabla -------
		def crear_tabla(frame):
			columnas = ("Mayorista", "Total Comprado")
			tree = ttk.Treeview(frame, columns=columnas, show="headings", height=14)

			tree.heading("Mayorista", text="Mayorista")
			tree.heading("Total Comprado", text="Total (MXN)")

			tree.column("Mayorista", anchor="w", width=350)
			tree.column("Total Comprado", anchor="center", width=180)

			tree.pack(expand=True, fill="both", pady=10)
			return tree

		tabla_hoy = crear_tabla(tab_hoy)
		tabla_semana = crear_tabla(tab_semana)
		tabla_mes = crear_tabla(tab_mes)

		datos_exportar = {"hoy": [], "semana": [], "mes": []}

		# =========================
		#   SQL + TABLAS
		# =========================
		def cargar_top(fecha_inicio, fecha_fin, tabla, nombre_tabla):
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()

			query = """
			SELECT m.nombre, 
				ROUND(SUM(v.total), 4) AS total_gastado
			FROM ventas v
			JOIN mayoristas m ON m.id_mayorista = v.id_mayorista
			WHERE date(v.fecha) BETWEEN date(?) AND date(?)
			GROUP BY v.id_mayorista
			ORDER BY total_gastado DESC
			LIMIT 10;
			"""

			cur.execute(query, (fecha_inicio, fecha_fin))
			datos = cur.fetchall()
			conn.close()

			# Limpiar tabla
			for item in tabla.get_children():
				tabla.delete(item)

			datos_exportar[nombre_tabla] = datos

			if datos:
				for row in datos:
					tabla.insert("", "end", values=(row[0], f"${row[1]:,.4f}"))
			else:
				tabla.insert("", "end", values=("Sin registros", 0))

		# --- Fechas ---
		hoy = datetime.now().strftime("%Y-%m-%d")
		semana = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
		mes = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

		# Cargar datos iniciales
		cargar_top(hoy, hoy, tabla_hoy, "hoy")
		cargar_top(semana, hoy, tabla_semana, "semana")
		cargar_top(mes, hoy, tabla_mes, "mes")

		# --- Exportar CSV ---
		def exportar_csv():
			archivo = filedialog.asksaveasfilename(
				defaultextension=".csv",
				filetypes=[("Archivo CSV", "*.csv")],
				title="Guardar Reporte"
			)
			if not archivo:
				return

			try:
				with open(archivo, "w", newline="", encoding="utf-8") as f:
					writer = csv.writer(f)
					writer.writerow(["Periodo", "Mayorista", "Total Comprado"])

					for row in datos_exportar["hoy"]:
						writer.writerow(["Hoy"] + list(row))
					for row in datos_exportar["semana"]:
						writer.writerow(["Semana"] + list(row))
					for row in datos_exportar["mes"]:
						writer.writerow(["Mes"] + list(row))

				messagebox.showinfo("Éxito", "Reporte exportado correctamente.")
			except Exception as e:
				messagebox.showerror("Error", str(e))

		tk.Button(
			ventana,
			text="💾 Exportar CSV",
			bg="#f39c12",
			fg="white",
			font=("Segoe UI", 11, "bold"),
			width=20,
			command=exportar_csv
		).pack(pady=5)

		tk.Button(
			ventana,
			text="❌ Cerrar",
			bg="#e74c3c",
			fg="white",
			font=("Segoe UI", 11, "bold"),
			width=15,
			command=ventana.destroy
		).pack(pady=5)

		import tkinter as tk
		from tkinter import ttk, filedialog, messagebox
		from datetime import datetime, timedelta
		import csv

		# ===== Ventana =====
		ventana = tk.Toplevel(self.root)
		ventana.title("🛒 Reporte de Mayoristas")
		ventana.geometry("750x650")
		ventana.config(bg="#1e1e1e")
		ventana.transient(self.root)
		ventana.grab_set()
		ventana.focus_force()

		# 🔑 cierre correcto
		def cerrar():
			try:
				ventana.grab_release()
			except:
				pass
			ventana.destroy()

		ventana.protocol("WM_DELETE_WINDOW", cerrar)

		tk.Label(
			ventana,
			text="🛒 Top Mayoristas que Más Compran",
			bg="#1e1e1e",
			fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(pady=10)

		# ================= TABS =================
		tabs = ttk.Notebook(ventana)
		tabs.pack(expand=True, fill="both", padx=10, pady=10)

		tab_hoy = tk.Frame(tabs, bg="#1e1e1e")
		tab_semana = tk.Frame(tabs, bg="#1e1e1e")
		tab_mes = tk.Frame(tabs, bg="#1e1e1e")

		tabs.add(tab_hoy, text="Hoy")
		tabs.add(tab_semana, text="Semana")
		tabs.add(tab_mes, text="Mes")

		# =============== TABLAS =================
		def crear_tabla(frame):
			tree = ttk.Treeview(
				frame,
				columns=("Mayorista", "Total Comprado"),
				show="headings",
				height=14
			)
			tree.heading("Mayorista", text="Mayorista")
			tree.heading("Total Comprado", text="Total (MXN)")
			tree.column("Mayorista", width=350, anchor="w")
			tree.column("Total Comprado", width=180, anchor="center")
			tree.pack(expand=True, fill="both", pady=10)
			return tree

		tabla_hoy = crear_tabla(tab_hoy)
		tabla_semana = crear_tabla(tab_semana)
		tabla_mes = crear_tabla(tab_mes)

		datos_exportar = {"hoy": [], "semana": [], "mes": []}

		# =============== CONSULTA =================
		def cargar_top(fecha_inicio, fecha_fin, tabla, key):
			for i in tabla.get_children():
				tabla.delete(i)

			with self.get_db_connection() as conn:
				cur = conn.cursor()
				cur.execute("""
					SELECT m.nombre,
						ROUND(SUM(v.total), 4)
					FROM ventas v
					JOIN mayoristas m ON m.id_mayorista = v.id_mayorista
					WHERE date(v.fecha) BETWEEN date(?) AND date(?)
					GROUP BY v.id_mayorista
					ORDER BY SUM(v.total) DESC
					LIMIT 10
				""", (fecha_inicio, fecha_fin))
				rows = cur.fetchall()

			datos_exportar[key] = rows

			if rows:
				for r in rows:
					tabla.insert("", "end", values=(r[0], f"${r[1]:,.4f}"))
			else:
				tabla.insert("", "end", values=("Sin registros", "0.00"))

		# =============== FECHAS =================
		hoy = datetime.now().strftime("%Y-%m-%d")
		semana = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
		mes = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

		cargar_top(hoy, hoy, tabla_hoy, "hoy")
		cargar_top(semana, hoy, tabla_semana, "semana")
		cargar_top(mes, hoy, tabla_mes, "mes")

		# =============== EXPORTAR =================
		def exportar_csv():
			archivo = filedialog.asksaveasfilename(
				defaultextension=".csv",
				filetypes=[("Archivo CSV", "*.csv")]
			)
			if not archivo:
				return

			with open(archivo, "w", newline="", encoding="utf-8") as f:
				writer = csv.writer(f)
				writer.writerow(["Periodo", "Mayorista", "Total Comprado"])
				for k in ("hoy", "semana", "mes"):
					for row in datos_exportar[k]:
						writer.writerow([k.capitalize(), row[0], row[1]])

			messagebox.showinfo("Éxito", "Reporte exportado correctamente.", parent=ventana)

		# =============== BOTONES =================
		tk.Button(
			ventana,
			text="💾 Exportar CSV",
			bg="#f39c12",
			fg="white",
			font=("Segoe UI", 11, "bold"),
			width=20,
			command=exportar_csv
		).pack(pady=5)

		tk.Button(
			ventana,
			text="❌ Cerrar",
			bg="#e74c3c",
			fg="white",
			font=("Segoe UI", 11, "bold"),
			width=15,
			command=cerrar
		).pack(pady=5)


	def abrir_productos(self):
		win = tk.Toplevel(self.root)
		win.title("Gestión de Productos")
		win.geometry("1200x650")
		win.config(bg="#2b2b2b")

		# === HACER LA VENTANA MODAL (SIEMPRE AL FRENTE) ===
		win.transient(self.root)   # La asocia a la principal
		win.grab_set()             # Bloquea interacción fuera de ella
		win.focus_force()          # La trae al frente

		# --- BARRA SUPERIOR ---
		top_bar = tk.Frame(win, bg="#1e1e1e")
		top_bar.pack(fill="x", pady=5)

		botones = [
			("➕ Agregar nuevo", self.agregar_producto_nuevo),
			("🔼 Aumentar stock", self.aumentar_stock),
			("🔽 Quitar stock", self.quitar_stock),
			("❌ Eliminar", self.eliminar_producto),
			("✏️ Modificar", self.modificar_producto),
			("🏷️ Departamento", self.gestionar_departamentos),
		]

		for txt, cmd in botones:
			tk.Button(
				top_bar, text=txt, command=cmd,
				bg="#0078D7", fg="white",
				font=("Segoe UI", 10, "bold"),
				relief="flat", height=2, width=15
			).pack(side="left", padx=5)

		
		# === BUSCADOR A LA DERECHA ===
		search_frame = tk.Frame(top_bar, bg="#1e1e1e")
		search_frame.pack(side="right", padx=10)

		self.entry_buscar_prod = tk.Entry(search_frame, width=25, 
									font=("Segoe UI", 10))
		self.entry_buscar_prod.pack(side="left", padx=5)

		btn_buscar = tk.Button(
			search_frame,
			text="🔍",
			command=self.buscar_producto_en_tabla,
			bg="#0078D7",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			relief="flat",
			width=4
		)
		btn_buscar.pack(side="left")

		# === LISTBOX DE SUGERENCIAS ===
		self.listbox_sugerencias = tk.Listbox(
			win,
			width=40,
			height=6,
			bg="#333",
			fg="white",
			font=("Segoe UI", 10)
		)
		self.listbox_sugerencias.place_forget()


		# --- EVENTOS DEL BUSCADOR ---
		def mostrar_sugerencias(event):
			texto = self.entry_buscar_prod.get()

			if len(texto) < 1:
				self.listbox_sugerencias.place_forget()
				return

			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("SELECT nombre_producto FROM productos WHERE nombre_producto LIKE ?", (f"{texto}%",))
			resultados = cur.fetchall()
			conn.close()

			self.listbox_sugerencias.delete(0, tk.END)

			if resultados:
				for r in resultados:
					self.listbox_sugerencias.insert(tk.END, r[0])

				x = self.entry_buscar_prod.winfo_rootx() - win.winfo_rootx()
				y = self.entry_buscar_prod.winfo_rooty() - win.winfo_rooty() + 28

				self.listbox_sugerencias.place(x=x, y=y)
			else:
				self.listbox_sugerencias.place_forget()

		def seleccionar_sugerencia(event):
			self.root.after(10, _seleccionar_sugerencia_real)


		def _seleccionar_sugerencia_real():
			indice = self.listbox_sugerencias.curselection()
			if not indice:
				return

			seleccion = self.listbox_sugerencias.get(indice[0])
			self.entry_buscar_prod.delete(0, tk.END)
			self.entry_buscar_prod.insert(0, seleccion)

			self.listbox_sugerencias.place_forget()
			self.buscar_producto_en_tabla()



		# === BINDINGS IMPORTANTES ===
		self.entry_buscar_prod.bind("<KeyRelease>", mostrar_sugerencias)
		self.listbox_sugerencias.bind("<ButtonRelease-1>", seleccionar_sugerencia)
		self.entry_buscar_prod.bind("<KeyRelease>", self.buscar_producto_en_tabla)


		# --- CONTENEDOR IZQUIERDO (75% del ancho) ---
		frame_izquierdo = tk.Frame(win, bg="#2b2b2b")
		frame_izquierdo.place(relx=0, rely=0.12, relwidth=0.75, relheight=0.88)

		# --- TABLA DE PRODUCTOS ---
		cols = ("ID", "Nombre", "Precio", "Stock", "Departamento")
		self.tree_prod = ttk.Treeview(frame_izquierdo, columns=cols, show="headings", height=20)

		for col in cols:
			self.tree_prod.heading(col, text=col)
			self.tree_prod.column(col, anchor="center", width=150)

		# 💥 UN SOLO Treeview. NO LO DUBLIQUES
		self.tree_prod.pack(fill="both", expand=True, padx=10, pady=10)

		# Tag para stock bajo
		self.tree_prod.tag_configure("stock_bajo", foreground="red", font=("Segoe UI", 10, "bold"))



		# Cargar los productos en la tabla
		self.cargar_tabla_productos()

	def buscar_producto_en_tabla(self, event=None):
		texto = self.entry_buscar_prod.get().strip().lower()

		if texto == "":
			self.cargar_tabla_productos()
			return

		for row in self.tree_prod.get_children():
			self.tree_prod.delete(row)

		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()
		cur.execute("""
			SELECT id_producto, nombre_producto, precio_venta, stock, departamento
			FROM productos
			WHERE LOWER(nombre_producto) LIKE ?
			ORDER BY nombre_producto ASC
		""", (f"%{texto}%",))

		for fila in cur.fetchall():
			stock = fila[3]

			if stock <= 3:
				self.tree_prod.insert("", "end", values=fila, tags=("stock_bajo",))
			else:
				self.tree_prod.insert("", "end", values=fila)

		conn.close()

	def cargar_tabla_productos(self):
		for row in self.tree_prod.get_children():
			self.tree_prod.delete(row)

		conn = sqlite3.connect(DB_PATH)
		conn.execute("PRAGMA foreign_keys = ON;")
		cur = conn.cursor()
		cur.execute("""
			SELECT id_producto, nombre_producto, precio_venta, stock, departamento
			FROM productos ORDER BY nombre_producto ASC
		""")

		for fila in cur.fetchall():
			stock = fila[3]

			if stock <= 3:
				self.tree_prod.insert("", "end", values=fila, tags=("stock_bajo",))
			else:
				self.tree_prod.insert("", "end", values=fila)

		conn.close()

	def agregar_producto_nuevo(self):
		nuevo = tk.Toplevel(self.root)
		nuevo.grab_set()     # Hace la ventana modal
		nuevo.focus_force()  # Fuerza que reciba el foco
		nuevo.title("Agregar producto nuevo")
		nuevo.geometry("400x380")
		nuevo.config(bg="#2b2b2b")

		# Variables
		nombre_var = tk.StringVar()
		precio_var = tk.DoubleVar()
		stock_var = tk.IntVar()
		dep_var = tk.StringVar()

		tk.Label(nuevo, text="Agregar nuevo producto", bg="#2b2b2b", fg="white",
				font=("Segoe UI", 13, "bold")).pack(pady=10)

		# --- Nombre ---
		tk.Label(nuevo, text="Nombre", bg="#2b2b2b", fg="white", font=("Segoe UI", 10)).pack(pady=3)
		tk.Entry(nuevo, textvariable=nombre_var, font=("Segoe UI", 11), width=25).pack()

		# --- Precio ---
		tk.Label(nuevo, text="Precio", bg="#2b2b2b", fg="white", font=("Segoe UI", 10)).pack(pady=3)
		tk.Entry(nuevo, textvariable=precio_var, font=("Segoe UI", 11), width=25).pack()

		# --- Stock ---
		tk.Label(nuevo, text="Stock", bg="#2b2b2b", fg="white", font=("Segoe UI", 10)).pack(pady=3)
		tk.Entry(nuevo, textvariable=stock_var, font=("Segoe UI", 11), width=25).pack()

		# --- Departamento con AUTOCOMPLETADO ---
		tk.Label(nuevo, text="Departamento", bg="#2b2b2b", fg="white",
				font=("Segoe UI", 10)).pack(pady=3)

		entry_dep = tk.Entry(nuevo, textvariable=dep_var, font=("Segoe UI", 11), width=25)
		entry_dep.pack()

		# === Listbox para sugerencias ===
		listbox = tk.Listbox(nuevo, width=25, height=5, font=("Segoe UI", 10))

		# Obtener departamentos existentes
		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()
		cur.execute("SELECT DISTINCT departamento FROM productos WHERE departamento != ''")
		departamentos = [d[0] for d in cur.fetchall()]
		conn.close()

		def actualizar_sugerencias(event=None):
			texto = dep_var.get().lower()

			if not texto:
				listbox.place_forget()
				return

			filtrados = [d for d in departamentos if texto in d.lower()]

			if not filtrados:
				listbox.place_forget()
				return

			listbox.delete(0, tk.END)
			for item in filtrados:
				listbox.insert(tk.END, item)

			# Posicionar
			listbox.place(
				x=entry_dep.winfo_x(),
				y=entry_dep.winfo_y() + entry_dep.winfo_height() + 2
			)

			listbox.lift()   # 🔥 IMPORTANTE: trae la lista al frente

		entry_dep.bind("<KeyRelease>", actualizar_sugerencias)

		def seleccionar_con_click(event):
			if listbox.curselection():
				seleccionado = listbox.get(listbox.curselection())
				dep_var.set(seleccionado)
				listbox.place_forget()

		listbox.bind("<<ListboxSelect>>", seleccionar_con_click)

		def seleccionar_con_enter(event):
			if listbox.size() > 0:
				seleccionado = listbox.get(0)
				dep_var.set(seleccionado)
				listbox.place_forget()
				return "break"

		entry_dep.bind("<Return>", seleccionar_con_enter)

		def seleccionar_con_enter(event):
			if listbox.size() > 0:
				seleccionado = listbox.get(0)
				dep_var.set(seleccionado)
				listbox.place_forget()
				return "break"

		entry_dep.bind("<Return>", seleccionar_con_enter)

		def guardar():
			nombre = nombre_var.get().strip()
			precio = precio_var.get()
			stock = stock_var.get()
			dep = dep_var.get().strip()

			# Validaciones
			if not nombre:
				messagebox.showwarning("Campos vacíos", "El nombre es obligatorio.")
				return
			if precio < 0:
				messagebox.showwarning("Valor inválido", "El precio no puede ser negativo.")
				return
			if stock < 0:
				messagebox.showwarning("Valor inválido", "El stock no puede ser negativo.")
				return

			try:
				conn = sqlite3.connect(DB_PATH)
				conn.execute("PRAGMA foreign_keys = ON;")
				cur = conn.cursor()

				# 🔥=== VALIDAR SI EL PRODUCTO YA EXISTE ===
				cur.execute("SELECT COUNT(*) FROM productos WHERE LOWER(nombre_producto) = LOWER(?)", (nombre,))
				existe = cur.fetchone()[0]

				if existe > 0:
					messagebox.showerror(
						"Producto duplicado",
						f"El producto '{nombre}' ya existe.\n\nCambia el nombre para poder guardarlo."
					)
					return  # NO guarda

				# === INSERTAR PRODUCTO NUEVO ===
				cur.execute("""
					INSERT INTO productos (nombre_producto, precio_venta, stock, departamento)
					VALUES (?, ?, ?, ?)
				""", (nombre, precio, stock, dep))

				conn.commit()

				# --- Mensaje de éxito que se cierra solo ---
				msg = tk.Toplevel(nuevo)
				msg.title("Éxito")
				msg.config(bg="#2b2b2b")
				msg.resizable(False, False)

				# Tamaño de la ventana
				ancho = 330
				alto = 120

				# Obtener tamaño de pantalla
				screen_w = msg.winfo_screenwidth()
				screen_h = msg.winfo_screenheight()

				# Calcular posición centrada
				x = int((screen_w / 2) - (ancho / 2))
				y = int((screen_h / 2) - (alto / 2))

				msg.geometry(f"{ancho}x{alto}+{x}+{y}")

				tk.Label(
					msg,
					text=f"Producto '{nombre}' agregado correctamente.",
					bg="#2b2b2b",
					fg="white",
					font=("Segoe UI", 10)
				).pack(pady=20)

				# Auto cerrar en 2 segundos
				msg.after(2000, msg.destroy)
				msg.after(2000, lambda: nuevo.destroy())
				msg.after(2000, self.cargar_tabla_productos)


			except Exception as e:
				messagebox.showerror("Error al guardar", str(e))

			finally:
				conn.close()

		# --- BOTÓN GUARDAR ---
		btn_guardar = tk.Button(nuevo, text="Guardar",
			command=guardar, bg="#4CAF50", fg="white", font=("Segoe UI", 11, "bold"),
			relief="flat", width=15, cursor="hand2")
		btn_guardar.pack(pady=15)

	def aumentar_stock(self):
		item = self.tree_prod.selection()
		if not item:
			messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto de la tabla.")
			return

		idp = self.tree_prod.item(item)["values"][0]
		cantidad = simpledialog.askinteger("Aumentar stock", "Cantidad a agregar:")
		if cantidad:
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("UPDATE productos SET stock = stock + ? WHERE id_producto = ?", (cantidad, idp))
			conn.commit()
			conn.close()
			self.cargar_tabla_productos()

	def quitar_stock(self):
		item = self.tree_prod.selection()
		if not item:
			messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto.")
			return

		idp = self.tree_prod.item(item)["values"][0]
		cantidad = simpledialog.askinteger("Quitar stock", "Cantidad a reducir:")
		if cantidad:
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("UPDATE productos SET stock = stock - ? WHERE id_producto = ?", (cantidad, idp))
			conn.commit()
			conn.close()
			self.cargar_tabla_productos()

	def eliminar_producto(self):
		item = self.tree_prod.selection()
		if not item:
			messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para eliminar.")
			return

		idp = self.tree_prod.item(item)["values"][0]
		if messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar este producto?"):
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("DELETE FROM productos WHERE id_producto = ?", (idp,))
			conn.commit()
			conn.close()
			self.cargar_tabla_productos()

	def modificar_producto(self):
		import tkinter as tk
		from tkinter import messagebox
		import sqlite3

		# Obtener selección
		selected = self.tree_prod.focus()
		if not selected:
			messagebox.showwarning("Atención", "Seleccione un producto para modificar.")
			return

		valores = self.tree_prod.item(selected, "values")
		prod_id, nombre, precio, stock, depto = valores

		# === Ventana para modificar ===
		win_edit = tk.Toplevel(self.root)
		win_edit.title("Modificar Producto")
		win_edit.geometry("400x450")
		win_edit.config(bg="#2b2b2b")
		win_edit.transient(self.root)
		win_edit.grab_set()

		# ===== CAMPOS =====
		# Nombre
		tk.Label(win_edit, text="Nombre:", fg="white", bg="#2b2b2b").pack(pady=5)
		entry_nombre = tk.Entry(win_edit, font=("Segoe UI", 11))
		entry_nombre.insert(0, nombre)
		entry_nombre.pack()

		# Precio
		tk.Label(win_edit, text="Precio:", fg="white", bg="#2b2b2b").pack(pady=5)
		entry_precio = tk.Entry(win_edit, font=("Segoe UI", 11))
		entry_precio.insert(0, precio)
		entry_precio.pack()

		# Stock
		tk.Label(win_edit, text="Stock:", fg="white", bg="#2b2b2b").pack(pady=5)
		entry_stock = tk.Entry(win_edit, font=("Segoe UI", 11))
		entry_stock.insert(0, stock)
		entry_stock.pack()

		# Departamento
		tk.Label(win_edit, text="Departamento:", fg="white", bg="#2b2b2b").pack(pady=5)
		dep_var = tk.StringVar()
		entry_depto = tk.Entry(win_edit, textvariable=dep_var, font=("Segoe UI", 11))
		dep_var.set(depto)
		entry_depto.pack()

		# === Listbox para sugerencias ===
		listbox = tk.Listbox(win_edit, width=25, height=5, font=("Segoe UI", 10))

		# Obtener departamentos existentes
		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()
		cur.execute("SELECT DISTINCT departamento FROM productos WHERE departamento != ''")
		departamentos = [d[0] for d in cur.fetchall()]
		conn.close()

		# -----------------------------------
		# ACTUALIZAR SUGERENCIAS
		# -----------------------------------
		def actualizar_sugerencias(event=None):
			texto = dep_var.get().lower()

			if not texto:
				listbox.place_forget()
				return

			filtrados = [d for d in departamentos if texto in d.lower()]

			if not filtrados:
				listbox.place_forget()
				return

			listbox.delete(0, tk.END)
			for item in filtrados:
				listbox.insert(tk.END, item)

			# Posicionar justo debajo del entry
			listbox.place(
				x=entry_depto.winfo_x(),
				y=entry_depto.winfo_y() + entry_depto.winfo_height() + 2
			)
			listbox.lift()

		entry_depto.bind("<KeyRelease>", actualizar_sugerencias)

		# Seleccionar con click
		def seleccionar_click(event):
			if listbox.curselection():
				seleccionado = listbox.get(listbox.curselection())
				dep_var.set(seleccionado)
				listbox.place_forget()

		listbox.bind("<<ListboxSelect>>", seleccionar_click)

		# Seleccionar con Enter
		def seleccionar_enter(event):
			if listbox.size() > 0:
				seleccionado = listbox.get(0)
				dep_var.set(seleccionado)
				listbox.place_forget()
				return "break"

		entry_depto.bind("<Return>", seleccionar_enter)

		# -----------------------------------
		# GUARDAR CAMBIOS
		# -----------------------------------
		def guardar():
			nuevo_nombre = entry_nombre.get().strip()
			nuevo_precio = entry_precio.get().strip()
			nuevo_stock = entry_stock.get().strip()
			nuevo_depto = dep_var.get().strip()

			# Validaciones
			try:
				nuevo_precio = float(nuevo_precio)
			except:
				messagebox.showerror("Error", "El precio debe ser número.")
				return

			try:
				nuevo_stock = int(nuevo_stock)
			except:
				messagebox.showerror("Error", "El stock debe ser número entero.")
				return

			# Guardar en BD
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("""
				UPDATE productos
				SET nombre_producto = ?, precio_venta = ?, stock = ?, departamento = ?
				WHERE id_producto = ?
			""", (nuevo_nombre, nuevo_precio, nuevo_stock, nuevo_depto, prod_id))
			conn.commit()
			conn.close()

			# Actualizar tabla
			self.cargar_tabla_productos()

			messagebox.showinfo("Éxito", "Producto modificado correctamente.")
			win_edit.destroy()

		# Botón GUARDAR
		tk.Button(
			win_edit, text="Guardar cambios",
			bg="#0078D7", fg="white",
			font=("Segoe UI", 10, "bold"),
			command=guardar
		).pack(pady=20)
	 
	def gestionar_departamentos(self):
		import tkinter as tk
		from tkinter import ttk, messagebox
		import sqlite3

		win = tk.Toplevel(self.root)
		# === Ajustar ventana al 75% ancho y pegada a la derecha ===
		win.update_idletasks()
		screen_width = win.winfo_screenwidth()
		screen_height = win.winfo_screenheight()

		ancho = int(screen_width * 0.45)
		alto = int(screen_height)

		# Posición: pegada a la derecha
		x = screen_width - ancho
		y = 0

		win.geometry(f"{ancho}x{alto}+{x}+{y}")

		win.title("🏬 Gestión de Departamentos")
		win.geometry("450x450")
		win.config(bg="#1e1e1e")
		win.transient(self.root)
		win.grab_set()

		tk.Label(
			win, text="🏬 Gestión de Departamentos",
			bg="#1e1e1e", fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(pady=10)

		# ==== FRAME TABLA ====
		frame_tabla = tk.Frame(win, bg="#1e1e1e")
		frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

		columnas = ("Departamento",)
		tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=10)

		tabla.heading("Departamento", text="Departamento")
		tabla.column("Departamento", anchor="center", width=350)

		tabla.pack(fill="both", expand=True)

		# Cargar departamentos
		def cargar_departamentos():
			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()
			cur.execute("SELECT DISTINCT departamento FROM productos WHERE departamento IS NOT NULL")
			datos = cur.fetchall()
			conn.close()

			tabla.delete(*tabla.get_children())
			for d in datos:
				tabla.insert("", "end", values=(d[0],))

		cargar_departamentos()

		# ==== FRAME ACCIONES ====
		frame_botones = tk.Frame(win, bg="#1e1e1e")
		frame_botones.pack(pady=10)

		entry_var = tk.StringVar()

		tk.Entry(
			frame_botones, textvariable=entry_var,
			font=("Segoe UI", 11), width=25
		).grid(row=0, column=0, padx=5)

		# --- Función agregar ---
		def agregar():
			nombre = entry_var.get().strip()
			if not nombre:
				messagebox.showwarning("Aviso", "Introduce un nombre.")
				return

			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()

			# Insertamos creando un producto ficticio solo para almacenar el departamento
			cur.execute("INSERT INTO productos (nombre_producto, departamento, precio_venta, stock) VALUES (?, ?, 0, 0)",
						(f"DeptoTemp-{nombre}", nombre))
			conn.commit()
			conn.close()

			entry_var.set("")
			cargar_departamentos()
			messagebox.showinfo("Éxito", "Departamento agregado.")

		# --- Función editar ---
		def editar():
			sel = tabla.selection()
			if not sel:
				messagebox.showwarning("Aviso", "Seleccione un departamento.")
				return

			original = tabla.item(sel[0])["values"][0]
			nuevo = entry_var.get().strip()

			if not nuevo:
				messagebox.showwarning("Aviso", "Introduce el nuevo nombre.")
				return

			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()

			cur.execute("UPDATE productos SET departamento = ? WHERE departamento = ?", (nuevo, original))
			conn.commit()
			conn.close()

			entry_var.set("")
			cargar_departamentos()
			messagebox.showinfo("Éxito", "Departamento actualizado.")

		# --- Función eliminar ---
		def eliminar():
			sel = tabla.selection()
			if not sel:
				messagebox.showwarning("Aviso", "Seleccione un departamento.")
				return

			departamento = tabla.item(sel[0])["values"][0]

			if messagebox.askyesno("Confirmar", f"¿Eliminar '{departamento}' de todos los productos?"):
				conn = sqlite3.connect("pos.db")
				cur = conn.cursor()
				cur.execute("UPDATE productos SET departamento = NULL WHERE departamento = ?", (departamento,))
				conn.commit()
				conn.close()

				cargar_departamentos()
				messagebox.showinfo("Listo", "Departamento eliminado.")

		# ===== Botones =====
		btn_agregar = tk.Button(frame_botones, text="➕ Agregar", bg="#27ae60", fg="white",
								font=("Segoe UI", 10, "bold"), width=10, command=agregar)
		btn_agregar.grid(row=1, column=0, padx=5, pady=3)

		btn_editar = tk.Button(frame_botones, text="✏️ Editar", bg="#3498db", fg="white",
							font=("Segoe UI", 10, "bold"), width=10, command=editar)
		btn_editar.grid(row=1, column=1, padx=5, pady=3)

		btn_eliminar = tk.Button(frame_botones, text="🗑️ Eliminar", bg="#e74c3c", fg="white",
								font=("Segoe UI", 10, "bold"), width=10, command=eliminar)
		btn_eliminar.grid(row=1, column=2, padx=5, pady=3)

		# Hover si ya tienes la función
		try:
			hover(btn_agregar, "#27ae60", "#2ecc71")
			hover(btn_editar, "#3498db", "#2980b9")
			hover(btn_eliminar, "#e74c3c", "#c0392b")
		except:
			pass  # si hover no existe, evita errores

	# --- reoprte de ventas ---
	
	# --- clientes mayoristas---   
	def abrir_mayoristas(self):
		win = tk.Toplevel(self.root)
		win.title("Gestión de Mayoristas / Clientes")
		win.geometry("850x500")
		win.config(bg="#2b2b2b")

		# === HACER LA VENTANA MODAL (SIEMPRE AL FRENTE) ===
		win.transient(self.root)   # Asociada a la ventana principal
		win.grab_set()             # Bloquea interacción fuera de ella
		win.focus_force()          # Trae la ventana al frente

		# --- Barra superior ---
		top = tk.Frame(win, bg="#1e1e1e", height=50)
		top.pack(fill="x")

		tk.Button(
			top, text="➕ Nuevo", bg="#0078D7", fg="white",
			font=("Segoe UI", 10, "bold"),
			command=lambda: self.nuevo_mayorista(win)
		).pack(side="left", padx=10)

		tk.Button(
			top, text="✏️ Editar", bg="#4CAF50", fg="white",
			font=("Segoe UI", 10, "bold"),
			command=lambda: self.editar_mayorista(win)
		).pack(side="left", padx=10)

		tk.Button(
			top, text="❌ Eliminar", bg="#D32F2F", fg="white",
			font=("Segoe UI", 10, "bold"),
			command=self.eliminar_mayorista
		).pack(side="left", padx=10)

		# --- Tabla de mayoristas ---
		cols = ("ID", "Nombre", "Teléfono", "Empresa", "Dirección")
		self.tree_may = ttk.Treeview(win, columns=cols, show="headings", height=20)

		for col in cols:
			self.tree_may.heading(col, text=col)
			self.tree_may.column(col, width=150, anchor="center")

		self.tree_may.pack(fill="both", expand=True, padx=10, pady=10)

		# Cargar los registros
		self.cargar_mayoristas()

	def cargar_mayoristas(self):
		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()
		cur.execute("SELECT id_mayorista, nombre, telefono, empresa, direccion FROM mayoristas ORDER BY nombre ASC")
		filas = cur.fetchall()
		conn.close()

		for i in self.tree_may.get_children():
			self.tree_may.delete(i)

		for f in filas:
			self.tree_may.insert("", "end", values=f)

	def nuevo_mayorista(self, parent):
		nuevo = tk.Toplevel(parent)
		nuevo.title("Agregar Mayorista")
		nuevo.geometry("400x350")
		nuevo.config(bg="#2b2b2b")

		campos = {
			"Nombre": tk.StringVar(),
			"Teléfono": tk.StringVar(),
			"Empresa": tk.StringVar(),
			"Dirección": tk.StringVar()
		}

		for c, var in campos.items():
			tk.Label(nuevo, text=c, bg="#2b2b2b", fg="white", font=("Segoe UI", 10)).pack(pady=4)
			tk.Entry(nuevo, textvariable=var, font=("Segoe UI", 11), width=30).pack()

		def guardar():
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("""
				INSERT INTO mayoristas (nombre, telefono, empresa, direccion)
				VALUES (?, ?, ?, ?)
			""", (campos["Nombre"].get(), campos["Teléfono"].get(),
				campos["Empresa"].get(), campos["Dirección"].get()))
			conn.commit()
			conn.close()
			messagebox.showinfo("Éxito", "Mayorista agregado.")
			nuevo.destroy()
			self.cargar_mayoristas()

		tk.Button(nuevo, text="Guardar", bg="#4CAF50", fg="white",
				font=("Segoe UI", 11, "bold"), command=guardar).pack(pady=15)

	def editar_mayorista(self, parent):
		item = self.tree_may.selection()
		if not item:
			messagebox.showwarning("Selecciona un registro", "Selecciona un mayorista.")
			return

		datos = self.tree_may.item(item)["values"]
		id_m = datos[0]

		edit = tk.Toplevel(parent)
		edit.title("Editar Mayorista")
		edit.geometry("400x350")
		edit.config(bg="#2b2b2b")

		campos = {
			"Nombre": tk.StringVar(value=datos[1]),
			"Teléfono": tk.StringVar(value=datos[2]),
			"Empresa": tk.StringVar(value=datos[3]),
			"Dirección": tk.StringVar(value=datos[4])
		}

		for c, var in campos.items():
			tk.Label(edit, text=c, bg="#2b2b2b", fg="white").pack(pady=4)
			tk.Entry(edit, textvariable=var, font=("Segoe UI", 11), width=30).pack()

		def actualizar():
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("""
				UPDATE mayoristas
				SET nombre=?, telefono=?, empresa=?, direccion=?
				WHERE id_mayorista=?
			""", (campos["Nombre"].get(), campos["Teléfono"].get(),
				campos["Empresa"].get(), campos["Dirección"].get(), id_m))
			conn.commit()
			conn.close()
			messagebox.showinfo("Éxito", "Datos actualizados.")
			edit.destroy()
			self.cargar_mayoristas()

		tk.Button(edit, text="Actualizar", bg="#4CAF50", fg="white",
				font=("Segoe UI", 11, "bold"), command=actualizar).pack(pady=15)

	def eliminar_mayorista(self):
		item = self.tree_may.selection()
		if not item:
			messagebox.showwarning("Selecciona un registro", "Selecciona un mayorista.")
			return

		id_m = self.tree_may.item(item)["values"][0]
		if messagebox.askyesno("Confirmar", "¿Eliminar este mayorista?"):
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("DELETE FROM mayoristas WHERE id_mayorista = ?", (id_m,))
			conn.commit()
			conn.close()
			self.cargar_mayoristas()


    #---ventas ---
	def abrir_historial_ventas(self):
		import tkinter as tk
		from tkinter import ttk, messagebox
		import sqlite3
		from datetime import datetime

		# === VERIFICAR TKCALENDAR ===
		try:
			from tkcalendar import Calendar 
		except Exception:
			messagebox.showerror(
				"Error",
				"No se pudo cargar tkcalendar.\nInstala con:\n\npip install tkcalendar"
			)
			return

		# === VENTANA PRINCIPAL ===
		ventas_win = tk.Toplevel(self.root)
		ventas_win.title("🧾 Historial de Ventas")
		ventas_win.geometry("1150x650")
		ventas_win.configure(bg="#1e1e1e")

		# === HACERLA MODAL ===
		ventas_win.transient(self.root)
		ventas_win.grab_set()
		ventas_win.focus_force()

		# === CENTRAR LA VENTANA ===
		ventas_win.update_idletasks()
		w = 1150
		h = 650
		sw = ventas_win.winfo_screenwidth()
		sh = ventas_win.winfo_screenheight()
		x = (sw - w) // 2
		y = (sh - h) // 2
		ventas_win.geometry(f"{w}x{h}+{x}+{y}")


		# === FRAME PRINCIPAL ===
		main_frame = tk.Frame(ventas_win, bg="#1e1e1e")
		main_frame.pack(fill="both", expand=True, padx=10, pady=10)

		# === IZQUIERDA ===
		left_frame = tk.Frame(main_frame, bg="#1e1e1e", width=750)
		left_frame.pack(side="left", fill="y", padx=(0, 10))
		left_frame.pack_propagate(False)

		# === DERECHA ===
		right_frame = tk.Frame(main_frame, bg="#1e1e1e", width=380)
		right_frame.pack(side="right", fill="y")
		right_frame.pack_propagate(False)

		# ================= TABLA VENTAS =================
		tk.Label(
			left_frame,
			text="📋 Lista de Ventas",
			bg="#1e1e1e",
			fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(anchor="w", pady=(0, 5))

		columnas_ventas = ("id_venta", "fecha", "usuario", "mayorista", "total", "tipo_pago")
		tree_ventas = ttk.Treeview(left_frame, columns=columnas_ventas, show="headings", height=8)

		for col in columnas_ventas:
			tree_ventas.heading(col, text=col.upper())
			tree_ventas.column(col, anchor="center", width=100)
		tree_ventas.pack(fill="x", padx=5, pady=(0, 10))

		# ================= TABLA DETALLE =================
		tk.Label(
			left_frame,
			text="🧾 Ticket de la Venta Seleccionada",
			bg="#1e1e1e",
			fg="white",
			font=("Segoe UI", 13, "bold")
		).pack(anchor="w", pady=(0, 5))

		txt_ticket = tk.Text(
			left_frame,
			bg="white",
			fg="black",
			font=("Consolas", 10),
			relief="sunken",
			height=30,
			width=50   
		)
		txt_ticket.pack(expand=False, padx=5, pady=5)
		txt_ticket.insert("end", "Selecciona una venta para ver su ticket...\n")
		txt_ticket.config(state="disabled")


		# ================= BOTÓN CORTE DEL DÍA =================
		btn_corte = tk.Button(
			right_frame,
			text="📊 Corte del Día",
			bg="#2980b9",
			fg="white",
			font=("Segoe UI", 12, "bold")
		)
		btn_corte.pack(pady=(10, 5), padx=10, fill="x")

		# === BOTÓN REIMPRIMIR TICKET ===
		def reimprimir_ticket_seleccionado():
			seleccion = tree_ventas.selection()
			if not seleccion:
				messagebox.showwarning("Aviso", "Selecciona una venta primero.")
				return

			id_venta = tree_ventas.item(seleccion[0])["values"][0]

			try:
				# Obtener datos de la venta (ya correctos desde BD)
				datos_venta = self.obtener_datos_venta(id_venta)
				if not datos_venta:
					messagebox.showwarning("Aviso", "No se encontraron datos de la venta.")
					return

				# Generar e imprimir ticket EXACTO al original
				self.generar_ticket(datos_venta)
				self.abrir_cajon()  # opcional

			except Exception as e:
				messagebox.showerror("Error", f"No se pudo reimprimir el ticket:\n{e}")


		btn_reimprimir = tk.Button(
			right_frame,
			text="🖨️ Reimprimir Ticket",
			bg="#16a085",
			fg="white",
			font=("Segoe UI", 12, "bold"),
			command=reimprimir_ticket_seleccionado
		)
		btn_reimprimir.pack(pady=(0, 5), padx=10, fill="x")


		# === BOTÓN CALENDARIO ===
		fecha_seleccionada = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

		def seleccionar_fecha():
			cal_win = tk.Toplevel(ventas_win)
			cal_win.title("Seleccionar fecha")
			cal_win.geometry("300x300")

			cal_win.transient(ventas_win)
			cal_win.grab_set()
			cal_win.focus_force()

			cal = Calendar(cal_win, selectmode='day', date_pattern='yyyy-mm-dd')
			cal.pack(pady=20)

			def ok_fecha():
				fecha_seleccionada.set(cal.get_date())
				cal_win.destroy()
				corte_dia()

			tk.Button(
				cal_win,
				text="Aceptar",
				command=ok_fecha,
				bg="#27ae60",
				fg="white"
			).pack(pady=10)

		btn_calendario = tk.Button(
			right_frame,
			text="📅 Seleccionar Fecha",
			bg="#f39c12",
			fg="white",
			font=("Segoe UI", 12, "bold"),
			command=seleccionar_fecha
		)
		btn_calendario.pack(pady=(0, 5), padx=10, fill="x")

		# ================= TEXTO CORTE =================
		txt_corte = tk.Text(
			right_frame,
			bg="white",
			fg="black",
			font=("Consolas", 1),
			relief="sunken",
			height=30
		)
		txt_corte.pack(fill="both", expand=True, padx=10, pady=(5, 10))
		txt_corte.insert(tk.END, "📋 Corte del Día aparecerá aquí...\n")
		txt_corte.config(state="disabled")

		# ================= FUNCIONES INTERNAS =================
		def cargar_ventas():
			tree_ventas.delete(*tree_ventas.get_children())
			try:
				conn = sqlite3.connect("pos.db")
				cur = conn.cursor()
				cur.execute("""
					SELECT 
						v.id_venta, v.fecha, v.id_usuario,
						COALESCE(m.nombre, 'Mostrador') AS mayorista,
						v.total, v.tipo_pago
					FROM ventas v
					LEFT JOIN mayoristas m ON v.id_mayorista = m.id_mayorista
					ORDER BY v.fecha DESC
				""")
				for row in cur.fetchall():
					id_venta, fecha, usuario, mayorista, total, tipo_pago = row
					tree_ventas.insert("", tk.END, values=(
						id_venta, fecha, usuario, mayorista,
						f"${total:,.2f}", tipo_pago
					))
				conn.close()
			except Exception as e:
				messagebox.showerror("Error", f"No se pudieron cargar las ventas:\n{e}")

		def mostrar_detalle(event=None):
			if event:
				tree = event.widget
			else:
				tree = tree_ventas  # tu Treeview

			if not tree.selection():
				return

			id_venta = tree.item(tree.selection()[0])["values"][0]

			datos_venta = self.obtener_datos_venta(id_venta)
			if not datos_venta:
				return

			# =================== GENERAR TEXTO DEL TICKET REAL ===================
			texto_final = self.generar_ticket(datos_venta, imprimir=False)


			# =================== MOSTRAR EN EL TEXT WIDGET ===================
			txt_ticket.config(state="normal")
			txt_ticket.delete("1.0", "end")
			txt_ticket.insert("1.0", texto_final)
			txt_ticket.config(state="disabled")


		def corte_dia():
			import sqlite3
			from tkinter import messagebox

			fecha = fecha_seleccionada.get()
			if not fecha:
				messagebox.showwarning("Fecha requerida", "Selecciona una fecha para generar el corte.")
				return

			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()

			# ================== TOTAL VENTAS ==================
			cur.execute("SELECT SUM(total) FROM ventas WHERE date(fecha) = ?", (fecha,))
			total_ventas = cur.fetchone()[0] or 0.0

			# ================== TOTAL GASTOS ==================
			cur.execute("""
				SELECT categoria, SUM(monto)
				FROM gastos
				WHERE date(fecha) = ?
				GROUP BY categoria
			""", (fecha,))
			gastos_categoria = cur.fetchall()
			total_gastos = sum(g[1] for g in gastos_categoria) if gastos_categoria else 0.0

			# ================== TOTAL DEVOLUCIONES ==================
			cur.execute("""
				SELECT SUM(monto)
				FROM devoluciones
				WHERE date(fecha) = ?
			""", (fecha,))
			total_devoluciones = cur.fetchone()[0] or 0.0

			# ================== TOTAL SALARIOS ==================
			cur.execute("""
				SELECT SUM(monto)
				FROM salarios
				WHERE date(fecha) = ?
			""", (fecha,))
			total_salarios = cur.fetchone()[0] or 0.0

			# ================== VENTAS POR MAYORISTA ==================
			cur.execute("""
				SELECT COALESCE(m.nombre, 'Mostrador') AS nombre, SUM(v.total)
				FROM ventas v
				LEFT JOIN mayoristas m ON v.id_mayorista = m.id_mayorista
				WHERE date(v.fecha) = ?
				GROUP BY nombre
				ORDER BY nombre = 'Mostrador' DESC, SUM(v.total) DESC
			""", (fecha,))
			ventas_mayoristas = cur.fetchall()
			total_mayoristas = sum(t for n, t in ventas_mayoristas if n != "Mostrador")

			# ================== MÉTODOS DE PAGO ==================
			ventas_pago = {}

			cur.execute("SELECT id_venta FROM ventas WHERE date(fecha) = ?", (fecha,))
			ventas_ids = [r[0] for r in cur.fetchall()]

			for id_venta in ventas_ids:
				datos = self.obtener_datos_venta(id_venta)

				cambio = datos.get("cambio", 0.0)

				for metodo, monto in datos.get("pagos", []):
					metodo_normalizado = metodo.strip().lower()

					if metodo_normalizado == "efectivo":
						monto_real = monto - cambio
					else:
						monto_real = monto

					ventas_pago[metodo_normalizado] = (
						ventas_pago.get(metodo_normalizado, 0.0) + monto_real
					)

			efectivo = ventas_pago.get("efectivo", 0.0)
			tarjeta = ventas_pago.get("tarjeta", 0.0)

			# ================== TOTAL FINAL DEL DÍA (EFECTIVO AJUSTADO) ==================
			total_final_dia = (
				efectivo
				- total_gastos
				- total_devoluciones
				- total_salarios
			)

			# ================== FONDO Y CAJA FINAL ==================
			fondo_inicial = getattr(self, "fondo_caja", 0.0)

			caja_final = (
				fondo_inicial
				+ efectivo
				- total_gastos
				- total_devoluciones
				- total_salarios
			)

			# ================== LIMPIAR TXT ==================
			txt_corte.config(state="normal")
			txt_corte.delete("1.0", "end")

			# ================== COLORES ==================
			txt_corte.tag_config("titulo", foreground="#00aaff", font=("Consolas", 12, "bold"))
			txt_corte.tag_config("seccion", foreground="#0a5f2d", font=("Consolas", 11, "bold"))
			txt_corte.tag_config("naranja", foreground="#402B04", font=("Consolas", 11))
			txt_corte.tag_config("item", foreground="#000000", font=("Consolas", 11))
			txt_corte.tag_config("strong", foreground="#00aaff", font=("Consolas", 11, "bold"))

			# ================== ENCABEZADO ==================
			txt_corte.insert("end", f"📅 Corte del Día - {fecha}\n", "titulo")
			txt_corte.insert("end", "-" * 40 + "\n\n", "strong")

			# ================== RESUMEN ==================
			txt_corte.insert("end", "📘 Resumen del día\n", "seccion")
			txt_corte.insert("end", f"Fondo inicial: ${fondo_inicial:,.2f}\n", "naranja")
			txt_corte.insert("end", f"Total ventas: ${total_ventas:,.2f}\n", "naranja")
			txt_corte.insert("end", f"Total gastos: ${total_gastos:,.2f}\n", "naranja")
			txt_corte.insert("end", f"Total devoluciones: ${total_devoluciones:,.2f}\n", "naranja")
			txt_corte.insert("end", f"Total salarios: ${total_salarios:,.2f}\n\n", "naranja")

			# ================== VENTAS POR MAYORISTA ==================
			txt_corte.insert("end", "💰 Ventas por mayorista\n", "seccion")
			for nombre, total in ventas_mayoristas:
				txt_corte.insert("end", f" - {nombre}: ${total:,.2f}\n", "naranja")
			txt_corte.insert("end", f"\nTotal mayoristas: ${total_mayoristas:,.2f}\n\n", "naranja")

			# ================== MÉTODOS DE PAGO ==================
			txt_corte.insert("end", "🧾 Ventas por tipo de pago\n", "seccion")
			for metodo, total in ventas_pago.items():
				txt_corte.insert("end", f" - {metodo.capitalize()}: ${total:,.2f}\n", "naranja")

			txt_corte.insert("end", "\n")

			# ================== TOTAL FINAL ==================
			txt_corte.insert("end", "💵 Total final dia: ", "seccion")
			txt_corte.insert("end", f"${total_final_dia:,.2f}\n\n", "naranja")

			txt_corte.insert("end", "🏦 Caja final con fondo: ", "seccion")
			txt_corte.insert("end", f"${caja_final:,.2f}\n\n", "naranja")

			# ================== GASTOS DETALLADOS ==================
			if gastos_categoria:
				txt_corte.insert("end", "💸 Gastos por categoría\n", "seccion")
				for categoria, monto in gastos_categoria:
					txt_corte.insert("end", f" - {categoria}: ${monto:,.2f}\n", "naranja")

			txt_corte.config(state="disabled")
			conn.close()

		# ================= EVENTOS =================
		tree_ventas.bind("<<TreeviewSelect>>", mostrar_detalle)
		btn_corte.config(command=corte_dia)

		# Cargar ventas al abrir la ventana
		cargar_ventas()

		# === BINDINGS ===
		tree_ventas.bind("<<TreeviewSelect>>", mostrar_detalle)
		btn_corte.config(command=corte_dia)

		# === CARGAR AL ABRIR ===
		cargar_ventas()
	

	def pedir_fondo(self):
		fondo_win = tk.Toplevel(self.root)
		fondo_win.title("Fondo de Caja")
		fondo_win.configure(bg="#222")
		fondo_win.resizable(False, False)
		fondo_win.transient(self.root)
		fondo_win.grab_set()

		# Centrar ventana
		w, h = 380, 200
		sw = fondo_win.winfo_screenwidth()
		sh = fondo_win.winfo_screenheight()
		x = (sw - w) // 2
		y = (sh - h) // 3
		fondo_win.geometry(f"{w}x{h}+{x}+{y}")

		tk.Label(fondo_win, text="Ingrese fondo inicial:", bg="#222", fg="white",
				font=("Segoe UI", 13, "bold")).pack(pady=(25,5))

		entry_frame = tk.Frame(fondo_win, bg="#222")
		entry_frame.pack()
		tk.Label(entry_frame, text="$", bg="#222", fg="white",
				font=("Segoe UI", 14, "bold")).pack(side="left", padx=5)

		entry_fondo = tk.Entry(entry_frame, font=("Segoe UI", 14), width=10, justify="center")
		entry_fondo.pack(side="left")
		entry_fondo.focus()

		def guardar_fondo(event=None):  # <-- permite recibir evento de Enter
			try:
				valor = entry_fondo.get().replace(",", "").strip()
				self.fondo_caja = float(valor)  # queda disponible hasta cerrar sesión
				fondo_win.destroy()
			except:
				messagebox.showerror("Error", "Ingrese un monto válido (solo números).")

		tk.Button(fondo_win, text="Guardar", command=guardar_fondo, bg="#27ae60",
				fg="white", font=("Segoe UI", 12, "bold"), width=12).pack(pady=20)

		# Asociar tecla Enter al guardar
		fondo_win.bind("<Return>", guardar_fondo)

		self.root.wait_window(fondo_win)

	# --- FUNCION CERRAR SESIÓN Y RESPALDO ---
	def cerrar_sesion(self):
		respuesta = messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar la sesión y respaldar los datos?")
		if respuesta:
			try:
				# Crear carpeta de respaldo si no existe
				respaldo_folder = "respaldo_pos"
				import os
				if not os.path.exists(respaldo_folder):
					os.makedirs(respaldo_folder)

				# Copiar la base de datos con nombre de fecha y hora
				now = datetime.now().strftime("%Y%m%d_%H%M%S")
				shutil.copy("pos.db", f"{respaldo_folder}/pos_backup_{now}.db")

				messagebox.showinfo("Respaldo Realizado", f"Respaldo guardado en {respaldo_folder}")
			except Exception as e:
				messagebox.showerror("Error", f"No se pudo hacer el respaldo:\n{e}")

			# Reiniciar valores de sesión
			self.fondo_caja = 0

			# Opcional: cerrar la ventana principal y finalizar sesión
			self.root.destroy()


		# --- configuracion ---
	def abrir_configuracion_ticket(self):

		# ==================== VENTANA ====================
		win = tk.Toplevel(self.root)
		win.title("Configuración del ticket")
		win.geometry("500x760")
		win.config(bg="#2b2b2b")

			# === HACER LA VENTANA MODAL ===
		win.transient(self.root)
		win.grab_set()
		win.focus_force()

		# ==================== BD ====================
		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()

		cur.execute("""
			CREATE TABLE IF NOT EXISTS configuracion_tickets (
				id INTEGER PRIMARY KEY,
				nombre_negocio TEXT,
				direccion TEXT,
				telefono TEXT,
				pie_ticket TEXT,
				logo_path TEXT
			)
		""")

		cur.execute("SELECT nombre_negocio, direccion, telefono, pie_ticket, logo_path FROM configuracion_tickets LIMIT 1")
		row = cur.fetchone()

		if not row:
			cur.execute("""
				INSERT INTO configuracion_tickets (id, nombre_negocio, direccion, telefono, pie_ticket, logo_path)
				VALUES (1, 'NEGOCIO SIN NOMBRE', 'Dirección no configurada',
						'Teléfono no registrado', 'Gracias por su compra 🙏', NULL)
			""")
			conn.commit()
			cur.execute("SELECT nombre_negocio, direccion, telefono, pie_ticket, logo_path FROM configuracion_tickets LIMIT 1")
			row = cur.fetchone()

		conn.close()

		nombre = tk.StringVar(value=row[0])
		direccion = tk.StringVar(value=row[1])
		telefono = tk.StringVar(value=row[2])
		pie_ticket = tk.StringVar(value=row[3])
		logo_actual = row[4]

		# ==================== CAMPOS ====================
		def campo(lbl, var):
			frame = tk.Frame(win, bg="#2b2b2b")
			frame.pack(pady=5)

			tk.Label(frame, text=lbl, fg="white", bg="#2b2b2b", font=("Segoe UI", 10, "bold")).pack(anchor="w")
			tk.Entry(frame, textvariable=var, width=45, font=("Segoe UI", 10)).pack()

		campo("Nombre del negocio:", nombre)
		campo("Dirección:", direccion)
		campo("Teléfono:", telefono)

		tk.Label(win, text="Pie del ticket:", fg="white", bg="#2b2b2b",
				font=("Segoe UI", 10, "bold")).pack()
		txt_pie = tk.Text(win, width=35, height=3)
		txt_pie.insert("1.0", pie_ticket.get())
		txt_pie.pack()

		# ==================== LOGO ====================
		logo_container = tk.Frame(win, bg="#2b2b2b")
		logo_container.pack(fill="x", pady=10)

		tk.Label(
			logo_container,
			text="Logo (opcional):",
			fg="white",
			bg="#2b2b2b",
			font=("Segoe UI", 10, "bold")
		).pack(anchor="w", padx=20)

		logo_frame = tk.Frame(logo_container, bg="#2b2b2b")
		logo_frame.pack(anchor="w", padx=20, pady=5)

		def elegir_logo():
			from tkinter import filedialog
			path = filedialog.askopenfilename(
				filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp")]
			)
			if path:
				logo_path.set(path)
				lbl_logo.config(text=os.path.basename(path))

		logo_path = tk.StringVar(value=logo_actual)

		tk.Button(
			logo_frame,
			text="Elegir imagen",
			command=elegir_logo,
			bg="#008cff",
			fg="white",
			width=15
		).pack(side="left")

		lbl_logo = tk.Label(
			logo_frame,
			text=os.path.basename(logo_actual) if logo_actual else "Sin logo",
			fg="lightgray",
			bg="#2b2b2b",
			anchor="w"
		)
		lbl_logo.pack(side="left", padx=10)

		# ==================== VISTA PREVIA ====================
		tk.Label(win, text="Vista previa:", fg="lightgreen",
				bg="#2b2b2b", font=("Segoe UI", 11, "bold")).pack(pady=5)
		vista = tk.Text(win, width=35, height=16, font=("Consolas", 5),
						bg="white", fg="black")
		vista.pack()

		def generar_vista():
			pie_ticket.set(txt_pie.get("1.0", "end").strip())
			vista.delete("1.0", "end")
			vista.insert("end",
				f"{nombre.get().center(42)}\n"
				f"{direccion.get().center(42)}\n"
				f"Tel: {telefono.get()}\n"
				+ "="*42 + "\n"
				"Fecha | No. Venta | Pago\n"
				+ "-"*42 + "\n"
				f"{'Producto':<17}{'Cant':<6}{'P.Unit':<9}{'Total':<8}\n"
				+ "-"*42 + "\n"
				"Totales y cambio\n"
				+ "="*42 + "\n"
				f"{pie_ticket.get().center(42)}"
			)

		generar_vista()

		# ==================== IMPRESORA ====================
		tk.Label(win, text="Impresora:", fg="white", bg="#2b2b2b",
				font=("Segoe UI", 10, "bold")).pack(pady=5)

		impresoras = self.listar_impresoras()
		cmb_imp = ttk.Combobox(win, values=impresoras, state="readonly", width=45)
		cmb_imp.pack()

		imp_guardada = self.obtener_impresora_configurada()
		if imp_guardada and imp_guardada in impresoras:
			cmb_imp.set(imp_guardada)
		elif impresoras:
			cmb_imp.current(0)

		# ==================== GUARDAR ====================
		def guardar():
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("""
				UPDATE configuracion_tickets SET
				nombre_negocio=?, direccion=?, telefono=?, pie_ticket=?, logo_path=?
				WHERE id=1
			""", (nombre.get(), direccion.get(), telefono.get(), txt_pie.get("1.0", "end").strip(), logo_path.get()))
			conn.commit()
			conn.close()

			self.guardar_impresora(cmb_imp.get())

			messagebox.showinfo("OK", "Configuración guardada correctamente")

		botones_frame = tk.Frame(win, bg="#2b2b2b")
		botones_frame.pack(pady=15)

		tk.Button(
			botones_frame,
			text="Guardar",
			bg="#28a745",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			width=18,
			command=guardar
		).pack(side="left", padx=10)

		tk.Button(
			botones_frame,
			text="Imprimir prueba",
			bg="#17a2b8",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			width=18,
			command=self.imprimir_prueba
		).pack(side="left", padx=10)

	def listar_impresoras(self):
		import win32print

		impresoras = []
		for (flags, description, name, comment) in win32print.EnumPrinters(
				win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):

			impresoras.append(name)

		return impresoras

	def seleccionar_impresora(self):
		import tkinter as tk
		from tkinter import ttk, messagebox
		import sqlite3

		win = tk.Toplevel(self.root)
		win.title("Seleccionar impresora")
		win.geometry("400x200")

		impresoras = self.listar_impresoras()

		tk.Label(win, text="Seleccione la impresora para tickets:",
				font=("Segoe UI", 10, "bold")).pack(pady=10)

		combo = ttk.Combobox(win, values=impresoras, state="readonly")
		combo.pack(pady=5, fill="x", padx=20)

		# Cargar impresora guardada
		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()
		cur.execute("""
			CREATE TABLE IF NOT EXISTS configuracion_impresora (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				nombre TEXT
			)
		""")
		cur.execute("SELECT nombre FROM configuracion_impresora LIMIT 1")
		row = cur.fetchone()
		conn.close()

		if row:
			combo.set(row[0])
		else:
			if impresoras:
				combo.current(0)

		def guardar():
			nombre = combo.get()
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("DELETE FROM configuracion_impresora")
			cur.execute("INSERT INTO configuracion_impresora (nombre) VALUES (?)", (nombre,))
			conn.commit()
			conn.close()
			messagebox.showinfo("Impresora guardada", f"✔ Impresora '{nombre}' establecida.")
			win.destroy()

		tk.Button(win, text="Guardar",
				bg="#27ae60", fg="white",
				font=("Segoe UI", 10, "bold"),
				command=guardar).pack(pady=15)

	def obtener_impresora_configurada(self):
		import sqlite3
		import win32print

		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()
		cur.execute("SELECT nombre FROM configuracion_impresora LIMIT 1")
		row = cur.fetchone()
		conn.close()

		if row:
			return row[0]
		else:
			return win32print.GetDefaultPrinter()  # Impresora predeterminada del sistema

	def guardar_impresora(self, nombre_impresora):
		import sqlite3
		from tkinter import messagebox

		try:
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()

			# Crear tabla si no existe
			cur.execute("""
				CREATE TABLE IF NOT EXISTS impresora_config (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					impresora TEXT
				)
			""")

			# Limpiar registro anterior
			cur.execute("DELETE FROM impresora_config")

			# Guardar nueva impresora
			cur.execute("INSERT INTO impresora_config (impresora) VALUES (?)", 
						(nombre_impresora,))
			conn.commit()
			conn.close()

			messagebox.showinfo("Éxito", "Impresora guardada correctamente.")

		except Exception as e:
			messagebox.showerror("Error", f"No se pudo guardar la impresora:\n{e}")

	def imprimir_prueba(self):
		try:
			impresora = self.obtener_impresora_configurada()

			import win32print
			import win32ui
			from tkinter import messagebox

			hPrinter = win32print.OpenPrinter(impresora)
			hJob = win32print.StartDocPrinter(hPrinter, 1, ("Prueba de ticket", None, "RAW"))
			win32print.StartPagePrinter(hPrinter)

			texto = "=== PRUEBA DE IMPRESIÓN ===\nImpresora funcionando correctamente.\n\n"
			win32print.WritePrinter(hPrinter, texto.encode("utf-8"))

			win32print.EndPagePrinter(hPrinter)
			win32print.EndDocPrinter(hPrinter)
			win32print.ClosePrinter(hPrinter)

			messagebox.showinfo("Éxito", "🖨️ La prueba de impresión ha sido enviada correctamente.")

		except Exception as e:
			messagebox.showerror("Error", f"No se pudo imprimir la prueba:\n{e}")


	# --- usuarios ---
	def abrir_usuarios(self):
		import tkinter as tk
		from tkinter import ttk, messagebox
		import sqlite3

		win = tk.Toplevel(self.root)
		win.title("👤 Gestión de Usuarios")
		win.geometry("1000x550")
		win.config(bg="#1e1e1e")

			# === HACER LA VENTANA MODAL ===
		win.transient(self.root)
		win.grab_set()
		win.focus_force()

		tk.Label(win, text="👤 Usuarios del Sistema", bg="#1e1e1e",
				fg="white", font=("Segoe UI", 16, "bold")).pack(pady=10)

		# ======== FILTRO POR PUESTO ========
		frame_filtro = tk.Frame(win, bg="#1e1e1e")
		frame_filtro.pack(pady=5)

		tk.Label(frame_filtro, text="Filtrar por puesto:", bg="#1e1e1e",
				fg="white", font=("Segoe UI", 11)).pack(side="left", padx=5)

		filtro_puesto = ttk.Combobox(frame_filtro, state="readonly", width=25)
		filtro_puesto.pack(side="left")

		def cargar_puestos():
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("SELECT DISTINCT puesto FROM usuarios WHERE puesto IS NOT NULL AND puesto<>''")
			puestos = [p[0] for p in cur.fetchall()]
			conn.close()

			filtro_puesto["values"] = ["Todos"] + puestos
			filtro_puesto.set("Todos")

		cargar_puestos()

		# ======== TABLA ========
		columnas = ("ID", "Nombre", "Usuario", "Puesto", "Sueldo")
		tabla = ttk.Treeview(win, columns=columnas, show="headings", height=18)

		for col in columnas:
			tabla.heading(col, text=col)
			tabla.column(col, anchor="center", width=150)

		tabla.pack(expand=True, fill="both", padx=10)

		# ======== Cargar datos ========
		def cargar():
			for r in tabla.get_children():
				tabla.delete(r)

			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()

			# SELECT correcto según tu tabla real
			base_query = "SELECT id_usuario, nombre, usuario, puesto, sueldo FROM usuarios"

			if filtro_puesto.get() != "Todos":
				cur.execute(base_query + " WHERE puesto=?", (filtro_puesto.get(),))
			else:
				cur.execute(base_query)

			rows = cur.fetchall()
			conn.close()

			for r in rows:
				sueldo_valor = r[4] if r[4] is not None else 0
				sueldo_formateado = f"${sueldo_valor:,.2f}"

				tabla.insert("", "end", values=(r[0], r[1], r[2], r[3], sueldo_formateado))

		cargar()

		filtro_puesto.bind("<<ComboboxSelected>>", lambda e: cargar())

		# ==================================================
		#                      CRUD
		# ==================================================

		# ---- AGREGAR ----
		def agregar_usuario():
			top = tk.Toplevel(win)
			top.title("➕ Nuevo Usuario")
			top.geometry("350x400")
			top.config(bg="#1e1e1e")

			campos = ["Nombre", "Usuario", "Contraseña", "Puesto", "Sueldo"]
			entradas = {}

			for c in campos:
				tk.Label(top, text=c, fg="white", bg="#1e1e1e",
						font=("Segoe UI", 11)).pack(pady=5)
				e = tk.Entry(top, show="*" if c == "Contraseña" else None)
				e.pack()
				entradas[c] = e

			def guardar():
				nombre = entradas["Nombre"].get()
				usuario = entradas["Usuario"].get()
				contrasena = entradas["Contraseña"].get()
				puesto = entradas["Puesto"].get()
				sueldo = entradas["Sueldo"].get()

				if nombre == "" or usuario == "" or contrasena == "":
					messagebox.showwarning("Error", "Todos los campos obligatorios.")
					return

				conn = sqlite3.connect(DB_PATH)
				cur = conn.cursor()
				cur.execute("""
					INSERT INTO usuarios(nombre, usuario, contrasena, puesto, sueldo)
					VALUES (?, ?, ?, ?, ?)
				""", (nombre, usuario, contrasena, puesto, sueldo))
				conn.commit()
				conn.close()

				cargar_puestos()
				cargar()
				top.destroy()

			tk.Button(top, text="Guardar", bg="#27ae60", fg="white",
					font=("Segoe UI", 11, "bold"), command=guardar).pack(pady=20)

		# ---- EDITAR ----
		def editar_usuario():
			try:
				item = tabla.item(tabla.selection()[0])
			except:
				messagebox.showinfo("Aviso", "Selecciona un usuario.")
				return

			idu, nombre, usuario, puesto, sueldo = item["values"]
			sueldo_num = float(str(sueldo).replace("$", "").replace(",", ""))

			top = tk.Toplevel(win)
			top.title("✏ Editar Usuario")
			top.geometry("350x400")
			top.config(bg="#1e1e1e")

			campos = {
				"Nombre": nombre,
				"Usuario": usuario,
				"Puesto": puesto,
				"Sueldo": sueldo_num
			}

			entradas = {}

			for c, val in campos.items():
				tk.Label(top, text=c, fg="white", bg="#1e1e1e",
						font=("Segoe UI", 11)).pack(pady=5)
				e = tk.Entry(top)
				e.insert(0, val)
				e.pack()
				entradas[c] = e

			def guardar():
				conn = sqlite3.connect(DB_PATH)
				cur = conn.cursor()
				cur.execute("""
					UPDATE usuarios
					SET nombre=?, usuario=?, puesto=?, sueldo=?
					WHERE id_usuario=?
				""", (
					entradas["Nombre"].get(),
					entradas["Usuario"].get(),
					entradas["Puesto"].get(),
					entradas["Sueldo"].get(),
					idu
				))
				conn.commit()
				conn.close()

				cargar()
				cargar_puestos()
				top.destroy()

			tk.Button(top, text="Guardar cambios", bg="#2980b9", fg="white",
					font=("Segoe UI", 11, "bold"), command=guardar).pack(pady=20)

		# ---- CAMBIAR CONTRASEÑA ----
		def cambiar_pass():
			try:
				item = tabla.item(tabla.selection()[0])
			except:
				messagebox.showinfo("Aviso", "Selecciona un usuario.")
				return

			idu = item["values"][0]

			top = tk.Toplevel(win)
			top.title("🔐 Cambiar Contraseña")
			top.geometry("300x200")
			top.config(bg="#1e1e1e")

			tk.Label(top, text="Nueva contraseña:", fg="white",
					bg="#1e1e1e").pack(pady=10)
			e = tk.Entry(top, show="*")
			e.pack()

			def guardar():
				conn = sqlite3.connect(DB_PATH)

				cur = conn.cursor()
				cur.execute("UPDATE usuarios SET contrasena=? WHERE id_usuario=?",
							(e.get(), idu))
				conn.commit()
				conn.close()

				top.destroy()
				messagebox.showinfo("OK", "Contraseña actualizada.")

			tk.Button(top, text="Guardar", bg="#8e44ad", fg="white",
					font=("Segoe UI", 11, "bold"), command=guardar).pack(pady=20)

		# ---- ELIMINAR ----
		def eliminar_usuario():
			try:
				item = tabla.item(tabla.selection()[0])
			except:
				messagebox.showinfo("Aviso", "Selecciona un usuario.")
				return

			idu = item["values"][0]

			if not messagebox.askyesno("Eliminar", "¿Eliminar usuario?"):
				return

			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()
			cur.execute("DELETE FROM usuarios WHERE id_usuario=?", (idu,))
			conn.commit()
			conn.close()

			cargar()
			cargar_puestos()

		# ======== BOTONES ========
		frame_btn = tk.Frame(win, bg="#1e1e1e")
		frame_btn.pack(pady=15)

		botones = [
			("➕ Agregar", agregar_usuario, "#27ae60"),
			("✏ Editar", editar_usuario, "#2980b9"),
			("🔐 Cambiar contraseña", cambiar_pass, "#8e44ad"),
			("🗑 Eliminar", eliminar_usuario, "#c0392b"),
			("❌ Cerrar", win.destroy, "#7f8c8d")
		]

		for t, cmd, color in botones:
			tk.Button(frame_btn, text=t, command=cmd,
					bg=color, fg="white",
					font=("Segoe UI", 10, "bold"),
					width=22, height=2).pack(side="left", padx=10)

	# --- informacion que cura ---
	def informacion_programa(self):
		import tkinter as tk

		win = tk.Toplevel(self.root)
		win.title("ℹ️ Información del Programa")
		win.geometry("500x400")
		win.config(bg="#0a0a0a")  # Negro opaco
		win.transient(self.root)
		win.grab_set()

		tk.Label(
			win,
			text="Información del Programa",
			bg="#0a0a0a",
			fg="#1abc9c",   # verde azulado
			font=("Segoe UI", 16, "bold")
		).pack(pady=15)

		texto = (
			"👤 CREADOR DEL SISTEMA\n"
			"Kelvin Bravo Rivera\n"
			"Ciudad de México\n\n"
			"📱 Teléfono de contacto:\n"
			"5584396121\n\n"
			"🛠 Servicios:\n"
			"- Mantenimiento del sistema\n"
			"- Creación de plataformas y apps\n"
			"- Desarrollo para computadora y celular\n\n"
			"📩 Para cotizaciones:\n"
			"Envíe mensaje por WhatsApp\n"
			"con el nombre del proyecto y\n"
			"las características deseadas."
		)

		tk.Label(
			win,
			text=texto,
			bg="#0a0a0a",
			fg="#1abc9c",
			justify="left",
			font=("Segoe UI", 11)
		).pack(padx=20, pady=10)

		tk.Button(
			win,
			text="Cerrar",
			bg="#1abc9c",
			fg="black",
			font=("Segoe UI", 11, "bold"),
			width=15,
			command=win.destroy
		).pack(pady=15)


# --- botones derechos ---
	def abrir_gastos(self):
		import tkinter as tk
		from tkinter import messagebox, ttk
		import sqlite3
		from datetime import datetime

		win = tk.Toplevel(self.root)
		win.title("📉 Registrar Gasto")
		win.geometry("400x360")
		win.config(bg="#1e1e1e")

		# --- Campos ---
		tk.Label(win, text="Categoría:", bg="#1e1e1e", fg="white", font=("Segoe UI", 11)).pack(pady=5)
		categoria_var = tk.StringVar()
		combo = ttk.Combobox(win, textvariable=categoria_var, font=("Segoe UI", 11), state="readonly")
		combo["values"] = ["Papelería", "Limpieza", "Insumos", "Devolución", "Pasajes", "Otros"]
		combo.current(0)
		combo.pack(pady=5)

		tk.Label(win, text="Descripción:", bg="#1e1e1e", fg="white", font=("Segoe UI", 11)).pack(pady=5)
		desc_var = tk.StringVar()
		tk.Entry(win, textvariable=desc_var, font=("Segoe UI", 11)).pack(pady=5)

		tk.Label(win, text="Monto:", bg="#1e1e1e", fg="white", font=("Segoe UI", 11)).pack(pady=5)
		monto_var = tk.StringVar()
		tk.Entry(win, textvariable=monto_var, font=("Segoe UI", 11)).pack(pady=5)

		# --- Función guardar ---
		def guardar_gasto():
			categoria = categoria_var.get()
			descripcion = desc_var.get().strip()

			try:
				monto = float(monto_var.get())
			except ValueError:
				messagebox.showerror("Error", "Monto inválido.")
				return

			if not descripcion:
				messagebox.showwarning("Atención", "Ingrese una descripción del gasto.")
				return

			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()

			# aseguramos que la tabla tenga la estructura correcta
			cur.execute("""
				CREATE TABLE IF NOT EXISTS gastos (
					id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
					fecha DATE,
					categoria TEXT,
					descripcion TEXT,
					monto REAL
				)
			""")

			cur.execute("""
				INSERT INTO gastos (fecha, categoria, descripcion, monto)
				VALUES (?, ?, ?, ?)
			""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), categoria, descripcion, monto))

			conn.commit()
			conn.close()

			messagebox.showinfo("Éxito", "💸 Gasto registrado correctamente.")
			win.destroy()

		# --- Botones ---
		tk.Button(win, text="Guardar", bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"),
				command=guardar_gasto).pack(pady=10)
		tk.Button(win, text="Cancelar", bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"),
				command=win.destroy).pack(pady=5)

	def pagar_salario(self):
		win_sal = tk.Toplevel(self.root)
		win_sal.title("💰 Pagar Salario")
		win_sal.geometry("450x400")  # Más ancho y alto
		win_sal.grab_set()
		win_sal.focus_force()
		win_sal.config(bg="#2b2b2b")

		tk.Label(win_sal, text="Empleado:", bg="#2b2b2b", fg="white").pack(pady=5)

		# ======= Traer todos los empleados activos =======
		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()
		cur.execute("SELECT id, nombre || ' ' || apellido FROM empleados WHERE estado='Activo'")
		empleados = cur.fetchall()  # Devuelve lista de tuplas (id, "Nombre Apellido")
		conn.close()

		# Diccionario para relacionar nombre con ID
		emp_dict = {nombre: emp_id for emp_id, nombre in empleados}
		emp_names = list(emp_dict.keys())  # Lista de todos los nombres

		# Combobox con todos los empleados
		empleado_var = tk.StringVar()
		combo_emp = ttk.Combobox(win_sal, textvariable=empleado_var, values=emp_names, width=40)
		combo_emp.pack(pady=5, fill="x", padx=20)

		tk.Label(win_sal, text="Monto:", bg="#2b2b2b", fg="white").pack(pady=5)
		monto_var = tk.StringVar()
		tk.Entry(win_sal, textvariable=monto_var, bg="#3b3b3b", fg="white").pack(pady=5, fill="x", padx=20)

		def guardar_salario():
			emp_name = empleado_var.get()
			if not emp_name or emp_name not in emp_dict:
				messagebox.showerror("Error", "Selecciona un empleado válido.", parent=win_sal)
				return
			try:
				monto = float(monto_var.get())
			except ValueError:
				messagebox.showerror("Error", "Monto inválido.", parent=win_sal)
				return

			emp_id = emp_dict[emp_name]
			fecha = datetime.now().strftime("%Y-%m-%d")

			try:
				conn = sqlite3.connect(DB_PATH)
				cur = conn.cursor()
				cur.execute("""
					INSERT INTO salarios(empleado_id, fecha, monto)
					VALUES (?, ?, ?)
				""", (emp_id, fecha, monto))
				conn.commit()
				conn.close()
				messagebox.showinfo("Éxito", "Salario pagado correctamente.", parent=win_sal)
				win_sal.destroy()

				# Actualizar treeview de salarios si el reporte está abierto
				if hasattr(self, "tree_sal") and hasattr(self, "lbl_total"):
					self.actualizar_tree_salarios()
			except Exception as e:
				messagebox.showerror("Error", str(e), parent=win_sal)

		tk.Button(win_sal, text="Guardar", command=guardar_salario, bg="red", fg="white",
				font=("Segoe UI", 12, "bold")).pack(pady=20)
		
	def buscar_producto(self):
		texto = self.search_var.get().strip()
		if not texto:
			return

		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()

		# Traer stock también
		cur.execute("""
			SELECT id_producto, nombre_producto, precio_venta, stock
			FROM productos
			WHERE nombre_producto LIKE ?
			LIMIT 1
		""", (f"%{texto}%",))

		fila = cur.fetchone()
		conn.close()

		if not fila:
			return

		id_producto, nombre, precio, stock = fila

		if stock <= 0:
			from tkinter import messagebox
			messagebox.showwarning("Sin stock", f"El producto '{nombre}' no tiene stock disponible.")
			return

		# Intentar agregar 1 unidad, pero respetando el stock
		self.agregar_producto(id_producto, nombre, 1, precio, stock)


	def agregar_producto(self, id_producto, nombre, cantidad, precio, stock):
		"""Agrega producto al treeview respetando stock máximo."""

		for item in self.tree.get_children():
			valores = list(self.tree.item(item, "values"))

			if valores[0] == str(id_producto):
				cantidad_actual = int(valores[2])
				precio_unit = float(valores[3])

				# Nueva cantidad sin exceder stock
				nueva_cantidad = min(cantidad_actual + cantidad, stock)
				if nueva_cantidad == cantidad_actual:
					from tkinter import messagebox
					messagebox.showinfo("Stock insuficiente",
										f"No puedes agregar más '{nombre}'. Stock máximo: {stock}.")
					return

				subtotal_real = nueva_cantidad * precio_unit
				valores[2] = nueva_cantidad
				valores[4] = f"{subtotal_real:.2f}"
				valores[5] = "0.00"

				self.tree.item(item, values=valores, tags=())
				self.actualizar_totales()
				return

		# ➕ PRODUCTO NUEVO
		cantidad_final = min(cantidad, stock)
		self.tree.insert(
			"",
			"end",
			values=(
				id_producto,
				nombre,
				cantidad_final,
				f"{precio:.2f}",
				f"{cantidad_final * precio:.2f}",
				"0.00"
			)
		)
		self.actualizar_totales()

	def actualizar_totales(self):
		total_general = 0
		for item in self.tree.get_children():
			valores = self.tree.item(item, "values")
			total_general += float(valores[4])  # Columna “Total”

		self.total = total_general
		self.label_total.config(text=f"TOTAL: ${total_general:.2f}")

	# --- descuento ---
	def aplicar_descuento(self):
		if not self.tree.get_children():
			messagebox.showwarning("Atención", "No hay productos en el carrito.")
			return

		ventana = tk.Toplevel(self.root)
		ventana.title("Aplicar Descuento")
		ventana.configure(bg="#1e1e1e")
		ventana.resizable(False, False)
		ventana.grab_set()

		tk.Label(
			ventana, text="🧾 Aplicar Descuento",
			bg="#1e1e1e", fg="white",
			font=("Segoe UI", 14, "bold")
		).pack(pady=10)

		tipo_var = tk.StringVar(value="%")
		alcance_var = tk.StringVar(value="producto")

		frame_tipo = tk.Frame(ventana, bg="#1e1e1e")
		frame_tipo.pack(pady=5)

		tk.Radiobutton(frame_tipo, text="%", variable=tipo_var, value="%",
					bg="#1e1e1e", fg="white", selectcolor="#333").pack(side="left", padx=5)
		tk.Radiobutton(frame_tipo, text="$", variable=tipo_var, value="$",
					bg="#1e1e1e", fg="white", selectcolor="#333").pack(side="left", padx=5)

		frame_alcance = tk.Frame(ventana, bg="#1e1e1e")
		frame_alcance.pack(pady=5)

		tk.Radiobutton(frame_alcance, text="Producto seleccionado",
					variable=alcance_var, value="producto",
					bg="#1e1e1e", fg="white", selectcolor="#333").pack(anchor="w")

		tk.Radiobutton(frame_alcance, text="Todo el carrito",
					variable=alcance_var, value="total",
					bg="#1e1e1e", fg="white", selectcolor="#333").pack(anchor="w")

		valor_entry = tk.Entry(ventana, width=10, justify="center")
		valor_entry.pack(pady=8)

		def aplicar_a_item(item, tipo, valor):
			vals = list(self.tree.item(item, "values"))

			cantidad = int(vals[2])
			precio_unitario = float(vals[3])

			subtotal_real = precio_unitario * cantidad

			if tipo == "%":
				descuento_unit = precio_unitario * (valor / 100)
			else:
				descuento_unit = valor

			descuento_unit = min(descuento_unit, precio_unitario)

			descuento_total = descuento_unit * cantidad
			nuevo_subtotal = subtotal_real - descuento_total

			vals[4] = f"{nuevo_subtotal:.2f}"
			vals[5] = f"{descuento_total:.2f}"

			self.tree.item(item, values=vals,
						tags=("descuento",) if descuento_total > 0 else ())

		def confirmar():
			try:
				valor = float(valor_entry.get())
			except ValueError:
				messagebox.showerror("Error", "Ingrese un valor válido")
				return

			tipo = tipo_var.get()
			alcance = alcance_var.get()

			if alcance == "producto":
				seleccion = self.tree.selection()
				if not seleccion:
					messagebox.showwarning("Atención", "Seleccione un producto")
					return
				aplicar_a_item(seleccion[0], tipo, valor)

			else:  # TODO EL CARRITO
				for item in self.tree.get_children():
					aplicar_a_item(item, tipo, valor)

			self.actualizar_totales()
			ventana.destroy()

		frame_btn = tk.Frame(ventana, bg="#1e1e1e")
		frame_btn.pack(pady=15)

		tk.Button(frame_btn, text="Aplicar", bg="#28a745", fg="white",
				width=12, command=confirmar).pack(side="left", padx=8)

		tk.Button(frame_btn, text="Cancelar", bg="#dc3545", fg="white",
				width=12, command=ventana.destroy).pack(side="left", padx=8)

	# --- finalizar venta ---
	def finalizar_venta(self):
		import tkinter as tk
		from tkinter import messagebox
		import sqlite3
		import datetime
		import os

		# Si no hay items, no continuar
		if self.total <= 0:
			messagebox.showwarning("Sin venta", "No hay productos agregados.")
			return

		# Aseguramos existencia de la tabla ventas_pagos
		try:
			with sqlite3.connect(DB_PATH) as conn:
				cur = conn.cursor()
				cur.execute("""
					CREATE TABLE IF NOT EXISTS ventas_pagos (
						id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
						id_venta INTEGER,
						metodo TEXT,
						monto REAL,
						FOREIGN KEY (id_venta) REFERENCES ventas(id_venta)
					)
				""")
				conn.commit()
		except Exception:
			pass

		# === Ventana de Pago (un solo Toplevel) ===
		pago_win = tk.Toplevel(self.root)
		pago_win.title("Finalizar Venta")
		w, h = 920, 420
		x = (pago_win.winfo_screenwidth() // 2) - (w // 2)
		y = (pago_win.winfo_screenheight() // 2) - (h // 2)
		pago_win.geometry(f"{w}x{h}+{x}+{y}")
		pago_win.configure(bg="#2b2b2b")
		pago_win.resizable(False, False)
		pago_win.transient(self.root)
		pago_win.grab_set()

		# Título
		tk.Label(
			pago_win, text="💰 Finalizar Venta", bg="#2b2b2b",
			fg="white", font=("Segoe UI", 16, "bold")
		).pack(pady=10)

		# Contenedor principal
		frame = tk.Frame(pago_win, bg="#2b2b2b")
		frame.pack(fill="both", expand=True)

		# ------------------ LEFT: tipo de pago ------------------
		left = tk.Frame(frame, bg="#2b2b2b")
		left.pack(side="left", fill="y", padx=12, pady=6)

		tipo_pago = tk.StringVar(value="Efectivo")

		tk.Label(left, text="Tipo de pago (selecciona):", bg="#2b2b2b",
				fg="white", font=("Segoe UI", 12, "bold")).pack(pady=5)

		metodos = [
			("💵 Efectivo", "Efectivo"),
			("💳 Tarjeta", "Tarjeta"),
			("🔄 Transferencia", "Transferencia"),
			("📝 Otro", "Otro")
		]

		for texto, val in metodos:
			btn = tk.Radiobutton(
				left,
				text=texto,
				value=val,
				variable=tipo_pago,
				indicatoron=0,
				width=18,
				pady=8,
				bg="#3a3a3a",
				fg="white",
				selectcolor="#1E5128",
				activebackground="#2E2E2E",
				activeforeground="white",
				font=("Segoe UI", 11, "bold"),
				borderwidth=2,
				relief="solid",
				highlightthickness=1,
				highlightbackground="#444444",
				highlightcolor="#4CAF50"
			)
			btn.pack(pady=6)

		# ==== Detectar selección "Otro" ====
		def pedir_otro_metodo():
			if tipo_pago.get() != "Otro":
				return

			win = tk.Toplevel(pago_win)
			win.title("Otro método de pago")
			win.geometry("350x180")
			win.configure(bg="#2b2b2b")
			win.transient(pago_win)
			win.grab_set()

			tk.Label(win, text="Especifica el método de pago:",
					bg="#2b2b2b", fg="white",
					font=("Segoe UI", 12)).pack(pady=10)

			metodo_var = tk.StringVar()
			entry = tk.Entry(win, textvariable=metodo_var, font=("Segoe UI", 12), width=28)
			entry.pack(pady=5)
			entry.focus_set()

			def guardar_otro():
				metodo = metodo_var.get().strip()
				if not metodo:
					messagebox.showwarning("Aviso", "Debes escribir un nombre.")
					return
				tipo_pago.set(metodo)
				win.destroy()

			tk.Button(win, text="Guardar", bg="#4CAF50", fg="white",
					font=("Segoe UI", 11, "bold"), width=12,
					command=guardar_otro).pack(pady=12)

		tipo_pago.trace_add("write", lambda *args: pedir_otro_metodo())

		# ------------------ CENTER: recibido / agregar pagos ------------------
		center = tk.Frame(frame, bg="#2b2b2b")
		center.pack(side="left", expand=True, padx=8, pady=6)

		tk.Label(center, text=f"Total a pagar: ${self.total:.2f}",
				bg="#2b2b2b", fg="#00FF7F",
				font=("Segoe UI", 14, "bold")).pack(pady=6)

		# Entrada para monto que se va a agregar como pago
		tk.Label(center, text="Monto a agregar:", bg="#2b2b2b",
				fg="white", font=("Segoe UI", 11)).pack()
		monto_add_var = tk.DoubleVar(value=0.0)
		ent_monto_add = tk.Entry(center, textvariable=monto_add_var, font=("Segoe UI", 12),
								justify="center", width=18)
		ent_monto_add.pack(pady=6)
		ent_monto_add.focus_set()

		# Botones agregar / eliminar
		btns_row = tk.Frame(center, bg="#2b2b2b")
		btns_row.pack(pady=6)

		tk.Button(btns_row, text="➕ Agregar", bg="#3498db", fg="white",
				font=("Segoe UI", 10, "bold"),
				command=lambda: agregar_pago()).pack(side="left", padx=6)
		tk.Button(btns_row, text="🗑️ Eliminar Seleccion", bg="#e74c3c", fg="white",
				font=("Segoe UI", 10, "bold"),
				command=lambda: eliminar_pago()).pack(side="left", padx=6)

		# Treeview de pagos agregados
		from tkinter import ttk
		pagos_tree = ttk.Treeview(center, columns=("metodo", "monto"), show="headings", height=6)
		pagos_tree.heading("metodo", text="Método")
		pagos_tree.heading("monto", text="Monto")
		pagos_tree.column("metodo", width=200, anchor="center")
		pagos_tree.column("monto", width=120, anchor="center")
		pagos_tree.pack(pady=8, padx=6, fill="x")

		lbl_totales = tk.Label(center, text="Pagado: $0.00   —   Restante: ${:.2f}".format(self.total),
							bg="#2b2b2b", fg="#FFD700", font=("Segoe UI", 12, "bold"))
		lbl_totales.pack(pady=4)

		# Estado interno: lista de pagos
		pagos_agregados = []  # lista de tuples (metodo, monto)

		def actualizar_totales_pagos():
			total_pagado = sum(p[1] for p in pagos_agregados)
			diferencia = total_pagado - self.total

			if diferencia >= 0:
				cambio = diferencia
				lbl_totales.config(
					text=f"Pagado: ${total_pagado:.2f}   —   Cambio: ${cambio:.2f}"
				)
				btn_confirmar.config(bg="#2b2b2b")  # habilitado visual
			else:
				restante = abs(diferencia)
				lbl_totales.config(
					text=f"Pagado: ${total_pagado:.2f}   —   Restante: ${restante:.2f}"
				)
				btn_confirmar.config(bg="#7a7a7a")  # deshabilitado visual

		def agregar_pago():
			metodo = tipo_pago.get() or "Efectivo"
			try:
				monto = float(monto_add_var.get() or 0)
			except Exception:
				messagebox.showwarning("Error", "Monto inválido.")
				return
			if monto <= 0:
				messagebox.showwarning("Error", "Ingresa un monto mayor a 0.")
				return
			# Añadir pago (no bloqueamos exceso; se permitirá y se calculará cambio)
			pagos_agregados.append((metodo, monto))
			pagos_tree.insert("", "end", values=(metodo, f"{monto:.2f}"))
			monto_add_var.set(0.0)
			actualizar_totales_pagos()

		def eliminar_pago():
			sel = pagos_tree.selection()
			if not sel:
				messagebox.showwarning("Aviso", "Selecciona un pago a eliminar.")
				return
			for it in sel:
				vals = pagos_tree.item(it)["values"]
				try:
					metodo = vals[0]
					monto = float(vals[1])
				except Exception:
					continue
				# eliminar de lista interna (primera coincidencia)
				for i, p in enumerate(pagos_agregados):
					if p[0] == metodo and abs(p[1] - monto) < 0.0001:
						pagos_agregados.pop(i)
						break
				pagos_tree.delete(it)
			actualizar_totales_pagos()

		# ------------------ RIGHT: mayorista + confirmar ------------------
		right = tk.Frame(frame, bg="#2b2b2b")
		right.pack(side="right", fill="y", padx=12, pady=6)

		mayorista_id = tk.IntVar(value=0)

		lbl_may = tk.Label(right, text="Mayorista: Ninguno",
						bg="#2b2b2b", fg="gray", font=("Segoe UI", 11))
		lbl_may.pack(pady=5)

		def buscar_mayorista():
			win = tk.Toplevel(pago_win)
			win.title("Seleccionar mayorista")
			win.geometry("400x400")
			win.configure(bg="#2b2b2b")
			win.transient(pago_win)
			win.grab_set()

			tree = ttk.Treeview(win, columns=("id", "nombre"), show="headings")
			tree.heading("id", text="ID")
			tree.heading("nombre", text="Nombre")
			tree.pack(expand=True, fill="both", padx=10, pady=10)

			try:
				with sqlite3.connect(DB_PATH) as conn:
					cur = conn.cursor()
					cur.execute("SELECT id_mayorista, nombre FROM mayoristas")
					for row in cur.fetchall():
						tree.insert("", "end", values=row)
			except Exception:
				pass

			def seleccionar():
				try:
					item = tree.item(tree.selection())["values"]
					mayorista_id.set(item[0])
					lbl_may.config(text=f"Mayorista: {item[1]}", fg="#00FF7F")
					win.destroy()
				except Exception:
					messagebox.showwarning("Aviso", "Selecciona un registro.")

			tk.Button(win, text="Seleccionar", bg="#4CAF50",
					fg="white", command=seleccionar).pack(pady=10)

		tk.Button(right, text="🔍 Buscar Mayorista", bg="#0078D7",
				fg="white", font=("Segoe UI", 10, "bold"),
				command=buscar_mayorista).pack(pady=5)

		# Agregar nuevo mayorista (mantiene tu flujo)
		def agregar_mayorista():
			win = tk.Toplevel(pago_win)
			win.title("Nuevo Mayorista")
			win.geometry("350x350")
			win.configure(bg="#2b2b2b")
			win.transient(pago_win)
			win.grab_set()

			tk.Label(win, text="Registrar Mayorista", bg="#2b2b2b",
					fg="white", font=("Segoe UI", 14, "bold")).pack(pady=10)

			frm = tk.Frame(win, bg="#2b2b2b")
			frm.pack(pady=10)

			tk.Label(frm, text="Nombre:", bg="#2b2b2b", fg="white").grid(row=0, column=0, sticky="w")
			ent_nombre = tk.Entry(frm, width=30)
			ent_nombre.grid(row=0, column=1, pady=5)

			tk.Label(frm, text="Teléfono:", bg="#2b2b2b", fg="white").grid(row=1, column=0, sticky="w")
			ent_tel = tk.Entry(frm, width=30)
			ent_tel.grid(row=1, column=1, pady=5)

			tk.Label(frm, text="Dirección:", bg="#2b2b2b", fg="white").grid(row=2, column=0, sticky="w")
			ent_dir = tk.Entry(frm, width=30)
			ent_dir.grid(row=2, column=1, pady=5)

			tk.Label(frm, text="Empresa:", bg="#2b2b2b", fg="white").grid(row=3, column=0, sticky="w")
			ent_emp = tk.Entry(frm, width=30)
			ent_emp.grid(row=3, column=1, pady=5)

			def guardar_may():
				nombre = ent_nombre.get().strip()
				tel = ent_tel.get().strip()
				dirc = ent_dir.get().strip()
				emp = ent_emp.get().strip()

				if not nombre:
					messagebox.showwarning("Falta nombre", "El nombre es obligatorio.")
					return

				try:
					with sqlite3.connect(DB_PATH) as conn:
						cur = conn.cursor()
						cur.execute("""
							INSERT INTO mayoristas (nombre, telefono, direccion, empresa)
							VALUES (?, ?, ?, ?)
						""", (nombre, tel, dirc, emp))

						nuevo_id = cur.lastrowid
						mayorista_id.set(nuevo_id)
						lbl_may.config(text=f"Mayorista: {nombre}", fg="#00FF7F")
				except Exception as e:
					messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
					return

				win.destroy()

			tk.Button(win, text="Guardar", bg="#4CAF50", fg="white",
					font=("Segoe UI", 11, "bold"), width=12,
					command=guardar_may).pack(pady=15)

		tk.Button(right, text="➕ Nuevo Mayorista", bg="#4CAF50",
				fg="white", font=("Segoe UI", 10, "bold"),
				width=18, command=agregar_mayorista).pack(pady=5)

		# ------------------ Confirmar pago (guardado + ticket + cierre) ------------------
		def confirmar_pago():
			# Validaciones: debe haber pagos y suma >= total
			if not pagos_agregados:
				messagebox.showwarning("Error", "No se han agregado pagos.")
				return

			total_pagado = sum(p[1] for p in pagos_agregados)
			if total_pagado < self.total:
				faltante = self.total - total_pagado
				messagebox.showwarning("Error", f"Aún falta pagar: ${faltante:.2f}")
				return

			fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			try:
				with sqlite3.connect(DB_PATH) as conn:
					conn.execute("PRAGMA foreign_keys = ON")
					cur = conn.cursor()

					# Insertar venta
					cur.execute("""
						INSERT INTO ventas (fecha, id_usuario, id_mayorista, total, tipo_pago)
						VALUES (?, ?, ?, ?, ?)
					""", (
						fecha,
						None,
						mayorista_id.get() or None,
						self.total,
						", ".join([p[0] for p in pagos_agregados])
					))
					id_venta = cur.lastrowid

					# Guardar detalle y actualizar stock
					for item in self.tree.get_children():
						valores = self.tree.item(item)["values"]

						id_producto = int(valores[0])        # ✅ ID real del producto
						nombre = valores[1]                  # Nombre para mostrar
						cantidad = int(valores[2])
						precio_unitario = float(valores[3])
						subtotal = float(valores[4])         # Total con descuento

						# Insertar en ventas_detalle
						cur.execute("""
							INSERT INTO ventas_detalle
							(id_venta, id_producto, cantidad, precio_unitario, subtotal)
							VALUES (?, ?, ?, ?, ?)
						""", (id_venta, id_producto, cantidad, precio_unitario, subtotal))

						# Actualizar stock
						cur.execute("UPDATE productos SET stock = stock - ? WHERE id_producto = ?",
									(cantidad, id_producto))

					# Guardar pagos
					for metodo, monto in pagos_agregados:
						cur.execute("""
							INSERT INTO ventas_pagos (id_venta, metodo, monto)
							VALUES (?, ?, ?)
						""", (id_venta, metodo, monto))

					conn.commit()

					# 🔁 Volver a leer pagos REALES desde BD
					cur.execute("""
						SELECT metodo, monto
						FROM ventas_pagos
						WHERE id_venta = ?
					""", (id_venta,))
					pagos_reales = cur.fetchall()


			except Exception as e:
				messagebox.showerror("Error", f"No se pudo guardar la venta:\n{e}")
				return

			# Preparar datos para el ticket
			productos_ticket = []
			total_productos = 0
			for item in self.tree.get_children():
				valores = self.tree.item(item)["values"]
				nombre = valores[1]                  # Nombre real
				cantidad = int(valores[2])
				precio = float(valores[3])
				subtotal = float(valores[4])         # Total con descuento
				descuento = float(valores[5]) if len(valores) > 5 else 0.0
				productos_ticket.append((nombre, cantidad, precio, subtotal, descuento))
				total_productos += cantidad

			cambio = total_pagado - self.total if total_pagado > self.total else 0.0

			datos_venta = {
				"id_venta": id_venta,
				"fecha": fecha,
				"pagos": pagos_reales,
				"pagos": pagos_agregados.copy(),
				"productos": productos_ticket,
				"total_productos": total_productos,
				"total_venta": self.total,
				"recibido": total_pagado,
				"cambio": cambio
			}

			# Generar e imprimir ticket
			try:
				self.generar_ticket(datos_venta)
				self.abrir_cajon()
			except Exception as e:
				messagebox.showwarning("Ticket", f"No se pudo generar/imprimir el ticket:\n{e}")

			# Mensaje final
			mensaje_pago = "\n".join([f"{m}: ${x:.2f}" for m, x in pagos_agregados])
			messagebox.showinfo(
				"Venta completada",
				f"Pagos:\n{mensaje_pago}\n\nTotal: ${self.total:.2f}\nRecibido: ${total_pagado:.2f}\nCambio: ${cambio:.2f}"
			)

			# Cerrar ventana de pago
			try:
				pago_win.grab_release()
				pago_win.destroy()
			except Exception:
				pass

			# Limpiar carrito y UI
			try:
				self.nueva_venta()
			except Exception:
				self.total = 0
				try:
					self.actualizar_totales()
				except Exception:
					pass

		# Botón confirmar (usa la función interna que cierra pago_win)
		btn_confirmar = tk.Button(right, text="✅ Confirmar Pago", bg="#7a7a7a",
				fg="white", font=("Segoe UI", 12, "bold"),
				width=18, height=2, command=confirmar_pago)
		btn_confirmar.pack(pady=20)

		# Inicializar totales
		actualizar_totales_pagos()

	def generar_ticket(self, datos_venta, imprimir=True):
		import sqlite3

		# ================== CONFIGURACIÓN ==================
		conn = sqlite3.connect(DB_PATH)
		cur = conn.cursor()
		try:
			cur.execute("""
				SELECT nombre_negocio, direccion, telefono, pie_ticket, logo_path
				FROM configuracion_tickets
				LIMIT 1
			""")
			conf = cur.fetchone()
		except Exception:
			conf = None
		finally:
			conn.close()

		if conf and len(conf) >= 4:
			nombre, direc, tel, pie = conf[:4]
			logo = conf[4] if len(conf) > 4 else None
		else:
			nombre = direc = tel = pie = ""
			logo = None

		# ================== FORMATO ==================
		ANCHO = 32
		line = "-" * ANCHO
		texto = []

		# ================== ENCABEZADO ==================
		texto.append(nombre.center(ANCHO))
		texto.append(direc.center(ANCHO))
		texto.append(f"Tel: {tel}".center(ANCHO))
		texto.append(line)

		texto.append(f"Fecha: {datos_venta['fecha']}")
		texto.append(f"Venta #{datos_venta['id_venta']}")
		texto.append(line)

		texto.append(f"{'Prod':<10}{'Cnt':<4}{'P.Unit':<8}{'Final':<8}")
		texto.append(line)

		# ================== PRODUCTOS ==================
		for prod, cant, unit, subtotal, descuento in datos_venta["productos"]:
			final = subtotal
			ahorro = (unit * cant) - subtotal

			if ahorro > 0:
				texto.append(f"{'':<10}{'':<4}{'Ahorro':<8}{ahorro:<7.2f}")

			texto.append(f"{prod[:10]:<10}{cant:<4}{unit:<8.2f}{final:<8.2f}")

		# ================== TOTALES ==================
		texto.append(line)
		texto.append(f"Artículos: {datos_venta['total_productos']}")
		texto.append(f"TOTAL: ${datos_venta['total_venta']:.2f}")

		# ================== PAGOS ==================
		pagos = datos_venta.get("pagos", [])
		if pagos:
			texto.append(line)
			texto.append("Pagos recibidos:".center(ANCHO))
			for metodo, monto in pagos:
				texto.append(f"{metodo:<12} ${monto:.2f}")
			texto.append(f"Total recibido: ${datos_venta.get('recibido', 0.0):.2f}")
			texto.append(f"Cambio: ${datos_venta.get('cambio', 0.0):.2f}")

		# ================== PIE ==================
		texto.append(line)
		texto.append(pie.center(ANCHO))

		# ================== UNIR TEXTO ==================
		texto_final = "\n".join(texto) + "\n\n\n"

		# ================== IMPRIMIR ==================
		if imprimir:
			self.imprimir_ticket_raw(texto_final, logo)

		return texto_final

	def escpos_logo(self, img):
		width, height = img.size
		width_bytes = (width + 7) // 8
		bitmap = bytearray()

		for y in range(height):
			for x in range(0, width, 8):
				byte = 0
				for bit in range(8):
					if x + bit < width:
						if img.getpixel((x + bit, y)) == 0:
							byte |= 1 << (7 - bit)
				bitmap.append(byte)

		header = b'\x1d\x76\x30\x00'
		header += bytes([
			width_bytes & 0xFF,
			(width_bytes >> 8) & 0xFF,
			height & 0xFF,
			(height >> 8) & 0xFF
		])

		return header + bitmap

	def imprimir_ticket_raw(self, texto, logo_path=None):
		import win32print
		from PIL import Image
		import os

		impresora = self.obtener_impresora_configurada()
		if not impresora:
			raise Exception("No hay impresora configurada")

		hPrinter = win32print.OpenPrinter(impresora)

		try:
			win32print.StartDocPrinter(hPrinter, 1, ("Ticket", None, "RAW"))
			win32print.StartPagePrinter(hPrinter)

			# ===== RESET IMPRESORA (CLAVE) =====
			win32print.WritePrinter(hPrinter, b"\x1b@")

			# ===== LOGO (OPCIONAL) =====
			if logo_path and os.path.exists(logo_path):
				try:
					img = Image.open(logo_path)
					img = img.convert("L")
					img = img.resize((384, int(img.height * 384 / img.width)))
					img = img.point(lambda x: 0 if x < 160 else 255, '1')

					data = self.escpos_logo(img)
					if data:
						win32print.WritePrinter(hPrinter, data)
				except Exception as e:
					print("Error logo:", e)

			# ===== TEXTO =====
			win32print.WritePrinter(
				hPrinter,
				texto.encode("cp437", errors="replace")
			)

			# ===== SALTOS + CORTE =====
			win32print.WritePrinter(hPrinter, b"\n\n\n")
			win32print.WritePrinter(hPrinter, b"\x1dV\x00")  # CORTE TOTAL

			win32print.EndPagePrinter(hPrinter)
			win32print.EndDocPrinter(hPrinter)

		finally:
			win32print.ClosePrinter(hPrinter)

	def abrir_cajon(self):
		import win32print
		import time

		try:
			impresora = self.obtener_impresora_configurada()
			if not impresora:
				raise Exception("No hay impresora configurada.")

			# Comando ESC/POS para abrir cajón de dinero
			comando = b'\x1B\x70\x00\x19\xFA'   # ESC p 0 25 250

			hPrinter = win32print.OpenPrinter(impresora)
			win32print.StartDocPrinter(hPrinter, 1, ("Abrir Cajón", None, "RAW"))
			win32print.StartPagePrinter(hPrinter)

			win32print.WritePrinter(hPrinter, comando)

			win32print.EndPagePrinter(hPrinter)
			win32print.EndDocPrinter(hPrinter)
			win32print.ClosePrinter(hPrinter)

			print("Cajón abierto correctamente.")

		except Exception as e:
			print(f"Error al abrir cajón: {e}")

	def aumentar_cantidad(self):
		seleccion = self.tree.selection()
		if not seleccion:
			return

		item = seleccion[0]
		vals = list(self.tree.item(item, "values"))

		cantidad = int(vals[2]) + 1
		precio_unit = float(vals[3])
		descuento_total = float(vals[5] or 0)

		# Descuento unitario actual
		descuento_unit = descuento_total / (cantidad - 1) if cantidad > 1 else 0

		# Recalcular
		subtotal_real = precio_unit * cantidad
		descuento_nuevo = descuento_unit * cantidad
		nuevo_subtotal = subtotal_real - descuento_nuevo

		vals[2] = cantidad
		vals[4] = f"{nuevo_subtotal:.2f}"
		vals[5] = f"{descuento_nuevo:.2f}"

		self.tree.item(item, values=vals,
					tags=("descuento",) if descuento_nuevo > 0 else ())

		self.actualizar_totales()

	def reducir_cantidad(self):
		seleccion = self.tree.selection()
		if not seleccion:
			return

		item = seleccion[0]
		vals = list(self.tree.item(item, "values"))

		cantidad = int(vals[2])
		precio_unit = float(vals[3])
		descuento_total = float(vals[5] or 0)

		# 🔴 SI SOLO HAY 1, ELIMINAR DEL CARRITO
		if cantidad == 1:
			self.tree.delete(item)
			self.actualizar_totales()
			return

		# ===== SI HAY MÁS DE 1, REDUCIR =====
		descuento_unit = descuento_total / cantidad if cantidad > 0 else 0
		cantidad -= 1

		subtotal_real = precio_unit * cantidad
		descuento_nuevo = descuento_unit * cantidad
		nuevo_subtotal = subtotal_real - descuento_nuevo

		vals[2] = cantidad
		vals[4] = f"{nuevo_subtotal:.2f}"
		vals[5] = f"{descuento_nuevo:.2f}"

		self.tree.item(
			item,
			values=vals,
			tags=("descuento",) if descuento_nuevo > 0 else ()
		)

		self.actualizar_totales()

	def reimprimir_ticket_por_id(self, id_venta):
		import sqlite3
		from tkinter import messagebox

		try:
			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()

			# --- Obtener venta ---
			cur.execute("""
				SELECT fecha, total, recibido, cambio
				FROM ventas
				WHERE id_venta = ?
			""", (id_venta,))
			venta = cur.fetchone()

			if not venta:
				messagebox.showwarning("No encontrado", f"No existe la venta #{id_venta}.")
				conn.close()
				return

			fecha, total_venta, recibido, cambio = venta

			# --- Obtener productos ---
			cur.execute("""
				SELECT p.nombre_producto, d.cantidad, d.precio_unitario, d.subtotal, COALESCE(d.descuento, 0)
				FROM ventas_detalle d
				LEFT JOIN productos p ON p.id_producto = d.id_producto
				WHERE d.id_venta = ?
			""", (id_venta,))
			detalles = cur.fetchall()

			# --- Obtener pagos REALES ---
			cur.execute("""
				SELECT metodo, monto
				FROM ventas_pagos
				WHERE id_venta = ?
			""", (id_venta,))
			pagos = cur.fetchall()

			conn.close()

			# --- Construir datos para generar_ticket ---
			datos_venta = {
				"id_venta": id_venta,
				"fecha": fecha,
				"productos": detalles,
				"total_productos": sum(d[1] for d in detalles),
				"total_venta": total_venta,
				"pagos": pagos,  # ✅ sin modificar
				"recibido": recibido if recibido is not None else sum(m for _, m in pagos),
				"cambio": cambio if cambio is not None else 0,
			}

			# --- Reimprimir ticket EXACTO ---
			self.generar_ticket(datos_venta)
			self.abrir_cajon()  # opcional

		except Exception as e:
			messagebox.showerror("Error", f"No se pudo reimprimir el ticket:\n{e}")

	def reimprimir_ultimo_ticket(self):
		import sqlite3, datetime
		from tkinter import messagebox

		hoy = datetime.date.today().strftime("%Y-%m-%d")
		try:
			conn = sqlite3.connect("pos.db")
			cur = conn.cursor()
			cur.execute("""
				SELECT id_venta
				FROM ventas
				WHERE fecha LIKE ?
				ORDER BY id_venta DESC
				LIMIT 1
			""", (hoy + "%",))
			fila = cur.fetchone()
			conn.close()

			if not fila:
				messagebox.showwarning("Sin ventas", "No hay ventas registradas hoy.")
				return

			self.reimprimir_ticket_por_id(fila[0])

		except Exception as e:
			messagebox.showerror("Error", f"No se pudo reimprimir el último ticket:\n{e}")

	def devolucion_simple(self):
		import sqlite3
		from tkinter import messagebox, simpledialog
		from datetime import datetime

		if not self.tree.selection():
			messagebox.showwarning("Aviso", "Selecciona un producto del carrito.")
			return

		item = self.tree.selection()[0]
		vals = list(self.tree.item(item, "values"))

		id_producto = int(vals[0])
		nombre = vals[1]
		cantidad_actual = int(vals[2])
		precio_unit = float(vals[3])

		cantidad_dev = simpledialog.askinteger(
			"Devolución",
			f"Cantidad a devolver de '{nombre}' (máx {cantidad_actual}):",
			minvalue=1,
			maxvalue=cantidad_actual
		)
		if cantidad_dev is None:
			return

		monto_devuelto = precio_unit * cantidad_dev

		if not messagebox.askyesno(
			"Confirmar devolución",
			f"Producto: {nombre}\n"
			f"Cantidad: {cantidad_dev}\n"
			f"Monto: ${monto_devuelto:.2f}\n\n¿Confirmar?"
		):
			return

		try:
			conn = sqlite3.connect(DB_PATH)
			cur = conn.cursor()

			fecha = datetime.now().strftime("%Y-%m-%d")
			hora = datetime.now().strftime("%H:%M:%S")

			# 1️⃣ REGRESAR STOCK
			cur.execute("""
				UPDATE productos
				SET stock = stock + ?
				WHERE id_producto = ?
			""", (cantidad_dev, id_producto))

			# 2️⃣ REGISTRAR DEVOLUCIÓN
			cur.execute("""
				INSERT INTO devoluciones
				(id_venta, id_producto, cantidad, monto, fecha, hora)
				VALUES (?, ?, ?, ?, ?, ?)
			""", (
				self.id_venta_actual,
				id_producto,
				cantidad_dev,
				monto_devuelto,
				fecha,
				hora
			))

			# 3️⃣ REGISTRAR SALIDA DE CAJA (AFECTA CORTE)
			cur.execute("""
				INSERT INTO caja (monto, tipo, fecha, hora)
				VALUES (?, 'salida', ?, ?)
			""", (
				monto_devuelto,
				fecha,
				hora
			))

			conn.commit()
			conn.close()

			# 4️⃣ ACTUALIZAR CARRITO
			nueva_cant = cantidad_actual - cantidad_dev

			if nueva_cant > 0:
				nuevo_subtotal = nueva_cant * precio_unit
				vals[2] = nueva_cant
				vals[4] = f"{nuevo_subtotal:.2f}"
				self.tree.item(item, values=vals)
			else:
				self.tree.delete(item)

			self.actualizar_totales()

			messagebox.showinfo(
				"Devolución realizada",
				f"Se devolvieron ${monto_devuelto:.2f} al cliente."
			)

		except Exception as e:
			messagebox.showerror(
				"Error",
				f"No se pudo procesar la devolución:\n{e}"
			)

if __name__ == "__main__":
	root = tk.Tk()
	app = LoginWindow(root)  # PRIMERO EL LOGIN
	root.mainloop()




