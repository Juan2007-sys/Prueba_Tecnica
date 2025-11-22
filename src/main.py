import pandas as pd  
import numpy as np
from pathlib import Path

# Ruta base a la carpeta de datos
BASE_PATH = Path(__file__).resolve().parent.parent / "data"

# Función principal para cargar los archivos de datos
# y mostrar sus dimensiones
def main():
    print("Cargando Archivos ...")
    # Carga todos los archivos de la prueba desde la carpeta data 
    # La función verifica que cada archivo exista, se pueda leer y las dimensiones de cada uno

    try:
        asignacion = pd.read_excel(BASE_PATH / "Asignacion.xlsx") 
        demografico = pd.read_excel(BASE_PATH / "Demograficos.xlsx")
        empresas = pd.read_csv(BASE_PATH / "Empresas.csv", encoding="latin1", sep=";")  # Se usa latin1 para caracteres especiales y separador por que los csv no estan con UTF-8;
        pagos = pd.read_excel(BASE_PATH / "PAGOS_AFPNET.xlsx")
        zona_geo = pd.read_csv(BASE_PATH / "ZONA_GEOGRAFICA_Y_ACTIVIDAD_ECONOMICA.csv", encoding="latin1", sep=";")
        datos_rep = pd.read_excel(BASE_PATH / "DATOS_ADICIONALES_REP_LEGAL_INTELIBPO.xlsx")
        sabana_final = pd.read_csv(BASE_PATH / "sabana_final.csv", encoding="latin1", sep=";")

        # Muestra las dimensiones de cada archivo
        print("Archivos cargados exitosamente.")
        print("Asignacion:", asignacion.shape)
        print("Demograficos:", demografico.shape)
        print("Empresas:", empresas.shape)
        print("Pagos:", pagos.shape)
        print("Zona Geografica:", zona_geo.shape)
        print("Datos Representante Legal:", datos_rep.shape)
        print("Sabana Final:", sabana_final.shape)

        

        # Primer JOIN (Asignacion + Demograficos)
        # Se usa LEFT JOIN para conservar todas las filas de Asignacion
        consolidado = asignacion.merge(
            demografico,
            how="left",
            left_on="RUC",
            right_on="Ruc"
        ) 
        
        print("\nConsolidado JOIN1:", consolidado.shape)
        print(consolidado.head())

        # Segundo JOIN: consolidado (Asignacion + Demograficos) + Empresas
        # Se usa LEFT JOIN nuevamente sobre la clave RUC

        consolidado = consolidado.merge(
            empresas,
            how="left",
            on="RUC",
            suffixes=("","_EMP") # Evita conflictos de nombres de columnas
        )

        print("\nConsolidado JOIN2:", consolidado.shape)
        print(consolidado.head())

        


        # JOIN 3: Consolidado + Representante Legal

        consolidado = consolidado.merge(
            datos_rep,
            how="left",
            on="RUC",
            suffixes=("","_REP")
        )

        print("\nConsolidado JOIN3:", consolidado.shape)
        print(consolidado.head())

        

        # JOIN 4: Consolidado + Zona Geografica y Actividad Economica
        consolidado = consolidado.merge(
            zona_geo,
            how="left",
            on="RUC",
            suffixes=("","_GEO")
        )

        print("\nConsolidado JOIN4:", consolidado.shape)
        print(consolidado.head())

        print("\nColumnas PAGOS_AFPNET:")
        print(pagos.columns.tolist())


        # JOIN 5: Consolidado + PAGOS_AFPNET
        pagos_resumen = pagos.groupby("RUC", as_index=False)["Total"].sum()
        pagos_resumen = pagos_resumen.rename(columns={"Total": "MONTO_PAGO_ACUMULADO"})


      

        consolidado = consolidado.merge(    
            pagos_resumen,
            how="left",
            on="RUC"
        )

        consolidado["MONTO_PAGO_ACUMULADO"] = consolidado["MONTO_PAGO_ACUMULADO"].fillna(0)

        print("\nConsolidado JOIN5:", consolidado.shape)
        print(consolidado.head())

        print("\nResumen de pagos por RUC:")
        print(pagos_resumen.head())

        print ("\nFilas con pagos acumulados > 0:")
        print(consolidado[consolidado["MONTO_PAGO_ACUMULADO"] > 0].head())

        print("Archivos cargados y consolidados exitosamente.") 

        #Calculo de Dias de Mora Actual

        cols_fechas = {"FECHA_CORTE", "FECHA_VENCIMIENTO"}

        if cols_fechas.issubset(consolidado.columns):
            #convertir a tipo fecha 
            consolidado["FECHA_CORTE"] = pd.to_datetime(
                consolidado["FECHA_CORTE"], errors="coerce"
            )
            consolidado["FECHA_VENCIMIENTO"] = pd.to_datetime(
               consolidado["FECHA_VENCIMIENTO"], errors="coerce"
            )

            #Calcular diferencia en dias
            consolidado["DIAS_MORA_ACTUAL"] =(
                consolidado["FECHA_CORTE"] - consolidado["FECHA_VENCIMIENTO"]
            ).dt.days
        else:
            #Si el archivo no tiene fechas se crea una columan vacia
            consolidado["DIAS_MORA_ACTUAL"] = pd.NA
            print("[AVISO] No se encontraron FECHA_CORTE / FECHA_VENCIMIENTO en los datos.") 

        #Estado_Obligacion
        #Asegurar tipos numéricos
        
        dias = pd.to_numeric(consolidado["DIAS_MORA_ACTUAL"], errors="coerce")
        pagos = pd.to_numeric(consolidado["MONTO_PAGO_ACUMULADO"], errors="coerce").fillna(0)   

        con_al_dia = (pagos > 0) & (dias.fillna(9999) <= 30)
        con_en_mora = (pagos ==  0) | (dias.fillna(9999) > 30)

        consolidado["ESTADO_OBLIGACION"] = np.select(
            [con_al_dia, con_en_mora],
            ["AL DIA", "EN MORA"],
            default="REVISION"
        )

        print("\nConteo por ESTADO_OBLIGACION:")
        print(consolidado["ESTADO_OBLIGACION"].value_counts())


        print("\nEjemplos AL DIA:")
        print(consolidado.loc[consolidado["ESTADO_OBLIGACION"] == "AL DIA",
                      ["RUC", "RAZON_SOCIAL", "MONTO_PAGO_ACUMULADO",
                       "DIAS_MORA_ACTUAL", "ESTADO_OBLIGACION"]].head(5))

        

        print("\nEjemplos EN MORA:")
        print(consolidado[consolidado["ESTADO_OBLIGACION"] == "EN MORA"].head())

        # --- ORDENAR de salida igual a sabana_final.csv ---


        # Orden objetivo tomado de la plantilla
        orden_objetivo = sabana_final.columns.tolist()

        #DF resultado con mismo índice que tu consolidado
        consolidado_final = pd.DataFrame(index=consolidado.index)
        
        #Mapeo de columnas
        mapeo = {

            "NUM_IDENT": "RUC",                   # Identificador
            "NOMBRE_CLIENTE": "RAZON_SOCIAL",     # Nombre
            "SALDO_TOTAL": "Total general",       # Monto total
            "DIAS_MORA_ACTUAL": "DIAS_MORA_ACTUAL",
            "ESTADO_OBLIGACION": "ESTADO_OBLIGACION",
            # Si existen en tu consolidado, también se completan:
            "SEGMENTO": "SEGMENTO",
            "RUBRO": "RUBRO",

        }
         
        #Construcción columna a columna
        for col in orden_objetivo:
            if col in mapeo and mapeo[col] in consolidado.columns:
                consolidado_final[col] = consolidado[mapeo[col]]
            elif col in consolidado.columns:
                consolidado_final[col] = consolidado[col]
            else: 
                consolidado_final[col] = pd.NA  # Columna no encontrada, se llena con NA

        # Reordenar la plantilla 
        consolidado_final = consolidado_final[orden_objetivo]


        print("\nEstructura final (primeras 5 filas):")
        print(consolidado_final.head())
        print("\nCantidad de columnas finales:", consolidado_final.shape[1])
         

        #Exportar resultado final a CSV y Excel

        salida_csv = BASE_PATH / "consolidado_final.csv"
        consolidado_final.to_csv(salida_csv, index=False, encoding="latin1", sep=";")

        salida_excel = BASE_PATH / "consolidado_final.xlsx"
        consolidado_final.to_excel(salida_excel, index=False)

        #print(f"\nArchivo CSV generado correctamente en:\n{salida_csv}")
        #print(f"Archivo Excel generado correctamente en:\n{salida_excel}")

                    

            
            




        
    except Exception as e:
        # Captura errores en caso de que algún archivo no se pueda cargar
        print("Error al cargar los archivos:", e)

# Punto de entrada del script
if __name__ == "__main__":
    main()
