import pandas as pd
import os
import json
from scrapers.twitter_scraper import TwitterScraper
from scrapers.tiktok_scraper import TikTokScraper
from scrapers.facebook_scraper import FacebookScraper
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env en el mismo directorio
HERRAMIENTAS_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERRAMIENTAS_DIR, '.env'))

def main():
    # --- CONFIGURACIÓN ---
    # TOKEN: Se carga de .env para Apify
    APIFY_TOKEN = os.getenv("APIFY_TOKEN")
    
    # Fechas de búsqueda
    START_DATE = "2023-10-22"
    END_DATE = "2023-10-29"
    
    # --- CONFIGURACIÓN DE ENTRADA ---
    # Interruptores para activar/desactivar cada red social
    SCRAPE_TWITTER = False
    SCRAPE_TIKTOK = True
    SCRAPE_FACEBOOK = True

    # Variable para limitar el número de cuentas (None para procesar todas)
    LIMIT_ACCOUNTS = 2  # Cambia esto a None para procesar todos los candidatos
    MAX_TWEETS_PER_CANDIDATE = 50
    MAX_TIKTOK_PER_CANDIDATE = 50
    MAX_FACEBOOK_PER_CANDIDATE = 10
    
    # Ruta del archivo Excel de resultados (asumiendo que está en ../Colombia/)
    EXCEL_INPUT = os.path.join(os.path.dirname(HERRAMIENTAS_DIR), "Colombia", "Resultados electorales.xlsx")
    SHEET_NAME = "Redes Sociales"
    COLUMN_ID = "ID Candidato"
    COLUMN_TWITTER = "X / Twitter"
    COLUMN_TIKTOK = "TikTok"
    COLUMN_FACEBOOK = "Facebook"
    
    OUTPUT_DIR = os.path.join(HERRAMIENTAS_DIR, "resultados")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # --- PROCESO DE CARGA DE CUENTAS ---
    if not os.path.exists(EXCEL_INPUT):
        print(f"❌ Error: No se encontró el archivo Excel en {EXCEL_INPUT}")
        return

    try:
        print(f"📖 Cargando candidatos desde Excel: {EXCEL_INPUT}")
        df_excel = pd.read_excel(EXCEL_INPUT, sheet_name=SHEET_NAME)
        
        # Limpiar y procesar nombres de usuario
        def clean_username(val):
            if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
                return None
            val = str(val).strip()
            if "x.com/" in val: val = val.split("x.com/")[-1]
            elif "twitter.com/" in val: val = val.split("twitter.com/")[-1]
            elif "tiktok.com/@" in val: val = val.split("tiktok.com/@")[-1]
            return val.split("?")[0].strip("/").strip("@")

        def clean_fb_url(val):
            if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
                return None
            return str(val).strip()

        # Crear mapeo de Candidato -> IDs y Usuarios
        candidatos_data = []
        for _, row in df_excel.iterrows():
            tw_user = clean_username(row.get(COLUMN_TWITTER))
            tt_user = clean_username(row.get(COLUMN_TIKTOK))
            fb_url = clean_fb_url(row.get(COLUMN_FACEBOOK))
            cand_id = row.get(COLUMN_ID)
            
            if tw_user or tt_user or fb_url:
                candidatos_data.append({
                    "id_candidato": cand_id,
                    "twitter_user": tw_user,
                    "tiktok_user": tt_user,
                    "facebook_url": fb_url,
                    "nombre": row.get("Candidato")
                })
        
        print(f"✅ Se encontraron {len(candidatos_data)} candidatos con redes sociales.")
    except Exception as e:
        print(f"❌ Error al leer el Excel: {e}")
        return

    # Aplicar límite para pruebas
    if LIMIT_ACCOUNTS:
        print(f"🔬 Modo prueba activado: Limitando a los primeros {LIMIT_ACCOUNTS} candidatos.")
        candidatos_data = candidatos_data[:LIMIT_ACCOUNTS]

    # --- INICIALIZAR SCRAPERS ---
    tw_scraper = TwitterScraper(token=APIFY_TOKEN)
    tt_scraper = TikTokScraper(token=APIFY_TOKEN)
    fb_scraper = FacebookScraper(token=APIFY_TOKEN)

    # --- EJECUCIÓN ---
    for idx, cand in enumerate(candidatos_data, 1):
        print(f"\n--- [{idx}/{len(candidatos_data)}] PROCESANDO: {cand['nombre']} (ID: {cand['id_candidato']}) ---")
        
        # 1. Twitter
        if SCRAPE_TWITTER and cand['twitter_user']:
            df_tw = tw_scraper.process_account(cand['twitter_user'], START_DATE, END_DATE, max_tweets=MAX_TWEETS_PER_CANDIDATE)
            if not df_tw.empty:
                df_tw.insert(0, "id_candidato", cand['id_candidato'])
                save_append(df_tw, os.path.join(OUTPUT_DIR, f"tweets_full.csv"))
        
        # 2. TikTok
        if SCRAPE_TIKTOK and cand['tiktok_user']:
            df_tt = tt_scraper.fetch_profile_data([cand['tiktok_user']], max_items=MAX_TIKTOK_PER_CANDIDATE, start_date=START_DATE, end_date=END_DATE)
            if not df_tt.empty:
                df_tt.insert(0, "id_candidato", cand['id_candidato'])
                save_append(df_tt, os.path.join(OUTPUT_DIR, f"tiktok_full.csv"))

        # 3. Facebook
        if SCRAPE_FACEBOOK and cand['facebook_url']:
            df_fb = fb_scraper.process_account(cand['facebook_url'], START_DATE, END_DATE, max_posts=MAX_FACEBOOK_PER_CANDIDATE)
            if not df_fb.empty:
                df_fb.insert(0, "id_candidato", cand['id_candidato'])
                save_append(df_fb, os.path.join(OUTPUT_DIR, f"facebook_full.csv"))

def save_append(df, filepath):
    """Guarda los resultados haciendo append, asegurando que las columnas se alineen correctamente."""
    try:
        if df.empty:
            return

        file_exists = os.path.isfile(filepath)
        
        if file_exists:
            # Leer solo la primera fila para obtener los encabezados existentes
            existing_df_header = pd.read_csv(filepath, sep=";", nrows=0, encoding="utf-8-sig")
            existing_columns = existing_df_header.columns.tolist()
            
            # Reordenar y filtrar el nuevo DF para que coincida con el archivo
            # Las columnas nuevas en 'df' se ignoran para mantener la estructura del CSV
            # Las columnas faltantes en 'df' se llenan con NaN
            df = df.reindex(columns=existing_columns)
            
            df.to_csv(filepath, mode='a', index=False, header=False, encoding="utf-8-sig", sep=";")
        else:
            # Si el archivo no existe, lo creamos con el orden de columnas que traiga este DF
            df.to_csv(filepath, index=False, encoding="utf-8-sig", sep=";")
            
        print(f"💾 Datos agregados a: {filepath} ({len(df)} filas)")
    except Exception as e:
        print(f"❌ Error al guardar/append en {filepath}: {e}")

if __name__ == "__main__":
    main()
