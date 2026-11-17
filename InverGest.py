import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

meses_es = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}

class GestorDatos:
    def __init__(self):
        self.empresas = {
            "Nike": {"ticker": "NKE", "color": "#FF4500"},
            "Coca-Cola": {"ticker": "KO", "color": "#DC143C"},
            "Johnson & Johnson": {"ticker": "JNJ", "color": "#006400"},
            "PepsiCo": {"ticker": "PEP", "color": "#1E90FF"},
            "Apple": {"ticker": "AAPL", "color": "#555555"},
            "Microsoft": {"ticker": "MSFT", "color": "#00A4EF"},
            "Visa": {"ticker": "V", "color": "#1A237E"}
        }
        self.historial_operaciones = []
        self.empresa_seleccionada = "Nike"
        self.saldo_disponible = 50000000
        self.saldo_gastado = 0
        self.ganancias_acumuladas = 0

    def obtener_lista_empresas(self):
        return list(self.empresas.keys())

    def obtener_datos_historicos(self, nombre_empresa):
        ticker = self.empresas[nombre_empresa]["ticker"]
        try:
            activo = yf.Ticker(ticker)
            historico = activo.history(period="1y", interval="1mo")
            return historico, self.empresas[nombre_empresa]["color"]
        except Exception as e:
            print(f"Error obteniendo datos: {e}")
            return pd.DataFrame(), "#00f5d4"

    def registrar_operacion(self, tipo, nombre, cantidad, precio, comision):
        valor_total = cantidad * precio + comision
        if tipo == "Compra" and valor_total > self.saldo_disponible:
            return False, "Saldo insuficiente"
        if tipo == "Compra":
            self.saldo_disponible -= int(valor_total)
            self.saldo_gastado += int(valor_total)
        else:
            self.saldo_disponible += int(cantidad * precio - comision)
            self.saldo_gastado -= int(cantidad * precio)
            ganancia_venta = self.calcular_ganancia_venta(nombre, cantidad, precio, comision)
            self.ganancias_acumuladas += ganancia_venta

        self.historial_operaciones.append({
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tipo": tipo,
            "empresa": nombre,
            "cantidad": cantidad,
            "precio_unitario": precio,
            "comision": comision,
            "valor_total": round(valor_total, 2)
        })
        return True, "Operacion registrada con exito"

    def calcular_ganancia_venta(self, empresa, cantidad, precio_venta, comision):
        total_invertido = 0
        cantidad_disponible = 0
        for op in self.historial_operaciones:
            if op["tipo"] == "Compra" and op["empresa"] == empresa:
                total_invertido += op["cantidad"] * op["precio_unitario"]
                cantidad_disponible += op["cantidad"]
        if cantidad_disponible > 0:
            precio_promedio = total_invertido / cantidad_disponible
        else:
            precio_promedio = precio_venta
        ingresos = cantidad * precio_venta
        costo = cantidad * precio_promedio
        return ingresos - costo - comision

    def obtener_operaciones(self):
        return self.historial_operaciones

    def obtener_saldo(self):
        return self.saldo_disponible

    def obtener_saldo_gastado(self):
        return self.saldo_gastado

    def obtener_ganancias(self):
        return self.ganancias_acumuladas

    def reiniciar_transacciones(self):
        self.historial_operaciones.clear()
        self.saldo_disponible = 50000000
        self.saldo_gastado = 0
        self.ganancias_acumuladas = 0
        return True

    def obtener_precio_actual(self, nombre_empresa):
        try:
            ticker = self.empresas[nombre_empresa]["ticker"]
            activo = yf.Ticker(ticker)
            info = activo.info
            return info.get('currentPrice', 0.00)
        except:
            return 0.00

    def calcular_compras_activas(self):
        compras = []
        for op in self.historial_operaciones:
            if op["tipo"] == "Compra":
                try:
                    ticker = self.empresas[op["empresa"]]["ticker"]
                    activo = yf.Ticker(ticker)
                    info = activo.info
                    precio_actual = info.get('currentPrice', op["precio_unitario"])
                    rendimiento_div = info.get('dividendYield', 0.0) * 100
                    variacion = ((precio_actual - op["precio_unitario"]) / op["precio_unitario"]) * 100
                    valor_actual = op["cantidad"] * precio_actual
                    ganancia_perdida = valor_actual - (op["cantidad"] * op["precio_unitario"])
                    compras.append({
                        "empresa": op["empresa"],
                        "cantidad": op["cantidad"],
                        "precio_compra": op["precio_unitario"],
                        "precio_actual": round(precio_actual, 2),
                        "valor_actual": round(valor_actual, 2),
                        "ganancia_perdida": round(ganancia_perdida, 2),
                        "variacion": round(variacion, 2),
                        "rendimiento_div": round(rendimiento_div, 2)
                    })
                except Exception as e:
                    print(f"Error en compra: {e}")
        return compras

    def calcular_ventas_cerradas(self):
        ventas = []
        for i, op in enumerate(self.historial_operaciones):
            if op["tipo"] == "Venta":
                try:
                    cantidad_vendida = op["cantidad"]
                    precio_venta = op["precio_unitario"]
                    comision_venta = op["comision"]
                    precio_promedio_compra = 0
                    cantidad_restante = cantidad_vendida
                    for j in range(i-1, -1, -1):
                        if self.historial_operaciones[j]["tipo"] == "Compra" and self.historial_operaciones[j]["empresa"] == op["empresa"]:
                            compra = self.historial_operaciones[j]
                            usar = min(cantidad_restante, compra["cantidad"])
                            precio_promedio_compra += usar * compra["precio_unitario"]
                            cantidad_restante -= usar
                            if cantidad_restante <= 0:
                                break
                    if cantidad_vendida > 0:
                        precio_promedio_compra /= cantidad_vendida
                    ingresos = cantidad_vendida * precio_venta
                    costo = cantidad_vendida * precio_promedio_compra
                    ganancia_perdida = ingresos - costo - comision_venta
                    variacion = ((precio_venta - precio_promedio_compra) / precio_promedio_compra) * 100 if precio_promedio_compra > 0 else 0
                    ventas.append({
                        "empresa": op["empresa"],
                        "cantidad": cantidad_vendida,
                        "precio_compra_prom": round(precio_promedio_compra, 2),
                        "precio_venta": round(precio_venta, 2),
                        "ganancia_perdida": round(ganancia_perdida, 2),
                        "variacion": round(variacion, 2),
                        "fecha_venta": op["fecha"]
                    })
                except Exception as e:
                    print(f"Error en venta: {e}")
        return ventas
