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

class TwitterScraper:
    def __init__(self, token: str = None, output_dir: str = "resultados"):
        self.token = token or os.getenv("APIFY_TOKEN")
        if not self.token:
            raise ValueError("❌ No se encontró el APIFY_TOKEN. Verifica tu archivo .env")
        
        self.client = ApifyClient(self.token)
        self.actor_id = "gentle_cloud/twitter-tweets-scraper"
        self.output_dir = Path(HERRAMIENTAS_DIR) / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.colombia_tz = ZoneInfo("America/Bogota")

    def process_account(self, account: str, start_date: str, end_date: str, max_tweets: int = 200) -> pd.DataFrame:
        """Procesa una cuenta específica usando el Actor de Apify."""
        # Nota: El formato usual de búsqueda es from:usuario since:fecha until:fecha
        query = f"from:{account} since:{start_date} until:{end_date}"
        print(f"\n🚀 Iniciando Apify Twitter Scraper para @{account}...")
        print(f"🔎 Query: {query}")

        run_input = {
            "searchQueries": [query],
            "maxTweets": max_tweets,
            "getRetweets": True,
            "includeUserContext": True
        }

        try:
            # Llamar al actor
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            print(f"✅ Proceso completado en Apify para @{account}. Descargando dataset...")
            
            # Obtener resultados
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not items:
                print(f"⚠️ No se encontraron tuits para @{account}")
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
            df["account_queried"] = account

            # Formatear fechas si existen (los nombres de columnas pueden variar en Apify)
            date_cols = ["createdAt", "created_at", "date"]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                    df[f"{col}_col"] = df[col].dt.tz_convert("America/Bogota").dt.tz_localize(None)
            
            print(f"📊 {len(df)} tuits obtenidos para @{account}")
            return df

        except Exception as e:
            print(f"❌ Error procesando @{account} con Apify: {e}")
            traceback.print_exc()
            return pd.DataFrame()

    def save_results(self, combined_df: pd.DataFrame, individual_dfs: Dict[str, pd.DataFrame], start_date: str, end_date: str):
        """Guarda los resultados en Excel y CSV."""
        if combined_df.empty:
            print("⚠️ No hay datos para guardar.")
            return

        filename_base = f"tweets_apify_{start_date}_to_{end_date}"
        xlsx_path = self.output_dir / f"{filename_base}.xlsx"
        csv_path = self.output_dir / f"{filename_base}.csv"

        try:
            # Excel con múltiples hojas
            with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
                combined_df.to_excel(writer, sheet_name="Todos", index=False)
                for acc, df in individual_dfs.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=acc[:31], index=False)

            # CSV de respaldo
            combined_df.to_csv(csv_path, index=False, encoding="utf-8-sig", sep=";")
            
            print(f"\n✨ Guardado exitoso!")
            print(f"📊 Excel: {xlsx_path}")
            print(f"💾 CSV: {csv_path}")

        except Exception as e:
            print(f"❌ Error al guardar archivos: {e}")
            traceback.print_exc()
