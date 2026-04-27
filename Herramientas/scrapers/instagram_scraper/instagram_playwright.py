import asyncio
import os
import datetime
import re
import random
from playwright.async_api import async_playwright
import pandas as pd

# Configuración
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(SCRIPT_DIR, 'test_accounts.txt')
RESULTS_FILE = os.path.join(SCRIPT_DIR, 'test_results_insta.csv')
SCREENSHOT_PATH = os.path.join(SCRIPT_DIR, 'error_instagram.png')
HEADLESS = False 

DEFAULT_START_DATE = "2023-10-22"
DEFAULT_END_DATE = "2023-10-29"

def parse_number(text):
    if not text: return 0
    text = re.sub(r'[^0-9]', '', text)
    try: return int(text)
    except: return 0

async def dismiss_popups(page):
    popups = ["Ahora no", "Not now", "Cerrar", "Close", "Aceptar", "Accept"]
    for text in popups:
        try:
            btn = page.get_by_role("button", name=re.compile(text, re.IGNORECASE))
            if await btn.count() > 0:
                await btn.first.click(timeout=3000)
                await asyncio.sleep(1)
        except: pass

async def scrape_instagram_account(context, handle, start_date, end_date):
    page = await context.new_page()
    posts_data = []
    handle = handle.strip('@')
    
    dt_start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    dt_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59)

    try:
        print(f"\n🚀 Navegando a: @{handle}")
        # Intentar cargar la página con un tiempo de espera generoso
        await page.goto(f"https://www.instagram.com/{handle}/", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(8)
        
        # Guardar título para diagnóstico
        title = await page.title()
        print(f"  📄 Título detectado: '{title}'")

        # Intentar despertar la página con scroll
        await page.mouse.wheel(0, 600)
        await asyncio.sleep(3)
        await page.mouse.wheel(0, -600)
        await asyncio.sleep(2)
        
        await dismiss_popups(page)

        # Verificar si hay posts reales
        first_post_selector = 'article a[href*="/p/"]'
        if await page.locator(first_post_selector).count() == 0:
            print("  ⚠️ No se ven posts. Tomando captura de diagnóstico...")
            await page.screenshot(path=SCREENSHOT_PATH)
            print(f"  📸 Captura guardada en: {SCREENSHOT_PATH}")
            
            # Verificar si es por login
            if "login" in page.url.lower():
                print("  🔑 REDIRECCIÓN A LOGIN DETECTADA. Debes loguearte primero.")
            return []

        # Click en el primer post
        try:
            first_post = page.locator(first_post_selector).first
            await first_post.click(force=True)
            await page.wait_for_selector('time', timeout=15000)
        except Exception as e:
            await page.screenshot(path=SCREENSHOT_PATH)
            print(f"  ❌ Fallo al abrir el post: {e}. Captura guardada.")
            return []

        while True:
            # 1. Extraer Fecha
            time_el = page.locator('time').first
            time_str = await time_el.get_attribute('datetime')
            post_dt = datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00')).replace(tzinfo=None)

            if post_dt > dt_end:
                pass 
            elif post_dt < dt_start:
                print(f"  🏁 Límite alcanzado ({start_date}).")
                break
            else:
                likes = 0
                try:
                    metrics_text = await page.locator('section').filter(has=page.locator('span')).first.inner_text()
                    match = re.search(r'([0-9.,KMB]+)', metrics_text)
                    if match: likes = parse_number(match.group(1))
                except: pass

                posts_data.append({
                    'account': handle, 'date': post_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    'likes': likes, 'url': page.url
                })
                print(f"  [+] {post_dt.strftime('%Y-%m-%d')} | L: {likes}")

            # 2. Navegar al siguiente
            next_btn = page.locator('svg[aria-label="Siguiente"], svg[aria-label="Next"]').locator('..')
            if await next_btn.count() > 0:
                await next_btn.first.click()
                await asyncio.sleep(random.uniform(3, 6))
            else:
                print("  🏁 Fin de la galería.")
                break

    except Exception as e:
        print(f"❌ Error en @{handle}: {e}")
    finally:
        await page.close()
    return posts_data

async def main():
    print("\n" + "="*60)
    print("   INSTAGRAM SCRAPER (PLAYWRIGHT / DIAGNÓSTICO)")
    print("="*60)
    
    start = DEFAULT_START_DATE
    end = DEFAULT_END_DATE
    
    if not os.path.exists(ACCOUNTS_FILE): return

    with open(ACCOUNTS_FILE, 'r') as f:
        accounts = [line.strip() for line in f if line.strip()]

    async with async_playwright() as p:
        user_data = os.path.join(SCRIPT_DIR, 'insta_user_data')
        
        # Lanzamiento con modo anti-detección reforzado
        context = await p.chromium.launch_persistent_context(
            user_data, 
            headless=HEADLESS,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        page = await context.new_page()
        await page.goto("https://www.instagram.com/", wait_until="networkidle")
        
        # Forzar Login si es necesario
        if await page.locator('input[name="username"]').count() > 0:
            print("\n🔑 ESPERANDO LOGIN... (Manten esta ventana abierta hasta loguearte)")
            try:
                await page.wait_for_selector('svg[aria-label="Inicio"], svg[aria-label="Home"]', timeout=300000)
                print("✅ Sesión detectada.")
                await asyncio.sleep(5)
                await dismiss_popups(page)
            except:
                print("❌ Login fallido."); await context.close(); return
        
        await page.close()

        all_results = []
        for handle in accounts:
            data = await scrape_instagram_account(context, handle, start_date=start, end_date=end)
            all_results.extend(data)
            await asyncio.sleep(random.uniform(10, 20)) # Pausa larga entre candidatos
        
        if all_results:
            df = pd.DataFrame(all_results)
            df.to_csv(RESULTS_FILE, index=False, sep=";", encoding="utf-8-sig")
            print(f"\n🎉 HECHO. Datos en {RESULTS_FILE}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
