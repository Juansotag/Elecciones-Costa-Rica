import asyncio
import csv
import datetime
import os
import re
from playwright.async_api import async_playwright, TimeoutError

# Configuration
ACCOUNTS_FILE = 'accounts.txt'
RESULTS_FILE = 'results.csv'
HEADLESS = False  # Set to False to see the browser (helpful for debugging/login)

def read_accounts(filepath):
    """Reads account handles from a file."""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return []
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def parse_number(text):
    """Parses number strings like '1.2K', '5M', '10,000' into integers."""
    if not text:
        return 0
    text = text.replace(',', '')
    multiplier = 1
    if 'K' in text:
        multiplier = 1000
        text = text.replace('K', '')
    elif 'M' in text:
        multiplier = 1000000
        text = text.replace('M', '')
    elif 'B' in text:
        multiplier = 1000000000
        text = text.replace('B', '')
    
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return 0

async def scrape_account(context, handle, n_days):
    """Scrapes a single account for posts from the last n_days."""
    page = await context.new_page()
    posts_data = []
    followers_count = 0
    
    try:
        print(f"Navigating to https://x.com/{handle}...")
        # Increase timeout for navigation and remove strict networkidle check which often fails on X
        await page.goto(f"https://x.com/{handle}", timeout=60000)
        try:
            await page.wait_for_load_state('domcontentloaded', timeout=30000)
        except Exception:
            print("Warning: domcontentloaded timed out, continuing...")

        # Wait for ANY content to load (profile header or timeline)
        try:
            await page.wait_for_selector('div[data-testid="primaryColumn"]', timeout=15000)
        except Exception:
            print("Warning: primary column not found, page might not have loaded correctly.")
        
        # Extract Followers
        try:
            # Try multiple selectors for followers
            followers_element = await page.wait_for_selector('a[href$="/verified_followers"] span, a[href$="/followers"] span', timeout=10000)
            if followers_element:
                followers_text = await followers_element.inner_text()
                followers_count = parse_number(followers_text)
                print(f"Account: {handle}, Followers: {followers_count}")
        except Exception as e:
            print(f"Could not extract followers for {handle}: {e}")

        # Navigate to tweets (sometimes profile defaults to "Highlights" or other tabs)
        # We want the main timeline. Usually just the profile URL is fine, but let's ensure we are on the right tab if needed.
        # For now, we assume the default view shows tweets.
        
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=n_days)
        print(f"Scraping posts since {cutoff_date.strftime('%Y-%m-%d')}...")

        # Keep track of unique tweet IDs to avoid duplicates
        seen_tweet_ids = set()
        consecutive_old_tweets = 0
        last_height = await page.evaluate("document.body.scrollHeight")
        scrolled_same_count = 0
        
        while True:
            # Get all articles (tweets)
            tweets = await page.locator('article[data-testid="tweet"]').all()
            
            new_tweets_found = False
            for tweet in tweets:
                try:
                    # 1. Extract Tweet URL first (needed for ID and Author check)
                    link_element = tweet.locator('a[href*="/status/"]')
                    #print('_____-_____')
                    #print(link_element)
                    #print('tweet text: ', await tweet.locator('div[data-testid="tweetText"]').inner_text())
                    if await link_element.count() > 0:
                        tweet_url = await link_element.first.get_attribute('href')
                    else:
                        continue
                    #print(f"Tweet URL: {tweet_url}", "Tweet text: ", await tweet.locator('div[data-testid="tweetText"]').inner_text())
                    # 2. Check Author via URL to distinguish Reposts from Originals/Quotes
                    # Originals/Quotes have the handle in the URL: /Handle/status/ID
                    # Reposts have the original author's handle: /Other/status/ID
                    # We check if the URL contains the target handle.
                    
                    # Normalize handle (remove @, lower case)
                    target_handle = handle.lower().strip('@')
                    if f"/{target_handle}/status/" not in tweet_url.lower():
                        # This is a Repost (or other content), skip it.
                        # We do NOT add to seen_tweet_ids here because we might want to skip it silently, 
                        # but actually adding it to seen is fine to avoid re-checking.
                        # However, for the stop logic, we just continue.
                        continue

                    # Deduplicate
                    if tweet_url in seen_tweet_ids:
                        continue
                    seen_tweet_ids.add(tweet_url)
                    post_id = tweet_url.split('/')[-1]

                    # 3. Check if Pinned
                    social_context = tweet.locator('div[data-testid="socialContext"]')
                    is_pinned = False
                    if await social_context.count() > 0:
                        text = await social_context.first.inner_text()
                        if "Pinned" in text:
                            is_pinned = True

                    # 4. Check Date
                    time_element = tweet.locator('time')
                    if await time_element.count() == 0:
                        continue
                        
                    # Use .first to avoid strict mode violation in case of Quote Tweets (which have 2 time elements)
                    timestamp_str = await time_element.first.get_attribute('datetime')
                    post_datetime = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    if post_datetime < cutoff_date:
                        if not is_pinned:
                             consecutive_old_tweets += 1
                             if consecutive_old_tweets >= 5:
                                 print(f"Reached posts older than {n_days} days. Stopping.")
                                 return posts_data
                        # If pinned and old, just skip saving it, but don't stop.
                        continue
                    else:
                        # Found a new tweet (Original or Quote)
                        if not is_pinned:
                            consecutive_old_tweets = 0
                    
                    # Extract Text
                    text_element = tweet.locator('div[data-testid="tweetText"]')
                    post_text = ""
                    if await text_element.count() > 0:
                        # Use .first to avoid strict mode violation in case of Quote Tweets
                        post_text = await text_element.first.inner_text()
                        # Clean up newlines and collapse whitespace
                        post_text = re.sub(r'\s+', ' ', post_text).strip()

                    new_tweets_found = True
                    
                    # Metrics
                    # Comments (Replies)
                    comments_loc = tweet.locator('button[data-testid="reply"]')
                    comments_count = 0
                    if await comments_loc.count() > 0:
                        aria_label = await comments_loc.get_attribute('aria-label')
                        if aria_label:
                            clean_text = aria_label.lower().replace(' replies', '').replace(' reply', '')
                            comments_count = parse_number(clean_text)
                        else:
                            comments_val = await comments_loc.inner_text()
                            comments_count = parse_number(comments_val)

                    # Likes
                    likes_loc = tweet.locator('button[data-testid="like"]')
                    likes_count = 0
                    if await likes_loc.count() > 0:
                        aria_label = await likes_loc.get_attribute('aria-label')
                        if aria_label:
                            clean_text = aria_label.lower().replace(' likes', '').replace(' like', '')
                            likes_count = parse_number(clean_text)
                        else:
                            likes_val = await likes_loc.inner_text()
                            likes_count = parse_number(likes_val)

                    # Reposts
                    retweets_loc = tweet.locator('button[data-testid="retweet"]')
                    retweets_count = 0
                    if await retweets_loc.count() > 0:
                        aria_label = await retweets_loc.get_attribute('aria-label')
                        if aria_label:
                            clean_text = aria_label.lower().replace(' reposts', '').replace(' repost', '')
                            retweets_count = parse_number(clean_text)
                        else:
                            retweets_val = await retweets_loc.inner_text()
                            retweets_count = parse_number(retweets_val)
                        
                    # Add to results
                    posts_data.append({
                        'fetch_datetime': datetime.datetime.now().isoformat(),
                        'fetch_N_days': n_days,
                        'account': handle,
                        'followers': followers_count,
                        'post_datetime': post_datetime.isoformat(),
                        'post_comments': comments_count,
                        'post_likes': likes_count,
                        'post_reposts': retweets_count,
                        'post_id': post_id,
                        'post_text': post_text
                    })
                    
                except Exception as e:
                    print(f"\n!!! Error parsing tweet !!!")
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        # Try to print some context about the failing tweet
                        if await tweet.locator('div[data-testid="tweetText"]').count() > 0:
                            text = await tweet.locator('div[data-testid="tweetText"]').inner_text()
                            print(f"Failing Tweet Text: {text}")
                        else:
                            print("Failing Tweet has no text element.")
                        
                        # Print the HTML of the tweet for inspection
                        # print(f"Tweet HTML: {await tweet.inner_html()}") 
                    except Exception as inner_e:
                        print(f"Could not retrieve failing tweet context: {inner_e}")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
                    continue

            # Scroll logic improvement: Slower scrolling to ensure all tweets load
            # Scroll by half the viewport height to avoid skipping content
            await page.evaluate("window.scrollBy(0, window.innerHeight * 0.5)")
            await page.wait_for_timeout(2000) # Wait for load (increased from 1500)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            current_scroll = await page.evaluate("window.scrollY + window.innerHeight")

            if new_height <= current_scroll + 50: # Close to bottom
                 scrolled_same_count += 1
                 if scrolled_same_count > 10: # Try more times (slower scroll means more steps needed)
                    print("Reached end of timeline or stuck.")
                    break
            else:
                scrolled_same_count = 0
                last_height = new_height
                
            # Stop condition based on date is handled inside the loop
            
    except Exception as e:
        print(f"Error scraping {handle}: {e}")
    finally:
        await page.close()
        
    return posts_data

