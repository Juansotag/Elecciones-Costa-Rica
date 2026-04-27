import instaloader
import argparse
from datetime import datetime, timedelta
import time
import sys

class InstagramScraper:
    def __init__(self):
        self.L = instaloader.Instaloader()
        # Puedes cargar sesión aquí si fuera necesario
        # self.L.load_session_from_file('tu_usuario')

    def get_account_data(self, username):
        """Obtiene metadatos de la cuenta, incluyendo seguidores."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            return {
                "username": profile.username,
                "followers": profile.followers,
                "is_private": profile.is_private,
                "is_verified": profile.is_verified
            }
        except instaloader.ProfileNotExistsException:
            print(f"Error: El perfil {username} no existe.")
            return None
        except Exception as e:
            print(f"Error obteniendo datos para {username}: {e}")
            return None

    def get_posts_in_range(self, username, start_date, end_date):
        """Extrae posts dentro de un rango de fechas específico."""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            posts_data = []
            
            print(f"Buscando posts para {username} entre {start_date.date()} y {end_date.date()}...")
            
            for post in profile.get_posts():
                # Si el post es más reciente que nuestra fecha de fin, lo saltamos
                if post.date > end_date:
                    continue
                
                # Si el post es más antiguo que nuestra fecha de inicio, dejamos de buscar
                if post.date < start_date:
                    break
                
                posts_data.append({
                    "date": post.date,
                    "post_id": post.shortcode,
                    "likes": post.likes,
                    "comments": post.comments,
                    "url": f"https://www.instagram.com/p/{post.shortcode}/"
                })
                
                # Pequeña pausa para no saturar a Instagram
                time.sleep(1.5) 
                
            return posts_data
            
        except Exception as e:
            print(f"Error extrayendo posts de {username}: {e}")
            return []

if __name__ == "__main__":
    # Mantengo el main original por compatibilidad pero con la nueva lógica
    print("Usa batch_scraper.py para ejecución por lotes.")
