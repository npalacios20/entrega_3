# -*- coding: utf-8 -*-

import queue
import threading
import math
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gestor_datos import (GestorDatos, CATEGORIA_RV, CATEGORIA_RF,
                          TIPOS_RENTA_FIJA)

meses_es = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}

INTERVALO_AUTO_ACTUALIZACION_MS = 60_000


# --------------------------------------------------------------------------
# Formato de números
# --------------------------------------------------------------------------
def fmt_cop(valor, signo=False):
    texto = f"{abs(valor):,.0f}"
    if valor < 0:
        return f"-${texto} COP"
    return f"{'+' if signo and valor > 0 else ''}${texto} COP"


def fmt_usd(valor):
    return f"${valor:,.2f} USD"


def fmt_pct(valor, signo=False):
    if valor is None:
        return "N/D"
    return f"{'+' if signo and valor > 0 else ''}{valor:,.2f}%"


class TableroInverGest:
    def __init__(self, root):
        self.root = root
        self.root.title("CMN InverGest")
        self.root.geometry("1400x850")
        self.root.configure(bg="#0F172A")

        self.gestor = GestorDatos()
        self.cola = queue.Queue()
        self._token_grafico = 0
        self._token_resumen = 0

        self.inicializar_estilo()
        self.crear_interfaz()
        self.cambiar_empresa("Nike")
        self.actualizar_formulario()
        self.actualizar_todo()
        self._cargar_trm()

        self.root.after(100, self._procesar_cola)
        self.root.after(INTERVALO_AUTO_ACTUALIZACION_MS, self._auto_actualizar)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

    # ======================================================================
    # Utilidades: hilos, estilo
    # ======================================================================
    def ejecutar_async(self, funcion, callback):
        """Ejecuta 'funcion' en un hilo y llama 'callback(resultado)' en el hilo de Tk."""
        def trabajo():
            try:
                resultado = funcion()
            except Exception as e:  # se entrega al callback
                resultado = e
            self.cola.put((callback, resultado))
        threading.Thread(target=trabajo, daemon=True).start()

    def _procesar_cola(self):
        try:
            while True:
                callback, resultado = self.cola.get_nowait()
                try:
                    callback(resultado)
                except Exception as e:
                    print(f"Error en callback: {e}")
        except queue.Empty:
            pass
        self.root.after(100, self._procesar_cola)

    def _auto_actualizar(self):
        self.actualizar_analisis()
        self.root.after(INTERVALO_AUTO_ACTUALIZACION_MS, self._auto_actualizar)

    def cerrar(self):
        self.root.destroy()

    def inicializar_estilo(self):
        self.colores = {
            "fondo": "#0F172A",
            "panel": "#1E293B",
            "acento": "#00F5D4",
            "texto": "#F8FAFC",
            "boton": "#334155",
            "boton_activo": "#00F5D4",
            "borde": "#475569",
            "disponible": "#10B981",
            "gastado": "#F59E0B",
            "ganancia": "#8B5CF6",
            "positivo": "#10B981",
            "negativo": "#EF4444",
            "gris": "#94A3B8",
        }
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#1E293B", foreground="#F8FAFC",
                             fieldbackground="#1E293B", rowheight=26, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", background="#334155", foreground="#00F5D4",
                             font=("Segoe UI", 9, "bold"))
        self.style.configure("TNotebook", background=self.colores["fondo"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.colores["boton"],
                             foreground=self.colores["texto"], padding=(16, 7),
                             font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab",
                       background=[("selected", self.colores["acento"])],
                       foreground=[("selected", "#000000")])
        self.style.configure("TCombobox", fieldbackground="#334155", background="#334155",
                             foreground="white", arrowcolor="white")
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", "#334155"), ("!readonly", "#334155")],
                       foreground=[("readonly", "white"), ("!readonly", "white")])
        self.root.option_add("*TCombobox*Listbox.background", "#334155")
        self.root.option_add("*TCombobox*Listbox.foreground", "white")

    # ======================================================================
    # Construcción de la interfaz
    # ======================================================================
    def crear_interfaz(self):
        marco_superior = tk.Frame(self.root, bg=self.colores["fondo"])
        marco_superior.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(marco_superior, text="CMN InverGest",
                 font=("Segoe UI", 20, "bold"), bg=self.colores["fondo"],
                 fg=self.colores["acento"]).pack(side=tk.LEFT)

        self.lbl_ganancia = tk.Label(marco_superior, text="Ganancias realizadas: $ 0 COP",
                                     font=("Segoe UI", 11, "bold"), bg=self.colores["ganancia"],
                                     fg="white", padx=12, pady=6, relief=tk.FLAT)
        self.lbl_ganancia.pack(side=tk.RIGHT, padx=(10, 0))

        self.lbl_gastado = tk.Label(marco_superior, text="Invertido: $ 0 COP",
                                    font=("Segoe UI", 11, "bold"), bg=self.colores["gastado"],
                                    fg="white", padx=12, pady=6, relief=tk.FLAT)
        self.lbl_gastado.pack(side=tk.RIGHT, padx=(10, 0))

        self.lbl_saldo = tk.Label(marco_superior, text="Disponible: $ 50,000,000 COP",
                                  font=("Segoe UI", 11, "bold"), bg=self.colores["disponible"],
                                  fg="white", padx=12, pady=6, relief=tk.FLAT)
        self.lbl_saldo.pack(side=tk.RIGHT, padx=(10, 0))

        self.lbl_trm = tk.Label(marco_superior, text="TRM: consultando...",
                                font=("Segoe UI", 10), bg=self.colores["panel"],
                                fg=self.colores["gris"], padx=10, pady=6)
        self.lbl_trm.pack(side=tk.RIGHT)

        marco_principal = tk.Frame(self.root, bg=self.colores["fondo"])
        marco_principal.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        marco_izquierdo = tk.Frame(marco_principal, bg=self.colores["fondo"])
        marco_izquierdo.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        self.crear_seccion_operaciones(marco_izquierdo)
        self.crear_seccion_historial(marco_izquierdo)

        marco_derecho = tk.Frame(marco_principal, bg=self.colores["fondo"])
        marco_derecho.pack(side=tk.RIGHT, fill=tk.Y)
        self.crear_seccion_prediccion(marco_derecho)

        marco_central = tk.Frame(marco_principal, bg=self.colores["fondo"])
        marco_central.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        self.notebook = ttk.Notebook(marco_central)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        tab_mercado = tk.Frame(self.notebook, bg=self.colores["panel"], padx=15, pady=15)
        tab_portafolio = tk.Frame(self.notebook, bg=self.colores["panel"], padx=15, pady=15)
        tab_posiciones = tk.Frame(self.notebook, bg=self.colores["panel"], padx=15, pady=15)
        self.notebook.add(tab_mercado, text="Mercado")
        self.notebook.add(tab_portafolio, text="Portafolio")
        self.notebook.add(tab_posiciones, text="Posiciones")

        self.crear_tab_mercado(tab_mercado)
        self.crear_tab_portafolio(tab_portafolio)
        self.crear_tab_posiciones(tab_posiciones)

    # ---------------- Formulario de operaciones ----------------
    def crear_seccion_operaciones(self, padre):
        c = self.colores
        marco = tk.LabelFrame(padre, text="Registrar Operación",
                              font=("Segoe UI", 11, "bold"),
                              bg=c["panel"], fg=c["acento"], padx=12, pady=10)
        marco.pack(fill=tk.X, pady=(0, 12))

        def etiqueta(texto):
            return tk.Label(marco, text=texto, bg=c["panel"], fg=c["texto"],
                            font=("Segoe UI", 9), anchor="w")

        def entrada():
            return tk.Entry(marco, bg="#334155", fg="white", insertbackground="white",
                            width=20, relief=tk.FLAT)

        # Fila 0: comprar / vender
        marco_botones = tk.Frame(marco, bg=c["panel"])
        marco_botones.grid(row=0, column=0, columnspan=3, pady=6)
        self.btn_compra = tk.Button(
            marco_botones, text="COMPRAR",
            command=lambda: self.seleccionar_tipo_operacion("Compra"),
            bg="#10B981", fg="white", font=("Segoe UI", 10, "bold"),
            padx=18, pady=6, relief=tk.FLAT, cursor="hand2")
        self.btn_compra.pack(side=tk.LEFT, padx=5)
        self.btn_venta = tk.Button(
            marco_botones, text="VENDER",
            command=lambda: self.seleccionar_tipo_operacion("Venta"),
            bg="#EF4444", fg="white", font=("Segoe UI", 10, "bold"),
            padx=18, pady=6, relief=tk.FLAT, cursor="hand2")
        self.btn_venta.pack(side=tk.LEFT, padx=5)
        self.var_tipo = tk.StringVar(value="Compra")
        self.btn_compra.config(relief=tk.RAISED, bd=2)

        # Fila 1: categoría
        etiqueta("Categoría:").grid(row=1, column=0, sticky="w", pady=3)
        self.combo_categoria = ttk.Combobox(marco, values=[CATEGORIA_RV, CATEGORIA_RF],
                                            state="readonly", width=18)
        self.combo_categoria.grid(row=1, column=1, pady=3, columnspan=2, sticky="w")
        self.combo_categoria.set(CATEGORIA_RV)
        self.combo_categoria.bind("<<ComboboxSelected>>", lambda e: self.actualizar_formulario())

        # Fila 2: tipo de renta fija
        lbl_subtipo = etiqueta("Tipo:")
        lbl_subtipo.grid(row=2, column=0, sticky="w", pady=3)
        self.combo_subtipo = ttk.Combobox(marco, values=TIPOS_RENTA_FIJA,
                                          state="readonly", width=18)
        self.combo_subtipo.grid(row=2, column=1, pady=3, columnspan=2, sticky="w")
        self.combo_subtipo.set(TIPOS_RENTA_FIJA[0])

        # Fila 3: activo (empresa o nombre del título)
        self.lbl_activo = etiqueta("Empresa:")
        self.lbl_activo.grid(row=3, column=0, sticky="w", pady=3)
        self.combo_empresa = ttk.Combobox(marco, values=self.gestor.obtener_lista_empresas(),
                                          state="readonly", width=18)
        self.combo_empresa.grid(row=3, column=1, pady=3, columnspan=2, sticky="w")
        self.combo_empresa.set("Nike")
        self.combo_nombre = ttk.Combobox(marco, values=[], width=18)
        self.combo_nombre.grid(row=3, column=1, pady=3, columnspan=2, sticky="w")

        # Fila 4: fecha
        etiqueta("Fecha (DD/MM/AAAA):").grid(row=4, column=0, sticky="w", pady=3)
        self.entry_fecha = entrada()
        self.entry_fecha.grid(row=4, column=1, pady=3, columnspan=2, sticky="w")
        self.entry_fecha.insert(0, datetime.now().strftime("%d/%m/%Y"))

        # Fila 5: cantidad
        self.lbl_cantidad = etiqueta("Cantidad:")
        self.lbl_cantidad.grid(row=5, column=0, sticky="w", pady=3)
        self.entry_cantidad = entrada()
        self.entry_cantidad.grid(row=5, column=1, pady=3, columnspan=2, sticky="w")

        # Fila 6: precio
        self.lbl_precio = etiqueta("Precio (USD):")
        self.lbl_precio.grid(row=6, column=0, sticky="w", pady=3)
        self.entry_precio = tk.Entry(marco, bg="#334155", fg="white", insertbackground="white",
                                     width=16, relief=tk.FLAT)
        self.entry_precio.grid(row=6, column=1, pady=3, sticky="w")
        self.btn_precio_mercado = tk.Button(
            marco, text="↻", command=self.usar_precio_actual, bg="#3B82F6", fg="white",
            font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2", width=3)
        self.btn_precio_mercado.grid(row=6, column=2, padx=(4, 0), sticky="w")
        self.lbl_cierre_info = tk.Label(marco, text="Se consulta el cierre histórico según la fecha.",
                                        bg=c["panel"], fg=c["gris"], font=("Segoe UI", 8))
        self.lbl_cierre_info.grid(row=13, column=0, columnspan=3, sticky="w", pady=(2, 0))

        # Fila 7: comisión
        self.lbl_comision = etiqueta("Comisión (USD):")
        self.lbl_comision.grid(row=7, column=0, sticky="w", pady=3)
        self.entry_comision = entrada()
        self.entry_comision.grid(row=7, column=1, pady=3, columnspan=2, sticky="w")

        # Fila 8: TRM (solo acciones)
        lbl_trm_f = etiqueta("TRM histórica (COP/USD):")
        lbl_trm_f.grid(row=8, column=0, sticky="w", pady=3)
        self.entry_trm = entrada()
        self.entry_trm.grid(row=8, column=1, pady=3, columnspan=2, sticky="w")

        # Fila 9: tasa (solo renta fija, compras)
        lbl_tasa = etiqueta("Tasa E.A. (%):")
        lbl_tasa.grid(row=9, column=0, sticky="w", pady=3)
        self.entry_tasa = entrada()
        self.entry_tasa.grid(row=9, column=1, pady=3, columnspan=2, sticky="w")

        # Fila 10: vencimiento (solo renta fija, compras)
        lbl_venc = etiqueta("Vence (DD/MM/AAAA):")
        lbl_venc.grid(row=10, column=0, sticky="w", pady=3)
        self.entry_vencimiento = entrada()
        self.entry_vencimiento.grid(row=10, column=1, pady=3, columnspan=2, sticky="w")

        self.btn_confirmar = tk.Button(marco, text="Confirmar", command=self.registrar_operacion,
                                       bg="#00F5D4", fg="#000000",
                                       font=("Segoe UI", 10, "bold"), padx=10, pady=5,
                                       relief=tk.FLAT, cursor="hand2")
        self.btn_confirmar.grid(row=11, column=0, columnspan=3, pady=(8, 4))

        tk.Button(marco, text="Eliminar Todo", command=self.confirmar_reinicio,
                  bg="#6B7280", fg="white", font=("Segoe UI", 9, "bold"),
                  padx=10, pady=4, relief=tk.FLAT, cursor="hand2"
                  ).grid(row=12, column=0, columnspan=3, pady=2)

        tk.Button(marco, text="Registrar cupón / interés RF",
                  command=self.registrar_pago_renta_fija,
                  bg="#2563EB", fg="white", font=("Segoe UI", 9, "bold"),
                  padx=8, pady=4, relief=tk.FLAT, cursor="hand2"
                  ).grid(row=14, column=0, columnspan=3, pady=3)

        # Grupos de widgets que se muestran/ocultan según categoría y tipo
        self.filas = {
            "subtipo": [lbl_subtipo, self.combo_subtipo],
            "empresa": [self.combo_empresa],
            "nombre": [self.combo_nombre],
            "trm": [lbl_trm_f, self.entry_trm],
            "tasa": [lbl_tasa, self.entry_tasa],
            "venc": [lbl_venc, self.entry_vencimiento],
            "btn_precio": [self.btn_precio_mercado],
            "cierre_info": [self.lbl_cierre_info],
        }

    def _mostrar(self, clave, visible):
        for w in self.filas[clave]:
            if visible:
                w.grid()
            else:
                w.grid_remove()

    def actualizar_formulario(self):
        """Ajusta los campos visibles según categoría (RV/RF) y tipo (compra/venta)."""
        rv = self.combo_categoria.get() == CATEGORIA_RV
        compra = self.var_tipo.get() == "Compra"

        self._mostrar("subtipo", (not rv) and compra)
        self._mostrar("empresa", rv)
        self._mostrar("nombre", not rv)
        self._mostrar("trm", rv)
        self._mostrar("tasa", (not rv) and compra)
        self._mostrar("venc", (not rv) and compra)
        self._mostrar("btn_precio", False)
        self._mostrar("cierre_info", True)

        if rv:
            self.lbl_cierre_info.config(
                text="Precio y TRM: ingrésalos si los conoces; si los dejas vacíos se consultan históricos."
            )
            self.lbl_activo.config(text="Empresa:")
            self.lbl_cantidad.config(text="Cantidad (acciones):")
            self.lbl_precio.config(text="Precio unitario (USD):")
            self.lbl_comision.config(text="Comisión (USD):")
            self.entry_precio.config(state="normal")
        else:
            self.lbl_cierre_info.config(
                text="Devolución de capital: registra una venta; deja el valor vacío para calcular capital + interés."
            )
            self.entry_precio.config(state="normal")
            self.lbl_activo.config(text="Emisor / Nombre:")
            self.lbl_cantidad.config(text="Cantidad (títulos):")
            self.lbl_precio.config(text="Valor unit. (COP):" if compra else "Valor venta (COP):")
            self.lbl_comision.config(text="Comisión (COP):")
            self.combo_nombre.config(values=self.gestor.obtener_nombres_renta_fija())

    def seleccionar_tipo_operacion(self, tipo):
        self.var_tipo.set(tipo)
        if tipo == "Compra":
            self.btn_compra.config(relief=tk.RAISED, bd=2)
            self.btn_venta.config(relief=tk.FLAT, bd=0)
        else:
            self.btn_venta.config(relief=tk.RAISED, bd=2)
            self.btn_compra.config(relief=tk.FLAT, bd=0)
        self.actualizar_formulario()

    # ---------------- Historial ----------------
    def crear_seccion_historial(self, padre):
        c = self.colores
        marco = tk.LabelFrame(padre, text="Historial", font=("Segoe UI", 11, "bold"),
                              bg=c["panel"], fg=c["acento"], padx=8, pady=8)
        marco.pack(fill=tk.BOTH, expand=True)

        columnas = ("fecha", "tipo", "activo", "cantidad", "total")
        self.tabla_op = ttk.Treeview(marco, columns=columnas, show="headings", height=5)
        encabezados = {"fecha": ("Fecha", 72), "tipo": ("Tipo", 52), "activo": ("Activo", 85),
                       "cantidad": ("Cant.", 45), "total": ("Total", 95)}
        for col, (texto, ancho) in encabezados.items():
            self.tabla_op.heading(col, text=texto)
            self.tabla_op.column(col, width=ancho, anchor="center")
        self.tabla_op.tag_configure("Compra", foreground=c["positivo"])
        self.tabla_op.tag_configure("Venta", foreground=c["negativo"])
        self.tabla_op.tag_configure("Ingreso RF", foreground=c["positivo"])

        scrollbar = ttk.Scrollbar(marco, orient=tk.VERTICAL, command=self.tabla_op.yview)
        self.tabla_op.configure(yscrollcommand=scrollbar.set)
        self.tabla_op.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ---------------- Pestaña Mercado ----------------
    def crear_tab_mercado(self, tab):
        c = self.colores
        contenedor = tk.Frame(tab, bg=c["panel"])
        contenedor.pack(fill=tk.X, pady=(0, 8))

        tk.Label(contenedor, text="Selecciona una empresa:", font=("Segoe UI", 10),
                 bg=c["panel"], fg=c["gris"]).grid(row=0, column=0, columnspan=4, pady=(0, 6))

        self.botones_empresas = {}
        for i, nombre in enumerate(self.gestor.obtener_lista_empresas()):
            btn = tk.Button(contenedor, text=nombre,
                            command=lambda n=nombre: self.cambiar_empresa(n),
                            font=("Segoe UI", 9, "bold"), bg=c["boton"], fg=c["texto"],
                            padx=8, pady=5, relief=tk.FLAT, cursor="hand2")
            btn.grid(row=1 + i // 4, column=i % 4, padx=4, pady=3, sticky="ew")
            self.botones_empresas[nombre] = btn
        for col in range(4):
            contenedor.columnconfigure(col, weight=1)

        self.titulo_grafico = tk.Label(tab, text="Precios mensuales - Nike",
                                       font=("Segoe UI", 14, "bold"),
                                       bg=c["panel"], fg=c["acento"])
        self.titulo_grafico.pack(pady=(0, 6))

        self.figura = Figure(figsize=(8, 4.5), dpi=100, facecolor="#1E293B")
        self.ejes = self.figura.add_subplot(111)
        self.ejes.set_facecolor("#1E293B")
        self.lienzo = FigureCanvasTkAgg(self.figura, master=tab)
        self.lienzo.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ---------------- Pestaña Portafolio ----------------
    def crear_tab_portafolio(self, tab):
        c = self.colores
        marco_tarjetas = tk.Frame(tab, bg=c["panel"])
        marco_tarjetas.pack(fill=tk.X)

        items = [
            ("invertido", "Valor total invertido"),
            ("valor_actual", "Valor actual del portafolio"),
            ("rent_acum", "Rentabilidad acumulada"),
            ("rent_ea", "Rentabilidad efectiva anual (E.A.)"),
            ("dividendos", "Dividendos recibidos"),
            ("intereses", "Intereses acumulados (RF)"),
            ("realizadas", "Ganancias realizadas"),
            ("patrimonio", "Patrimonio total"),
        ]
        self.tarjetas = {}
        for idx, (clave, titulo) in enumerate(items):
            fila, col = divmod(idx, 4)
            marco_tarjetas.columnconfigure(col, weight=1, uniform="tarjeta")
            tarjeta = tk.Frame(marco_tarjetas, bg=c["boton"], padx=10, pady=8)
            tarjeta.grid(row=fila, column=col, padx=4, pady=4, sticky="nsew")
            tk.Label(tarjeta, text=titulo, font=("Segoe UI", 8), bg=c["boton"],
                     fg=c["gris"], wraplength=150, justify="left").pack(anchor="w")
            valor = tk.Label(tarjeta, text="—", font=("Segoe UI", 11, "bold"),
                             bg=c["boton"], fg=c["texto"])
            valor.pack(anchor="w", pady=(4, 0))
            self.tarjetas[clave] = valor

        tk.Label(tab, text="Distribución del portafolio", font=("Segoe UI", 12, "bold"),
                 bg=c["panel"], fg=c["acento"]).pack(pady=(12, 0))

        self.figura_pie = Figure(figsize=(6, 3.2), dpi=100, facecolor="#1E293B")
        self.ejes_pie = self.figura_pie.add_subplot(111)
        self.lienzo_pie = FigureCanvasTkAgg(self.figura_pie, master=tab)
        self.lienzo_pie.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.lbl_distribucion = tk.Label(tab, text="Renta variable: 0.00%   |   Renta fija: 0.00%",
                                         font=("Segoe UI", 10, "bold"), bg=c["panel"],
                                         fg=c["texto"])
        self.lbl_distribucion.pack(pady=(4, 0))

        self.lbl_nota_ea = tk.Label(tab, text="", font=("Segoe UI", 8), bg=c["panel"],
                                    fg=c["gris"], wraplength=650, justify="center")
        self.lbl_nota_ea.pack(pady=(4, 0))

        self.mostrar_distribucion(None)

    # ---------------- Pestaña Posiciones ----------------
    def crear_tab_posiciones(self, tab):
        c = self.colores
        tk.Label(tab, text="Posiciones abiertas (valores en COP)", font=("Segoe UI", 12, "bold"),
                 bg=c["panel"], fg=c["acento"]).pack(pady=(0, 8))

        marco = tk.Frame(tab, bg=c["panel"])
        marco.pack(fill=tk.BOTH, expand=True)

        columnas = ("tipo", "activo", "cantidad", "costo", "valor", "resultado",
                    "rent", "rend", "detalle")
        self.tabla_pos = ttk.Treeview(marco, columns=columnas, show="headings")
        config = {
            "tipo": ("Tipo", 60), "activo": ("Activo", 100), "cantidad": ("Cant.", 50),
            "costo": ("Invertido", 90), "valor": ("Valor actual", 90),
            "resultado": ("Resultado", 85), "rent": ("Rent. %", 60),
            "rend": ("Div./Interés", 85), "detalle": ("Detalle", 150),
        }
        for col, (texto, ancho) in config.items():
            self.tabla_pos.heading(col, text=texto)
            self.tabla_pos.column(col, width=ancho, anchor="center")
        self.tabla_pos.tag_configure("ganancia", foreground=c["positivo"])
        self.tabla_pos.tag_configure("perdida", foreground=c["negativo"])

        scroll = ttk.Scrollbar(marco, orient=tk.VERTICAL, command=self.tabla_pos.yview)
        self.tabla_pos.configure(yscrollcommand=scroll.set)
        self.tabla_pos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ---------------- Panel de análisis ----------------
    def crear_seccion_prediccion(self, padre):
        c = self.colores
        marco = tk.LabelFrame(padre, text="Análisis y Proyección", font=("Segoe UI", 11, "bold"),
                              bg=c["panel"], fg=c["acento"], padx=10, pady=10)
        marco.pack(fill=tk.BOTH, expand=True)

        contenedor = tk.Frame(marco, bg=c["panel"])
        contenedor.pack(fill=tk.BOTH, expand=True)
        self.texto_prediccion = tk.Text(contenedor, wrap=tk.WORD, bg="#0F172A", fg="#F8FAFC",
                                        font=("Segoe UI", 9), relief=tk.FLAT, padx=8, pady=8,
                                        height=18, width=42)
        scroll = ttk.Scrollbar(contenedor, orient=tk.VERTICAL, command=self.texto_prediccion.yview)
        self.texto_prediccion.configure(yscrollcommand=scroll.set)
        self.texto_prediccion.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.texto_prediccion.tag_configure("titulo", foreground=c["acento"],
                                            font=("Segoe UI", 9, "bold"))
        self.texto_prediccion.tag_configure("negrita", font=("Segoe UI", 9, "bold"))
        self.texto_prediccion.tag_configure("pos", foreground=c["positivo"])
        self.texto_prediccion.tag_configure("neg", foreground=c["negativo"])
        self.texto_prediccion.tag_configure("gris", foreground=c["gris"])
        self.texto_prediccion.config(state=tk.DISABLED)

        tk.Button(marco, text="Actualizar Proyección", command=self.actualizar_analisis,
                  bg="#3B82F6", fg="white", font=("Segoe UI", 10, "bold"),
                  padx=15, pady=6, relief=tk.FLAT, cursor="hand2").pack(fill=tk.X, pady=(10, 0))
        tk.Label(marco, text="Se actualiza automáticamente cada 60 s", font=("Segoe UI", 8),
                 bg=c["panel"], fg=c["gris"]).pack(pady=(4, 0))

    # ======================================================================
    # Mercado: selección de empresa y gráfico
    # ======================================================================
    def cambiar_empresa(self, nombre):
        for nom, btn in self.botones_empresas.items():
            if nom == nombre:
                btn.config(bg=self.colores["boton_activo"], fg="#000000")
            else:
                btn.config(bg=self.colores["boton"], fg=self.colores["texto"])
        self.gestor.empresa_seleccionada = nombre
        self.combo_empresa.set(nombre)
        self.titulo_grafico.config(text="Precios mensuales - " + nombre)
        self.actualizar_grafico(nombre)

    def actualizar_grafico(self, nombre_empresa):
        self._token_grafico += 1
        token = self._token_grafico

        self.ejes.clear()
        self.ejes.set_facecolor("#1E293B")
        self.ejes.text(0.5, 0.5, "Cargando datos...", ha="center", va="center",
                       color="#94A3B8", fontsize=12, transform=self.ejes.transAxes)
        self.lienzo.draw_idle()

        def tarea():
            df, color = self.gestor.obtener_datos_historicos(nombre_empresa)
            try:
                dividendo = self.gestor.obtener_resumen_dividendo(nombre_empresa)
            except Exception:
                dividendo = None
            return nombre_empresa, df, color, dividendo

        def listo(resultado):
            if token != self._token_grafico:
                return  # el usuario ya cambió de empresa
            if isinstance(resultado, Exception):
                print(f"Error al cargar gráfico: {resultado}")
                return
            self._dibujar_grafico(*resultado)

        self.ejecutar_async(tarea, listo)

    def _dibujar_grafico(self, nombre_empresa, df, color, dividendo):
        self.ejes.clear()
        self.ejes.set_facecolor("#1E293B")

        if df is None or df.empty:
            self.ejes.text(0.5, 0.5, "Sin datos disponibles", ha="center", va="center",
                           color="#94A3B8", fontsize=12, transform=self.ejes.transAxes)
        else:
            df = df.copy()
            etiquetas = [f"{meses_es[d.month]} {str(d.year)[2:]}" for d in df.index]
            posiciones = list(range(len(df)))
            cierres = df["Close"].tolist()

            self.ejes.plot(posiciones, cierres, color=color, linewidth=3, marker="o", markersize=6)
            self.ejes.fill_between(posiciones, cierres, alpha=0.15, color=color)
            for x, cierre in zip(posiciones, cierres):
                self.ejes.annotate(f"${cierre:.2f}", (x, cierre), xytext=(0, 8),
                                   textcoords="offset points", ha="center", va="bottom",
                                   color="#F8FAFC", fontsize=8,
                                   bbox=dict(boxstyle="round,pad=0.2", fc="#1E293B",
                                             ec="none", alpha=0.7))
            self.ejes.set_xticks(posiciones)
            self.ejes.set_xticklabels(etiquetas)
            self.ejes.set_ylabel("Precio USD ($)", color="#94A3B8", fontsize=10)
            self.ejes.tick_params(axis="x", colors="#94A3B8", labelsize=8)
            self.ejes.tick_params(axis="y", colors="#94A3B8", labelsize=9)
            for spine in self.ejes.spines.values():
                spine.set_color("#475569")
            if dividendo:
                porcentaje, valor_anual = dividendo
                self.ejes.set_title(
                    f"Dividendos: {porcentaje:.2f}%  |  ${valor_anual:.2f}/acc/año",
                    pad=10, loc="right", fontsize=9, color="#00F5D4")
        self.figura.tight_layout()
        self.lienzo.draw()

    # ======================================================================
    # Registro de operaciones
    # ======================================================================
    @staticmethod
    def _num(entry, nombre, obligatorio=True):
        texto = entry.get().strip().replace(" ", "")
        if not texto:
            if obligatorio:
                raise ValueError(f"Ingresa un valor para: {nombre}")
            return None
        # Acepta decimal con coma o punto y separadores de miles habituales.
        if "," in texto and "." in texto:
            if texto.rfind(",") > texto.rfind("."):
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", "")
        elif "," in texto:
            texto = texto.replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            raise ValueError(f"Valor numérico inválido en: {nombre}")
        if not math.isfinite(valor):
            raise ValueError(f"El valor de {nombre} debe ser finito")
        return valor

    def registrar_operacion(self):
        tipo = self.var_tipo.get()
        categoria = self.combo_categoria.get()
        fecha = self.entry_fecha.get().strip()

        try:
            cantidad = self._num(self.entry_cantidad, "Cantidad")
            comision = self._num(self.entry_comision, "Comisión", obligatorio=False) or 0.0
            if cantidad <= 0 or comision < 0:
                raise ValueError("La cantidad debe ser mayor que cero y la comisión no puede ser negativa")

            if categoria == CATEGORIA_RV:
                nombre = self.combo_empresa.get()
                if not nombre:
                    raise ValueError("Selecciona una empresa")
                fecha_obj = self.gestor.parsear_fecha(fecha)
                if fecha_obj > datetime.now().date():
                    raise ValueError("La fecha de la operación no puede ser futura")
                precio_manual = self._num(self.entry_precio, "Precio unitario", obligatorio=False)
                if precio_manual is not None and precio_manual <= 0:
                    raise ValueError("El precio debe ser mayor que cero")
                trm_override = self._num(self.entry_trm, "TRM", obligatorio=False)
                if trm_override is not None and trm_override <= 0:
                    raise ValueError("La TRM debe ser mayor que cero")
                subtipo, tasa, vencimiento = "Acción", None, None
                self.lbl_cierre_info.config(text="Consultando datos históricos faltantes...")
                self.btn_confirmar.config(state=tk.DISABLED)

                def cierre_listo(resultado):
                    self.btn_confirmar.config(state=tk.NORMAL)
                    if isinstance(resultado, Exception):
                        self.lbl_cierre_info.config(text="No se pudieron consultar los datos históricos.")
                        messagebox.showerror("Datos históricos", str(resultado))
                        return
                    precio_final, fecha_cierre, trm_usada, fecha_trm = resultado
                    self._finalizar_registro(
                        tipo, nombre, cantidad, precio_final, comision, categoria, subtipo,
                        tasa, vencimiento, fecha, trm_usada, fecha_cierre, fecha_trm
                    )

                def consultar_datos_operacion():
                    if precio_manual is None:
                        precio_final, fecha_cierre = self.gestor.obtener_precio_cierre(nombre, fecha_obj)
                    else:
                        precio_final, fecha_cierre = precio_manual, None
                    if trm_override is None:
                        trm_historica, fecha_trm = self.gestor.obtener_trm_fecha(fecha_obj)
                    else:
                        trm_historica, fecha_trm = trm_override, None
                    return precio_final, fecha_cierre, trm_historica, fecha_trm

                self.ejecutar_async(consultar_datos_operacion, cierre_listo)
                return

            nombre = self.combo_nombre.get().strip()
            if not nombre:
                raise ValueError("Escribe el emisor o nombre del título")
            subtipo = self.combo_subtipo.get() if tipo == "Compra" else ""
            trm = None
            if tipo == "Compra":
                precio = self._num(self.entry_precio, "Valor unitario")
                tasa = self._num(self.entry_tasa, "Tasa E.A.")
                vencimiento = self.entry_vencimiento.get().strip()
                if not vencimiento:
                    raise ValueError("Ingresa la fecha de vencimiento")
            else:
                precio = self._num(self.entry_precio, "Valor de venta", obligatorio=False)
                tasa, vencimiento = None, None
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self._finalizar_registro(
            tipo, nombre, cantidad, precio, comision, categoria, subtipo,
            tasa, vencimiento, fecha, trm, None, None
        )

    def _finalizar_registro(self, tipo, nombre, cantidad, precio, comision,
                            categoria, subtipo, tasa, vencimiento, fecha, trm,
                            fecha_cierre, fecha_trm=None):
        exito, mensaje = self.gestor.registrar_operacion(
            tipo, nombre, cantidad, precio, comision,
            categoria=categoria, subtipo=subtipo, tasa=tasa,
            vencimiento=vencimiento, fecha=fecha, trm=trm,
            fecha_precio=fecha_cierre, fecha_trm=fecha_trm
        )
        if not exito:
            messagebox.showerror("Error", mensaje)
            return

        if categoria == CATEGORIA_RV:
            fecha_operacion = self.gestor.parsear_fecha(fecha)
            if fecha_cierre:
                precio_txt = (f"Precio tomado del cierre histórico: ${precio:.2f} USD "
                              f"({fecha_cierre.strftime('%d/%m/%Y')})")
                if fecha_cierre < fecha_operacion:
                    precio_txt += "\nNo hubo rueda bursátil en la fecha indicada; se tomó el último cierre anterior."
            else:
                precio_txt = f"Precio manual ingresado: ${precio:.2f} USD"
            if fecha_trm:
                trm_txt = f"TRM histórica consultada: ${trm:,.2f} COP/USD ({fecha_trm.strftime('%d/%m/%Y')})"
            elif self._num(self.entry_trm, "TRM", obligatorio=False) is not None:
                trm_txt = f"TRM manual ingresada: ${trm:,.2f} COP/USD"
            else:
                trm_txt = f"ADVERTENCIA: no se obtuvo fecha histórica de TRM; se usó respaldo ${trm:,.2f} COP/USD"
            self.lbl_cierre_info.config(text=f"{precio_txt} | {trm_txt}")
            messagebox.showinfo(
                "Operación registrada",
                f"{mensaje}.\n{precio_txt}.\n{trm_txt}.\n"
                f"Fecha contable de la operación: {fecha_operacion.strftime('%d/%m/%Y')}."
            )
        else:
            messagebox.showinfo("Éxito", mensaje)

        self.entry_precio.config(state="normal")
        for entry in (self.entry_cantidad, self.entry_precio, self.entry_comision,
                      self.entry_tasa, self.entry_vencimiento, self.entry_trm):
            entry.delete(0, tk.END)
        self.actualizar_formulario()
        self.actualizar_todo()

    def usar_precio_actual(self):
        """Compatibilidad: las operaciones de acciones usan cierre histórico, no precio en vivo."""
        messagebox.showinfo(
            "Precio de la operación",
            "El precio se consulta automáticamente usando el cierre histórico de la fecha indicada."
        )

    def _cargar_trm(self):
        def listo(trm):
            if isinstance(trm, Exception):
                return
            self.lbl_trm.config(text=f"TRM: ${trm:,.2f} COP/USD")
        self.ejecutar_async(self.gestor.obtener_trm, listo)

    def registrar_pago_renta_fija(self):
        """Registra un cupón/interés recibido de un título de renta fija."""
        nombres = self.gestor.obtener_nombres_renta_fija()
        if not nombres:
            messagebox.showwarning("Sin títulos", "Primero registra una compra de CDT, bono o TES.")
            return
        nombre = simpledialog.askstring(
            "Pago de renta fija", "Nombre exacto del título:\n" + ", ".join(nombres), parent=self.root
        )
        if nombre is None:
            return
        nombre = nombre.strip()
        if nombre not in nombres:
            messagebox.showerror("Título no encontrado", "Selecciona uno de los títulos registrados.")
            return
        monto = simpledialog.askfloat(
            "Pago de renta fija", "Valor del cupón/interés recibido (COP):",
            minvalue=0.01, parent=self.root
        )
        if monto is None:
            return
        fecha_txt = simpledialog.askstring(
            "Fecha del pago", "Fecha del pago (DD/MM/AAAA):",
            initialvalue=datetime.now().strftime("%d/%m/%Y"), parent=self.root
        )
        if fecha_txt is None:
            return
        exito, mensaje = self.gestor.registrar_pago_renta_fija(nombre, monto, fecha_txt)
        if not exito:
            messagebox.showerror("Pago no registrado", mensaje)
            return
        messagebox.showinfo("Pago registrado", mensaje)
        self.actualizar_todo()

    def confirmar_reinicio(self):
        respuesta = messagebox.askyesno(
            "Confirmar", "¿Eliminar todas las transacciones? Se reiniciará el saldo a $50,000,000 COP")
        if respuesta:
            self.gestor.reiniciar_transacciones()
            self.actualizar_formulario()
            self.actualizar_todo()
            messagebox.showinfo("Completado", "Todo reiniciado correctamente")

    # ======================================================================
    # Actualización de pantallas
    # ======================================================================
    def actualizar_todo(self):
        self.actualizar_tabla_operaciones()
        self.actualizar_saldos()
        self.actualizar_analisis()

    def actualizar_tabla_operaciones(self):
        for fila in self.tabla_op.get_children():
            self.tabla_op.delete(fila)
        for op in self.gestor.obtener_operaciones():
            cantidad_txt = f"{op['cantidad']:g}" if op["tipo"] != "Ingreso RF" else "—"
            tipo_txt = "Cupón RF" if op["tipo"] == "Ingreso RF" else op["tipo"]
            self.tabla_op.insert("", tk.END, tags=(op["tipo"],), values=(
                op["fecha_txt"], tipo_txt, op["activo"], cantidad_txt,
                f"{op['valor_total']:,.2f} {op['moneda']}"))

    def actualizar_saldos(self):
        self.lbl_saldo.config(text="Disponible: " + fmt_cop(self.gestor.obtener_saldo()))
        self.lbl_gastado.config(text="Invertido: " + fmt_cop(self.gestor.obtener_saldo_gastado()))
        self.lbl_ganancia.config(text="Ganancias realizadas: " + fmt_cop(self.gestor.obtener_ganancias()))

    def actualizar_analisis(self):
        """Recalcula el portafolio (precios en vivo) en segundo plano."""
        self._token_resumen += 1
        token = self._token_resumen
        self._texto_simple("Calculando portafolio...\n")

        def listo(resultado):
            if token != self._token_resumen:
                return
            if isinstance(resultado, Exception):
                self._texto_simple(f"Error al calcular el portafolio:\n{resultado}\n")
                return
            self.mostrar_tarjetas(resultado)
            self.mostrar_distribucion(resultado)
            self.mostrar_posiciones(resultado)
            self.mostrar_analisis_texto(resultado)
            self.actualizar_saldos()

        self.ejecutar_async(self.gestor.calcular_resumen_portafolio, listo)

    # ---------------- Pestaña Portafolio ----------------
    def _color_signo(self, valor):
        return self.colores["positivo"] if valor >= 0 else self.colores["negativo"]

    def mostrar_tarjetas(self, res):
        t = self.tarjetas
        t["invertido"].config(text=fmt_cop(res["total_invertido"]), fg=self.colores["texto"])
        t["valor_actual"].config(text=fmt_cop(res["valor_actual"]), fg=self.colores["texto"])
        t["rent_acum"].config(text=fmt_pct(res["rentabilidad_acumulada"], True),
                              fg=self._color_signo(res["rentabilidad_acumulada"]))
        ea = res["rentabilidad_ea"]
        t["rent_ea"].config(text=fmt_pct(ea, True),
                            fg=self._color_signo(ea) if ea is not None else self.colores["gris"])
        t["dividendos"].config(text=fmt_cop(res["dividendos_cop"]), fg=self.colores["texto"])
        t["intereses"].config(text=fmt_cop(res["intereses_cop"]), fg=self.colores["texto"])
        t["realizadas"].config(text=fmt_cop(res["ganancia_realizada"], True),
                               fg=self._color_signo(res["ganancia_realizada"]))
        t["patrimonio"].config(text=fmt_cop(res["patrimonio"]), fg=self.colores["texto"])

        if res["rentabilidad_ea"] is not None and res["ea_referencial"]:
            self.lbl_nota_ea.config(
                text=f"La rentabilidad E.A. es referencial: solo han pasado {res['dias']} día(s) "
                     "desde la primera operación.")
        else:
            self.lbl_nota_ea.config(
                text="La rentabilidad E.A. se calcula con flujos fechados (XIRR): compras, ventas, "
                     "dividendos y valor actual de las posiciones abiertas.")

    def mostrar_distribucion(self, res):
        c = self.colores
        self.ejes_pie.clear()
        self.ejes_pie.set_facecolor(c["panel"])

        if not res or res["valor_actual"] <= 0:
            self.ejes_pie.text(0.5, 0.5, "Sin posiciones abiertas", ha="center", va="center",
                               color="#94A3B8", fontsize=12, transform=self.ejes_pie.transAxes)
            self.ejes_pie.axis("off")
            self.lbl_distribucion.config(text="Renta variable: 0.00%   |   Renta fija: 0.00%")
        else:
            datos = [("Renta variable", res["valor_rv"], "#3B82F6"),
                     ("Renta fija", res["valor_rf"], "#10B981")]
            datos = [d for d in datos if d[1] > 0]
            self.ejes_pie.pie([d[1] for d in datos], labels=[d[0] for d in datos],
                              colors=[d[2] for d in datos], autopct="%1.1f%%", startangle=90,
                              textprops={"color": "#F8FAFC", "fontsize": 10},
                              wedgeprops={"edgecolor": "#1E293B"})
            self.ejes_pie.axis("equal")
            self.lbl_distribucion.config(
                text=f"Renta variable: {res['pct_rv']:.2f}%   |   Renta fija: {res['pct_rf']:.2f}%")
        self.figura_pie.tight_layout()
        self.lienzo_pie.draw()

    # ---------------- Pestaña Posiciones ----------------
    def mostrar_posiciones(self, res):
        for fila in self.tabla_pos.get_children():
            self.tabla_pos.delete(fila)
        for p in res["posiciones"]:
            if p["categoria"] == CATEGORIA_RV:
                rendimiento = fmt_cop(p["dividendos_cop"])
                detalle = f"Div. {p['rend_div_pct']:.2f}% anual"
                if not p["precio_en_vivo"]:
                    detalle += " (sin precio en vivo)"
            else:
                rendimiento = fmt_cop(p["interes_cop"])
                detalle = f"{p['tasa']:.2f}% E.A. · vence {p['vencimiento'].strftime('%d/%m/%Y')}"
                if p["estado"] == "Vencido":
                    detalle += " (vencido)"
            etiqueta = "ganancia" if p["resultado_cop"] >= 0 else "perdida"
            self.tabla_pos.insert("", tk.END, tags=(etiqueta,), values=(
                p["subtipo"], p["activo"], f"{p['cantidad']:g}",
                f"{p['costo_cop']:,.0f}", f"{p['valor_actual_cop']:,.0f}",
                f"{p['resultado_cop']:+,.0f}", f"{p['rentabilidad_pct']:+.2f}%",
                rendimiento.replace(" COP", ""), detalle))

    # ---------------- Panel de texto ----------------
    def _texto_simple(self, mensaje):
        self.texto_prediccion.config(state=tk.NORMAL)
        self.texto_prediccion.delete("1.0", tk.END)
        self.texto_prediccion.insert(tk.END, mensaje)
        self.texto_prediccion.config(state=tk.DISABLED)

    def _t(self, texto, tag=None):
        self.texto_prediccion.insert(tk.END, texto, tag or ())

    def _seccion(self, titulo):
        sep = "=" * 38
        self._t(sep + "\n", "gris")
        self._t(titulo + "\n", "titulo")
        self._t(sep + "\n\n", "gris")

    def _linea(self, etiqueta, valor, tag=None, ancho=20):
        self._t("   " + etiqueta.ljust(ancho))
        self._t(valor + "\n", tag)

    def mostrar_analisis_texto(self, res):
        self.texto_prediccion.config(state=tk.NORMAL)
        self.texto_prediccion.delete("1.0", tk.END)

        posiciones, ventas = res["posiciones"], res["ventas"]
        if not posiciones and not ventas:
            self._t("No tienes operaciones registradas aún.\n\n")
            self._t("Registra una compra para empezar.\n")
        else:
            self._mostrar_resumen_texto(res)
            self._mostrar_renta_variable_texto(posiciones)
            self._mostrar_renta_fija_texto(posiciones)
            self._mostrar_ventas_texto(ventas, res)
            self._t("\n" + "=" * 38 + "\n", "gris")
            self._t("Actualizado: " + res["fecha_calculo"].strftime("%d/%m/%Y %H:%M:%S") + "\n", "gris")
        self.texto_prediccion.config(state=tk.DISABLED)

    def _mostrar_resumen_texto(self, res):
        sig = lambda v: "pos" if v >= 0 else "neg"
        self._seccion("RESUMEN DEL PORTAFOLIO (COP)")
        self._linea("Total invertido:", fmt_cop(res["total_invertido"]))
        self._linea("Valor actual:", fmt_cop(res["valor_actual"]))
        self._linea("Resultado total:", fmt_cop(res["resultado_total"], True), sig(res["resultado_total"]))
        self._linea("Rent. acumulada:", fmt_pct(res["rentabilidad_acumulada"], True),
                    sig(res["rentabilidad_acumulada"]))
        ea = res["rentabilidad_ea"]
        nota = "  (referencial)" if ea is not None and res["ea_referencial"] else ""
        self._linea("Rent. E.A.:", fmt_pct(ea, True) + nota, sig(ea) if ea is not None else "gris")
        self._linea("Renta variable:", f"{res['pct_rv']:.2f}%")
        self._linea("Renta fija:", f"{res['pct_rf']:.2f}%")
        self._linea("Dividendos:", fmt_cop(res["dividendos_cop"]))
        self._linea("Cupones RF cobrados:", fmt_cop(res.get("ingresos_rf_cop", 0.0)))
        self._linea("Intereses RF pendientes:", fmt_cop(res["intereses_cop"]))
        self._linea("TRM usada:", f"${res['trm']:,.2f}")
        self._t("\n")

    def _mostrar_renta_variable_texto(self, posiciones):
        rv = [p for p in posiciones if p["categoria"] == CATEGORIA_RV]
        self._seccion("RENTA VARIABLE")
        if not rv:
            self._t("Sin acciones en cartera.\n\n")
            return
        for p in rv:
            tag = "pos" if p["resultado_cop"] >= 0 else "neg"
            estado = "GANANCIA" if p["resultado_cop"] >= 0 else "PÉRDIDA"
            self._t(p["activo"] + "\n", "negrita")
            self._linea("Cantidad:", f"{p['cantidad']:g} acciones")
            self._linea("Precio compra:", fmt_usd(p["precio_compra_prom"]))
            precio_txt = fmt_usd(p["precio_actual"]) + ("" if p["precio_en_vivo"] else " (sin conexión)")
            self._linea("Precio actual:", precio_txt)
            self._linea("Invertido:", fmt_cop(p["costo_cop"]))
            self._linea("Valor actual:", fmt_cop(p["valor_actual_cop"]))
            self._linea("Resultado:", fmt_cop(p["resultado_cop"], True) + "  " + estado, tag)
            self._linea("Variación precio:", fmt_pct(p["variacion"], True),
                        "pos" if p["variacion"] >= 0 else "neg")
            self._linea("Dividendos cobrados:", fmt_cop(p["dividendos_cop"]))
            self._linea("Rend. dividendo:", f"{p['rend_div_pct']:.2f}% anual "
                                            f"(${p['div_anual_accion']:.2f}/acc)")
            self._t("-" * 38 + "\n\n", "gris")

    def _mostrar_renta_fija_texto(self, posiciones):
        rf = [p for p in posiciones if p["categoria"] == CATEGORIA_RF]
        self._seccion("RENTA FIJA")
        if not rf:
            self._t("Sin títulos de renta fija.\n\n")
            return
        for p in rf:
            tag = "pos" if p["resultado_cop"] >= 0 else "neg"
            self._t(f"{p['activo']} ({p['subtipo']})\n", "negrita")
            self._linea("Cantidad:", f"{p['cantidad']:g} títulos")
            self._linea("Capital:", fmt_cop(p["capital_cop"]))
            self._linea("Tasa:", f"{p['tasa']:.2f}% E.A.")
            vence = p["vencimiento"].strftime("%d/%m/%Y")
            if p["estado"] == "Vencido":
                self._linea("Vencimiento:", f"{vence} (VENCIDO)", "neg")
            else:
                self._linea("Vencimiento:", f"{vence} ({p['dias_para_vencer']} días)")
            self._linea("Días transcurridos:", str(p["dias_transcurridos"]))
            self._linea("Intereses acum.:", fmt_cop(p["interes_cop"]), "pos")
            self._linea("Valor actual:", fmt_cop(p["valor_actual_cop"]))
            self._linea("Resultado:", fmt_cop(p["resultado_cop"], True), tag)
            self._t("-" * 38 + "\n\n", "gris")

    def _mostrar_ventas_texto(self, ventas, res):
        self._seccion("VENTAS CERRADAS (COP)")
        if not ventas:
            self._t("Sin ventas registradas.\n")
            return
        total = 0.0
        for v in ventas:
            total += v["ganancia_perdida"]
            tag = "pos" if v["ganancia_perdida"] >= 0 else "neg"
            estado = "GANANCIA" if v["ganancia_perdida"] >= 0 else "PÉRDIDA"
            moneda = "$" if v["moneda"] == "USD" else "$"
            sufijo = " USD" if v["moneda"] == "USD" else " COP"
            self._t(f"{v['activo']} — {v['fecha_venta']}\n", "negrita")
            self._linea("Cantidad vendida:", f"{v['cantidad']:g}")
            self._linea("Precio compra:", f"{moneda}{v['precio_compra_prom']:,.2f}{sufijo}")
            self._linea("Precio venta:", f"{moneda}{v['precio_venta']:,.2f}{sufijo}")
            self._linea("Resultado venta:", fmt_cop(v["ganancia_perdida"], True) + "  " + estado, tag)
            self._linea("Variación:", fmt_pct(v["variacion"], True), tag)
            self._t("-" * 38 + "\n\n", "gris")
        self._linea("Ganancia total ventas:", fmt_cop(total, True), "pos" if total >= 0 else "neg", ancho=23)


if __name__ == "__main__":
    root = tk.Tk()
    app = TableroInverGest(root)
    root.mainloop()
