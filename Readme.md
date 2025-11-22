1. Lenguaje y Librerías Utilizadas
Lenguaje de Programación: Python 3.11.9
Librerías/Paquetes:
pandas — manejo de DataFrames, JOINs, groupby
numpy — lógica condicional vectorizada
openpyxl — lectura y escritura de archivos Excel
pathlib — manejo robusto de rutas internas del proyecto

2. Estrategia de Implementación

Mi enfoque para simular la BBDD fue:
Usé DataFrames de Pandas para simular tablas en memoria y el método .merge() para realizar cada LEFT JOIN, además de groupby().sum() para agrupar los pagos por RUC.


3. Pasos para Ejecutar

Clonar el repositorio: https://github.com/Juan2007-sys/Prueba_Tecnica.git

Instalar dependencias:
pip install -r requirements.txt

Ejecutar el script principal:
python src/main.py

El resultado (la tabla final consolidada) se guarda en:
data/consolidado_final.csv
data/consolidado_final.xlsx


4. Justificación de la Lógica de Código

A. Agregación de Pagos 
Para calcular el MONTO_PAGO_ACUMULADO, seguí los siguientes pasos:
Agrupación: Agrupé el archivo PAGOS_AFPNET.xlsx por la columna RUC, que es la clave de identificación presente en todas las fuentes.

Cálculo: Usé la función sum() sobre la columna Total, que representa el valor abonado por cada RUC.
Unión: El resultado del groupby fue unido a la tabla maestra utilizando merge(..., on="RUC", how="left").
Nulos: Los valores nulos resultantes del LEFT JOIN se reemplazaron por 0, usando:

consolidado["MONTO_PAGO_ACUMULADO"].fillna(0, inplace=True)


5. ANÁLISIS Y RETROSPECTIVA 

1. Herramientas y Justificación
Utilicé Python porque permite procesar diferentes fuentes (CSV y Excel) de forma muy flexible.
Elegí Pandas porque sus DataFrames permiten simular estructuras tabulares muy parecidas a las de una base de datos, incluyendo joins, filtrados y agrupaciones.
La combinación de .merge(), .groupby() y .fillna() permite reproducir operaciones comunes de SQL (LEFT JOIN, agregación, manejo de nulos) pero de forma eficiente en memoria.

2. Lógica y Diseño de Cruces

Realicé los JOINs en el siguiente orden, siempre usando LEFT JOIN para conservar todos los registros de la tabla maestra (Asignación):
Asignacion + Demograficos

Empresas
DATOS_ADICIONALES_REP_LEGAL_INTELIBPO
ZONA_GEOGRAFICA_Y_ACTIVIDAD_ECONOMICA
Resultados de pago agregados (PAGOS_AFPNET)

El uso de LEFT JOIN asegura que si un cliente no tiene datos en otras tablas, igual permanezca en el resultado final.
En el campo MONTO_PAGO_ACUMULADO, manejé los nulos reemplazándolos por 0, dado que un LEFT JOIN produce NaN cuando un cliente no tiene pagos registrados.
Esto evita errores en cálculos posteriores y aplica la lógica: “si no tiene pagos → pago acumulado = 0”.

3. Retos y Soluciones

Reto: Manejar correctamente las fechas para calcular DIAS_MORA_ACTUAL.
Solución: Convertí las columnas FECHA_CORTE y FECHA_VENCIMIENTO a formato datetime con pd.to_datetime(..., errors="coerce"). Esto garantiza que valores no válidos no rompan el código.

Reto: Estandarizar la llave de unión entre diferentes fuentes.
Solución: Todos los archivos proporcionados tenían la columna RUC, lo cual permitió unificar la clave sin renombrar campos adicionales.

Reto: Construir la salida final con el mismo orden exacto que sabana_final.csv.
Solución: Leí primero las columnas de sabana_final.csv y generé un DataFrame final respetando 100% ese orden.

4. Aprendizaje

Aprendí que Python con Pandas puede funcionar casi como un motor de base de datos, permitiendo hacer JOINs, agregaciones y cálculos igual que en SQL. No sabía que se podía simular todo un proceso ETL completo: extraer datos, limpiarlos, transformarlos y generar una tabla final lista para usar. También reforcé el manejo de fechas, nulos y el orden de columnas. En general, entendí que Python sirve muchísimo para este tipo de procesos y facilita el trabajo con varias fuentes al mismo tiempo.