async def main():
    # Get N days input
    try:
        n_days = int(input("Enter N (number of days to look back): "))
    except ValueError:
        print("Invalid input. Defaulting to 7 days.")
        n_days = 7
        
    accounts = read_accounts(ACCOUNTS_FILE)
    if not accounts:
        print("No accounts found.")
        return

    # Persistent context for login session
    user_data_dir = './user_data'
    
    async with async_playwright() as p:
        # Launch browser with persistent context
        print("Launching browser...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=HEADLESS,
            channel="chrome", # Try to use installed chrome if available, or just chromium
            args=["--disable-blink-features=AutomationControlled"] # Try to hide automation
        )
        
        # Check login status
        page = await context.new_page()
        await page.goto("https://x.com/home")
        await page.wait_for_timeout(3000)
        
        if "login" in page.url or await page.locator('a[href="/login"]').count() > 0:
            print("\n" + "="*50)
            print("PLEASE LOG IN TO X.COM IN THE BROWSER WINDOW.")
            print("The script will wait until you are logged in.")
            print("Once logged in (you see your timeline), press ENTER in this terminal to continue.")
            print("="*50 + "\n")
            
            print("Waiting for login... (Timeout in 5 minutes)")
            try:
                await page.wait_for_selector('div[data-testid="SideNav_AccountSwitcher_Button"]', timeout=300000) # 5 mins
                print("Login detected!")
            except TimeoutError:
                print("Login timed out. Exiting.")
                await context.close()
                return
        else:
            print("Already logged in.")
            
        await page.close()

        all_data = []
        for handle in accounts:
            print(f"Processing {handle}...")
            data = await scrape_account(context, handle, n_days)
            all_data.extend(data)
            await asyncio.sleep(2) # Polite delay

        # Save results
        if all_data:
            keys = ['fetch_datetime', 'fetch_N_days', 'account', 'followers', 'post_datetime', 'post_comments', 'post_likes', 'post_reposts', 'post_id', 'post_text']
            file_exists = os.path.exists(RESULTS_FILE)
            
            with open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(all_data)
            print(f"Appended {len(all_data)} posts to {RESULTS_FILE}")
        else:
            print("No posts found.")

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
