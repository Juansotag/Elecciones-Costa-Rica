import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

def realizar_eda():
    base_path = os.path.dirname(os.path.abspath(__file__))
    resultados_path = os.path.join(base_path, 'resultados')
    
    # 1. Cargar datos unificados
    csv_unificado = os.path.join(resultados_path, 'redes_unificadas.csv')
    if not os.path.exists(csv_unificado):
        print(f"Error: No se encontró el archivo {csv_unificado}")
        return
    
    df_redes = pd.read_csv(csv_unificado, sep=';', encoding='utf-8-sig')
    
    # 2. Cargar datos electorales
    # Ajustar ruta al Excel de Colombia
    excel_electoral = os.path.join(os.path.dirname(base_path), 'Colombia', 'Resultados electorales.xlsx')
    if not os.path.exists(excel_electoral):
        print(f"Error: No se encontró el archivo {excel_electoral}")
        return
    
    df_electoral = pd.read_excel(excel_electoral, sheet_name='Candidatos E-26 ALC')
    
    # 3. Unificar nombres de columnas para el merge
    df_electoral = df_electoral.rename(columns={'ID Candidato': 'id_candidato'})
    
    # 4. Merge
    df_completo = pd.merge(df_redes, df_electoral[['id_candidato', 'Candidato', 'Ganador', 'Votos']], on='id_candidato', how='left')
    
    print(f"Datos combinados correctamente. Total de filas: {len(df_completo)}")
    
    # 5. Análisis Exploratorio
    
    # Pregunta 1: Candidatos con mayor número de interacciones totales
    # Creamos una métrica de 'interacciones_totales'
    interact_cols = ['likes', 'comentarios', 'compartidos', 'favoritos']
    df_completo['interacciones_totales'] = df_completo[interact_cols].sum(axis=1)
    
    top_interacciones = df_completo.groupby('Candidato')['interacciones_totales'].sum().sort_values(ascending=False).head(10)
    
    print("\n--- Top 10 Candidatos por Interacciones Totales ---")
    print(top_interacciones)
    
    # Pregunta 2: Interacciones promedio por publicación (por red y tipo)
    promedio_por_red = df_completo.groupby(['red_social']).agg({
        'likes': 'mean',
        'comentarios': 'mean',
        'compartidos': 'mean',
        'vistas': 'mean',
        'favoritos': 'mean'
    }).round(2)
    
    print("\n--- Interacciones Promedio por Publicación (por Red Social) ---")
    print(promedio_por_red)
    
    # Promedio por Candidato y Red
    promedio_candidato_red = df_completo.groupby(['Candidato', 'red_social'])['interacciones_totales'].mean().unstack().round(2)
    print("\n--- Interacciones Promedio por Candidato y Red (Muestra Top 5) ---")
    print(promedio_candidato_red.head())
    
    # Pregunta 3: Relación entre interacciones y ganar
    print("\n--- Relación entre Interacciones y Ganar ---")
    
    # Agrupamos por id_candidato para tener métricas por persona
    stats_candidato = df_completo.groupby(['id_candidato', 'Candidato', 'Ganador']).agg({
        'interacciones_totales': 'sum',
        'id_candidato': 'count', # número de publicaciones
        'Votos': 'first'
    }).rename(columns={'id_candidato': 'num_publicaciones'})
    
    stats_candidato['interacciones_promedio'] = (stats_candidato['interacciones_totales'] / stats_candidato['num_publicaciones']).round(2)
    
    # Comparación Ganadores vs No Ganadores
    comparativa_ganadores = stats_candidato.groupby('Ganador').agg({
        'interacciones_totales': 'mean',
        'interacciones_promedio': 'mean',
        'num_publicaciones': 'mean',
        'Votos': 'mean'
    }).round(2)
    
    print(comparativa_ganadores)
    
    # Conclusiones rápidas
    print("\n--- Conclusiones del Análisis ---")
    winner_avg = comparativa_ganadores.loc['Sí', 'interacciones_totales'] if 'Sí' in comparativa_ganadores.index else 0
    loser_avg = comparativa_ganadores.loc['No', 'interacciones_totales'] if 'No' in comparativa_ganadores.index else 0
    
    if winner_avg > loser_avg:
        print(f"En promedio, los ganadores tuvieron más interacciones totales ({winner_avg}) que los que no ganaron ({loser_avg}).")
    else:
        print(f"Curiosamente, los no ganadores tuvieron más interacciones totales en promedio ({loser_avg}) que los ganadores ({winner_avg}).")

    # Guardar reporte detallado
    output_report = os.path.join(resultados_path, 'analisis_eda_redes.csv')
    stats_candidato.to_csv(output_report, sep=';', encoding='utf-8-sig')
    print(f"\nReporte detallado guardado en: {output_report}")

if __name__ == "__main__":
    realizar_eda()
