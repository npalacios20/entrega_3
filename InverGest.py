import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime


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
        self.historial_operaciones.append({
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tipo": tipo,
            "empresa": nombre,
            "cantidad": cantidad,
            "precio_unitario": precio,
            "comision": comision,
            "valor_total": round(valor_total, 2)
        })
    
    def obtener_operaciones(self):
        return self.historial_operaciones


class TableroInverGest:
    def __init__(self, root):
        self.root = root
        self.root.title("CMN InverGest — Histórico de Precios 2026")
        self.root.geometry("1280x850")
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
            "borde": "#475569"
        }
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#1E293B", foreground="#F8FAFC",
                            fieldbackground="#1E293B", rowheight=28, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", background="#334155", foreground="#00F5D4",
                            font=("Segoe UI", 10, "bold"))
    
    def crear_interfaz(self):
        tk.Label(self.root, text="📊 CMN InverGest — Comportamiento Histórico 2026",
                font=("Segoe UI", 20, "bold"), bg=self.colores["fondo"],
                fg=self.colores["acento"]).pack(pady=15)
        
        tk.Label(self.root, text="Selecciona una empresa para ver su comportamiento mensual:",
                font=("Segoe UI", 11), bg=self.colores["fondo"], fg="#94A3B8").pack(pady=(0, 10))
        
        self.contenedor_botones = tk.Frame(self.root, bg=self.colores["fondo"])
        self.contenedor_botones.pack(pady=(0, 20))
        
        self.botones_empresas = {}
        for nombre in self.gestor.obtener_lista_empresas():
            btn = tk.Button(
                self.contenedor_botones,
                text=nombre,
                command=lambda n=nombre: self.cambiar_empresa(n),
                font=("Segoe UI", 10, "bold"),
                bg=self.colores["boton"],
                fg=self.colores["texto"],
                padx=15, pady=8,
                relief=tk.FLAT,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=6)
            self.botones_empresas[nombre] = btn
        
        self.contenedor_grafico = tk.Frame(self.root, bg=self.colores["panel"], padx=15, pady=15)
        self.contenedor_grafico.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        self.titulo_grafico = tk.Label(
            self.contenedor_grafico,
            text="📈 Precios mensuales — Nike (2026)",
            font=("Segoe UI", 14, "bold"),
            bg=self.colores["panel"],
            fg=self.colores["acento"]
        )
        self.titulo_grafico.pack(pady=(0, 10))
        
        self.figura = plt.Figure(figsize=(11, 4.5), dpi=100, facecolor="#1E293B")
        self.ejes = self.figura.add_subplot(111)
        self.ejes.set_facecolor("#1E293B")
        
        self.lienzo = FigureCanvasTkAgg(self.figura, master=self.contenedor_grafico)
        self.lienzo.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.seccion_inferior = tk.Frame(self.root, bg=self.colores["fondo"])
        self.seccion_inferior.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        marco_operaciones = tk.LabelFrame(
            self.seccion_inferior,
            text="💱 Registrar Operación",
            font=("Segoe UI", 11, "bold"),
            bg=self.colores["panel"],
            fg=self.colores["acento"],
            padx=15, pady=15
        )
        marco_operaciones.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        self.var_tipo = tk.StringVar(value="Compra")
        tk.Radiobutton(marco_operaciones, text="Compra", variable=self.var_tipo, value="Compra",
                      bg=self.colores["panel"], fg=self.colores["texto"], selectcolor=self.colores["boton"],
                      activebackground=self.colores["panel"], activeforeground=self.colores["texto"],
                      font=("Segoe UI", 10)).grid(row=0, column=0, pady=8, sticky="w")
        tk.Radiobutton(marco_operaciones, text="Venta", variable=self.var_tipo, value="Venta",
                      bg=self.colores["panel"], fg=self.colores["texto"], selectcolor=self.colores["boton"],
                      activebackground=self.colores["panel"], activeforeground=self.colores["texto"],
                      font=("Segoe UI", 10)).grid(row=0, column=1, pady=8, sticky="w", padx=20)
        
        tk.Label(marco_operaciones, text="Empresa:", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.combo_empresa = ttk.Combobox(marco_operaciones, values=self.gestor.obtener_lista_empresas(), state="readonly", width=25)
        self.combo_empresa.grid(row=1, column=1, pady=5)
        self.combo_empresa.set("Nike")
        
        tk.Label(marco_operaciones, text="Cantidad:", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_cantidad = tk.Entry(marco_operaciones, bg="#334155", fg="white", insertbackground="white", width=28)
        self.entry_cantidad.grid(row=2, column=1, pady=5)
        
        tk.Label(marco_operaciones, text="Precio Unitario ($):", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_precio = tk.Entry(marco_operaciones, bg="#334155", fg="white", insertbackground="white", width=28)
        self.entry_precio.grid(row=3, column=1, pady=5)
        
        tk.Label(marco_operaciones, text="Comisión ($):", bg=self.colores["panel"], fg=self.colores["texto"],
                font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w", pady=5)
        self.entry_comision = tk.Entry(marco_operaciones, bg="#334155", fg="white", insertbackground="white", width=28)
        self.entry_comision.grid(row=4, column=1, pady=5)
        
        tk.Button(
            marco_operaciones,
            text="✅ Registrar Operación",
            command=self.registrar_operacion,
            bg="#00F5D4", fg="#000000",
            font=("Segoe UI", 11, "bold"),
            padx=20, pady=8,
            relief=tk.FLAT, cursor="hand2"
        ).grid(row=5, column=0, columnspan=2, pady=12)
        
        marco_historial = tk.LabelFrame(
            self.seccion_inferior,
            text="📝 Historial de Operaciones",
            font=("Segoe UI", 11, "bold"),
            bg=self.colores["panel"],
            fg=self.colores["acento"],
            padx=15, pady=15
        )
        marco_historial.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        columnas = ("fecha", "tipo", "empresa", "cantidad", "precio", "comision", "total")
        self.tabla_op = ttk.Treeview(marco_historial, columns=columnas, show="headings", height=8)
        
        encabezados = {
            "fecha": "Fecha", "tipo": "Tipo", "empresa": "Empresa",
            "cantidad": "Cantidad", "precio": "P. Unit ($)", "comision": "Comisión ($)", "total": "Total ($)"
        }
        for col, texto in encabezados.items():
            self.tabla_op.heading(col, text=texto)
            self.tabla_op.column(col, width=90, anchor="center")
        
        scrollbar = ttk.Scrollbar(marco_historial, orient=tk.VERTICAL, command=self.tabla_op.yview)
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
        self.titulo_grafico.config(text=f"📈 Precios mensuales — {nombre} (2026)")
        self.actualizar_grafico(nombre)
    
    def actualizar_grafico(self, nombre_empresa):
        df, color = self.gestor.obtener_datos_historicos(nombre_empresa)
        
        self.ejes.clear()
        self.ejes.set_facecolor("#1E293B")
        
        if df.empty:
            self.ejes.text(0.5, 0.5, "No hay datos disponibles\npara mostrar",
                          ha="center", va="center", color="#94A3B8", fontsize=14,
                          transform=self.ejes.transAxes)
        else:
            df['Mes'] = df.index.strftime('%b')
            self.ejes.plot(df['Mes'], df['Close'], color=color, linewidth=3, marker='o', markersize=5)
            self.ejes.fill_between(df['Mes'], df['Close'], alpha=0.2, color=color)
            self.ejes.set_title(f"Comportamiento del precio — {nombre_empresa}",
                               color="#F8FAFC", fontsize=13, pad=15)
            self.ejes.set_ylabel("Precio en USD ($)", color="#94A3B8", fontsize=11)
            self.ejes.tick_params(axis='x', colors="#94A3B8", labelsize=10)
            self.ejes.tick_params(axis='y', colors="#94A3B8", labelsize=10)
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
        
        self.gestor.registrar_operacion(tipo, empresa, cantidad, precio, comision)
        messagebox.showinfo("Éxito", f"Operación de {tipo} registrada correctamente")
        self.entry_cantidad.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.entry_comision.delete(0, tk.END)
        self.actualizar_tabla_operaciones()
    
    def actualizar_tabla_operaciones(self):
        for fila in self.tabla_op.get_children():
            self.tabla_op.delete(fila)
        
        operaciones = self.gestor.obtener_operaciones()
        for op in operaciones:
            self.tabla_op.insert("", tk.END, values=(
                op["fecha"], op["tipo"], op["empresa"],
                op["cantidad"], op["precio_unitario"],
                op["comision"], op["valor_total"]
            ))


if __name__ == "__main__":
    root = tk.Tk()
    app = TableroInverGest(root)
    root.mainloop()
