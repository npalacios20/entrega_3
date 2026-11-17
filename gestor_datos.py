# -*- coding: utf-8 -*-
"""
gestor_datos.py
===============
Lógica, datos y cálculos del sistema CMN InverGest (seguimiento de portafolio).

Características principales
---------------------------
* Renta Variable: acciones (precios en tiempo real vía yfinance, en USD).
* Renta Fija: CDT, Bonos y TES (en COP) con tasa E.A. y fecha de vencimiento.
* Registro de compras y ventas con fecha, cantidad, precio, comisión.
* Método FIFO para calcular el costo de lo vendido y las ganancias realizadas.
* Dividendos recibidos (histórico de yfinance según las acciones que se tenían
  el día anterior a la fecha ex-dividendo).
* Intereses acumulados de renta fija: capital * ((1 + E.A.)^(días/365) - 1).
* Todo el portafolio se consolida en COP usando la TRM (USD/COP).
* Cálculos: valor invertido, valor actual, distribución RF/RV,
  rentabilidad acumulada y rentabilidad efectiva anual (E.A.).
"""

import time
from datetime import datetime, date, timedelta

import pandas as pd
import yfinance as yf

# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------
SALDO_INICIAL = 50_000_000          # COP
TRM_RESPALDO = 4000.0               # Se usa solo si no hay conexión
CATEGORIA_RV = "Renta Variable"
CATEGORIA_RF = "Renta Fija"
TIPOS_RENTA_FIJA = ["CDT", "Bono", "TES"]
EPS = 1e-9

TTL_PRECIO = 60            # segundos que se reutiliza un precio consultado
TTL_DIVIDENDOS = 3600
TTL_TRM = 600


