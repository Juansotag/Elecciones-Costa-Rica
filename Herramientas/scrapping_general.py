import pandas as pd
import os
import json
import asyncio
import datetime
from scrapers.twitter_scraper import TwitterPlaywrightScraper as TwitterScraper
from scrapers.tiktok_scraper import TikTokScraper
from scrapers.facebook_scraper import FacebookScraper
from dotenv import load_dotenv

# Cargar variables de entorno
HERRAMIENTAS_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERRAMIENTAS_DIR, '.env'))

def main():
    # --- CONFIGURACIÓN ---
    APIFY_TOKEN = os.getenv("APIFY_TOKEN")
    START_DATE = "2023-10-22"
    END_DATE = "2023-10-29"
    
    # Interruptores
    SCRAPE_TWITTER = True
    SCRAPE_TIKTOK = False
    SCRAPE_FACEBOOK = False
    
    LIMIT_ACCOUNTS = 5
    MAX_TWEETS_PER_CANDIDATE = 50
    MAX_TIKTOK_PER_CANDIDATE = 50
    MAX_FACEBOOK_PER_CANDIDATE = 50
    
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
        print(f"Error: No se encontró el archivo Excel en {EXCEL_INPUT}")
        return

    try:
        print(f"Cargando candidatos desde Excel: {EXCEL_INPUT}")
        df_excel = pd.read_excel(EXCEL_INPUT, sheet_name=SHEET_NAME)
        
        def clean_username(val):
            if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan": return None
            val = str(val).strip()
            if "x.com/" in val: val = val.split("x.com/")[-1]
            elif "twitter.com/" in val: val = val.split("twitter.com/")[-1]
            elif "tiktok.com/@" in val: val = val.split("tiktok.com/@")[-1]
            return val.split("?")[0].strip("/").strip("@")

        candidatos_data = []
        for _, row in df_excel.iterrows():
            tw_user = clean_username(row.get(COLUMN_TWITTER))
            tt_user = clean_username(row.get(COLUMN_TIKTOK))
            fb_url = str(row.get(COLUMN_FACEBOOK)).strip() if not pd.isna(row.get(COLUMN_FACEBOOK)) else None
            cand_id = row.get(COLUMN_ID)
            
            if tw_user or tt_user or fb_url:
                candidatos_data.append({
                    "id_candidato": cand_id,
                    "twitter_user": tw_user,
                    "tiktok_user": tt_user,
                    "facebook_url": fb_url,
                    "nombre": row.get("Candidato")
                })
        
        if LIMIT_ACCOUNTS:
            candidatos_data = candidatos_data[:LIMIT_ACCOUNTS]
        print(f"Se procesaran {len(candidatos_data)} candidatos.")
    except Exception as e:
        print(f"Error al leer el Excel: {e}"); return

    # --- INICIALIZAR SCRAPERS ---
    tw_scraper = TwitterScraper(headless=False)
    tt_scraper = TikTokScraper(token=APIFY_TOKEN)
    fb_scraper = FacebookScraper(token=APIFY_TOKEN)

    # --- REGISTRO DE REPORTE ---
    reporte_ejecucion = []

    # --- EJECUCIÓN CON MANEJO DE ERRORES ---
    for idx, cand in enumerate(candidatos_data, 1):
        print(f"\n--- [{idx}/{len(candidatos_data)}] PROCESANDO: {cand['nombre']} ---")
        
        res_status = {
            "id_candidato": cand['id_candidato'],
            "nombre": cand['nombre'],
            "twitter_status": "No aplica" if not cand['twitter_user'] else "Pendiente",
            "twitter_count": 0,
            "tiktok_status": "No aplica" if not cand['tiktok_user'] else "Pendiente",
            "tiktok_count": 0,
            "facebook_status": "No aplica" if not cand['facebook_url'] else "Pendiente",
            "facebook_count": 0,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 1. Twitter
        if SCRAPE_TWITTER and cand['twitter_user']:
            try:
                print(f"  Twitter: @{cand['twitter_user']}...")
                df_tw = asyncio.run(tw_scraper.run_scraper([cand['twitter_user']], START_DATE, END_DATE))
                if not df_tw.empty:
                    df_tw.insert(0, "id_candidato", cand['id_candidato'])
                    save_append(df_tw, os.path.join(OUTPUT_DIR, "tweets_full.csv"))
                    res_status["twitter_status"] = "OK"
                    res_status["twitter_count"] = len(df_tw)
                else:
                    res_status["twitter_status"] = "Sin resultados"
            except Exception as e:
                print(f"  Error Twitter: {e}")
                res_status["twitter_status"] = f"ERROR: {str(e)[:50]}"

        # 2. TikTok
        if SCRAPE_TIKTOK and cand['tiktok_user']:
            try:
                print(f"  TikTok: @{cand['tiktok_user']}...")
                df_tt = tt_scraper.fetch_profile_data([cand['tiktok_user']], max_items=MAX_TIKTOK_PER_CANDIDATE, start_date=START_DATE, end_date=END_DATE)
                if not df_tt.empty:
                    df_tt.insert(0, "id_candidato", cand['id_candidato'])
                    save_append(df_tt, os.path.join(OUTPUT_DIR, "tiktok_full.csv"))
                    res_status["tiktok_status"] = "OK"
                    res_status["tiktok_count"] = len(df_tt)
                else:
                    res_status["tiktok_status"] = "Sin resultados"
            except Exception as e:
                print(f"  Error TikTok: {e}")
                res_status["tiktok_status"] = f"ERROR: {str(e)[:50]}"

        # 3. Facebook
        if SCRAPE_FACEBOOK and cand['facebook_url']:
            try:
                print(f"  Facebook: {cand['facebook_url']}...")
                df_fb = fb_scraper.process_account(cand['facebook_url'], START_DATE, END_DATE, max_posts=MAX_FACEBOOK_PER_CANDIDATE)
                if not df_fb.empty:
                    df_fb.insert(0, "id_candidato", cand['id_candidato'])
                    save_append(df_fb, os.path.join(OUTPUT_DIR, "facebook_full.csv"))
                    res_status["facebook_status"] = "OK"
                    res_status["facebook_count"] = len(df_fb)
                else:
                    res_status["facebook_status"] = "Sin resultados"
            except Exception as e:
                print(f"  Error Facebook: {e}")
                res_status["facebook_status"] = f"ERROR: {str(e)[:50]}"

        reporte_ejecucion.append(res_status)
        pd.DataFrame(reporte_ejecucion).to_csv(os.path.join(OUTPUT_DIR, "reporte_proceso.csv"), index=False, sep=";", encoding="utf-8-sig")

    # --- RESUMEN FINAL ---
    df_final = pd.DataFrame(reporte_ejecucion)
    print(f"\nPROCESO FINALIZADO")
    print(f"Reporte detallado en: {OUTPUT_DIR}/reporte_proceso.csv")
    
    # Metricas de uso
    for net in ['twitter', 'tiktok', 'facebook']:
        total_cand = len(df_final[df_final[f"{net}_status"] != "No aplica"])
        total_activos = len(df_final[df_final[f"{net}_count"] > 0])
        print(f"Total {net.capitalize()}: {total_cand} cuentas encontradas, {total_activos} con actividad en el periodo.")

def save_append(df, filepath):
    try:
        if df.empty: return
        file_exists = os.path.isfile(filepath)
        if file_exists:
            existing_df_header = pd.read_csv(filepath, sep=";", nrows=0, encoding="utf-8-sig")
            df = df.reindex(columns=existing_df_header.columns.tolist())
            df.to_csv(filepath, mode='a', index=False, header=False, encoding="utf-8-sig", sep=";")
        else:
            df.to_csv(filepath, index=False, encoding="utf-8-sig", sep=";")
    except Exception as e:
        print(f"    Error guardando: {e}")

if __name__ == "__main__":
    main()
