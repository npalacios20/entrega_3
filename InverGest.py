import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
from datetime import datetime


class GestorDatos:
    def __init__(self):
        self.empresas = {}
        self.historial_operaciones = []
    
    def agregar_empresa(self, nombre, ticker, sector):
        try:
            activo = yf.Ticker(ticker)
            info = activo.info
            precio_actual = info.get('currentPrice', 0.0)
            rendimiento_div = info.get('dividendYield', 0.0) * 100
            dividendo_ultimo = activo.dividends.iloc[-1] if not activo.dividends.empty else 0.0
            historico = activo.history(period="1y")
            rendimiento_anual = ((historico['Close'].iloc[-1] - historico['Close'].iloc[0]) / historico['Close'].iloc[0]) * 100 if not historico.empty else 0.0
            
            self.empresas[nombre] = {
                "ticker": ticker,
                "sector": sector,
                "precio_actual": round(precio_actual, 2),
                "dividendo_ultimo": round(dividendo_ultimo, 4),
                "rendimiento_div": round(rendimiento_div, 2),
                "rendimiento_anual": round(rendimiento_anual, 2),
                "fecha_actualizacion": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            return True, f"{nombre} agregado correctamente"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def eliminar_empresa(self, nombre):
        if nombre in self.empresas:
            del self.empresas[nombre]
            return True, f"{nombre} eliminado"
        return False, "Empresa no encontrada"
    
    def actualizar_datos(self, nombre):
        if nombre not in self.empresas:
            return False, "Empresa no encontrada"
        return self.agregar_empresa(nombre, self.empresas[nombre]["ticker"], self.empresas[nombre]["sector"])
    
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
    
    def obtener_portafolio(self):
        return self.empresas
    
    def obtener_operaciones(self):
        return self.historial_operaciones
class TableroInverGest:
    def __init__(self, root):
        self.root = root
        self.root.title("CMN InverGest — Tablero de Control")
        self.root.geometry("1200x750")
        self.root.configure(bg="#1a1a2e")
        
        self.gestor = GestorDatos()
        self.inicializar_estilo()
        self.crear_interfaz()
        self.cargar_empresas_iniciales()
    
    def inicializar_estilo(self):
        self.colores = {
            "fondo": "#1a1a2e",
            "panel": "#16213e",
            "acento": "#00f5d4",
            "positivo": "#4ade80",
            "negativo": "#f87171",
            "texto": "#eaeaea",
            "boton": "#0f3460",
            "entrada": "#0f3460"
        }
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#16213e", foreground="#eaeaea", 
                            fieldbackground="#16213e", rowheight=30, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", background="#0f3460", foreground="#00f5d4",
                            font=("Segoe UI", 10, "bold"))
    
    def crear_interfaz(self):
        tk.Label(self.root, text="📊 CMN InverGest — Tablero de Control de Inversiones",
                font=("Segoe UI", 18, "bold"), bg=self.colores["fondo"],
                fg=self.colores["acento"]).pack(pady=15)
        
        marco_principal = tk.Frame(self.root, bg=self.colores["fondo"])
        marco_principal.pack(fill=tk.BOTH, expand=True, padx=20)
        
        marco_izquierdo = tk.Frame(marco_principal, bg=self.colores["fondo"], width=350)
        marco_izquierdo.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        self.crear_seccion_agregar_empresa(marco_izquierdo)
        self.crear_seccion_registrar_operacion(marco_izquierdo)
        self.crear_seccion_acciones(marco_izquierdo)
        
        marco_derecho = tk.Frame(marco_principal, bg=self.colores["fondo"])
        marco_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.crear_panel_resumen(marco_derecho)
        self.crear_tabla_portafolio(marco_derecho)
        self.crear_tabla_operaciones(marco_derecho)
    
    def crear_seccion_agregar_empresa(self, padre):
        marco = tk.LabelFrame(padre, text="➕ Agregar Empresa", font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"], padx=10, pady=10)
        marco.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(marco, text="Nombre:", bg=self.colores["panel"], fg=self.colores["texto"]).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_nombre = tk.Entry(marco, bg=self.colores["entrada"], fg="white", insertbackground="white")
        self.entry_nombre.grid(row=0, column=1, pady=5)
        
        tk.Label(marco, text="Símbolo:", bg=self.colores["panel"], fg=self.colores["texto"]).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_ticker = tk.Entry(marco, bg=self.colores["entrada"], fg="white", insertbackground="white")
        self.entry_ticker.grid(row=1, column=1, pady=5)
        
        tk.Label(marco, text="Sector:", bg=self.colores["panel"], fg=self.colores["texto"]).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_sector = tk.Entry(marco, bg=self.colores["entrada"], fg="white", insertbackground="white")
        self.entry_sector.grid(row=2, column=1, pady=5)
        
        tk.Button(marco, text="Agregar", command=self.agregar_empresa, bg=self.colores["acento"],
                fg="#000", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=10).grid(row=3, column=0, columnspan=2, pady=10)
    
    def crear_seccion_registrar_operacion(self, padre):
        marco = tk.LabelFrame(padre, text="💱 Registrar Operación", font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"], padx=10, pady=10)
        marco.pack(fill=tk.X, pady=(0, 15))
        
        self.var_tipo = tk.StringVar(value="Compra")
        tk.Radiobutton(marco, text="Compra", variable=self.var_tipo, value="Compra",
                      bg=self.colores["panel"], fg=self.colores["texto"], selectcolor=self.colores["entrada"],
                      activebackground=self.colores["panel"], activeforeground=self.colores["texto"]).grid(row=0, column=0, pady=5)
        tk.Radiobutton(marco, text="Venta", variable=self.var_tipo, value="Venta",
                      bg=self.colores["panel"], fg=self.colores["texto"], selectcolor=self.colores["entrada"],
                      activebackground=self.colores["panel"], activeforeground=self.colores["texto"]).grid(row=0, column=1, pady=5)
        
        tk.Label(marco, text="Empresa:", bg=self.colores["panel"], fg=self.colores["texto"]).grid(row=1, column=0, sticky="w", pady=5)
        self.combo_empresa = ttk.Combobox(marco, state="readonly")
        self.combo_empresa.grid(row=1, column=1, pady=5)
        
        tk.Label(marco, text="Cantidad:", bg=self.colores["panel"], fg=self.colores["texto"]).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_cantidad = tk.Entry(marco, bg=self.colores["entrada"], fg="white", insertbackground="white")
        self.entry_cantidad.grid(row=2, column=1, pady=5)
        
        tk.Label(marco, text="Precio Unit.:", bg=self.colores["panel"], fg=self.colores["texto"]).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_precio = tk.Entry(marco, bg=self.colores["entrada"], fg="white", insertbackground="white")
        self.entry_precio.grid(row=3, column=1, pady=5)
        
        tk.Label(marco, text="Comisión:", bg=self.colores["panel"], fg=self.colores["texto"]).grid(row=4, column=0, sticky="w", pady=5)
        self.entry_comision = tk.Entry(marco, bg=self.colores["entrada"], fg="white", insertbackground="white")
        self.entry_comision.grid(row=4, column=1, pady=5)
        
        tk.Button(marco, text="Registrar", command=self.registrar_operacion, bg=self.colores["acento"],
                fg="#000", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=10).grid(row=5, column=0, columnspan=2, pady=10)
    
    def crear_seccion_acciones(self, padre):
        marco = tk.LabelFrame(padre, text="🔄 Acciones", font=("Segoe UI", 11, "bold"),
                             bg=self.colores["panel"], fg=self.colores["acento"], padx=10, pady=10)
        marco.pack(fill=tk.X)
        
        tk.Button(marco, text="🔄 Actualizar Datos del Mercado", command=self.actualizar_todo,
                bg="#3b82f6", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=10).pack(fill=tk.X, pady=5)
        tk.Button(marco, text="🗑️ Eliminar Seleccionado", command=self.eliminar_empresa,
                bg="#ef4444", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=10).pack(fill=tk.X, pady=5)
        tk.Button(marco, text="📋 Exportar Reporte", command=self.exportar_reporte,
                bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=10).pack(fill=tk.X, pady=5)
    
    def crear_panel_resumen(self, padre):
        marco = tk.Frame(padre, bg=self.colores["panel"], padx=15, pady=15)
        marco.pack(fill=tk.X, pady=(0, 15))
        
        self.lbl_total = tk.Label(marco, text="💰 Valor Total del Portafolio: $0.00",
                                 font=("Segoe UI", 14, "bold"), bg=self.colores["panel"], fg=self.colores["acento"])
        self.lbl_total.pack(side=tk.LEFT)
        
        self.lbl_empresas = tk.Label(marco, text="📈 Empresas: 0",
                                    font=("Segoe UI", 12), bg=self.colores["panel"], fg=self.colores["texto"])
        self.lbl_empresas.pack(side=tk.LEFT, padx=30)
        
        self.lbl_actualizacion = tk.Label(marco, text="Última actualización: --",
                                         font=("Segoe UI", 10), bg=self.colores["panel"], fg="#9ca3af")
        self.lbl_actualizacion.pack(side=tk.RIGHT)
    
    def crear_tabla_portafolio(self, padre):
        tk.Label(padre, text="📊 Mi Portafolio", font=("Segoe UI", 12, "bold"),
                bg=self.colores["fondo"], fg=self.colores["acento"]).pack(anchor="w", pady=(0, 8))
        
        columnas = ("nombre", "ticker", "sector", "precio", "dividendo", "rend_div", "rend_anual", "fecha")
        self.tabla = ttk.Treeview(padre, columns=columnas, show="headings", height=8)
        
        encabezados = {
            "nombre": "Empresa", "ticker": "Símbolo", "sector": "Sector",
            "precio": "Precio ($)", "dividendo": "Últ. Div ($)",
            "rend_div": "Rto Div (%)", "rend_anual": "Rto Anual (%)", "fecha": "Actualización"
        }
        for col, texto in encabezados.items():
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=110, anchor="center")
        
        scrollbar = ttk.Scrollbar(padre, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def crear_tabla_operaciones(self, padre):
        tk.Label(padre, text="📝 Historial de Operaciones", font=("Segoe UI", 12, "bold"),
                bg=self.colores["fondo"], fg=self.colores["acento"]).pack(anchor="w", pady=(15, 8))
        
        columnas_op = ("fecha", "tipo", "empresa", "cantidad", "precio", "comision", "total")
        self.tabla_op = ttk.Treeview(padre, columns=columnas_op, show="headings", height=6)
        
        enc_op = {
            "fecha": "Fecha", "tipo": "Tipo", "empresa": "Empresa",
            "cantidad": "Cantidad", "precio": "P. Unit ($)", "comision": "Comisión ($)", "total": "Total ($)"
        }
        for col, texto in enc_op.items():
            self.tabla_op.heading(col, text=texto)
            self.tabla_op.column(col, width=110, anchor="center")
        
        scrollbar_op = ttk.Scrollbar(padre, orient=tk.VERTICAL, command=self.tabla_op.yview)
        self.tabla_op.configure(yscrollcommand=scrollbar_op.set)
        
        self.tabla_op.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_op.pack(side=tk.RIGHT, fill=tk.Y)
    def cargar_empresas_iniciales(self):
        empresas_iniciales = [
            ("Nike", "NKE", "Indumentaria deportiva"),
            ("Coca-Cola", "KO", "Bebidas y consumo"),
            ("Johnson & Johnson", "JNJ", "Salud y farmacéutica"),
            ("PepsiCo", "PEP", "Bebidas y alimentos"),
            ("Apple", "AAPL", "Tecnología"),
            ("Microsoft", "MSFT", "Software y servicios en la nube"),
            ("Visa", "V", "Servicios de pago")
        ]
        for nombre, ticker, sector in empresas_iniciales:
            self.gestor.agregar_empresa(nombre, ticker, sector)
        self.actualizar_tabla()
        self.actualizar_combo_empresas()
    
    def agregar_empresa(self):
        nombre = self.entry_nombre.get().strip()
        ticker = self.entry_ticker.get().strip().upper()
        sector = self.entry_sector.get().strip()
        
        if not nombre or not ticker:
            messagebox.showwarning("Advertencia", "Completa los campos Nombre y Símbolo")
            return
        
        exito, mensaje = self.gestor.agregar_empresa(nombre, ticker, sector)
        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self.entry_nombre.delete(0, tk.END)
            self.entry_ticker.delete(0, tk.END)
            self.entry_sector.delete(0, tk.END)
            self.actualizar_tabla()
            self.actualizar_combo_empresas()
        else:
            messagebox.showerror("Error", mensaje)
    
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
    
    def actualizar_tabla(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        
        datos = self.gestor.obtener_portafolio()
        for nombre, info in datos.items():
            self.tabla.insert("", tk.END, values=(
                nombre,
                info["ticker"],
                info["sector"],
                info["precio_actual"],
                info["dividendo_ultimo"],
                info["rendimiento_div"],
                info["rendimiento_anual"],
                info["fecha_actualizacion"]
            ))
        self.lbl_empresas.config(text=f"📈 Empresas: {len(datos)}")
        self.lbl_actualizacion.config(text=f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    def actualizar_tabla_operaciones(self):
        for fila in self.tabla_op.get_children():
            self.tabla_op.delete(fila)
        
        operaciones = self.gestor.obtener_operaciones()
        for op in operaciones:
            self.tabla_op.insert("", tk.END, values=(
                op["fecha"],
                op["tipo"],
                op["empresa"],
                op["cantidad"],
                op["precio_unitario"],
                op["comision"],
                op["valor_total"]
            ))
    
    def actualizar_combo_empresas(self):
        nombres = list(self.gestor.obtener_portafolio().keys())
        self.combo_empresa['values'] = nombres
    
    def actualizar_todo(self):
        for nombre in list(self.gestor.obtener_portafolio().keys()):
            self.gestor.actualizar_datos(nombre)
        self.actualizar_tabla()
        messagebox.showinfo("Éxito", "Todos los datos actualizados correctamente")
    
    def eliminar_empresa(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una empresa de la tabla")
            return
        item = self.tabla.item(seleccion[0])
        nombre = item['values'][0]
        exito, mensaje = self.gestor.eliminar_empresa(nombre)
        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self.actualizar_tabla()
            self.actualizar_combo_empresas()
        else:
            messagebox.showerror("Error", mensaje)
    
    def exportar_reporte(self):
        datos = self.gestor.obtener_portafolio()
        operaciones = self.gestor.obtener_operaciones()
        
        with open("reporte_portafolio.txt", "w", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write("REPORTE DEL PORTAFOLIO DE INVERSIONES\n")
            f.write(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("EMPRESAS EN EL PORTAFOLIO:\n\n")
            for nombre, info in datos.items():
                f.write(f"Empresa: {nombre}\n")
                f.write(f"  Símbolo: {info['ticker']}\n")
                f.write(f"  Sector: {info['sector']}\n")
                f.write(f"  Precio actual: ${info['precio_actual']}\n")
                f.write(f"  Último dividendo: ${info['dividendo_ultimo']}\n")
                f.write(f"  Rendimiento por dividendo: {info['rendimiento_div']}%\n")
                f.write(f"  Rendimiento anual: {info['rendimiento_anual']}%\n")
                f.write(f"  Última actualización: {info['fecha_actualizacion']}\n")
                f.write("-" * 40 + "\n")
            
            f.write("\nOPERACIONES REALIZADAS:\n\n")
            if not operaciones:
                f.write("No hay operaciones registradas.\n")
            else:
                for op in operaciones:
                    f.write(f"Fecha: {op['fecha']}\n")
                    f.write(f"  Tipo: {op['tipo']}\n")
                    f.write(f"  Empresa: {op['empresa']}\n")
                    f.write(f"  Cantidad: {op['cantidad']}\n")
                    f.write(f"  Precio unitario: ${op['precio_unitario']}\n")
                    f.write(f"  Comisión: ${op['comision']}\n")
                    f.write(f"  Total: ${op['valor_total']}\n")
                    f.write("-" * 40 + "\n")
        
        messagebox.showinfo("Éxito", "Reporte exportado como 'reporte_portafolio.txt'")


if __name__ == "__main__":
    root = tk.Tk()
    app = TableroInverGest(root)
    root.mainloop()