class GestorDatos:
    """Contiene los datos, las operaciones y todos los cálculos del portafolio."""

    def __init__(self):
        self.empresas = {
            "Nike": {"ticker": "NKE", "color": "#FF4500"},
            "Coca-Cola": {"ticker": "KO", "color": "#DC143C"},
            "Johnson & Johnson": {"ticker": "JNJ", "color": "#006400"},
            "PepsiCo": {"ticker": "PEP", "color": "#1E90FF"},
            "Apple": {"ticker": "AAPL", "color": "#555555"},
            "Microsoft": {"ticker": "MSFT", "color": "#00A4EF"},
            "Visa": {"ticker": "V", "color": "#1A237E"},
        }
        self.historial_operaciones = []
        self.empresa_seleccionada = "Nike"
        self.saldo_inicial = SALDO_INICIAL

        self._contador_ops = 0
        self._cache_precios = {}
        self._cache_dividendos = {}
        self._cache_trm = None

    # ======================================================================
    # Utilidades generales
    # ======================================================================
    def obtener_lista_empresas(self):
        return list(self.empresas.keys())

    @staticmethod
    def parsear_fecha(valor):
        """Convierte texto DD/MM/AAAA (o AAAA-MM-DD) a objeto date."""
        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        texto = str(valor).strip()
        for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(texto, formato).date()
            except ValueError:
                continue
        raise ValueError("Fecha inválida. Usa el formato DD/MM/AAAA")

    @staticmethod
    def calcular_interes(capital, tasa_ea, desde, hasta, vencimiento=None):
        """
        Interés acumulado con tasa efectiva anual.
        Si hay vencimiento, el interés deja de acumularse en esa fecha.
        Devuelve (interes, dias_transcurridos).
        """
        fin = min(hasta, vencimiento) if vencimiento else hasta
        dias = max((fin - desde).days, 0)
        interes = capital * ((1 + tasa_ea / 100.0) ** (dias / 365.0) - 1)
        return interes, dias

    # ======================================================================
    # Datos de mercado (con caché para no saturar la red)
    # ======================================================================
    def obtener_trm(self):
        """TRM (COP por USD) desde Yahoo Finance; usa un valor de respaldo si falla."""
        ahora = time.time()
        if self._cache_trm and ahora - self._cache_trm[1] < TTL_TRM:
            return self._cache_trm[0]
        try:
            historico = yf.Ticker("COP=X").history(period="5d")
            cierres = historico["Close"].dropna()
            valor = float(cierres.iloc[-1])
            if valor > 0:
                self._cache_trm = (valor, ahora)
                return valor
        except Exception as e:
            print(f"Error obteniendo TRM: {e}")
        if self._cache_trm:
            return self._cache_trm[0]
        # Reintenta en ~1 minuto en lugar de esperar todo el TTL
        self._cache_trm = (TRM_RESPALDO, ahora - TTL_TRM + 60)
        return TRM_RESPALDO

    def obtener_datos_historicos(self, nombre_empresa):
        ticker = self.empresas[nombre_empresa]["ticker"]
        try:
            activo = yf.Ticker(ticker)
            historico = activo.history(period="1y", interval="1mo")
            return historico, self.empresas[nombre_empresa]["color"]
        except Exception as e:
            print(f"Error obteniendo datos: {e}")
            return pd.DataFrame(), "#00f5d4"

    @staticmethod
    def _consultar_precio(ticker):
        activo = yf.Ticker(ticker)
        try:
            precio = float(activo.fast_info["last_price"])
            if precio > 0:
                return precio
        except Exception:
            pass
        try:
            info = activo.info
            precio = info.get("currentPrice") or info.get("regularMarketPrice")
            if precio and float(precio) > 0:
                return float(precio)
        except Exception:
            pass
        try:
            cierres = activo.history(period="5d")["Close"].dropna()
            if not cierres.empty:
                return float(cierres.iloc[-1])
        except Exception as e:
            print(f"Error obteniendo precio de {ticker}: {e}")
        return 0.0

    def obtener_precio_actual(self, nombre_empresa):
        """Precio de mercado (USD) en tiempo casi real. 0.0 si no se pudo obtener."""
        ticker = self.empresas[nombre_empresa]["ticker"]
        ahora = time.time()
        cacheado = self._cache_precios.get(ticker)
        if cacheado and ahora - cacheado[0] < TTL_PRECIO:
            return cacheado[1]
        precio = self._consultar_precio(ticker)
        if precio > 0:
            self._cache_precios[ticker] = (ahora, precio)
            return precio
        return cacheado[1] if cacheado else 0.0

    def obtener_dividendos_historicos(self, nombre_empresa):
        """Lista de (fecha_ex_dividendo, dividendo_por_accion_USD)."""
        ticker = self.empresas[nombre_empresa]["ticker"]
        ahora = time.time()
        cacheado = self._cache_dividendos.get(ticker)
        if cacheado and ahora - cacheado[0] < TTL_DIVIDENDOS:
            return cacheado[1]
        try:
            serie = yf.Ticker(ticker).dividends
            lista = [(indice.date(), float(monto)) for indice, monto in serie.items()]
            self._cache_dividendos[ticker] = (ahora, lista)
            return lista
        except Exception as e:
            print(f"Error obteniendo dividendos de {ticker}: {e}")
            return cacheado[1] if cacheado else []

    def obtener_resumen_dividendo(self, nombre_empresa):
        """Devuelve (rendimiento_anual_%, dividendo_anual_por_accion_USD)."""
        hoy = date.today()
        limite = hoy - timedelta(days=365)
        anual = sum(m for f, m in self.obtener_dividendos_historicos(nombre_empresa)
                    if limite < f <= hoy)
        precio = self.obtener_precio_actual(nombre_empresa)
        porcentaje = (anual / precio * 100) if precio > 0 else 0.0
        return porcentaje, anual

    # ======================================================================
    # Registro de operaciones
    # ======================================================================
    def registrar_operacion(self, tipo, nombre, cantidad, precio, comision,
                            categoria=CATEGORIA_RV, subtipo="Acción",
                            tasa=None, vencimiento=None, fecha=None, trm=None):
        """
        Registra una compra o venta.

        Renta variable: precio y comisión en USD; se guarda la TRM de la operación.
        Renta fija: valores en COP; en compras se requiere tasa E.A. (%) y
        vencimiento. En ventas, si precio es None se usa el valor actual
        (capital + intereses acumulados) del título.
        Devuelve (exito, mensaje).
        """
        try:
            fecha = self.parsear_fecha(fecha) if fecha not in (None, "") else date.today()
            vencimiento = (self.parsear_fecha(vencimiento)
                           if vencimiento not in (None, "") else None)
        except ValueError as e:
            return False, str(e)

        if tipo not in ("Compra", "Venta"):
            return False, "Tipo de operación inválido"
        if categoria not in (CATEGORIA_RV, CATEGORIA_RF):
            return False, "Categoría de activo inválida"
        if not nombre:
            return False, "Selecciona o escribe el activo"
        if cantidad is None or cantidad <= 0:
            return False, "La cantidad debe ser mayor que cero"
        if comision is None or comision < 0:
            return False, "La comisión no puede ser negativa"
        if fecha > date.today():
            return False, "La fecha de la operación no puede ser futura"

        if categoria == CATEGORIA_RV:
            if nombre not in self.empresas:
                return False, "Empresa no reconocida"
            if precio is None or precio <= 0:
                return False, "El precio debe ser mayor que cero"
            subtipo = "Acción"
            tasa, vencimiento = None, None
            if trm is None:
                trm = self.obtener_trm()
            if trm <= 0:
                return False, "La TRM debe ser mayor que cero"
        else:
            if subtipo not in TIPOS_RENTA_FIJA and tipo == "Compra":
                return False, "Tipo de renta fija inválido (CDT, Bono o TES)"
            trm = 1.0
            if tipo == "Compra":
                if precio is None or precio <= 0:
                    return False, "El valor unitario debe ser mayor que cero"
                if tasa is None or tasa < 0:
                    return False, "Ingresa una tasa E.A. válida (%)"
                if vencimiento is None or vencimiento <= fecha:
                    return False, "El vencimiento debe ser posterior a la fecha de compra"
            else:
                previas = [o for o in self.historial_operaciones if o["fecha"] <= fecha]
                lotes, _, _ = self._procesar_activo(categoria, nombre, ops=previas)
                if not lotes:
                    return False, "No tienes ese título en cartera a esa fecha"
                lote = lotes[0]
                subtipo = lote["subtipo"]
                tasa, vencimiento = lote["tasa"], lote["vencimiento"]
                if precio is None:
                    interes, _ = self.calcular_interes(
                        lote["precio"], lote["tasa"], lote["fecha"], fecha, lote["vencimiento"])
                    precio = lote["precio"] + interes
                if precio <= 0:
                    return False, "El valor unitario debe ser mayor que cero"

        self._contador_ops += 1
        bruto = cantidad * precio
        valor_total = bruto + comision if tipo == "Compra" else bruto - comision
        operacion = {
            "id": self._contador_ops,
            "fecha": fecha,
            "fecha_txt": fecha.strftime("%d/%m/%Y"),
            "tipo": tipo,
            "categoria": categoria,
            "subtipo": subtipo,
            "activo": nombre,
            "cantidad": float(cantidad),
            "precio_unitario": float(precio),
            "comision": float(comision),
            "tasa": tasa,
            "vencimiento": vencimiento,
            "trm": float(trm),
            "moneda": "USD" if categoria == CATEGORIA_RV else "COP",
            "valor_total": round(valor_total, 2),
            "valor_total_cop": valor_total * trm,
        }

        # Validar que nunca se venda más de lo que se tiene
        _, _, valido = self._procesar_activo(
            categoria, nombre, ops=self.historial_operaciones + [operacion])
        if not valido:
            return False, "No tienes suficientes unidades para vender en esa fecha"

        if tipo == "Compra" and operacion["valor_total_cop"] > self.obtener_saldo() + 1e-6:
            return False, "Saldo insuficiente"

        self.historial_operaciones.append(operacion)
        return True, "Operación registrada con éxito"

    def obtener_operaciones(self):
        return list(self.historial_operaciones)

    def obtener_nombres_renta_fija(self):
        nombres = []
        for op in self.historial_operaciones:
            if op["categoria"] == CATEGORIA_RF and op["activo"] not in nombres:
                nombres.append(op["activo"])
        return nombres

    def reiniciar_transacciones(self):
        self.historial_operaciones.clear()
        self._contador_ops = 0
        return True

    # ======================================================================
    # Motor FIFO (lotes abiertos y ventas cerradas)
    # ======================================================================
    def _activos_registrados(self):
        vistos = []
        for op in list(self.historial_operaciones):
            clave = (op["categoria"], op["activo"])
            if clave not in vistos:
                vistos.append(clave)
        return vistos

    def _procesar_activo(self, categoria, nombre, ops=None):
        """
        Reproduce cronológicamente las operaciones de un activo con FIFO.
        Devuelve (lotes_abiertos, ventas_cerradas, valido).
        Los valores monetarios de ventas y costos se expresan en COP.
        """
        fuente = list(self.historial_operaciones) if ops is None else ops
        relevantes = sorted(
            (o for o in fuente if o["categoria"] == categoria and o["activo"] == nombre),
            key=lambda o: (o["fecha"], 0 if o["tipo"] == "Compra" else 1, o["id"]))

        lotes, ventas, valido = [], [], True
        for o in relevantes:
            if o["tipo"] == "Compra":
                lotes.append({
                    "op_id": o["id"],
                    "fecha": o["fecha"],
                    "subtipo": o["subtipo"],
                    "cantidad": o["cantidad"],
                    "precio": o["precio_unitario"],
                    "comision_unit": o["comision"] / o["cantidad"],
                    "trm": o["trm"],
                    "tasa": o["tasa"],
                    "vencimiento": o["vencimiento"],
                })
                continue

            restante = o["cantidad"]
            costo_cop = 0.0
            costo_precio = 0.0
            for lote in lotes:
                if restante <= EPS:
                    break
                usar = min(restante, lote["cantidad"])
                if usar <= EPS:
                    continue
                costo_cop += usar * (lote["precio"] + lote["comision_unit"]) * lote["trm"]
                costo_precio += usar * lote["precio"]
                lote["cantidad"] -= usar
                restante -= usar
            lotes = [l for l in lotes if l["cantidad"] > EPS]
            if restante > EPS:
                valido = False

            vendida = o["cantidad"] - max(restante, 0.0)
            comision_prop = o["comision"] * (vendida / o["cantidad"])
            ingreso_cop = (vendida * o["precio_unitario"] - comision_prop) * o["trm"]
            promedio = costo_precio / vendida if vendida > EPS else 0.0
            variacion = ((o["precio_unitario"] - promedio) / promedio * 100) if promedio > 0 else 0.0
            ventas.append({
                "op_id": o["id"],
                "fecha": o["fecha"],
                "fecha_venta": o["fecha_txt"],
                "activo": nombre,
                "categoria": categoria,
                "subtipo": o["subtipo"],
                "cantidad": vendida,
                "moneda": o["moneda"],
                "precio_compra_prom": promedio,
                "precio_venta": o["precio_unitario"],
                "comision": comision_prop,
                "ingreso_cop": ingreso_cop,
                "costo_cop": costo_cop,
                "ganancia_perdida": ingreso_cop - costo_cop,
                "variacion": variacion,
            })
        return lotes, ventas, valido

    def calcular_ventas_cerradas(self):
        """Ventas realizadas con su ganancia/pérdida neta en COP (FIFO)."""
        todas = []
        for categoria, nombre in self._activos_registrados():
            _, ventas, _ = self._procesar_activo(categoria, nombre)
            todas.extend(ventas)
        todas.sort(key=lambda v: (v["fecha"], v["op_id"]))
        return todas

    # ======================================================================
    # Saldos (no requieren internet)
    # ======================================================================
    def obtener_saldo(self):
        """Efectivo disponible en COP = saldo inicial - compras + ventas netas."""
        saldo = float(self.saldo_inicial)
        for op in list(self.historial_operaciones):
            bruto = op["cantidad"] * op["precio_unitario"]
            if op["tipo"] == "Compra":
                saldo -= (bruto + op["comision"]) * op["trm"]
            else:
                saldo += (bruto - op["comision"]) * op["trm"]
        return saldo

    def obtener_saldo_gastado(self):
        """Costo (con comisiones) en COP de las posiciones que siguen abiertas."""
        total = 0.0
        for categoria, nombre in self._activos_registrados():
            lotes, _, _ = self._procesar_activo(categoria, nombre)
            for l in lotes:
                total += l["cantidad"] * (l["precio"] + l["comision_unit"]) * l["trm"]
        return total

    def obtener_ganancias(self):
        """Ganancias realizadas (ventas cerradas) en COP, netas de comisiones."""
        return sum(v["ganancia_perdida"] for v in self.calcular_ventas_cerradas())

    # ======================================================================
    # Dividendos
    # ======================================================================
    def calcular_dividendos_activo(self, nombre):
        """
        Dividendos recibidos (USD) por una acción: para cada fecha ex-dividendo se
        multiplican las acciones que se tenían el día anterior por el dividendo.
        Devuelve (total_usd, detalle).
        """
        ops = [o for o in list(self.historial_operaciones)
               if o["categoria"] == CATEGORIA_RV and o["activo"] == nombre]
        if not ops:
            return 0.0, []
        hoy = date.today()
        total = 0.0
        detalle = []
        for fecha_ex, monto in self.obtener_dividendos_historicos(nombre):
            if fecha_ex > hoy:
                continue
            cantidad = 0.0
            for o in ops:
                if o["fecha"] < fecha_ex:
                    cantidad += o["cantidad"] if o["tipo"] == "Compra" else -o["cantidad"]
            if cantidad > EPS:
                total += cantidad * monto
                detalle.append({"fecha": fecha_ex, "cantidad": cantidad,
                                "por_accion": monto, "total_usd": cantidad * monto})
        return total, detalle

    # ======================================================================
    # Posiciones abiertas
    # ======================================================================
    def calcular_posiciones(self):
        """Posiciones abiertas agrupadas por activo, valoradas en COP."""
        activos = self._activos_registrados()
        hay_rv = any(c == CATEGORIA_RV for c, _ in activos)
        trm_actual = self.obtener_trm() if hay_rv else 1.0
        hoy = date.today()

        posiciones = []
        for categoria, nombre in activos:
            lotes, _, _ = self._procesar_activo(categoria, nombre)
            if not lotes:
                continue
            if categoria == CATEGORIA_RV:
                posiciones.append(self._posicion_renta_variable(nombre, lotes, trm_actual))
            else:
                posiciones.append(self._posicion_renta_fija(nombre, lotes, hoy))
        return posiciones

    def _posicion_renta_variable(self, nombre, lotes, trm_actual):
        cantidad = sum(l["cantidad"] for l in lotes)
        costo_cop = sum(l["cantidad"] * (l["precio"] + l["comision_unit"]) * l["trm"] for l in lotes)
        costo_precio = sum(l["cantidad"] * l["precio"] for l in lotes)
        promedio = costo_precio / cantidad

        precio_actual = self.obtener_precio_actual(nombre)
        en_vivo = precio_actual > 0
        if not en_vivo:
            precio_actual = promedio  # sin conexión: se valora al costo

        valor_actual = cantidad * precio_actual * trm_actual
        resultado = valor_actual - costo_cop
        dividendos_usd, detalle_div = self.calcular_dividendos_activo(nombre)
        rend_pct, div_anual = self.obtener_resumen_dividendo(nombre)

        return {
            "categoria": CATEGORIA_RV,
            "subtipo": "Acción",
            "activo": nombre,
            "cantidad": cantidad,
            "precio_compra_prom": promedio,
            "precio_actual": precio_actual,
            "precio_en_vivo": en_vivo,
            "costo_cop": costo_cop,
            "valor_actual_cop": valor_actual,
            "resultado_cop": resultado,
            "rentabilidad_pct": (resultado / costo_cop * 100) if costo_cop > 0 else 0.0,
            "variacion": ((precio_actual - promedio) / promedio * 100) if promedio > 0 else 0.0,
            "dividendos_cop": dividendos_usd * trm_actual,
            "dividendos_usd": dividendos_usd,
            "detalle_dividendos": detalle_div,
            "rend_div_pct": rend_pct,
            "div_anual_accion": div_anual,
            "trm_actual": trm_actual,
        }

    def _posicion_renta_fija(self, nombre, lotes, hoy):
        cantidad = sum(l["cantidad"] for l in lotes)
        capital = sum(l["cantidad"] * l["precio"] for l in lotes)
        costo_cop = sum(l["cantidad"] * (l["precio"] + l["comision_unit"]) for l in lotes)
        interes = 0.0
        tasa_ponderada = 0.0
        for l in lotes:
            capital_lote = l["cantidad"] * l["precio"]
            i, _ = self.calcular_interes(capital_lote, l["tasa"], l["fecha"], hoy, l["vencimiento"])
            interes += i
            tasa_ponderada += l["tasa"] * capital_lote
        tasa_ponderada /= capital if capital > 0 else 1.0

        vencimiento = min(l["vencimiento"] for l in lotes)
        desde = min(l["fecha"] for l in lotes)
        valor_actual = capital + interes
        resultado = valor_actual - costo_cop
        return {
            "categoria": CATEGORIA_RF,
            "subtipo": lotes[0]["subtipo"],
            "activo": nombre,
            "cantidad": cantidad,
            "capital_cop": capital,
            "tasa": tasa_ponderada,
            "vencimiento": vencimiento,
            "dias_transcurridos": max((hoy - desde).days, 0),
            "dias_para_vencer": (vencimiento - hoy).days,
            "estado": "Vencido" if vencimiento <= hoy else "Vigente",
            "interes_cop": interes,
            "costo_cop": costo_cop,
            "valor_actual_cop": valor_actual,
            "resultado_cop": resultado,
            "rentabilidad_pct": (resultado / costo_cop * 100) if costo_cop > 0 else 0.0,
            "variacion": (interes / capital * 100) if capital > 0 else 0.0,
        }

    # ======================================================================
    # Resumen global del portafolio
    # ======================================================================
    def calcular_resumen_portafolio(self):
        """
        Calcula todos los indicadores del portafolio (en COP):

        * total_invertido: costo (con comisiones) de las posiciones abiertas.
        * valor_actual: acciones a precio de mercado * TRM + renta fija con intereses.
        * distribución porcentual renta fija / renta variable (sobre valor_actual).
        * resultado_total = ganancia no realizada + ganancia realizada + dividendos.
        * rentabilidad acumulada = resultado_total / total comprado históricamente.
        * rentabilidad E.A. = (1 + rent. acumulada)^(365/días) - 1, con los días
          transcurridos desde la primera operación.
        """
        ops = list(self.historial_operaciones)
        hoy = date.today()
        posiciones = self.calcular_posiciones()
        ventas = self.calcular_ventas_cerradas()

        trm = self.obtener_trm() if any(o["categoria"] == CATEGORIA_RV for o in ops) else 1.0
        nombres_rv = [n for c, n in self._activos_registrados() if c == CATEGORIA_RV]
        dividendos_cop = sum(self.calcular_dividendos_activo(n)[0] for n in nombres_rv) * trm

        total_invertido = sum(p["costo_cop"] for p in posiciones)
        valor_rv = sum(p["valor_actual_cop"] for p in posiciones if p["categoria"] == CATEGORIA_RV)
        valor_rf = sum(p["valor_actual_cop"] for p in posiciones if p["categoria"] == CATEGORIA_RF)
        valor_actual = valor_rv + valor_rf
        intereses = sum(p["interes_cop"] for p in posiciones if p["categoria"] == CATEGORIA_RF)

        ganancia_no_realizada = valor_actual - total_invertido
        ganancia_realizada = sum(v["ganancia_perdida"] for v in ventas)
        resultado_total = ganancia_no_realizada + ganancia_realizada + dividendos_cop

        total_comprado = sum(
            (o["cantidad"] * o["precio_unitario"] + o["comision"]) * o["trm"]
            for o in ops if o["tipo"] == "Compra")
        rent_acum = (resultado_total / total_comprado * 100) if total_comprado > 0 else 0.0

        dias = (hoy - min(o["fecha"] for o in ops)).days if ops else 0
        rent_ea = None
        if total_comprado > 0:
            base = 1 + rent_acum / 100.0
            if base <= 0:
                rent_ea = -100.0
            else:
                rent_ea = (base ** (365.0 / max(dias, 1)) - 1) * 100

        saldo = self.obtener_saldo()
        return {
            "posiciones": posiciones,
            "ventas": ventas,
            "trm": trm,
            "total_invertido": total_invertido,
            "total_comprado": total_comprado,
            "valor_actual": valor_actual,
            "valor_rv": valor_rv,
            "valor_rf": valor_rf,
            "pct_rv": (valor_rv / valor_actual * 100) if valor_actual > 0 else 0.0,
            "pct_rf": (valor_rf / valor_actual * 100) if valor_actual > 0 else 0.0,
            "dividendos_cop": dividendos_cop,
            "intereses_cop": intereses,
            "ganancia_no_realizada": ganancia_no_realizada,
            "ganancia_realizada": ganancia_realizada,
            "resultado_total": resultado_total,
            "rentabilidad_acumulada": rent_acum,
            "rentabilidad_ea": rent_ea,
            "ea_referencial": dias < 30,
            "dias": dias,
            "saldo": saldo,
            "patrimonio": saldo + valor_actual + dividendos_cop,
            "fecha_calculo": datetime.now(),
        }
