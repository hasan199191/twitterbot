import os
import time
import random
import logging
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from gmail_reader import GmailReader
from dotenv import load_dotenv
from utils import get_random_user_agent, random_delay

logger = logging.getLogger(__name__)

class TwitterClient:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        # Session dosyasının tam yolunu kullan
        self.session_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twitter_session.json")
        self.is_logged_in = False  # Varsayılan olarak False, login kontrolü yapılacak
        
    def _setup_browser(self):
        """Initialize the browser with appropriate settings"""
        logger.info("Setting up browser")
        self.playwright = sync_playwright().start()
        
        # Performans için geliştirilmiş tarayıcı argümanları
        browser_args = [
            "--no-sandbox", 
            "--disable-setuid-sandbox", 
            "--disable-dev-shm-usage",
            "--enable-gpu",  # GPU hızlandırmayı etkinleştir
            "--disable-features=IsolateOrigins,site-per-process",  # İzolasyonu azaltarak hız kazanma
            "--disable-site-isolation-trials",
            "--enable-features=NetworkService,NetworkServiceInProcess",
            "--force-gpu-rasterization",  # Grafik hızlandırma
            "--disable-accelerated-video-decode=false",
            "--window-size=1920,1080"  # Tam boyutlu pencere
        ]
        logger.info(f"Browser arguments: {browser_args}")
        
        # Check if storage state exists and is valid
        storage_path = Path(self.session_file)
        storage_state = None
        
        if storage_path.exists():
            try:
                # Check if file contains valid JSON
                import json
                with open(storage_path, 'r') as f:
                    json.load(f)
                storage_state = str(storage_path)
                logger.info(f"Using existing session file: {storage_path}")
            except json.JSONDecodeError:
                logger.warning("Invalid session file, will create new session")
                storage_state = None
        else:
            logger.info("No session file found, will create new session")
        
        # Geliştirilmiş tarayıcı başlatma
        # Ortama göre headless ayarı: Render veya X sunucusu yoksa headless=True
        import platform
        is_render = os.environ.get("RENDER", "0") == "1" or os.environ.get("RENDER") == "true"
        # Windows'ta DISPLAY yok, localde GUI için headless=False, Render'da headless=True
        if is_render:
            headless = True
        elif platform.system() == "Windows":
            headless = False
        else:
            headless = not os.environ.get("DISPLAY")
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=browser_args,
            slow_mo=50
        )
        logger.info(f"Browser launched successfully with headless={headless}")
        
        # İyileştirilmiş tarayıcı bağlamı
        self.context = self.browser.new_context(
            user_agent=get_random_user_agent(),
            storage_state=storage_state,
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
            has_touch=False,
            ignore_https_errors=True
        )
        logger.info("Browser context created")
        
        # Create page
        self.page = self.context.new_page()
        logger.info("Browser page created")
        
        # Önce session ile giriş dene, olmazsa otomatik login dene, o da olmazsa manuel login dene
        try:
            if storage_state is not None:
                logger.info("Navigating directly to Twitter home page with session file")
                self.page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=120000)
                logger.info("Successfully navigated to Twitter home page")
                random_delay(8, 15)
                self._check_login_state()
                if self.is_logged_in:
                    logger.info("Session ile login başarılı!")
                    return
                else:
                    logger.warning("Session dosyası ile login başarısız. Otomatik login denenecek.")
            # Session yoksa veya geçersizse otomatik login dene
            if self._auto_login():
                self._check_login_state()
                if self.is_logged_in:
                    logger.info("Otomatik login başarılı!")
                    return
                else:
                    logger.warning("Otomatik login başarısız. Manuel login denenecek.")
            # Otomatik login de başarısızsa manuel login (sadece localde, headless=False ise)
            if not (os.environ.get("RENDER", "0") == "1" or os.environ.get("RENDER") == "true") and (not os.environ.get("DISPLAY") is None or platform.system() == "Windows"):
                logger.info("No valid session, opening login page for manual login...")
                self.page.goto("https://x.com/login", wait_until="domcontentloaded", timeout=120000)
                logger.info("Lütfen tarayıcıda elle giriş yapın. Giriş yaptıktan sonra tarayıcıyı kapatabilirsiniz.")
                last_url = None
                for i in range(120):
                    current_url = self.page.url
                    if current_url != last_url:
                        logger.info(f"Current URL: {current_url}")
                        last_url = current_url
                    if current_url.startswith("https://x.com/home") or current_url.startswith("https://twitter.com/home"):
                        logger.info("Elle login başarılı! Session dosyası kaydediliyor.")
                        self.context.storage_state(path=self.session_file)
                        break
                    time.sleep(1)
                else:
                    logger.warning("Elle login başarısız veya tamamlanmadı.")
            else:
                logger.error("Otomatik ve manuel login başarısız! Render ortamında elle login mümkün değildir. Session dosyasını localde oluşturup deploy edin.")
        except Exception as e:
            logger.error(f"Error navigating to Twitter home: {str(e)}")
            self.page.screenshot(path="navigation_error.png")
        
        # SÜRE İYİLEŞTİRMESİ 2: Genel timeout ayarı
        self.page.set_default_timeout(120000)  # 60s → 120s
        logger.info("Default timeout set to 120 seconds")

        # Otomatik login dene
        self._check_login_state()
        if not self.is_logged_in:
            logger.info("Otomatik login deneniyor...")
            if self._auto_login():
                self._check_login_state()
    
    def _check_login_state(self):
        """Check if the bot is logged in by looking for a UI element only visible when logged in."""
        try:
            # Look for the tweet compose box or user avatar
            selectors = [
                '[data-testid="SideNav_AccountSwitcher_Button"]',  # Avatar button
                '[data-testid="tweetTextarea_0"]',  # Compose box
                'a[aria-label*="Profile"]',
                'div[aria-label*="Account menu"]',
            ]
            found = False
            for selector in selectors:
                if self.page.query_selector(selector):
                    found = True
                    logger.info(f"Login state check: found element '{selector}', session is valid and logged in.")
                    break
            if not found:
                logger.warning("Login state check: could not find any logged-in UI elements. Session may be invalid or logged out.")
                self.is_logged_in = False
            else:
                self.is_logged_in = True
        except Exception as e:
            logger.error(f"Login state check failed: {str(e)}")
            self.is_logged_in = False

    def _split_into_tweets(self, content):
        """Split content into tweets while preserving sentence integrity"""
        # Give some buffer space for safety (URLs, emojis, etc.)
        TWEET_LIMIT = 260  # Reduced from 280 to give safety margin
        
        def clean_and_trim(text):
            return text.strip()
        
        def find_sentence_boundary(text, max_length):
            """Find the best place to split text without breaking sentences"""
            if len(text) <= max_length:
                return len(text)
                
            # Try to find the last sentence ending before max_length
            sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
            best_split = 0
            
            # Start looking from earlier in the text to ensure we stay well within limits
            safe_max = min(max_length - 20, len(text))  # Give 20 chars safety margin
            
            for i in range(safe_max, -1, -1):
                if i == 0:
                    break
                    
                # Check if we're at a sentence ending
                for ending in sentence_endings:
                    if text[i-1:i+1] == ending:
                        return i
                        
                # If we haven't found a sentence ending, look for the last complete word
                if best_split == 0 and text[i] == ' ':
                    best_split = i
            
            # If we couldn't find a good split point, use the last word boundary
            return best_split if best_split > 0 else min(max_length - 20, len(text))

        tweets = []
        remaining = content
        
        while remaining:
            # Clean up the remaining text
            remaining = clean_and_trim(remaining)
            if not remaining:
                break
                
            # If remaining text fits in one tweet
            if len(remaining) <= TWEET_LIMIT:
                tweets.append(remaining)
                break
                
            # Find the best place to split
            split_index = find_sentence_boundary(remaining, TWEET_LIMIT)
            
            if split_index == 0:
                logger.warning("Could not find a good split point")
                # Emergency split at TWEET_LIMIT - 20 if no good point found
                split_index = min(TWEET_LIMIT - 20, len(remaining))
                
            # Add the split portion to tweets
            tweets.append(clean_and_trim(remaining[:split_index]))
            remaining = clean_and_trim(remaining[split_index:])
            
        # Verify all tweets are within limit
        for i, tweet in enumerate(tweets):
            if len(tweet) > TWEET_LIMIT:
                logger.warning(f"Tweet {i+1} exceeds limit ({len(tweet)} chars), forcing split")
                # Force split at TWEET_LIMIT - 20 if somehow still too long
                first_part = clean_and_trim(tweet[:TWEET_LIMIT-20])
                second_part = clean_and_trim(tweet[TWEET_LIMIT-20:])
                tweets[i] = first_part
                tweets.insert(i + 1, second_part)
        
        logger.info(f"Split content into {len(tweets)} tweets")
        for i, tweet in enumerate(tweets, 1):
            logger.info(f"Thread part {i}: {tweet[:30]}... ({len(tweet)} chars)")
            
        return tweets

    def post_tweet(self, content):
        """Post a tweet or thread depending on content length"""
        # No need to check login since browser opens already logged in
        
        # Split content into tweets if necessary
        if len(content) > 280:
            logger.info(f"Content exceeds Twitter character limit ({len(content)} chars), creating thread")
            tweet_parts = self._split_into_tweets(content)
            logger.info(f"Split content into {len(tweet_parts)} tweets")
            return self.post_tweet_thread(tweet_parts)
        else:
            return self._post_single_tweet(content)

    def _post_single_tweet(self, content):
        """Post a single tweet"""
        try:
            logger.info("Posting single tweet")
            # Navigate to home if not already there
            if not self.page.url.startswith("https://twitter.com/home") and not self.page.url.startswith("https://x.com/home"):
                logger.info(f"Navigating to home from {self.page.url}")
                self.page.goto("https://x.com/home", wait_until="domcontentloaded")
                random_delay(2, 4)
            
            # Take screenshot of home page
            self.page.screenshot(path="home_before_compose.png")
            logger.info("Saved screenshot of home page")
            
            # Try multiple approaches to click compose tweet button
            compose_clicked = False
            
            # Approach 1: Try various selectors for the compose button
            compose_selectors = [
                'a[href="/compose/tweet"]',
                'a[data-testid="SideNav_NewTweet_Button"]',
                'a[aria-label="Post"]',
                'a[aria-label="Tweet"]',
                'div[aria-label="Tweet"]',
                'div[aria-label="Post"]'
            ]
            
            for selector in compose_selectors:
                logger.info(f"Trying compose button selector: {selector}")
                try:
                    if self.page.query_selector(selector):
                        self.page.click(selector)
                        logger.info(f"Clicked compose button using selector: {selector}")
                        compose_clicked = True
                        break
                except Exception as e:
                    logger.info(f"Selector {selector} failed: {str(e)}")
            
            # Approach 2: If selectors fail, try using JavaScript
            if not compose_clicked:
                logger.info("Trying JavaScript to find and click compose button")
                js_result = self.page.evaluate('''() => {
                    // Try to find compose button by common characteristics
                    const composeSelectors = [
                        'a[href="/compose/tweet"]',
                        '[data-testid="SideNav_NewTweet_Button"]',
                        '[aria-label="Post"]',
                        '[aria-label="Tweet"]',
                        '[data-testid="FloatingActionButton_Tweet"]',
                        '[data-icon="feather"]'
                    ];
                    
                    for (const selector of composeSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            element.click();
                            return `Clicked ${selector}`;
                        }
                    }
                    
                    // Look for any likely compose buttons
                    const allLinks = Array.from(document.querySelectorAll('a, div, button'));
                    const likelyComposeButton = allLinks.find(el => {
                        const ariaLabel = el.getAttribute('aria-label');
                        const text = el.textContent;
                        return (ariaLabel && 
                               (ariaLabel.includes('Tweet') || 
                                ariaLabel.includes('Post'))) ||
                               (text && 
                               (text.includes('Tweet') || 
                                text.includes('Post')));
                    });
                    
                    if (likelyComposeButton) {
                        likelyComposeButton.click();
                        return 'Clicked likely compose button';
                    }
                    
                    return 'No compose button found';
                }''')
                logger.info(f"JavaScript compose button result: {js_result}")
                
                if "Clicked" in js_result:
                    compose_clicked = True
        
            if not compose_clicked:
                logger.error("Could not find compose button")
                self.page.screenshot(path="compose_button_not_found.png")
                return False
                
            # Wait for compose dialog and take screenshot
            random_delay(2, 4)
            self.page.screenshot(path="compose_dialog.png")
            
            # Fill in tweet content
            logger.info("Entering tweet content")
            content_selectors = [
                'div[role="textbox"][data-testid="tweetTextarea_0"]',
                'div[contenteditable="true"][data-testid="tweetTextarea_0"]',
                'div[role="textbox"]',
                'div[contenteditable="true"]'
            ]
            
            content_entered = False
            for selector in content_selectors:
                try:
                    if self.page.query_selector(selector):
                        self.page.fill(selector, content)
                        logger.info(f"Entered content using selector: {selector}")
                        content_entered = True
                        break
                except Exception as e:
                    logger.info(f"Content selector {selector} failed: {str(e)}")
            
            if not content_entered:
                logger.error("Could not enter tweet content")
                self.page.screenshot(path="tweet_content_not_entered.png")
                return False
                
            random_delay(2, 4)
            
            # Click tweet/post button
            logger.info("Clicking post button")
            post_selectors = [
                'div[data-testid="tweetButtonInline"]',
                'div[data-testid="tweetButton"]',
                'div[role="button"]:has-text("Tweet")',
                'div[role="button"]:has-text("Post")'
            ]
            
            post_clicked = False
            for selector in post_selectors:
                try:
                    if self.page.query_selector(selector):
                        self.page.click(selector)
                        logger.info(f"Clicked post button using selector: {selector}")
                        post_clicked = True
                        break
                except Exception as e:
                    logger.info(f"Post button selector {selector} failed: {str(e)}")
            
            # Try JavaScript if regular selectors fail
            if not post_clicked:
                logger.info("Trying JavaScript to click post button")
                js_post_result = self.page.evaluate('''() => {
                    const postButtonSelectors = [
                        '[data-testid="tweetButtonInline"]',
                        '[data-testid="tweetButton"]'
                    ];
                    
                    for (const selector of postButtonSelectors) {
                        const button = document.querySelector(selector);
                        if (button) {
                            button.click();
                            return `Clicked ${selector}`;
                        }
                    }
                    
                    // Look for buttons with "Tweet" or "Post" text
                    const allButtons = Array.from(document.querySelectorAll('div[role="button"]'));
                    const postButton = allButtons.find(btn => 
                        btn.textContent.includes('Tweet') || 
                        btn.textContent.includes('Post'));
                    
                    if (postButton) {
                        postButton.click();
                        return 'Clicked button with Tweet/Post text';
                    }
                    
                    return 'No post button found';
                }''')
                logger.info(f"JavaScript post button result: {js_post_result}")
                
                if "Clicked" in js_post_result:
                    post_clicked = True
            
            if not post_clicked:
                logger.error("Could not click post button")
                self.page.screenshot(path="post_button_not_found.png")
                return False
                
            # Wait for tweet to be posted
            logger.info("Waiting for tweet to be posted")
            random_delay(4, 8)
            
            # Take screenshot of result
            self.page.screenshot(path="after_posting_tweet.png")
            
            logger.info("Tweet posted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {str(e)}")
            # Take screenshot of error state
            self.page.screenshot(path="tweet_error.png")
            return False

    def post_tweet_thread(self, content_list):
        """Post a thread of tweets"""
        # No need to check login since browser opens already logged in
        
        try:
            logger.info(f"Posting a thread with {len(content_list)} tweets")
            
            # Navigate to compose tweet page directly
            compose_url = "https://twitter.com/compose/tweet"
            logger.info(f"Navigating to {compose_url}")
            self.page.goto(compose_url, wait_until="domcontentloaded", timeout=120000)  # 60s → 120s
            random_delay(10, 20)  # 5-8s → 10-20s arttırıldı

            # Compose page HTML & screenshot for diagnostics (hemen başta kaydet)
            try:
                self.page.screenshot(path="compose_page_loaded.png")
                with open("compose_page_loaded.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                logger.info("Compose page screenshot and HTML saved (compose_page_loaded.*)")
            except Exception as e:
                logger.warning(f"Could not save compose page HTML/screenshot: {str(e)}")

            # Compose sayfasında challenge/captcha/engelleme var mı kontrol et
            page_html = self.page.content().lower()
            challenge_keywords = ["challenge", "verify", "unusual activity", "something went wrong", "robot", "suspended", "blocked", "error"]
            for keyword in challenge_keywords:
                if keyword in page_html:
                    logger.error(f"[COMPOSE] Sayfada '{keyword}' anahtarı tespit edildi! Muhtemelen bot engeli veya farklı bir ekran var. compose_page_loaded.html dosyasını inceleyin.")

            # Enter the first tweet
            logger.info(f"Entering content for tweet 1/{len(content_list)}")
            first_tweet_content = content_list[0]
            
            # SÜRE İYİLEŞTİRMESİ 4: Textarea bekleme süresi
            textarea_selectors = [
                '[data-testid="tweetTextarea_0"]',
                'div[role="textbox"][data-testid="tweetTextarea_0"]',
                'div[contenteditable="true"][data-testid="tweetTextarea_0"]',
                'div[role="textbox"]',
                'div[contenteditable="true"]'
            ]
            
            textarea_found = False
            for selector in textarea_selectors:
                try:
                    logger.info(f"Trying textarea selector: {selector}")
                    # Wait for textarea with longer timeout
                    textarea = self.page.wait_for_selector(selector, state="visible", timeout=60000)  # 30s → 60s
                    if textarea:
                        logger.info(f"Found textarea with selector: {selector}")
                        textarea_found = True
                        # Enter content
                        self.page.fill(selector, first_tweet_content)
                        logger.info("Entered content for first tweet")
                        random_delay(2, 3)
                        break
                except Exception as e:
                    logger.info(f"Selector {selector} failed: {str(e)}")
            
            if not textarea_found:
                # Try JavaScript as last resort
                logger.info("Using JavaScript to fill tweet content")
                js_result = self.page.evaluate('''(content) => {
                    // Try to find textareas by common characteristics
                    const textareas = Array.from(document.querySelectorAll('div[role="textbox"], div[contenteditable="true"]'));
                    if (textareas.length > 0) {
                        textareas[0].innerText = content;
                        return true;
                    }
                    return false;
                }''', first_tweet_content)
                if js_result:
                    textarea_found = True
                    logger.info("Filled textarea using JavaScript")
            if not textarea_found:
                logger.error("Tweet textarea bulunamadı! Sayfa HTML ve screenshot kaydediliyor.")
                # Ekstra teşhis dosyası
                self.page.screenshot(path="textarea_not_found.png")
                with open("textarea_not_found.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                # Ayrıca challenge/captcha var mı diye logla
                challenge = self.page.query_selector("input[name='captcha']") or self.page.query_selector("iframe[src*='captcha']") or self.page.query_selector("text=challenge")
                if challenge:
                    logger.error("Sayfada captcha veya challenge tespit edildi!")
                logger.error("compose_page_loaded.html dosyasını Render'dan indirip inceleyin. Twitter botu engelliyor olabilir!")
                raise Exception("Could not find tweet textarea")
                
            # Add remaining tweets to thread
            for i, tweet_content in enumerate(content_list[1:], 2):
                logger.info(f"Adding tweet {i}/{len(content_list)} to thread")
                
                try:
                    # First try to find the + Add button
                    add_button_found = False
                    add_button_selectors = [
                        '[data-testid="addButton"]',
                        'div[aria-label="Add"]',
                        'div[aria-label="Add post"]',
                        'div[role="button"]:has-text("Add")',
                    ]
                    
                    for selector in add_button_selectors:
                        try:
                            add_button = self.page.wait_for_selector(selector, state="visible", timeout=20000)  # 5s → 20s
                            if add_button:
                                logger.info(f"Found Add button with selector: {selector}")
                                # Try multiple ways to click the button
                                try:
                                    add_button.click(delay=100)  # Try with delay
                                    add_button_found = True
                                    break
                                except:
                                    try:
                                        add_button.click(force=True)  # Try force click
                                        add_button_found = True
                                        break
                                    except:
                                        continue
                        except:
                            continue
                    
                    if not add_button_found:
                        # Try JavaScript click as last resort
                        js_result = self.page.evaluate('''() => {
                            const selectors = [
                                '[data-testid="addButton"]',
                                '[aria-label="Add"]',
                                '[aria-label="Add post"]'
                            ];
                            for (const selector of selectors) {
                                const button = document.querySelector(selector);
                                if (button) {
                                    button.click();
                                    return true;
                                }
                            }
                            return false;
                        }''')
                        add_button_found = js_result
                    
                    if not add_button_found:
                        raise Exception("Could not find or click Add button")
                    
                    random_delay(2, 3)
                    
                    # Wait for and fill the new tweet textarea
                    next_textarea_selector = f'[data-testid="tweetTextarea_{i-1}"]'
                    self.page.wait_for_selector(next_textarea_selector, state="visible", timeout=20000)  # 5s → 20s
                    self.page.fill(next_textarea_selector, tweet_content)
                    logger.info(f"Entered content for tweet {i}")
                    random_delay(2, 3)
                    
                except Exception as e:
                    logger.error(f"Error adding tweet {i} to thread: {str(e)}")
                    self.page.screenshot(path=f"thread_tweet_{i}_error.png")
                    return False
            
            # Post the complete thread
            logger.info("Posting the complete thread")
            try:
                post_button = self.page.wait_for_selector('[data-testid="tweetButton"]', state="visible", timeout=20000)  # 5s → 20s
                if post_button:
                    post_button.click()
                    logger.info("Clicked post button")
                    random_delay(5, 8)
                    return True
            except Exception as e:
                logger.error(f"Error posting thread: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Thread posting failed: {str(e)}")
            return False
            
        return True

    def get_latest_tweet(self, username):
        """Get the latest tweet from a user"""
        # No need to check login since browser opens already logged in
        
        try:
            # Navigate to user's profile
            profile_url = f"https://twitter.com/{username}"
            logger.info(f"Getting latest tweet from {profile_url}")
            self.page.goto(profile_url, wait_until="domcontentloaded")
            random_delay(3, 5)
            
            # Wait for tweets to load
            selectors = [
                'article[data-testid="tweet"]',
                '[data-testid="tweet"]',
                'article[role="article"]'
            ]
            
            tweet_found = False
            tweet_element = None
            
            for selector in selectors:
                try:
                    tweet_element = self.page.wait_for_selector(selector, timeout=10000)
                    if tweet_element:
                        tweet_found = True
                        logger.info(f"Found tweet with selector: {selector}")
                        break
                except Exception as e:
                    logger.info(f"Selector {selector} failed: {str(e)}")
            
            if not tweet_found or not tweet_element:
                logger.error(f"Could not find latest tweet for @{username}")
                return None
            
            # Get tweet URL
            tweet_link = tweet_element.query_selector('a[href*="/status/"]')
            if not tweet_link:
                logger.error("Could not find tweet URL")
                return None
            
            tweet_url = tweet_link.get_attribute('href')
            if not tweet_url.startswith('http'):
                tweet_url = f"https://twitter.com{tweet_url}"
            
            # Get tweet text
            tweet_text = tweet_element.inner_text()
            
            return {
                "url": tweet_url,
                "text": tweet_text,
                "username": username
            }
            
        except Exception as e:
            logger.error(f"Error getting latest tweet from @{username}: {str(e)}")
            return None

    def post_comment(self, tweet_url, comment):
        """Post a comment on a tweet"""
        # No need to check login since browser opens already logged in
        
        try:
            # Navigate to tweet
            logger.info(f"Navigating to tweet: {tweet_url}")
            self.page.goto(tweet_url, wait_until="domcontentloaded")
            random_delay(3, 5)
            
            # Find and click reply button
            reply_selectors = [
                '[data-testid="reply"]',
                'div[aria-label="Reply"]',
                'div[role="button"]:has-text("Reply")'
            ]
            
            reply_clicked = False
            for selector in reply_selectors:
                try:
                    if self.page.query_selector(selector):
                        self.page.click(selector)
                        logger.info(f"Clicked reply button using selector: {selector}")
                        reply_clicked = True
                        break
                except Exception as e:
                    logger.info(f"Reply selector {selector} failed: {str(e)}")
            
            if not reply_clicked:
                logger.error("Could not click reply button")
                return False
            
            random_delay(2, 3)
            
            # Enter comment text
            textarea_selectors = [
                '[data-testid="tweetTextarea_0"]',
                'div[role="textbox"]',
                'div[contenteditable="true"]'
            ]
            
            comment_entered = False
            for selector in textarea_selectors:
                try:
                    if self.page.query_selector(selector):
                        self.page.fill(selector, comment)
                        logger.info(f"Entered comment using selector: {selector}")
                        comment_entered = True
                        break
                except Exception as e:
                    logger.info(f"Comment selector {selector} failed: {str(e)}")
            
            if not comment_entered:
                logger.error("Could not enter comment text")
                return False
            
            random_delay(2, 3)
            
            # Click reply/post button
            post_selectors = [
                '[data-testid="tweetButton"]',
                'div[data-testid="tweetButtonInline"]',
                'div[role="button"]:has-text("Reply")',
                'div[role="button"]:has-text("Post")'
            ]
            
            posted = False
            for selector in post_selectors:
                try:
                    if self.page.query_selector(selector):
                        self.page.click(selector)
                        logger.info(f"Clicked post button using selector: {selector}")
                        posted = True
                        break
                except Exception as e:
                    logger.info(f"Post selector {selector} failed: {str(e)}")
            
            if not posted:
                logger.error("Could not click post button")
                return False
            
            random_delay(3, 5)
            return True
            
        except Exception as e:
            logger.error(f"Error posting comment: {str(e)}")
            return False

    def close(self):
        """Close browser and playwright"""
        try:
            if self.context:
                # Save the session state before closing
                self.context.storage_state(path=self.session_file)
            
            if self.browser:
                self.browser.close()
                
            if self.playwright:
                self.playwright.stop()
                
            logger.info("Browser and Playwright closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

    def get_recent_tweets(self, username, hours=23, max_tweets=5):
        """Get recent tweets from a user within specified hours (avoiding pinned tweets)"""
        try:
            # Navigate to user's profile
            profile_url = f"https://twitter.com/{username}"
            logger.info(f"Getting recent tweets from {profile_url} (last {hours} hours)")
            self.page.goto(profile_url, wait_until="domcontentloaded")
            random_delay(3, 5)
            
            # Wait for tweets to load
            selectors = [
                'article[data-testid="tweet"]',
                '[data-testid="tweet"]',
                'article[role="article"]'
            ]
            
            recent_tweets = []
            
            # Try to find multiple tweet elements
            try:
                # Wait for first tweet to load
                self.page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
                
                # Get all tweet elements on the page
                tweet_elements = self.page.query_selector_all('article[data-testid="tweet"]')
                logger.info(f"Found {len(tweet_elements)} tweets on profile")
                
                for i, tweet_element in enumerate(tweet_elements[:max_tweets]):
                    try:
                        # Skip pinned tweets (they usually have a pin indicator)
                        pin_indicator = tweet_element.query_selector('[data-testid="pin"]')
                        if pin_indicator:
                            logger.info(f"Skipping pinned tweet for @{username}")
                            continue
                        
                        # Get tweet URL and ID
                        tweet_link = tweet_element.query_selector('a[href*="/status/"]')
                        if not tweet_link:
                            continue
                        
                        tweet_url = tweet_link.get_attribute('href')
                        if not tweet_url.startswith('http'):
                            tweet_url = f"https://twitter.com{tweet_url}"
                        
                        # Extract tweet ID from URL
                        tweet_id_match = re.search(r'/status/(\d+)', tweet_url)
                        tweet_id = tweet_id_match.group(1) if tweet_id_match else None
                        
                        if not tweet_id:
                            continue
                        
                        # Get tweet text
                        tweet_text = tweet_element.inner_text()
                        
                        # Try to get timestamp (this is approximate since Twitter uses relative times)
                        timestamp_element = tweet_element.query_selector('time')
                        timestamp = None
                        if timestamp_element:
                            timestamp = timestamp_element.get_attribute('datetime')
                        
                        # If no timestamp found, use current time minus index hours as approximation
                        if not timestamp:
                            from datetime import datetime, timedelta
                            estimated_time = datetime.now() - timedelta(minutes=i*30)  # Rough estimate
                            timestamp = estimated_time.isoformat()
                        
                        tweet_data = {
                            "id": tweet_id,
                            "url": tweet_url,
                            "text": tweet_text,
                            "username": username,
                            "timestamp": timestamp
                        }
                        
                        recent_tweets.append(tweet_data)
                        logger.info(f"Found tweet {i+1}: {tweet_id}")
                        
                    except Exception as e:
                        logger.warning(f"Error processing tweet {i+1} for @{username}: {str(e)}")
                        continue
                
                logger.info(f"Retrieved {len(recent_tweets)} recent tweets for @{username}")
                return recent_tweets
                
            except Exception as e:
                logger.error(f"Error finding tweets for @{username}: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting recent tweets from @{username}: {str(e)}")
            return []
    
    def _auto_login(self):
        import os
        username = os.getenv("TWITTER_USERNAME")
        password = os.getenv("TWITTER_PASSWORD")
        if not username or not password:
            logger.error("TWITTER_USERNAME veya TWITTER_PASSWORD .env dosyasında tanımlı değil!")
            return False

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"[Login Attempt {attempt}] Otomatik login başlatılıyor...")
                self.page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60000)

                # Kullanıcı adı inputu
                username_filled = False
                try:
                    self.page.wait_for_selector('input[name="text"]', timeout=10000)
                    self.page.fill('input[name="text"]', username)
                    username_filled = True
                    logger.info("Kullanıcı adı girildi: input[name='text']")
                except Exception as e:
                    logger.error(f"Kullanıcı adı inputu bulunamadı: {str(e)}")

                if not username_filled:
                    self.page.screenshot(path="username_input_not_found.png")
                    return False

                # Next butonu
                try:
                    self.page.click('div[role="button"]:has-text("Next")')
                    logger.info("Next butonuna tıklandı")
                except Exception as e:
                    logger.error(f"Next butonuna tıklanamadı: {str(e)}")
                    self.page.screenshot(path="next_button_click_failed.png")
                    return False

                self.page.wait_for_timeout(3000)

                # Şifre alanı
                try:
                    self.page.wait_for_selector('input[name="password"]', timeout=10000)
                    self.page.fill('input[name="password"]', password)
                    logger.info("Şifre girildi")
                except Exception as e:
                    logger.error(f"Şifre alanı bulunamadı: {str(e)}")

                    # 🔍 Teşhis amaçlı HTML & ekran görüntüsü kaydet
                    with open("password_input_debug.html", "w", encoding="utf-8") as f:
                        f.write(self.page.content())
                    self.page.screenshot(path="password_input_debug.png")
                    return False

                # Giriş butonu
                try:
                    self.page.click('div[role="button"]:has-text("Log in")')
                    logger.info("Giriş butonuna tıklandı")
                except Exception as e:
                    logger.error(f"Giriş butonuna tıklanamadı: {str(e)}")
                    return False

                self.page.wait_for_timeout(6000)

                # Giriş sonrası kontrol
                current_url = self.page.url
                logger.info(f"Login sonrası URL: {current_url}")
                if "home" in current_url:
                    self.context.storage_state(path=self.session_file)
                    return True
                else:
                    self.page.screenshot(path="login_failed_final.png")
            except Exception as e:
                logger.error(f"Otomatik login sırasında hata: {str(e)}")

        logger.error("Tüm otomatik login denemeleri başarısız oldu!")
        return False