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
        # Cambiamos al actor que el usuario prefiere (Lite Scraper que usa URLs)
        self.actor_id = "apidojo/twitter-scraper-lite" 
        self.output_dir = Path(HERRAMIENTAS_DIR) / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.colombia_tz = ZoneInfo("America/Bogota")

    def process_account(self, account: str, start_date: str, end_date: str, max_tweets: int = 100) -> pd.DataFrame:
        """Procesa una cuenta específica usando el Lite Scraper de Apify."""
        
        # El usuario prefiere URLs completas para este actor
        url = f"https://x.com/{account}"
        print(f"\n🚀 Iniciando Apify Lite Scraper para @{account}...")
        print(f"📅 Rango deseado: {start_date} al {end_date}")

        run_input = {
            "result_count": max_tweets,
            "since_date": start_date, # El actor solo acepta fecha inicial
            "start_urls": [
                { "url": url }
            ]
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

            # --- FILTRADO POR FECHAS (POST-PROCESO) ---
            # Identificar columna de fecha
            date_col = "createdAt" if "createdAt" in df.columns else "created_at"
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce", utc=True)
                
                # Convertir límites a datetime para comparar
                limit_start = pd.to_datetime(start_date).tz_localize("UTC")
                limit_end = pd.to_datetime(end_date).tz_localize("UTC").replace(hour=23, minute=59, second=59)
                
                # Filtrar
                mask = (df[date_col] >= limit_start) & (df[date_col] <= limit_end)
                df_filtered = df.loc[mask].copy()
                
                print(f"✂️ Filtrado: de {len(df)} tuits descargados, {len(df_filtered)} están en el rango {start_date} - {end_date}")
                df = df_filtered

            if df.empty:
                return pd.DataFrame()

            # Serializar estructuras complejas
            for col in df.columns:
                df[col] = df[col].apply(
                    lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x
                )

            # Agregar metadatos
            now = datetime.now(self.colombia_tz)
            df["timestamp_descarga"] = now.strftime("%Y-%m-%d %H:%M:%S")
            df["account_queried"] = account

            # Formatear fechas para el usuario (Bogotá)
            if date_col in df.columns:
                df[f"{date_col}_col"] = df[date_col].dt.tz_convert("America/Bogota").dt.tz_localize(None)
            
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