class TableroInverGest:
    def __init__(self, root):
        self.root = root
        self.root.title("CMN InverGest")
        self.root.geometry("1400x850")
        self.root.configure(bg="#0F172A")

        self.gestor = GestorDatos()
        self.inicializar_estilo()
        self.crear_interfaz()
        self.cambiar_empresa("Nike")

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
            "ganancia": "#8B5CF6"
        }
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#1E293B", foreground="#F8FAFC",
                            fieldbackground="#1E293B", rowheight=26, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", background="#334155", foreground="#00F5D4",
                            font=("Segoe UI", 9, "bold"))

    def crear_interfaz(self):
        marco_superior = tk.Frame(self.root, bg=self.colores["fondo"])
        marco_superior.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(marco_superior, text="CMN InverGest",
                font=("Segoe UI", 20, "bold"), bg=self.colores["fondo"],
                fg=self.colores["acento"]).pack(side=tk.LEFT)

        self.lbl_ganancia = tk.Label(marco_superior, text="Ganancias: $ 0 COP",
                                    font=("Segoe UI", 12, "bold"), bg=self.colores["ganancia"], fg="white",
                                    padx=15, pady=6, relief=tk.FLAT)
        self.lbl_ganancia.pack(side=tk.RIGHT, padx=(10, 0))

        self.lbl_gastado = tk.Label(marco_superior, text="Gastado: $ 0 COP",
                                   font=("Segoe UI", 12, "bold"), bg=self.colores["gastado"], fg="white",
                                   padx=15, pady=6, relief=tk.FLAT)
        self.lbl_gastado.pack(side=tk.RIGHT, padx=(10, 0))

        self.lbl_saldo = tk.Label(marco_superior, text="Disponible: $ 50,000,000 COP",
                                 font=("Segoe UI", 12, "bold"), bg=self.colores["disponible"], fg="white",
                                 padx=15, pady=6, relief=tk.FLAT)
        self.lbl_saldo.pack(side=tk.RIGHT)

        tk.Label(self.root, text="Selecciona una empresa:",
                font=("Segoe UI", 11), bg=self.colores["fondo"], fg="#94A3B8").pack(pady=(5, 8))

        self.contenedor_botones = tk.Frame(self.root, bg=self.colores["fondo"])
        self.contenedor_botones.pack(pady=(0, 15))

        self.botones_empresas = {}
        for nombre in self.gestor.obtener_lista_empresas():
            btn = tk.Button(
                self.contenedor_botones,
                text=nombre,
                command=lambda n=nombre: self.cambiar_empresa(n),
                font=("Segoe UI", 10, "bold"),
                bg=self.colores["boton"],
                fg=self.colores["texto"],
                padx=12, pady=6,
                relief=tk.FLAT,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=5)
            self.botones_empresas[nombre] = btn

        marco_principal = tk.Frame(self.root, bg=self.colores["fondo"])
        marco_principal.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        marco_izquierdo = tk.Frame(marco_principal, bg=self.colores["fondo"], width=280)
        marco_izquierdo.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        self.crear_seccion_operaciones(marco_izquierdo)
        self.crear_seccion_historial(marco_izquierdo)

        marco_central = tk.Frame(marco_principal, bg=self.colores["panel"], padx=15, pady=15)
        marco_central.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        self.titulo_grafico = tk.Label(
            marco_central,
            text="Precios mensuales - Nike",
            font=("Segoe UI", 14, "bold"),
            bg=self.colores["panel"],
            fg=self.colores["acento"]
        )
        self.titulo_grafico.pack(pady=(0, 10))

        self.figura = plt.Figure(figsize=(8, 4.5), dpi=100, facecolor="#1E293B")
        self.ejes = self.figura.add_subplot(111)
        self.ejes.set_facecolor("#1E293B")

        self.lienzo = FigureCanvasTkAgg(self.figura, master=marco_central)
        self.lienzo.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        marco_derecho = tk.Frame(marco_principal, bg=self.colores["fondo"], width=290)
        marco_derecho.pack(side=tk.RIGHT, fill=tk.Y)

        self.crear_seccion_prediccion(marco_derecho)
    def crear_seccion_operaciones(self, padre):
        marco = tk.LabelFrame(padre, text="Registrar Operacion",
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"],
                             padx=12, pady=12)
        marco.pack(fill=tk.X, pady=(0, 15))

        marco_botones = tk.Frame(marco, bg=self.colores["panel"])
        marco_botones.grid(row=0, column=0, columnspan=2, pady=6)

        self.btn_compra = tk.Button(
            marco_botones,
            text="COMPRAR",
            command=lambda: self.seleccionar_tipo_operacion("Compra"),
            bg="#10B981", fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20, pady=6,
            relief=tk.FLAT, cursor="hand2"
        )
        self.btn_compra.pack(side=tk.LEFT, padx=5)

        self.btn_venta = tk.Button(
            marco_botones,
            text="VENDER",
            command=lambda: self.seleccionar_tipo_operacion("Venta"),
            bg="#EF4444", fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20, pady=6,
            relief=tk.FLAT, cursor="hand2"
        )
        self.btn_venta.pack(side=tk.LEFT, padx=5)

        self.var_tipo = tk.StringVar(value="Compra")
        self.btn_compra.config(relief=tk.RAISED, bd=2)

        tk.Label(marco, text="Empresa:", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=4)
        self.combo_empresa = ttk.Combobox(marco, values=self.gestor.obtener_lista_empresas(), state="readonly", width=18)
        self.combo_empresa.grid(row=1, column=1, pady=4)
        self.combo_empresa.set("Nike")

        tk.Label(marco, text="Cantidad:", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_cantidad = tk.Entry(marco, bg="#334155", fg="white", insertbackground="white", width=18)
        self.entry_cantidad.grid(row=2, column=1, pady=4)

        tk.Label(marco, text="Precio ($):", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=4)
        self.entry_precio = tk.Entry(marco, bg="#334155", fg="white", insertbackground="white", width=18)
        self.entry_precio.grid(row=3, column=1, pady=4)

        tk.Label(marco, text="Comision ($):", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", pady=4)
        self.entry_comision = tk.Entry(marco, bg="#334155", fg="white", insertbackground="white", width=18)
        self.entry_comision.grid(row=4, column=1, pady=4)

        tk.Button(
            marco,
            text="Confirmar",
            command=self.registrar_operacion,
            bg="#00F5D4", fg="#000000",
            font=("Segoe UI", 10, "bold"),
            padx=10, pady=5,
            relief=tk.FLAT, cursor="hand2"
        ).grid(row=5, column=0, columnspan=2, pady=6)

        tk.Button(
            marco,
            text="Eliminar Todo",
            command=self.confirmar_reinicio,
            bg="#6B7280", fg="white",
            font=("Segoe UI", 9, "bold"),
            padx=10, pady=4,
            relief=tk.FLAT, cursor="hand2"
        ).grid(row=6, column=0, columnspan=2, pady=2)

    def seleccionar_tipo_operacion(self, tipo):
        self.var_tipo.set(tipo)
        if tipo == "Compra":
            self.btn_compra.config(relief=tk.RAISED, bd=2)
            self.btn_venta.config(relief=tk.FLAT, bd=0)
        else:
            self.btn_venta.config(relief=tk.RAISED, bd=2)
            self.btn_compra.config(relief=tk.FLAT, bd=0)

    def crear_seccion_historial(self, padre):
        marco = tk.LabelFrame(padre, text="Historial",
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"],
                             padx=8, pady=8)
        marco.pack(fill=tk.BOTH, expand=True)

        columnas = ("fecha", "tipo", "empresa", "cantidad", "total")
        self.tabla_op = ttk.Treeview(marco, columns=columnas, show="headings", height=5)

        encabezados = {
            "fecha": "Fecha", "tipo": "Tipo", "empresa": "Empresa",
            "cantidad": "Cant.", "total": "$ Total"
        }
        for col, texto in encabezados.items():
            self.tabla_op.heading(col, text=texto)
            self.tabla_op.column(col, width=50, anchor="center")

        scrollbar = ttk.Scrollbar(marco, orient=tk.VERTICAL, command=self.tabla_op.yview)
        self.tabla_op.configure(yscrollcommand=scrollbar.set)
        self.tabla_op.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def cambiar_empresa(self, nombre):
        for nom, btn in self.botones_empresas.items():
            if nom == nombre:
                btn.config(bg=self.colores["boton_activo"], fg="#000000")
            else:
                btn.config(bg=self.colores["boton"], fg=self.colores["texto"])
        self.gestor.empresa_seleccionada = nombre
        self.titulo_grafico.config(text="Precios mensuales - " + nombre)
        self.actualizar_grafico(nombre)
        precio = self.gestor.obtener_precio_actual(nombre)
        self.entry_precio.delete(0, tk.END)
        if precio > 0:
             pass
    def actualizar_grafico(self, nombre_empresa):
        df, color = self.gestor.obtener_datos_historicos(nombre_empresa)
        self.ejes.clear()
        self.ejes.set_facecolor("#1E293B")
        
        if df.empty:
            self.ejes.text(0.5, 0.5, "Sin datos disponibles",
                          ha="center", va="center", color="#94A3B8", fontsize=12,
                          transform=self.ejes.transAxes)
        else:
            df["MesNum"] = df.index.month
            df["Mes"] = df["MesNum"].map(meses_es)
            self.ejes.plot(df["Mes"], df["Close"], color=color, linewidth=3, marker='o', markersize=6)
            self.ejes.fill_between(df["Mes"], df["Close"], alpha=0.15, color=color)
            
            for i, fila in df.iterrows():
                self.ejes.text(fila["Mes"], fila["Close"] + 1.5, f"${fila['Close']:.2f}",
                              ha='center', va='bottom', color='#F8FAFC', fontsize=8,
                              bbox=dict(boxstyle="round,pad=0.2", fc="#1E293B", ec="none", alpha=0.7))
            
            self.ejes.set_ylabel("Precio USD ($)", color="#94A3B8", fontsize=10)
            self.ejes.tick_params(axis='x', colors="#94A3B8", labelsize=9)
            self.ejes.tick_params(axis='y', colors="#94A3B8", labelsize=9)
            for spine in self.ejes.spines.values():
                spine.set_color('#475569')    
            try:
                ticker = self.gestor.empresas[nombre_empresa]["ticker"]
                activo = yf.Ticker(ticker)
                info = activo.info
                rend_div = info.get('dividendYield', 0.0)
                porcentaje_div = rend_div * 100
                precio_actual = info.get('currentPrice', 0.0)
                valor_div_anual = precio_actual * rend_div
                self.ejes.set_title(f"Dividendos: {porcentaje_div:.2f}%  |  ${valor_div_anual:.2f}/acc/año", 
                                   pad=10, loc='right', fontsize=9, color="#00F5D4")
            except:
                pass
        self.figura.tight_layout()
        self.lienzo.draw()

    def registrar_operacion(self):
        tipo = self.var_tipo.get()
        empresa = self.combo_empresa.get()
        
        if not empresa:
            messagebox.showwarning("Advertencia", "Selecciona una empresa")
            return
        
        try:
            cantidad = float(self.entry_cantidad.get())
            precio = float(self.entry_precio.get())
            comision = float(self.entry_comision.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numericos validos")
            return
        
        exito, mensaje = self.gestor.registrar_operacion(tipo, empresa, cantidad, precio, comision)
        if not exito:
            messagebox.showerror("Error", mensaje)
            return
        
        messagebox.showinfo("Exito", mensaje)
        self.entry_cantidad.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.entry_comision.delete(0, tk.END)
        self.actualizar_todo()

    def actualizar_todo(self):
        self.actualizar_tabla_operaciones()
        self.actualizar_saldos()
        self.actualizar_prediccion()

    def actualizar_tabla_operaciones(self):
        for fila in self.tabla_op.get_children():
            self.tabla_op.delete(fila)
        operaciones = self.gestor.obtener_operaciones()
        for op in operaciones:
            self.tabla_op.insert("", tk.END, values=(
                op["fecha"], op["tipo"], op["empresa"],
                op["cantidad"], "$" + str(round(op["valor_total"], 2))
            ))

    def actualizar_saldos(self):
        self.lbl_saldo.config(text="Disponible: $ " + f"{self.gestor.obtener_saldo():,}" + " COP")
        self.lbl_gastado.config(text="Gastado: $ " + f"{self.gestor.obtener_saldo_gastado():,}" + " COP")
        self.lbl_ganancia.config(text="Ganancias: $ " + f"{self.gestor.obtener_ganancias():,}" + " COP")

    def confirmar_reinicio(self):
        respuesta = messagebox.askyesno("Confirmar", "Eliminar todas las transacciones? Se reiniciara el saldo a $50,000,000 COP")
        if respuesta:
            self.gestor.reiniciar_transacciones()
            self.actualizar_todo()
            messagebox.showinfo("Completado", "Todo reiniciado correctamente")
    def crear_seccion_prediccion(self, padre):
        marco = tk.LabelFrame(padre, text="Analisis y Proyeccion",
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"],
                             padx=10, pady=10)
        marco.pack(fill=tk.BOTH, expand=True)

        self.texto_prediccion = tk.Text(marco, wrap=tk.WORD, bg="#0F172A", fg="#F8FAFC",
                                       font=("Segoe UI", 9), relief=tk.FLAT, padx=8, pady=8, height=18)
        self.texto_prediccion.pack(fill=tk.BOTH, expand=True)
        self.texto_prediccion.config(state=tk.DISABLED)

        tk.Button(
            marco,
            text="Actualizar Proyeccion",
            command=self.actualizar_prediccion,
            bg="#3B82F6", fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15, pady=6,
            relief=tk.FLAT, cursor="hand2"
        ).pack(fill=tk.X, pady=(10, 0))

    def actualizar_prediccion(self):
        compras = self.gestor.calcular_compras_activas()
        ventas = self.gestor.calcular_ventas_cerradas()

        self.texto_prediccion.config(state=tk.NORMAL)
        self.texto_prediccion.delete("1.0", tk.END)

        if not compras and not ventas:
            self.texto_prediccion.insert(tk.END, "No tienes operaciones registradas aun.\n\n")
            self.texto_prediccion.insert(tk.END, "Registra una compra para empezar.\n")
        else:
            self.texto_prediccion.insert(tk.END, "=" * 50 + "\n")
            self.texto_prediccion.insert(tk.END, "COMPRAS ACTIVAS (USD $)\n")
            self.texto_prediccion.insert(tk.END, "=" * 50 + "\n\n")

            if not compras:
                self.texto_prediccion.insert(tk.END, "Sin compras activas.\n\n")
            else:
                total_invertido = 0
                total_valor_actual = 0
                total_ganancia = 0

                for c in compras:
                    total_invertido += c["cantidad"] * c["precio_compra"]
                    total_valor_actual += c["valor_actual"]
                    total_ganancia += c["ganancia_perdida"]

                    if c["ganancia_perdida"] >= 0:
                        signo_ganancia = "+"
                        estado = "GANANCIA"
                    else:
                        signo_ganancia = ""
                        estado = "PERDIDA"

                    self.texto_prediccion.insert(tk.END, c['empresa'] + "\n")
                    self.texto_prediccion.insert(tk.END, "   Cantidad:       " + str(c['cantidad']) + " acciones\n")
                    self.texto_prediccion.insert(tk.END, "   Precio compra: $" + str(c['precio_compra']) + "\n")
                    self.texto_prediccion.insert(tk.END, "   Precio actual: $" + str(c['precio_actual']) + "\n")
                    self.texto_prediccion.insert(tk.END, "   Valor actual:  $" + str(c['valor_actual']) + "\n")
                    self.texto_prediccion.insert(tk.END, "   Resultado:     " + signo_ganancia + "$" + str(c['ganancia_perdida']) + "  " + estado + "\n")
                    self.texto_prediccion.insert(tk.END, "   Variacion:     " + str(c['variacion']) + "%\n")
                    self.texto_prediccion.insert(tk.END, "   Dividendos:    " + str(c['rendimiento_div']) + "%\n")
                    self.texto_prediccion.insert(tk.END, "-" * 50 + "\n\n")

                self.texto_prediccion.insert(tk.END, "Total invertido:  $" + str(round(total_invertido, 2)) + " USD\n")
                self.texto_prediccion.insert(tk.END, "Valor actual:     $" + str(round(total_valor_actual, 2)) + " USD\n")
                if total_ganancia >= 0:
                    self.texto_prediccion.insert(tk.END, "Resultado actual: +$" + str(round(total_ganancia, 2)) + " USD\n\n")
                else:
                    self.texto_prediccion.insert(tk.END, "Resultado actual: $" + str(round(total_ganancia, 2)) + " USD\n\n")

            self.texto_prediccion.insert(tk.END, "=" * 50 + "\n")
            self.texto_prediccion.insert(tk.END, "VENTAS CERRADAS (USD $)\n")
            self.texto_prediccion.insert(tk.END, "=" * 50 + "\n\n")

            if not ventas:
                self.texto_prediccion.insert(tk.END, "Sin ventas registradas.\n")
            else:
                total_ganancia_ventas = 0
                for v in ventas:
                    total_ganancia_ventas += v["ganancia_perdida"]

                    if v["ganancia_perdida"] >= 0:
                        signo_venta = "+"
                        estado = "GANANCIA"
                    else:
                        signo_venta = ""
                        estado = "PERDIDA"

                    self.texto_prediccion.insert(tk.END, v['empresa'] + " — " + v['fecha_venta'] + "\n")
                    self.texto_prediccion.insert(tk.END, "   Cantidad vendida:   " + str(v['cantidad']) + "\n")
                    self.texto_prediccion.insert(tk.END, "   Precio compra:    $" + str(v['precio_compra_prom']) + "\n")
                    self.texto_prediccion.insert(tk.END, "   Precio venta:     $" + str(v['precio_venta']) + "\n")
                    self.texto_prediccion.insert(tk.END, "   Resultado venta:  " + signo_venta + "$" + str(v['ganancia_perdida']) + "  " + estado + "\n")
                    self.texto_prediccion.insert(tk.END, "   Variacion:        " + str(v['variacion']) + "%\n")
                    self.texto_prediccion.insert(tk.END, "-" * 50 + "\n\n")

                if total_ganancia_ventas >= 0:
                    self.texto_prediccion.insert(tk.END, "Ganancia total ventas: +$" + str(round(total_ganancia_ventas, 2)) + " USD\n")
                else:
                    self.texto_prediccion.insert(tk.END, "Ganancia total ventas: $" + str(round(total_ganancia_ventas, 2)) + " USD\n")
                self.texto_prediccion.insert(tk.END, "Ganancias acumuladas: $" + str(round(self.gestor.obtener_ganancias(), 0)) + " COP\n")

            self.texto_prediccion.insert(tk.END, "\n" + "=" * 50 + "\n")
            self.texto_prediccion.insert(tk.END, "Actualizado: " + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + "\n")

        self.texto_prediccion.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = TableroInverGest(root)
    root.mainloop()
