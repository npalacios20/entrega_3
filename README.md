<img width="2848" height="1424" alt="CMN InverGest" src="https://github.com/user-attachments/assets/a867414f-e872-445e-9ca5-c18acc1c3c87" />

# ***CNM InverGest*** 
## Indice

➤ [Colaboradores del proyecto](#Colaboradores)
➤ [Descripción del proyecto](#descripción)
➤ [Objetivos del proyecto](#Objetivos)
➤ [Funcionamiento del sistema](#Funcionamiento)
➤ [Diagrama UML](#Diagrama)

### Descripción

El proyecto **CMN InverGest** consiste en el desarrollo de un sistema de información orientado al registro, monitoreo y evaluación del desempeño de un portafolio de inversiones conformado por instrumentos de renta fija y renta variable. Esta herramienta permite llevar un control detallado de las operaciones financieras realizadas, así como calcular de forma precisa la rentabilidad real de los activos, considerando no solo las ganancias, sino también los costos, comisiones y rendimientos asociados a cada instrumento.

Desde una perspectiva técnica, el proyecto integra principios de programación orientada a objetos, manejo de estructuras de datos para el almacenamiento de información y lógica de cálculo financiero, permitiendo además actualizar la valoración de los activos según las variaciones del mercado en tiempo real, y generar reportes que facilitan la toma de decisiones de inversión.

### Objetivos

1. Implementar un sistema que permita registrar y almacenar operaciones de compra y venta de acciones, CDT, bonos y TES (Bono del estado), con toda la información necesaria: fecha, cantidad, precio y comisiones de cada transacción.

2. Permitir registrar de forma estructurada las operaciones de compra y venta, incluyendo el cálculo automático de los costos por comisiones asociadas a cada transacción, este seguimiento sera automatico, teniendo como base los rendimientos generados por cada activo, incluyendo los dividendos de las acciones y los intereses de los instrumentos de renta fija.

3. Calcular la rentabilidad acumulada y la rentabilidad efectiva anual del portafolio, utilizando las APIs financieras para obtener datos actualizados del mercado e integrando todos los flujos de ingresos y egresos registrados en el sistema.

4. Desarrollar la funcionalidad para actualizar el valor de mercado de cada activo mediante el consumo de APIs financieras, reflejando en tiempo real sus variaciones de precio y condiciones; además de programar los cálculos automáticos de la rentabilidad acumulada y la rentabilidad efectiva anual del portafolio, también tendrá la capacidad de generar reportes que muestren el valor total invertido, el valor actual del portafolio y la distribución de las inversiones entre renta fija y renta variable.

### Funcionamiento

1. Tener instalado **Python**
2. Instalar las librerías necesarias ejecutando en la terminal: pip install yfinance matplotlib pandas
3. Escribe en la terminal:python InverGest.py
4. Se abrirá la ventana principal del sistema
   
  ### 1️⃣ Seleccionar una empresa: 
  
En la parte superior verás los nombres de las empresas disponibles:
- Nike
- Coca-Cola
- Johnson & Johnson
- PepsiCo
- Apple
- Microsoft
- Visa

### 2️⃣ Registrar una compra

1. Haz clic en el botón **🟢 COMPRAR**
2. Verifica que aparezca la empresa correcta
3. Escribe la **cantidad** de acciones
4. Escribe el **precio por acción**
5. Escribe el valor de la **comisión** que cobra el bróker
6. Pulsa **Confirmar** ✅

### 3️⃣ Registrar una venta

1. Haz clic en el botón **🔴 VENDER**
2. Selecciona la empresa de la que quieres vender acciones
3. Escribe la **cantidad** de acciones a vender
4. Escribe el **precio de venta por acción**
5. Escribe la **comisión** de la operación
6. Pulsa **Confirmar** ✅

### 4️⃣ Ver el gráfico

En el centro de la pantalla verás la evolución de precios mensuales de la empresa seleccionada. Cada punto muestra su valor exacto al pasar el cursor.

### 5️⃣ Consultar el análisis de tu portafolio

En el panel derecho pulsa el botón **Actualizar Proyección** para ver:

- 📈 Tus compras activas actuales
- 💵 Valor invertido vs. valor actual
- ➕ Ganancia o pérdida de cada inversión
- 📊 Ventas cerradas y su resultado
- 💰 Ganancias acumuladas totales

### 6️⃣ Reiniciar todo

Si quieres empezar de cero, pulsa **Eliminar Todo** en el panel izquierdo. Se reiniciará tu saldo a $50,000,000 COP y se borrará el historial.

### Diagrama

<img width="2686" height="2652" alt="Diagrama UML" src="https://github.com/user-attachments/assets/886f4374-308b-4f76-af34-ed528bc4ffe5" />

### Colaboradores
Este proyecto ha sido desarrollado por: 

❖ Leidy Carolina David Valle  
❖ Martin Morales Muñoz  
❖ Nilson Palacios Cardenas  
### [⬆ Volver al Índice](#Indice)
