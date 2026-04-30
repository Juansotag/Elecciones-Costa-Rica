import pandas as pd
import os

def unificar_datos():
    base_path = os.path.dirname(os.path.abspath(__file__))
    resultados_path = os.path.join(base_path, 'resultados')
    
    # Archivos
    fb_file = os.path.join(resultados_path, 'facebook_full.csv')
    tk_file = os.path.join(resultados_path, 'tiktok_full.csv')
    tw_file = os.path.join(resultados_path, 'tweets_full.csv')
    
    dfs = []
    
    # 1. Procesar Facebook
    if os.path.exists(fb_file):
        print(f"Procesando Facebook: {fb_file}")
        df_fb = pd.read_csv(fb_file, sep=';', encoding='utf-8')
        df_fb['red_social'] = 'Facebook'
        
        # Renombrar para unificar, pero manteniendo el resto
        rename_map = {
            'pageName': 'usuario',
            'text': 'texto',
            'url': 'url',
            'likes': 'likes',
            'comments': 'comentarios',
            'shares': 'compartidos',
            'viewsCount': 'vistas'
        }
        if 'time_col' in df_fb.columns:
            rename_map['time_col'] = 'fecha'
        elif 'time' in df_fb.columns:
            rename_map['time'] = 'fecha'
            
        df_fb = df_fb.rename(columns=rename_map)
        dfs.append(df_fb)
    else:
        print(f"Advertencia: No se encontró {fb_file}")

    # 2. Procesar TikTok
    if os.path.exists(tk_file):
        print(f"Procesando TikTok: {tk_file}")
        df_tk = pd.read_csv(tk_file, sep=';', encoding='utf-8')
        df_tk['red_social'] = 'TikTok'
        
        # Renombrar para unificar
        rename_map = {
            'uploadedAt': 'fecha',
            'channel': 'usuario',
            'title': 'texto',
            'postPage': 'url',
            'likes': 'likes',
            'comments': 'comentarios',
            'shares': 'compartidos',
            'views': 'vistas'
        }
        df_tk = df_tk.rename(columns=rename_map)
        dfs.append(df_tk)
    else:
        print(f"Advertencia: No se encontró {tk_file}")

    # 3. Procesar Twitter
    if os.path.exists(tw_file):
        print(f"Procesando Twitter: {tw_file}")
        df_tw = pd.read_csv(tw_file, sep=';', encoding='utf-8')
        df_tw['red_social'] = 'Twitter'
        
        # Renombrar para unificar
        rename_map = {
            'date': 'fecha',
            'account': 'usuario',
            'text': 'texto',
            'url': 'url',
            'like_count': 'likes',
            'reply_count': 'comentarios',
            'retweet_count': 'compartidos',
            'view_count': 'vistas'
        }
        df_tw = df_tw.rename(columns=rename_map)
        dfs.append(df_tw)
    else:
        print(f"Advertencia: No se encontró {tw_file}")

    if dfs:
        # Concatenar todos. Los campos no comunes se llenarán con NaN
        print("\nConcatenando y unificando columnas...")
        df_final = pd.concat(dfs, ignore_index=True, sort=False)
        
        # Mover columnas importantes al principio para mejor visibilidad
        cols = ['id_candidato', 'red_social', 'fecha', 'usuario', 'texto', 'url', 'likes', 'comentarios', 'compartidos', 'vistas']
        # Agregar el resto de columnas que no están en la lista anterior
        other_cols = [c for c in df_final.columns if c not in cols]
        df_final = df_final[cols + other_cols]
        
        output_file = os.path.join(resultados_path, 'redes_unificadas_full.csv')
        df_final.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
        print(f"\nExito! Archivo unificado completo guardado en: {output_file}")
        print(f"Total de publicaciones: {len(df_final)}")
        print(f"Total de columnas: {len(df_final.columns)}")
        print("\nResumen por red social:")
        print(df_final['red_social'].value_counts())
    else:
        print("No se encontraron datos para unificar.")

if __name__ == "__main__":
    unificar_datos()
