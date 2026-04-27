import csv
import time
import random
import argparse
import os
from datetime import datetime
from scraper import InstagramScraper

def main():
    parser = argparse.ArgumentParser(description="Batch Instagram Scraper por Rango de Fechas")
    # Fechas por defecto alineadas con el resto del proyecto
    parser.add_argument("--start_date", type=str, default="2023-10-22", help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, default="2023-10-29", help="Fecha fin (YYYY-MM-DD)")
    parser.add_argument("--accounts_file", type=str, default="test_accounts.txt", help="Archivo con lista de cuentas")
    parser.add_argument("--output_file", type=str, default="test_results.csv", help="Archivo CSV de salida")
    
    args = parser.parse_args()
    
    # Convertir strings a objetos datetime para el filtro
    try:
        dt_start = datetime.strptime(args.start_date, "%Y-%m-%d")
        # El final del día de la fecha de fin
        dt_end = datetime.strptime(args.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    except ValueError:
        print("Error: El formato de fecha debe ser YYYY-MM-DD")
        return
    
    scraper = InstagramScraper()
    
    # Verificamos si el archivo ya existe para no escribir cabeceras duplicadas
    file_exists = os.path.isfile(args.output_file)
    
    with open(args.output_file, mode='a', newline='', encoding='utf-8-sig') as csvfile:
        # Estructura de columnas solicitada
        fieldnames = ['date_fetch', 'account', 'followers', 'post_id', 'post_timestamp', 'likes', 'comments', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        
        if not file_exists:
            writer.writeheader()
        
        try:
            with open(args.accounts_file, 'r') as f:
                accounts = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo de cuentas '{args.accounts_file}'.")
            return

        print(f"--- Iniciando Scraping de {len(accounts)} cuentas ---")
        print(f"Rango: {args.start_date} al {args.end_date}\n")

        for user in accounts:
            print(f"Procesando: @{user}...")
            
            # 1. Obtener info de la cuenta
            info = scraper.get_account_data(user)
            if not info:
                print(f"  Saltando @{user} por error en perfil.")
                continue
            
            followers = info['followers']
            
            # 2. Obtener posts en el rango
            posts = scraper.get_posts_in_range(user, dt_start, dt_end)
            
            for post in posts:
                writer.writerow({
                    'date_fetch': datetime.now().strftime("%Y-%m-%d"),
                    'account': user,
                    'followers': followers,
                    'post_id': post['post_id'],
                    'post_timestamp': post['date'].strftime("%Y-%m-%d %H:%M:%S"),
                    'likes': post['likes'],
                    'comments': post['comments'],
                    'url': post['url']
                })
            
            print(f"  Hecho: {len(posts)} posts guardados para @{user}.")
            
            # Pausa aleatoria para evitar que Instagram nos bloquee la IP
            wait = random.uniform(6, 12)
            time.sleep(wait)

if __name__ == "__main__":
    main()
