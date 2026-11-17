import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-darkgrid')

EMPRESAS = {
    "Nike": {"ticker": "NKE", "tipo": "Renta Variable", "sector": "Indumentaria deportiva"},
    "Coca-Cola": {"ticker": "KO", "tipo": "Renta Variable", "sector": "Bebidas y consumo"},
    "Johnson & Johnson": {"ticker": "JNJ", "tipo": "Renta Variable", "sector": "Salud y farmacéutica"},
    "PepsiCo": {"ticker": "PEP", "tipo": "Renta Variable", "sector": "Bebidas y alimentos"},
    "Apple": {"ticker": "AAPL", "tipo": "Renta Variable", "sector": "Tecnología"},
    "Microsoft": {"ticker": "MSFT", "tipo": "Renta Variable", "sector": "Software y nube"},
    "Visa": {"ticker": "V", "tipo": "Renta Variable", "sector": "Servicios de pago"}
}

class DatosEmpresa:
    def __init__(self, nombre, ticker, sector, tipo):
        self.nombre = nombre
        self.ticker = ticker
        self.sector = sector
        self.tipo = tipo
        self.activo = yf.Ticker(ticker)
        self.precio_actual = 0.0
        self.dividendos_historicos = pd.Series(dtype='float64')
        self.dividendo_ultimo = 0.0
        self.rendimiento_anual = 0.0
        self.dividendo_rendimiento = 0.0

    def cargar_datos(self):
        try:
            print(f"Cargando datos de {self.nombre} ({self.ticker})...")
            info = self.activo.info
            self.nombre_completo = info.get('longName', self.nombre)
            self.precio_actual = info.get('currentPrice', 0.0)
            self.dividendo_rendimiento = info.get('dividendYield', 0.0) * 100
            
            datos_div = self.activo.dividends
            if datos_div is not None and not datos_div.empty:
                self.dividendos_historicos = datos_div
                self.dividendo_ultimo = self.dividendos_historicos.iloc[-1]
                print(f"Último dividendo: ${self.dividendo_ultimo:.4f} — Total histórico: {len(self.dividendos_historicos)} pagos")
            else:
                print("No hay historial de dividendos disponible")
            
            historico = self.activo.history(period="1y")
            if historico is not None and not historico.empty:
                precio_inicial = historico['Close'].iloc[0]
                precio_final = historico['Close'].iloc[-1]
                self.rendimiento_anual = ((precio_final - precio_inicial) / precio_inicial) * 100
            return True
        except Exception as e:
            print(f"Error al cargar {self.nombre}: {e}")
            return False

    def resumen(self):
        total_pagos = len(self.dividendos_historicos) if self.dividendos_historicos is not None and not self.dividendos_historicos.empty else 0
        ultimo_div = round(self.dividendo_ultimo, 4) if self.dividendo_ultimo else 0.0
        return {
            "Nombre": self.nombre,
            "Ticker": self.ticker,
            "Sector": self.sector,
            "Precio Actual ($)": round(self.precio_actual, 2),
            "Último Dividendo ($)": ultimo_div,
            "Rendimiento por Dividendo (%)": round(self.dividendo_rendimiento, 2),
            "Rendimiento Anual (%)": round(self.rendimiento_anual, 2),
            "Total Pagos de Dividendos": total_pagos
        }

def cargar_portafolio():
    print("\n" + "="*70)
    print("       CMN InverGest — CARGA DE DATOS DESDE APIs FINANCIERAS")
    print("="*70 + "\n")
    portafolio = []
    for nombre, datos in EMPRESAS.items():
        empresa = DatosEmpresa(nombre, datos["ticker"], datos["sector"], datos["tipo"])
        if empresa.cargar_datos():
            portafolio.append(empresa)
    return portafolio

def mostrar_tabla_comparativa(portafolio):
    print("\n" + "="*70)
    print("                  RESUMEN COMPARATIVO DEL PORTAFOLIO")
    print("="*70)
    datos_tabla = [empresa.resumen() for empresa in portafolio]
    df = pd.DataFrame(datos_tabla)
    df = df.set_index("Nombre")
    print(df.to_string())
    print("\n")
    return df

