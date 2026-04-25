import os
import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv
from pathlib import Path

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

    def fetch_profile_data(self, usernames: list, max_items: int = 200, since: str = "", until: str = ""):
        """
        Llama al actor de Apify para extraer datos de perfiles de TikTok.
        """
        run_input = {
            "maxItems": max_items,
            "usernames": usernames,
            "since": since,
            "until": until
        }

        print(f"🚀 Iniciando scraper de TikTok para: {usernames}")
        print(f"📅 Rango: {until} al {since}")

        try:
            # Llamar al actor de forma síncrona
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            print(f"✅ Proceso completado en Apify. Descargando resultados del dataset...")
            
            # Obtener los items del dataset
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not items:
                print("⚠️ No se encontraron resultados.")
                return pd.DataFrame()

            df = pd.DataFrame(items)
            print(f"📊 Se obtuvieron {len(df)} registros.")
            return df

        except Exception as e:
            print(f"❌ Error al llamar a Apify: {e}")
            return pd.DataFrame()

    def save_to_csv(self, df: pd.DataFrame, filename: str = "tiktok_results.csv"):
        if df.empty:
            print("⚠️ No hay datos para guardar.")
            return
        
        output_path = Path(HERRAMIENTAS_DIR) / "resultados"
        output_path.mkdir(parents=True, exist_ok=True)
        
        full_path = output_path / filename
        # Usamos utf-8-sig para que Excel lo abra bien y punto y coma como separador
        df.to_csv(full_path, index=False, encoding="utf-8-sig", sep=";")
        print(f"💾 Resultados guardados en: {full_path}")

if __name__ == "__main__":
    # Ejemplo de uso
    scraper = TikTokScraper()
    
    # Datos de entrada según tu JSON
    usernames = ["carlosfgalan"]
    max_items = 20
    since = "2023-10-29"
    until = "2023-10-22"
    
    df = scraper.fetch_profile_data(usernames, max_items, since, until)
    scraper.save_to_csv(df, f"tiktok_{usernames[0]}_{until}_al_{since}.csv")
