import os
import pandas as pd
import json
from apify_client import ApifyClient
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Cargar variables de entorno (buscando en el directorio padre de 'scrapers')
SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
HERRAMIENTAS_DIR = os.path.dirname(SCRAPER_DIR)
load_dotenv(os.path.join(HERRAMIENTAS_DIR, ".env"))

class TikTokScraper:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("APIFY_TOKEN")
        if not self.token:
            raise ValueError("❌ No se encontró el APIFY_TOKEN. Verifica tu archivo .env")
        self.client = ApifyClient(self.token)
        self.actor_id = "apidojo/tiktok-profile-scraper"
        self.colombia_tz = ZoneInfo("America/Bogota")

    def fetch_profile_data(self, usernames: list, max_items: int = 100, start_date: str = "", end_date: str = ""):
        """
        Llama al actor de Apify para extraer datos de perfiles de TikTok y filtra por fecha.
        """
        # NOTA: Según las pruebas del usuario, este actor específico espera:
        # "since" -> Fecha más reciente (Final)
        # "until" -> Fecha más antigua (Inicio)
        run_input = {
            "maxItems": max_items,
            "usernames": usernames,
            "since": end_date,
            "until": start_date
        }

        print(f"🚀 Iniciando scraper de TikTok para: {usernames}")
        print(f"📅 Rango solicitado: {start_date} al {end_date}")

        try:
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            print(f"✅ Proceso completado en Apify. Descargando resultados...")
            
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not items:
                print("⚠️ No se encontraron resultados en TikTok.")
                return pd.DataFrame()

            df = pd.DataFrame(items)

            # --- FILTRADO POR FECHAS (POST-PROCESO) ---
            # En TikTok suele venir en 'createTime' como timestamp
            if "createTime" in df.columns:
                df["createTime_dt"] = pd.to_datetime(df["createTime"], unit="s", utc=True)
                
                limit_start = pd.to_datetime(start_date).tz_localize("UTC")
                # El end_date lo llevamos al final del día
                limit_end = pd.to_datetime(end_date).tz_localize("UTC").replace(hour=23, minute=59, second=59)
                
                mask = (df["createTime_dt"] >= limit_start) & (df["createTime_dt"] <= limit_end)
                df_filtered = df.loc[mask].copy()
                
                print(f"✂️ Filtrado TikTok: de {len(df)} videos descargados, {len(df_filtered)} están en el rango {start_date} - {end_date}")
                df = df_filtered

            if df.empty:
                return pd.DataFrame()

            # Serializar dicts/lists
            for col in df.columns:
                df[col] = df[col].apply(
                    lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x
                )

            # Formatear fecha para Colombia
            if "createTime_dt" in df.columns:
                df["createTime_col"] = df["createTime_dt"].dt.tz_convert("America/Bogota").dt.tz_localize(None)

            return df

        except Exception as e:
            print(f"❌ Error en TikTok Scraper: {e}")
            return pd.DataFrame()

    def save_to_csv(self, df: pd.DataFrame, filename: str = "tiktok_results.csv"):
        # Mantenemos este método por compatibilidad, aunque main.py usa save_append
        if df.empty: return
        output_path = Path(HERRAMIENTAS_DIR) / "resultados"
        output_path.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path / filename, index=False, encoding="utf-8-sig", sep=";")
