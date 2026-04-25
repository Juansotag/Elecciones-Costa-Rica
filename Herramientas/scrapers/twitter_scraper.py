import asyncio
import os
import datetime
import re
import random
from playwright.async_api import async_playwright
import pandas as pd

class TwitterPlaywrightScraper:
    def __init__(self, headless=False, user_data_dir=None):
        self.headless = headless
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.user_data_dir = user_data_dir or os.path.join(self.script_dir, "user_data")
        
    def parse_number(self, text):
        if not text: return 0
        text = re.sub(r'[^0-9.KMB]', '', text.upper())
        multiplier = 1
        if 'K' in text: multiplier = 1000; text = text.replace('K', '')
        elif 'M' in text: multiplier = 1000000; text = text.replace('M', '')
        elif 'B' in text: multiplier = 1000000000; text = text.replace('B', '')
        try:
            val = float(text)
            return int(val * multiplier)
        except:
            return 0

    def extract_metric(self, aria_label, keywords):
        if not aria_label: return 0
        for kw in keywords:
            match = re.search(r'(\d+[.,]?\d*[KMB]?)\s+' + kw, aria_label, re.IGNORECASE)
            if match:
                return self.parse_number(match.group(1))
        return 0

    async def scrape_account(self, context, handle, start_date, end_date):
        page = await context.new_page()
        posts_data = []
        handle = handle.strip('@')
        
        dt_end_plus = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        end_date_query = dt_end_plus.strftime("%Y-%m-%d")
        
        query = f"from:{handle} since:{start_date} until:{end_date_query}"
        search_url = f"https://x.com/search?q={query.replace(':', '%3A').replace(' ', '%20')}&src=typed_query&f=live"

        try:
            print(f"🔍 Navegando a X (@{handle})...")
            await page.goto(search_url, timeout=60000)
            
            # Simular un poco de movimiento inicial
            await page.mouse.move(random.randint(100, 600), random.randint(100, 600))
            
            try:
                await page.wait_for_selector('article[data-testid="tweet"], [data-testid="emptyState"]', timeout=20000)
            except:
                pass

            seen_ids = set()
            scroll_attempts = 0
            max_scrolls = 30
            consecutive_no_new = 0

            while scroll_attempts < max_scrolls:
                # Movimiento de mouse sutil
                if random.random() > 0.5:
                    await page.mouse.move(random.randint(0, 800), random.randint(0, 600))

                tweets = await page.locator('article[data-testid="tweet"]').all()
                new_found = 0
                
                for tweet in tweets:
                    try:
                        link_el = tweet.locator('a[href*="/status/"]')
                        if await link_el.count() == 0: continue
                        tweet_url = await link_el.first.get_attribute('href')
                        
                        if tweet_url in seen_ids: continue
                        seen_ids.add(tweet_url)
                        new_found += 1

                        text_el = tweet.locator('div[data-testid="tweetText"]')
                        text = await text_el.first.inner_text() if await text_el.count() > 0 else ""
                        time_str = await tweet.locator('time').first.get_attribute('datetime')
                        
                        reply_label = await tweet.locator('button[data-testid="reply"]').get_attribute('aria-label')
                        replies = self.extract_metric(reply_label, ['repl'])
                        
                        repost_label = await tweet.locator('button[data-testid="retweet"]').get_attribute('aria-label')
                        reposts = self.extract_metric(repost_label, ['repost'])
                        
                        like_label = await tweet.locator('button[data-testid="like"]').get_attribute('aria-label')
                        likes = self.extract_metric(like_label, ['like'])
                        
                        views_el = tweet.locator('a[href*="/analytics"]')
                        views_label = await views_el.get_attribute('aria-label') if await views_el.count() > 0 else ""
                        views = self.extract_metric(views_label, ['view'])

                        posts_data.append({
                            'account': handle,
                            'date': time_str,
                            'reply_count': replies,
                            'retweet_count': reposts,
                            'like_count': likes,
                            'view_count': views,
                            'text': text.replace("\n", " ").strip(),
                            'url': f"https://x.com{tweet_url}"
                        })
                        print(f"  [+] {time_str[:10]} | L:{likes} R:{reposts}")
                    except: continue
                
                if new_found > 0: consecutive_no_new = 0
                else: consecutive_no_new += 1
                
                if (len(tweets) == 0 and scroll_attempts > 2) or consecutive_no_new >= 5: break
                
                # Scroll aleatorio y pausa humana
                scroll_dist = random.randint(800, 1400)
                await page.evaluate(f"window.scrollBy(0, {scroll_dist})")
                
                # Esperar un tiempo aleatorio entre 2 y 5 segundos
                await page.wait_for_timeout(random.uniform(2500, 5000))
                scroll_attempts += 1

        except Exception as e:
            print(f"❌ Error para @{handle}: {e}")
        finally:
            await page.close()
        return posts_data

    async def run_scraper(self, accounts: list, start_date: str, end_date: str):
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                self.user_data_dir, 
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            page = await context.new_page()
            await page.goto("https://x.com/home")
            await page.wait_for_timeout(3000)
            
            if await page.locator('a[href="/login"]').count() > 0 or "login" in page.url:
                print("\n🔑 LOGIN REQUERIDO...")
                try:
                    await page.wait_for_selector('[data-testid="primaryColumn"]', timeout=300000)
                except:
                    await context.close(); return pd.DataFrame()
            await page.close()

            all_data = []
            for handle in accounts:
                data = await self.scrape_account(context, handle, start_date, end_date)
                all_data.extend(data)
                # Pausa aleatoria entre cuentas
                wait_between = random.uniform(3, 7)
                print(f"💤 Esperando {wait_between:.1f}s antes del siguiente candidato...")
                await asyncio.sleep(wait_between)
            
            await context.close()
            return pd.DataFrame(all_data)
