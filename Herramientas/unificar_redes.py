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
        
        # Procesar fecha
        raw_date = df_fb['time_col'] if 'time_col' in df_fb.columns else df_fb['time']
        dt_fb = pd.to_datetime(raw_date, errors='coerce')
        
        # Mapping
        df_fb_mapped = pd.DataFrame({
            'id_candidato': df_fb['id_candidato'],
            'red_social': 'Facebook',
            'fecha': dt_fb.dt.strftime('%Y-%m-%d'),
            'hora': dt_fb.dt.strftime('%H:%M:%S'),
            'usuario': df_fb['pageName'],
            'texto': df_fb['text'],
            'url': df_fb['url'],
            'likes': df_fb['likes'],
            'comentarios': df_fb['comments'],
            'compartidos': df_fb['shares'],
            'vistas': df_fb['viewsCount'] if 'viewsCount' in df_fb.columns else 0,
            # Reacciones específicas
            'fb_love': df_fb['reactionLoveCount'] if 'reactionLoveCount' in df_fb.columns else 0,
            'fb_haha': df_fb['reactionHahaCount'] if 'reactionHahaCount' in df_fb.columns else 0,
            'fb_care': df_fb['reactionCareCount'] if 'reactionCareCount' in df_fb.columns else 0,
            'fb_wow': df_fb['reactionWowCount'] if 'reactionWowCount' in df_fb.columns else 0,
            'fb_sad': df_fb['reactionSadCount'] if 'reactionSadCount' in df_fb.columns else 0,
            'fb_angry': df_fb['reactionAngryCount'] if 'reactionAngryCount' in df_fb.columns else 0,
            'favoritos': 0
        })
        dfs.append(df_fb_mapped)
    else:
        print(f"Advertencia: No se encontró {fb_file}")

    # 2. Procesar TikTok
    if os.path.exists(tk_file):
        print(f"Procesando TikTok: {tk_file}")
        df_tk = pd.read_csv(tk_file, sep=';', encoding='utf-8')
        
        # Procesar fecha (TikTok usa Unix timestamp en uploadedAt)
        dt_tk = pd.to_datetime(df_tk['uploadedAt'], unit='s', errors='coerce')
        
        # Mapping
        df_tk_mapped = pd.DataFrame({
            'id_candidato': df_tk['id_candidato'],
            'red_social': 'TikTok',
            'fecha': dt_tk.dt.strftime('%Y-%m-%d'),
            'hora': dt_tk.dt.strftime('%H:%M:%S'),
            'usuario': df_tk['channel'],
            'texto': df_tk['title'],
            'url': df_tk['postPage'],
            'likes': df_tk['likes'],
            'comentarios': df_tk['comments'],
            'compartidos': df_tk['shares'],
            'vistas': df_tk['views'],
            'favoritos': df_tk['bookmarks'] if 'bookmarks' in df_tk.columns else 0
        })
        dfs.append(df_tk_mapped)
    else:
        print(f"Advertencia: No se encontró {tk_file}")

    # 3. Procesar Twitter
    if os.path.exists(tw_file):
        print(f"Procesando Twitter: {tw_file}")
        df_tw = pd.read_csv(tw_file, sep=';', encoding='utf-8')
        
        # Procesar fecha (Twitter usa ISO 8601)
        dt_tw = pd.to_datetime(df_tw['date'], errors='coerce')
        
        # Mapping
        df_tw_mapped = pd.DataFrame({
            'id_candidato': df_tw['id_candidato'],
            'red_social': 'Twitter',
            'fecha': dt_tw.dt.strftime('%Y-%m-%d'),
            'hora': dt_tw.dt.strftime('%H:%M:%S'),
            'usuario': df_tw['account'],
            'texto': df_tw['text'],
            'url': df_tw['url'],
            'likes': df_tw['like_count'],
            'comentarios': df_tw['reply_count'],
            'compartidos': df_tw['retweet_count'],
            'vistas': df_tw['view_count'],
            'favoritos': 0
        })
        dfs.append(df_tw_mapped)
    else:
        print(f"Advertencia: No se encontró {tw_file}")

    if dfs:
        # Concatenar todos
        df_final = pd.concat(dfs, ignore_index=True)
        
        # Llenar NaNs con 0 y convertir a entero (int64)
        interact_cols = ['likes', 'comentarios', 'compartidos', 'vistas', 'favoritos', 
                        'fb_love', 'fb_haha', 'fb_care', 'fb_wow', 'fb_sad', 'fb_angry']
        df_final[interact_cols] = df_final[interact_cols].fillna(0).astype('int64')
        
        output_file = os.path.join(resultados_path, 'redes_unificadas.csv')
        df_final.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
        print(f"\n¡Éxito! Archivo unificado actualizado en: {output_file}")
        print(f"Total de publicaciones: {len(df_final)}")
        print("\nResumen por red social:")
        print(df_final['red_social'].value_counts())
    else:
        print("No se encontraron datos para unificar.")

if __name__ == "__main__":
    unificar_datos()



