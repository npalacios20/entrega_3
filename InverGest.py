import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

meses_es = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
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
        self.saldo_disponible = 50000000.00
    
    def obtener_lista_empresas(self):
        return list(self.empresas.keys())
    
    def obtener_datos_historicos(self, nombre_empresa):
        ticker = self.empresas[nombre_empresa]["ticker"]
        try:
            activo = yf.Ticker(ticker)
            inicio = datetime(2026, 1, 1)
            fin = datetime(2026, 12, 31)
            historico = activo.history(start=inicio, end=fin, interval="1mo")
            if historico.empty:
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
            self.saldo_disponible -= valor_total
        else:
            self.saldo_disponible += valor_total - comision
        self.historial_operaciones.append({
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tipo": tipo,
            "empresa": nombre,
            "cantidad": cantidad,
            "precio_unitario": precio,
            "comision": comision,
            "valor_total": round(valor_total, 2)
        })
        return True, "Operación registrada"
    
    def obtener_operaciones(self):
        return self.historial_operaciones
    
    def obtener_saldo(self):
        return self.saldo_disponible
    
    def calcular_prediccion(self):
        predicciones = []
        for op in self.historial_operaciones:
            if op["tipo"] == "Compra":
                try:
                    activo = yf.Ticker(self.empresas[op["empresa"]]["ticker"])
                    info = activo.info
                    precio_actual = info.get('currentPrice', op["precio_unitario"])
                    rendimiento_div = info.get('dividendYield', 0.0) * 100
                    variacion = ((precio_actual - op["precio_unitario"]) / op["precio_unitario"]) * 100
                    valor_actual = op["cantidad"] * precio_actual
                    ganancia_perdida = valor_actual - (op["cantidad"] * op["precio_unitario"])
                    predicciones.append({
                        "empresa": op["empresa"],
                        "cantidad": op["cantidad"],
                        "precio_compra": op["precio_unitario"],
                        "precio_actual": round(precio_actual, 2),
                        "valor_actual": round(valor_actual, 2),
                        "ganancia_perdida": round(ganancia_perdida, 2),
                        "variacion": round(variacion, 2),
                        "rendimiento_div": round(rendimiento_div, 2)
                    })
                except:
                    pass
        return predicciones


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
            "positivo": "#4ADE80",
            "negativo": "#F87171"
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
        
        tk.Label(marco_superior, text="📊 CMN InverGest",
                font=("Segoe UI", 20, "bold"), bg=self.colores["fondo"],
                fg=self.colores["acento"]).pack(side=tk.LEFT)
        
        self.lbl_saldo = tk.Label(marco_superior, text=f"💰 Saldo Disponible: $ {self.gestor.obtener_saldo():,.2f} COP",
                                 font=("Segoe UI", 14, "bold"), bg="#10B981", fg="white",
                                 padx=20, pady=8, relief=tk.FLAT)
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
        
        marco_izquierdo = tk.Frame(marco_principal, bg=self.colores["fondo"], width=320)
        marco_izquierdo.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        self.crear_seccion_operaciones(marco_izquierdo)
        self.crear_seccion_historial(marco_izquierdo)
        
        marco_central = tk.Frame(marco_principal, bg=self.colores["panel"], padx=15, pady=15)
        marco_central.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        self.titulo_grafico = tk.Label(
            marco_central,
            text="📈 Precios mensuales — Nike",
            font=("Segoe UI", 14, "bold"),
            bg=self.colores["panel"],
            fg=self.colores["acento"]
        )
        self.titulo_grafico.pack(pady=(0, 10))
        
        self.figura = plt.Figure(figsize=(7, 4.5), dpi=100, facecolor="#1E293B")
        self.ejes = self.figura.add_subplot(111)
        self.ejes.set_facecolor("#1E293B")
        
        self.lienzo = FigureCanvasTkAgg(self.figura, master=marco_central)
        self.lienzo.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        marco_derecho = tk.Frame(marco_principal, bg=self.colores["fondo"], width=350)
        marco_derecho.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.crear_seccion_prediccion(marco_derecho)
    
    def crear_seccion_operaciones(self, padre):
        marco = tk.LabelFrame(padre, text="💱 Registrar Operación",
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"],
                             padx=12, pady=12)
        marco.pack(fill=tk.X, pady=(0, 15))
        
        self.var_tipo = tk.StringVar(value="Compra")
        tk.Radiobutton(marco, text="Compra", variable=self.var_tipo, value="Compra",
                      bg=self.colores["panel"], fg=self.colores["texto"], selectcolor=self.colores["boton"],
                      activebackground=self.colores["panel"], activeforeground=self.colores["texto"],
                      font=("Segoe UI", 10)).grid(row=0, column=0, pady=6, sticky="w")
        tk.Radiobutton(marco, text="Venta", variable=self.var_tipo, value="Venta",
                      bg=self.colores["panel"], fg=self.colores["texto"], selectcolor=self.colores["boton"],
                      activebackground=self.colores["panel"], activeforeground=self.colores["texto"],
                      font=("Segoe UI", 10)).grid(row=0, column=1, pady=6, sticky="w", padx=15)
        
        tk.Label(marco, text="Empresa:", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=4)
        self.combo_empresa = ttk.Combobox(marco, values=self.gestor.obtener_lista_empresas(), state="readonly", width=22)
        self.combo_empresa.grid(row=1, column=1, pady=4)
        self.combo_empresa.set("Nike")
        
        tk.Label(marco, text="Cantidad:", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_cantidad = tk.Entry(marco, bg="#334155", fg="white", insertbackground="white", width=24)
        self.entry_cantidad.grid(row=2, column=1, pady=4)
        
        tk.Label(marco, text="Precio Unitario ($):", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=4)
        self.entry_precio = tk.Entry(marco, bg="#334155", fg="white", insertbackground="white", width=24)
        self.entry_precio.grid(row=3, column=1, pady=4)
        
        tk.Label(marco, text="Comisión ($):", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", pady=4)
        self.entry_comision = tk.Entry(marco, bg="#334155", fg="white", insertbackground="white", width=24)
        self.entry_comision.grid(row=4, column=1, pady=4)
        
        tk.Button(
            marco,
            text="✅ Registrar",
            command=self.registrar_operacion,
            bg="#00F5D4", fg="#000000",
            font=("Segoe UI", 10, "bold"),
            padx=15, pady=6,
            relief=tk.FLAT, cursor="hand2"
        ).grid(row=5, column=0, columnspan=2, pady=10)
    
    def crear_seccion_historial(self, padre):
        marco = tk.LabelFrame(padre, text="📝 Historial de Operaciones",
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"],
                             padx=12, pady=12)
        marco.pack(fill=tk.BOTH, expand=True)
        
        columnas = ("fecha", "tipo", "empresa", "cantidad", "total")
        self.tabla_op = ttk.Treeview(marco, columns=columnas, show="headings", height=8)
        
        encabezados = {
            "fecha": "Fecha", "tipo": "Tipo", "empresa": "Empresa",
            "cantidad": "Cantidad", "total": "Total ($)"
        }
        for col, texto in encabezados.items():
            self.tabla_op.heading(col, text=texto)
            self.tabla_op.column(col, width=55, anchor="center")
        
        scrollbar = ttk.Scrollbar(marco, orient=tk.VERTICAL, command=self.tabla_op.yview)
        self.tabla_op.configure(yscrollcommand=scrollbar.set)
        self.tabla_op.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def crear_seccion_prediccion(self, padre):
        marco = tk.LabelFrame(padre, text="📈 Análisis y Proyección",
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"],
                             padx=12, pady=12)
        marco.pack(fill=tk.BOTH, expand=True)
        
        self.texto_prediccion = tk.Text(marco, wrap=tk.WORD, bg="#0F172A", fg="#F8FAFC",
                                       font=("Segoe UI", 9), relief=tk.FLAT, padx=8, pady=8, height=22)
        self.texto_prediccion.pack(fill=tk.BOTH, expand=True)
        self.texto_prediccion.config(state=tk.DISABLED)
        
        tk.Button(
            marco,
            text="🔄 Actualizar Proyección",
            command=self.actualizar_prediccion,
            bg="#3B82F6", fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15, pady=6,
            relief=tk.FLAT, cursor="hand2"
        ).pack(fill=tk.X, pady=(10, 0))
    
    def cambiar_empresa(self, nombre):
        for nom, btn in self.botones_empresas.items():
            if nom == nombre:
                btn.config(bg=self.colores["boton_activo"], fg="#000000")
            else:
                btn.config(bg=self.colores["boton"], fg=self.colores["texto"])
        
        self.gestor.empresa_seleccionada = nombre
        self.titulo_grafico.config(text=f"📈 Precios mensuales — {nombre}")
        self.actualizar_grafico(nombre)
    
    def actualizar_grafico(self, nombre_empresa):
        df, color = self.gestor.obtener_datos_historicos(nombre_empresa)
        
        self.ejes.clear()
        self.ejes.set_facecolor("#1E293B")
        
        if df.empty:
            self.ejes.text(0.5, 0.5, "No hay datos disponibles",
                          ha="center", va="center", color="#94A3B8", fontsize=12,
                          transform=self.ejes.transAxes)
        else:
            df['MesNum'] = df.index.month
            df['Mes'] = df['MesNum'].map(meses_es)
            
            self.ejes.plot(df['Mes'], df['Close'], color=color, linewidth=3, marker='o', markersize=6)
            self.ejes.fill_between(df['Mes'], df['Close'], alpha=0.15, color=color)
            
            for i, fila in df.iterrows():
                self.ejes.text(fila['Mes'], fila['Close'] * 1.015, f"${fila['Close']:.2f}",
                              ha='center', va='bottom', color='#F8FAFC', fontsize=8,
                              bbox=dict(boxstyle="round,pad
                              bbox=dict(boxstyle="round,pad=0.2", fc="#1E293B", ec="none", alpha=0.7))
            
            self.ejes.set_ylabel("Precio en USD ($)", color="#94A3B8", fontsize=10)
            self.ejes.tick_params(axis='x', colors="#94A3B8", labelsize=9)
            self.ejes.tick_params(axis='y', colors="#94A3B8", labelsize=9)
            for spine in self.ejes.spines.values():
                spine.set_color('#475569')
        
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
            messagebox.showerror("Error", "Ingresa valores numéricos válidos")
            return
        
        exito, mensaje = self.gestor.registrar_operacion(tipo, empresa, cantidad, precio, comision)
        if not exito:
            messagebox.showerror("Error", mensaje)
            return
        
        messagebox.showinfo("Éxito", mensaje)
        self.entry_cantidad.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.entry_comision.delete(0, tk.END)
        self.actualizar_tabla_operaciones()
        self.actualizar_saldo()
        self.actualizar_prediccion()
    
    def actualizar_tabla_operaciones(self):
        for fila in self.tabla_op.get_children():
            self.tabla_op.delete(fila)
        
        operaciones = self.gestor.obtener_operaciones()
        for op in operaciones:
            self.tabla_op.insert("", tk.END, values=(
                op["fecha"], op["tipo"], op["empresa"],
                op["cantidad"], f"${op['valor_total']:,.2f}"
            ))
    
    def actualizar_saldo(self):
        self.lbl_saldo.config(text=f"💰 Saldo Disponible: $ {self.gestor.obtener_saldo():,.2f} COP")
    
    def actualizar_prediccion(self):
        predicciones = self.gestor.calcular_prediccion()
        self.texto_prediccion.config(state=tk.NORMAL)
        self.texto_prediccion.delete("1.0", tk.END)
        
        if not predicciones:
            self.texto_prediccion.insert(tk.END, "📌 No tienes inversiones registradas aún.\n\n")
            self.texto_prediccion.insert(tk.END, "Cuando compres acciones, verás aquí:\n")
            self.texto_prediccion.insert(tk.END, "• Su valor actual del mercado\n")
            self.texto_prediccion.insert(tk.END, "• Cuánto has ganado o perdido\n")
            self.texto_prediccion.insert(tk.END, "• Variación porcentual\n")
            self.texto_prediccion.insert(tk.END, "• Rendimiento por dividendos\n\n")
            self.texto_prediccion.insert(tk.END, "💡 Realiza tu primera compra para empezar a monitorear.")
        else:
            self.texto_prediccion.insert(tk.END, "=" * 45 + "\n")
            self.texto_prediccion.insert(tk.END, "📈 ANÁLISIS DE TUS INVERSIONES\n")
            self.texto_prediccion.insert(tk.END, "=" * 45 + "\n\n")
            
            total_invertido = 0
            total_valor_actual = 0
            total_ganancia = 0
            
            for p in predicciones:
                total_invertido += p["cantidad"] * p["precio_compra"]
                total_valor_actual += p["valor_actual"]
                total_ganancia += p["ganancia_perdida"]
                
                estado = "✅ SUBIÓ" if p["variacion"] >= 0 else "📉 BAJÓ"
                color_estado = "\033[92m" if p["variacion"] >= 0 else "\033[91m"
                
                self.texto_prediccion.insert(tk.END, f"🏢 {p['empresa']}\n")
                self.texto_prediccion.insert(tk.END, f"   Cantidad: {p['cantidad']} acciones\n")
                self.texto_prediccion.insert(tk.END, f"   Precio compra:  ${p['precio_compra']:.2f}\n")
                self.texto_prediccion.insert(tk.END, f"   Precio actual:  ${p['precio_actual']:.2f}\n")
                self.texto_prediccion.insert(tk.END, f"   Valor actual:   ${p['valor_actual']:.2f}\n")
                self.texto_prediccion.insert(tk.END, f"   Ganancia/Pérdida: ${p['ganancia_perdida']:.2f}\n")
                self.texto_prediccion.insert(tk.END, f"   Variación:      {p['variacion']:.2f}%  {estado}\n")
                self.texto_prediccion.insert(tk.END, f"   Dividendos:    {p['rendimiento_div']:.2f}%\n")
                self.texto_prediccion.insert(tk.END, "─" * 45 + "\n\n")
            
            self.texto_prediccion.insert(tk.END, "=" * 45 + "\n")
            self.texto_prediccion.insert(tk.END, "📊 RESUMEN GENERAL\n")
            self.texto_prediccion.insert(tk.END, "=" * 45 + "\n")
            self.texto_prediccion.insert(tk.END, f"Total invertido:   ${total_invertido:,.2f}\n")
            self.texto_prediccion.insert(tk.END, f"Valor actual:      ${total_valor_actual:,.2f}\n")
            
            estado_total = "✅ EN GANANCIA" if total_ganancia >= 0 else "📉 EN PÉRDIDA"
            self.texto_prediccion.insert(tk.END, f"Ganancia/Pérdida total: ${total_ganancia:,.2f}  {estado_total}\n")
            
            if total_invertido > 0:
                rendimiento_total = (total_ganancia / total_invertido) * 100
                self.texto_prediccion.insert(tk.END, f"Rendimiento total: {rendimiento_total:.2f}%\n")
            
            self.texto_prediccion.insert(tk.END, "=" * 45 + "\n")
            self.texto_prediccion.insert(tk.END, f"📅 Actualizado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        
        self.texto_prediccion.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = TableroInverGest(root)
    root.mainloop()
