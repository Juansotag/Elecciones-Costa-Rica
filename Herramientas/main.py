import pandas as pd
import os
import json
from scrapers.twitter_scraper import TwitterScraper
from scrapers.tiktok_scraper import TikTokScraper
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
    # Variable para limitar el número de cuentas (None para procesar todas)
    LIMIT_ACCOUNTS = 2  # Cambia esto a None para procesar todos los candidatos
    
    # Ruta del archivo Excel de resultados (asumiendo que está en ../Colombia/)
    EXCEL_INPUT = os.path.join(os.path.dirname(HERRAMIENTAS_DIR), "Colombia", "Resultados electorales.xlsx")
    SHEET_NAME = "Redes Sociales"
    COLUMN_ID = "ID Candidato"
    COLUMN_TWITTER = "X / Twitter"
    COLUMN_TIKTOK = "TikTok"
    
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

        # Crear mapeo de Candidato -> IDs y Usuarios
        candidatos_data = []
        for _, row in df_excel.iterrows():
            tw_user = clean_username(row.get(COLUMN_TWITTER))
            tt_user = clean_username(row.get(COLUMN_TIKTOK))
            cand_id = row.get(COLUMN_ID)
            
            if tw_user or tt_user:
                candidatos_data.append({
                    "id_candidato": cand_id,
                    "twitter_user": tw_user,
                    "tiktok_user": tt_user,
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
    tw_scraper = TwitterScraper(token=APIFY_TOKEN, output_dir="resultados")
    tt_scraper = TikTokScraper(token=APIFY_TOKEN)

    # --- EJECUCIÓN ---
    for idx, cand in enumerate(candidatos_data, 1):
        print(f"\n--- [{idx}/{len(candidatos_data)}] PROCESANDO: {cand['nombre']} (ID: {cand['id_candidato']}) ---")
        
        # 1. Twitter
        if cand['twitter_user']:
            df_tw = tw_scraper.process_account(cand['twitter_user'], START_DATE, END_DATE)
            if not df_tw.empty:
                df_tw.insert(0, "id_candidato", cand['id_candidato']) # Agregar Foreign Key
                save_append(df_tw, os.path.join(OUTPUT_DIR, f"tweets_full.csv"))
        
        # 2. TikTok
        if cand['tiktok_user']:
            df_tt = tt_scraper.fetch_profile_data([cand['tiktok_user']], max_items=20, since=END_DATE, until=START_DATE)
            if not df_tt.empty:
                df_tt.insert(0, "id_candidato", cand['id_candidato']) # Agregar Foreign Key
                save_append(df_tt, os.path.join(OUTPUT_DIR, f"tiktok_full.csv"))

def save_append(df, filepath):
    """Guarda los resultados haciendo append si el archivo ya existe."""
    try:
        file_exists = os.path.isfile(filepath)
        # Usamos utf-8-sig y punto y coma
        df.to_csv(filepath, mode='a', index=False, header=not file_exists, encoding="utf-8-sig", sep=";")
        print(f"💾 Datos agregados a: {filepath}")
    except Exception as e:
        print(f"❌ Error al guardar/append en {filepath}: {e}")

if __name__ == "__main__":
    main()