def graficar_dividendos(portafolio):
    print("Generando gráfico de comparación de dividendos...")
    fig, ejes = plt.subplots(2, 1, figsize=(14, 10))
    nombres = [e.nombre for e in portafolio]
    rendimientos = [e.dividendo_rendimiento for e in portafolio]
    colores = ['#2ecc71' if r > 2 else '#f39c12' if r > 0 else '#e74c3c' for r in rendimientos]
    ejes[0].bar(nombres, rendimientos, color=colores)
    ejes[0].set_title("Rendimiento por Dividendo Actual (%)", fontsize=14, fontweight='bold')
    ejes[0].set_ylabel("Rendimiento (%)", fontsize=12)
    ejes[0].tick_params(axis='x', rotation=30)
    ejes[0].grid(axis='y', alpha=0.3)
    pagos = [len(e.dividendos_historicos) if e.dividendos_historicos is not None else 0 for e in portafolio]
    ejes[1].bar(nombres, pagos, color='#3498db')
    ejes[1].set_title("Cantidad Total de Pagos de Dividendos Históricos", fontsize=14, fontweight='bold')
    ejes[1].set_ylabel("Número de Pagos", fontsize=12)
    ejes[1].tick_params(axis='x', rotation=30)
    ejes[1].grid(axis='y', alpha=0.3)
    plt.suptitle("CMN InverGest — Análisis de Dividendos", fontsize=18, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('analisis_dividendos.png', dpi=300, bbox_inches='tight')
    print("Gráfico guardado: analisis_dividendos.png")
    plt.show()

def graficar_evolucion_dividendos(portafolio):
    print("Generando gráfico de evolución histórica de dividendos...")
    fig, eje = plt.subplots(figsize=(16, 8))
    colores = {
        "Nike": "#E74C3C",
        "Coca-Cola": "#E67E22",
        "Johnson & Johnson": "#27AE60",
        "PepsiCo": "#9B59B6",
        "Apple": "#3498DB",
        "Microsoft": "#1ABC9C",
        "Visa": "#F1C40F"
    }
    for empresa in portafolio:
        if empresa.dividendos_historicos is not None and not empresa.dividendos_historicos.empty:
            datos = empresa.dividendos_historicos.resample('Y').sum()
            if len(datos) > 0:
                eje.plot(datos.index.year, datos.values,
                        marker='o', linewidth=2.5, markersize=6,
                        label=empresa.nombre, color=colores.get(empresa.nombre, '#888888'),
                        alpha=0.8)
    eje.set_title("Evolución Anual de Dividendos Pagados por Empresa", fontsize=16, fontweight='bold', pad=20)
    eje.set_xlabel("Año", fontsize=12)
    eje.set_ylabel("Dividendo Total por Año ($)", fontsize=12)
    eje.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize=10)
    eje.grid(alpha=0.3)
    plt.suptitle("CMN InverGest — Histórico de Dividendos", fontsize=18, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('evolucion_dividendos.png', dpi=300, bbox_inches='tight')
    print("Gráfico guardado: evolucion_dividendos.png")
    plt.show()

def main():
    print("\n" + "🔥"*35)
    print("          CMN InverGest — SISTEMA DE ANÁLISIS DE PORTAFOLIO")
    print("           Consultando datos en tiempo real desde APIs...")
    print("🔥"*35 + "\n")
    portafolio = cargar_portafolio()
    df_resumen = mostrar_tabla_comparativa(portafolio)
    graficar_dividendos(portafolio)
    graficar_evolucion_dividendos(portafolio)
    df_resumen.to_excel('resumen_portafolio.xlsx')
    print("Reporte guardado: resumen_portafolio.xlsx")
    print("\nAnálisis completado exitosamente!")

if __name__ == "__main__":
    main()
