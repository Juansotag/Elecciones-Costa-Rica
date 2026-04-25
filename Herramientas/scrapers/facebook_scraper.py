import os
import pandas as pd
import json
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import List, Optional, Dict, Any
from apify_client import ApifyClient
from dotenv import load_dotenv

# Cargar variables de entorno (buscando en el directorio padre de 'scrapers')
SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
HERRAMIENTAS_DIR = os.path.dirname(SCRAPER_DIR)
load_dotenv(os.path.join(HERRAMIENTAS_DIR, ".env"))

class FacebookScraper:
    def __init__(self, token: str = None, output_dir: str = "resultados"):
        self.token = token or os.getenv("APIFY_TOKEN")
        if not self.token:
            raise ValueError("❌ No se encontró el APIFY_TOKEN. Verifica tu archivo .env")
        
        self.client = ApifyClient(self.token)
        self.actor_id = "apify/facebook-posts-scraper"
        self.output_dir = Path(HERRAMIENTAS_DIR) / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.colombia_tz = ZoneInfo("America/Bogota")

    def process_account(self, fb_url: str, start_date: str, end_date: str, max_posts: int = 10) -> pd.DataFrame:
        """Procesa una cuenta de Facebook usando el actor de Apify."""
        
        print(f"\n🚀 Iniciando Apify Facebook Scraper para: {fb_url}")
        print(f"📅 Rango deseado: {start_date} al {end_date}")

        run_input = {
            "captionText": False,
            "onlyPostsNewerThan": start_date,
            "onlyPostsOlderThan": end_date,
            "resultsLimit": max_posts,
            "startUrls": [
                { "url": fb_url, "method": "GET" }
            ]
        }

        try:
            # Llamar al actor
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            print(f"✅ Proceso completado en Apify para Facebook. Descargando dataset...")
            
            # Obtener resultados
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not items:
                print(f"⚠️ No se encontraron posts de Facebook para esta URL.")
                return pd.DataFrame()

            df = pd.DataFrame(items)

            # Serializar estructuras complejas
            for col in df.columns:
                df[col] = df[col].apply(
                    lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x
                )

            # Agregar metadatos
            now = datetime.now(self.colombia_tz)
            df["timestamp_descarga"] = now.strftime("%Y-%m-%d %H:%M:%S")
            df["fb_url_queried"] = fb_url

            # Formatear fechas si existen
            date_cols = ["time", "date", "createdAt"]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                    df[f"{col}_col"] = df[col].dt.tz_convert("America/Bogota").dt.tz_localize(None)
            
            print(f"📊 {len(df)} posts de Facebook obtenidos.")
            return df

        except Exception as e:
            print(f"❌ Error procesando Facebook con Apify: {e}")
            traceback.print_exc()
            return pd.DataFrame()
