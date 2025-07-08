import os
import random
import time
import schedule
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from twitter_client import TwitterClient
from gemini_client import GeminiClient
from flask import Flask
import threading

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("twitter_bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Set encoding for stdout
import sys
sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Keywords for comment filtering
KEYWORDS = [
    "0G", "Allora", "ANIME", "Aptos", "Arbitrum", "Berachain", "Boop", 
    "Caldera", "Camp Network", "Corn", "Defi App", "dYdX", "Eclipse", 
    "Fogo", "Frax", "FUEL", "Huma", "Humanity Protocol", "Hyperbolic", 
    "Initia", "Injective", "Infinex", "IQ", "Irys", "Kaia", "Kaito", 
    "MegaETH", "Mitosis", "Monad", "Movement", "Multibank", "Multipli", 
    "Near", "Newton", "Novastro", "OpenLedger", "PARADEX", "PENGU", 
    "Polkadot", "Portal to BTC", "PuffPaw", "Pyth", "QUAI", "SatLayer", 
    "Sei", "Sidekick", "Skate", "Somnia", "Soon", "Soph Protocol", 
    "Soul Protocol", "Starknet", "Story", "Succinct", "Symphony", 
    "Theoriq", "Thrive Protocol", "Union", "Virtuals Protocol", "Wayfinder", 
    "XION", "YEET", "Zcash", "DeFi", "NFT", "Web3", "Layer2", "zkSync",
    "Ethereum", "Bitcoin", "Solana", "Polygon", "Avalanche", "Cosmos",
     "Anoma", "Bless", "Boundless", "GOAT Network", "Hana", "Katana", "Lombard", "Lumiterra", "MemeX", 
    "Mira Network", "Noya.ai", "Surf", "Turtle Club", "Warden Protocol", 
    "NEAR", "Overtake", "Peaq", "UXLINK", "Maplestory Universe", "Sunrise"
]

def load_commented_tweets():
    """Load list of already commented tweet IDs"""
    commented_file = "commented_tweets.json"
    if os.path.exists(commented_file):
        with open(commented_file, 'r') as f:
            return json.load(f)
    return []

def save_commented_tweet(tweet_id):
    """Save a tweet ID as commented"""
    commented_file = "commented_tweets.json"
    commented_tweets = load_commented_tweets()
    
    # Add new tweet ID
    if tweet_id not in commented_tweets:
        commented_tweets.append(tweet_id)
    
    # Keep only last 1000 tweets to prevent file from growing too large
    if len(commented_tweets) > 1000:
        commented_tweets = commented_tweets[-1000:]
    
    with open(commented_file, 'w') as f:
        json.dump(commented_tweets, f)

def is_tweet_recent(tweet_timestamp):
    """Check if tweet is from last 23 hours"""
    try:
        if not tweet_timestamp:
            return False
        
        # Parse tweet timestamp (Twitter format: "Mon Jan 01 00:00:00 +0000 2024")
        from datetime import datetime, timedelta
        import re
        
        # Clean timestamp string
        timestamp_str = str(tweet_timestamp).strip()
        
        # Try different timestamp formats
        formats = [
            "%a %b %d %H:%M:%S %z %Y",  # Twitter format
            "%Y-%m-%d %H:%M:%S",        # Simple format
            "%Y-%m-%dT%H:%M:%S.%fZ",    # ISO format
        ]
        
        tweet_time = None
        for fmt in formats:
            try:
                tweet_time = datetime.strptime(timestamp_str, fmt)
                break
            except:
                continue
        
        if not tweet_time:
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return False
        
        # Make timezone naive for comparison
        if tweet_time.tzinfo:
            tweet_time = tweet_time.replace(tzinfo=None)
        
        now = datetime.now()
        twentythree_hours_ago = now - timedelta(hours=2)
        
        is_recent = tweet_time > twentythree_hours_ago
        logger.info(f"Tweet time: {tweet_time}, Is recent (last 23h): {is_recent}")
        return is_recent
        
    except Exception as e:
        logger.error(f"Error checking tweet timestamp: {str(e)}")
        return False

def contains_keywords(text):
    """Check if text contains any of the target keywords (case-insensitive)"""
    if not text:
        return False
    
    text_lower = text.lower()
    for keyword in KEYWORDS:
        if keyword.lower() in text_lower:
            logger.info(f"Found keyword '{keyword}' in tweet text")
            return True
    return False

PROJECTS = [
    {"name": "Allora", "twitter": "@AlloraNetwork", "website": "allora.network", "category": "AI + Blockchain"},
    {"name": "Spark", "twitter": "@sparkdotfi", "website": "spark.fi", "category": "Rollup Infrastructure"},
    {"name": "Sapien", "twitter": "@JoinSapien", "website": "game.sapien.io", "category": "web3 gaming"},
    {"name": "Caldera", "twitter": "@Calderaxyz", "website": "caldera.xyz", "category": "Rollup Infrastructure"},
    {"name": "Camp Network", "twitter": "@campnetworkxyz", "website": "campnetwork.xyz", "category": "Social Layer"},
    {"name": "Eclipse", "twitter": "@EclipseFND", "website": "eclipse.builders", "category": "SVM L2"},
    {"name": "Fogo", "twitter": "@FogoChain", "website": "fogo.io", "category": "Gaming Chain"},
    {"name": "Humanity Protocol", "twitter": "@Humanityprot", "website": "humanity.org", "category": "Identity"},
    {"name": "Hyperbolic", "twitter": "@hyperbolic_labs", "website": "hyperbolic.xyz", "category": "AI Infrastructure"},
    {"name": "Infinex", "twitter": "@infinex", "website": "infinex.xyz", "category": "DeFi Frontend"},
    {"name": "Irys", "twitter": "@irys_xyz", "website": "irys.xyz", "category": "Data Storage"},
    {"name": "Katana", "twitter": "@KatanaRIPNet", "website": "katana.network", "category": "Gaming Infrastructure"},
    {"name": "Lombard", "twitter": "@Lombard_Finance", "website": "lombard.finance", "category": "Bitcoin DeFi"},
    {"name": "MegaETH", "twitter": "@megaeth_labs", "website": "megaeth.com", "category": "High-Performance L2"},
    {"name": "Mira Network", "twitter": "@mira_network", "website": "mira.network", "category": "Cross-Chain"},
    {"name": "Mitosis", "twitter": "@MitosisOrg", "website": "mitosis.org", "category": "Ecosystem Expansion"},
    {"name": "Monad", "twitter": "@monad_xyz", "website": "monad.xyz", "category": "Parallel EVM"},
    {"name": "Multibank", "twitter": "@multibank_io", "website": "multibank.io", "category": "Multi-Chain Banking"},
    {"name": "Multipli", "twitter": "@multiplifi", "website": "multipli.fi", "category": "Yield Optimization"},
    {"name": "Newton", "twitter": "@MagicNewton", "website": "newton.xyz", "category": "Cross-Chain Liquidity"},
    {"name": "Novastro", "twitter": "@Novastro_xyz", "website": "novastro.xyz", "category": "Cosmos DeFi"},
    {"name": "Noya.ai", "twitter": "@NetworkNoya", "website": "noya.ai", "category": "AI-Powered DeFi"},
    {"name": "OpenLedger", "twitter": "@OpenledgerHQ", "website": "openledger.xyz", "category": "Institutional DeFi"},
    {"name": "PARADEX", "twitter": "@tradeparadex", "website": "paradex.trade", "category": "Perpetuals DEX"},
    {"name": "Portal to BTC", "twitter": "@PortaltoBitcoin", "website": "portaltobitcoin.com", "category": "Bitcoin Bridge"},
    {"name": "Puffpaw", "twitter": "@puffpaw_xyz", "website": "puffpaw.xyz", "category": "Gaming + NFT"},
    {"name": "SatLayer", "twitter": "@satlayer", "website": "satlayer.xyz", "category": "Bitcoin L2"},
    {"name": "Sidekick", "twitter": "@Sidekick_Labs", "website": "N/A", "category": "Developer Tools"},
    {"name": "Somnia", "twitter": "@Somnia_Network", "website": "somnia.network", "category": "Virtual Society"},
    {"name": "Soul Protocol", "twitter": "@DigitalSoulPro", "website": "digitalsoulprotocol.com", "category": "Digital Identity"},
    {"name": "Succinct", "twitter": "@succinctlabs", "website": "succinct.xyz", "category": "Zero-Knowledge"},
    {"name": "Symphony", "twitter": "@SymphonyFinance", "website": "app.symphony.finance", "category": "Yield Farming"},
    {"name": "Theoriq", "twitter": "@theoriq_ai", "website": "theoriq.ai", "category": "AI Agents"},
    {"name": "Thrive Protocol", "twitter": "@thriveprotocol", "website": "thriveprotocol.com", "category": "Social DeFi"},
    {"name": "Union", "twitter": "@union_build", "website": "union.build", "category": "Cross-Chain Infrastructure"},
    {"name": "YEET", "twitter": "@yeet", "website": "yeet.com", "category": "Meme + Utility"},
    {"name": "Overtake", "twitter": "@overtake_world", "website": "overtake.world", "category": "Ecosystem Rewards"},
    {"name": "Bless", "twitter": "@theblessnetwork", "website": "bless.network", "category": "Token Airdrop"},
    {"name": "Peaq", "twitter": "@peaq", "website": "peaq.xyz", "category": "Consensus Layer"},
    {"name": "Warden Protocol", "twitter": "@wardenprotocol", "website": "wardenprotocol.org", "category": "Security"},
    {"name": "Hana Network", "twitter": "@HanaNetwork", "website": "hana.network", "category": "Layer 2"},
    {"name": "Goat Network", "twitter": "@GOATRollup", "website": "goat.network", "category": "Rollup"},
    {"name": "Pyth", "twitter": "@PythNetwork", "website": "pyth.network", "category": "Oracle"},
    {"name": "Soon", "twitter": "@soon_svm", "website": "N/A", "category": "Staking Rewards"},
    {"name": "Huma Finance", "twitter": "@humafinance", "website": "N/A", "category": "DeFi Protocol"},
    {"name": "Sunrise Layer", "twitter": "@SunriseLayer", "website": "N/A", "category": "Layer 2"},
    {"name": "Skate Chain", "twitter": "@skate_chain", "website": "N/A", "category": "DeFi"},
    {"name": "dYdX", "twitter": "@dYdX", "website": "dydx.exchange", "category": "Derivatives"},
    {"name": "Maplestory Universe", "twitter": "@MaplestoryU", "website": "N/A", "category": "Gaming"},
    {"name": "Arbitrum", "twitter": "@arbitrum", "website": "arbitrum.io", "category": "Rollup"},
    {"name": "Polkadot", "twitter": "@Polkadot", "website": "polkadot.network", "category": "Sharded Relay"},
    {"name": "Defi App", "twitter": "@defidotapp", "website": "defidotapp.com", "category": "DeFi Aggregator"},
    {"name": "Fomo", "twitter": "@tryfomo", "website": "tryfomo.com", "category": "Referral Rewards"},
    {"name": "Injective", "twitter": "@injective", "website": "injective.com", "category": "Dex"},
    {"name": "Mantle", "twitter": "@Mantle_Official", "website": "mantle.xyz", "category": "Scaling"},
    {"name": "Virtuals", "twitter": "@virtuals_io", "website": "virtuals.io", "category": "Social DeFi"},
    {"name": "UXLINK", "twitter": "@UXLINKofficial", "website": "uxlink.io", "category": "Social DeFi"},
    {"name": "Vooi", "twitter": "@vooi_io", "website": "vooi.io", "category": "Web3 Social + Video"},
    {"name": "Elympics", "twitter": "@elympics_ai", "website": "elympics.ai", "category": "Web3 Gaming Infra"},
    {"name": "Recall", "twitter": "@recallnet", "website": "recall.network", "category": "AI Memory Layer"}
]



TWITTER_ACCOUNTS = [
    "0x_ultra", "0xBreadguy", "beast_ico", "mdudas", "lex_node", "jessepollak", "0xWenMoon",
    "ThinkingUSD", "udiWertheimer", "vohvohh", "NTmoney", "0xMert_", "QwQiao", "DefiIgnas",
    "notthreadguy", "Chilearmy123", "Punk9277", "DeeZe", "stevenyuntcap", "ViktorBunin",
    "ayyyeandy", "andy8052", "Phineas_Sol", "MoonOverlord", "NarwhalTan", "theunipcs",
    "RyanWatkins_", "aixbt_agent", "ai_9684xtpa", "icebergy_", "Luyaoyuan1", "stacy_muur",
    "TheOneandOmsy", "jeffthedunker", "JoshuaDeuk", "0x_scientist", "inversebrah", "dachshundwizard",
    "gammichan", "sandeepnailwal", "segall_max", "blknoiz06", "0xmons", "hosseeb", "GwartyGwart",
    "JasonYanowitz", "Tyler_Did_It", "laurashin", "Dogetoshi", "benbybit", "MacroCRG", "Melt_Dem",
    "realitywarp", "lemiscate", "EasyEatsBodega", "sjdedic", "pet3rpan_", "naruto11eth",
    "sassal0x", "beaniemaxi", "Tradermayne", "DavidFBailey", "binji_x", "nic__carter",
    "DancingEddie_", "CryptoKaleo", "waleswoosh", "nikokampouris", "KookCapitalLLC", "iamDCinvestor",
    "Jack55750", "aeyakovenko", "VannaCharmer", "0xAbhiP", "Tiza4ThePeople", "Xeer", "howdymerry",
    "wizardofsoho", "punk9059", "TylerDurden", "0xNairolf", "jon_charb", "Lamboland_", "BroLeonAus",
    "HadickM", "farokh", "functi0nZer0", "EliBenSasson", "0xfoobar", "basedkarbon", "danielesesta",
    "thecryptoskanda", "drakefjustin", "AltcoinGordon", "S4mmyEth",
    "Slappjakke", "Pons_ETH", "SuhailKakar", "natealexnft", "TopoGigio_sol", "serpinxbt",
    "MaraCakeHotSale", "docXBT", "CloutedMind", "Pickle_cRypto", "0xSins", "StarPlatinumSOL",
    "Evan_ss6", "MaxResnick1", "0xCygaar", "AltcoinSherpa", "randomcdog", "kxkxkx85",
    "forgivenever", "milesdeutscher", "0x_Todd", "0xcarnation", "onchainmo", "superwoj",
    "RobertSagurton", "Auri_0x", "Adam_Tehc", "CryptoGodJohn", "gamiwtf", "HypoNyms", "jacqmelinek",
    "beijingdou", "kasperloock", "PaikCapital", "OkohEbina", "MINHxDYNASTY", "wals_eth",
    "0itsali0", "A_Leutenegger", "0x42069x", "dotkrueger", "Loopifyyy", "NateGeraci", "dcfgod",
    "JaseTheWizard", "BTC_Alert_", "naniXBT", "knowerofmarkets", "MacroMate8", "TheOG_General",
    "LeonWaidmann", "camolNFT", "DujunX", "SmokeyTheBera", "0xMatt1", "dabit3", "Gummybear1771",
    "NFTherder", "LSDinmycoffee", "KathySats", "cryptodude999"
]


REGENERATION_ACCOUNTS = [
    "nftmufettisi", "ajwarner90", "mdudas", "beast_ico", "Loopifyyy", "ayyyeandy"
]

def load_regenerated_tweets():
    """Load list of already regenerated tweet IDs."""
    regen_file = "regenerated_tweets.json"
    if os.path.exists(regen_file):
        with open(regen_file, 'r') as f:
            return json.load(f)
    return []

def save_regenerated_tweet(tweet_id):
    """Save a tweet ID as regenerated."""
    regen_file = "regenerated_tweets.json"
    regenerated = load_regenerated_tweets()
    if tweet_id not in regenerated:
        regenerated.append(tweet_id)
    # Keep only last 1000 to avoid file growing too large
    if len(regenerated) > 1000:
        regenerated = regenerated[-1000:]
    with open(regen_file, 'w') as f:
        json.dump(regenerated, f)

def regenerate_and_post_tweets(twitter_client, gemini_client):
    """Fetch last tweet from specific accounts, rewrite with Gemini, and post."""
    regenerated_tweets = load_regenerated_tweets()
    for username in REGENERATION_ACCOUNTS:
        try:
            # Sadece son 2 saat içindeki tweetleri al
            tweets = twitter_client.get_recent_tweets(username, hours=2, max_tweets=5)
            if not tweets:
                logger.info(f"No recent tweets found for @{username}")
                continue
            for tweet in tweets:
                tweet_id = tweet.get("id")
                tweet_text = tweet.get("text", "")
                # RT olanları atla
                if tweet.get("is_retweet") or tweet_text.strip().lower().startswith("rt "):
                    logger.info(f"Skipping retweet by @{username}")
                    continue
                if tweet_id in regenerated_tweets:
                    logger.info(f"Already regenerated tweet {tweet_id} by @{username}")
                    continue
                if not tweet_text or len(tweet_text) < 5:
                    logger.info(f"Tweet by @{username} is too short or empty, skipping")
                    continue
                prompt = f"Rewrite the following tweet in different words, keeping the same meaning, as a new tweet:\n\n{tweet_text}"
                new_tweet = gemini_client.generate_project_tweet({"text": prompt})
                if not new_tweet or len(new_tweet.strip()) < 5:
                    logger.info(f"Gemini did not return a valid tweet for @{username}")
                    continue
                success = twitter_client.post_tweet(new_tweet.strip())
                if success:
                    logger.info(f"Regenerated and posted tweet for @{username}")
                    save_regenerated_tweet(tweet_id)
                else:
                    logger.error(f"Failed to post regenerated tweet for @{username}")
                time.sleep(random.uniform(10, 20))  # Anti-spam delay
        except Exception as e:
            logger.error(f"Error processing regeneration for @{username}: {str(e)}")
        time.sleep(random.uniform(10, 20))  # Spam koruması

def run_bot():
    """Main function to run the bot tasks"""
    try:
        logger.info("Starting bot run")
        
        # Load current state
        state_file = "bot_state.json"
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
        else:
            state = {"project_index": 0, "twitter_account_index": 0}
        
        project_index = state["project_index"]
        twitter_account_index = state["twitter_account_index"]
          # Initialize clients
        twitter_client = TwitterClient()
        twitter_client._setup_browser()
        gemini_client = GeminiClient()

        # --- NEW TASK: Regenerate and post tweets from specific accounts ---
        regenerate_and_post_tweets(twitter_client, gemini_client)
        # --- END NEW TASK ---

        # Post project tweets - Select 3 projects sequentially
        selected_projects = []
        for _ in range(5):
            selected_projects.append(PROJECTS[project_index])
            project_index = (project_index + 1) % len(PROJECTS)
          # Post all tweets with one login session
        for project in selected_projects:
            try:
                tweet_content = gemini_client.generate_project_tweet(project)
                success = twitter_client.post_tweet(tweet_content)
                
                if success:
                    logger.info(f"Posted tweet about {project['name']}")
                else:
                    logger.error(f"Failed to post tweet about {project['name']}")
                    
                time.sleep(random.uniform(10, 15))  # Daha uzun bekleme
            except Exception as e:
                logger.error(f"Error posting tweet for {project['name']}: {str(e)}")
                # Screenshot for debugging
                try:
                    twitter_client.page.screenshot(path=f"error_{project['name']}.png")
                except:
                    pass
        
        # Comment on tweets - Select 15 accounts sequentially
        selected_accounts = []
        for _ in range(15):
            selected_accounts.append(TWITTER_ACCOUNTS[twitter_account_index])
            twitter_account_index = (twitter_account_index + 1) % len(TWITTER_ACCOUNTS)
        
        # Load already commented tweets
        commented_tweets = load_commented_tweets()
        
        # Comment on all tweets with same login session
        for username in selected_accounts:
            try:
                # Get recent tweets (not just latest) to avoid pin tweets
                recent_tweets = twitter_client.get_recent_tweets(username, hours=2, max_tweets=5)
                
                if not recent_tweets:
                    logger.info(f"No recent tweets found for @{username}")
                    continue
                
                # Process each recent tweet
                for tweet in recent_tweets:
                    tweet_id = tweet.get("id")
                    tweet_text = tweet.get("text", "")
                    tweet_timestamp = tweet.get("timestamp")
                    
                    # Skip if already commented on this tweet
                    if tweet_id in commented_tweets:
                        logger.info(f"Already commented on tweet {tweet_id} by @{username}")
                        continue
                    
                    # Skip if tweet is not recent (older than 23 hours)
                    if not is_tweet_recent(tweet_timestamp):
                        logger.info(f"Tweet by @{username} is older than 23 hours, skipping")
                        continue
                    
                    # Check if tweet contains keywords
                    if contains_keywords(tweet_text):
                        comment = gemini_client.generate_comment(username, tweet)
                        success = twitter_client.post_comment(tweet.get("url"), comment)
                        
                        if success:
                            # Save tweet ID as commented
                            save_commented_tweet(tweet_id)
                            logger.info(f"Commented on recent tweet by @{username} (contained keywords)")
                        else:
                            logger.error(f"Failed to comment on tweet by @{username}")
                        
                        # Only comment on one tweet per user to avoid spam
                        break
                    else:
                        logger.info(f"Tweet by @{username} doesn't contain keywords, skipping")
                
                time.sleep(random.uniform(3, 7))
                
            except Exception as e:
                logger.error(f"Error processing tweets for @{username}: {str(e)}")
        
        # --- YENİ GÖREV: Belirli hesapların tweetlerini yeniden üret ve paylaş ---
        regenerate_and_post_tweets(twitter_client, gemini_client)
        # --- YENİ GÖREV SONU ---

        # Save updated state
        state = {"project_index": project_index, "twitter_account_index": twitter_account_index}
        with open(state_file, 'w') as f:
            json.dump(state, f)
            
        # Close client
        twitter_client.close()
        logger.info("Bot run completed successfully")
    
    except Exception as e:
        logger.error(f"Bot run failed with error: {str(e)}")
        # Try to close browser if it's open
        try:
            if 'twitter_client' in locals():
                twitter_client.close()
        except:
            pass

app = Flask(__name__)

@app.route("/healthz")
def healthz():
    return "ok", 200

def start_web():
    app.run(host="0.0.0.0", port=8080)

def main():
    twitter_client = TwitterClient()

    # 1. Takip edilen hesapların tweetlerini paylaş
    try:
        twitter_client._setup_browser()
        # ...ilgili fonksiyonları çağır...
    except Exception as e:
        logger.error(f"Tweet paylaşırken hata: {str(e)}")
    finally:
        twitter_client.close()

    # 2. Belirlenen konularda içerik oluşturup paylaş
    try:
        twitter_client._setup_browser()
        # ...ilgili fonksiyonları çağır...
    except Exception as e:
        logger.error(f"İçerik paylaşırken hata: {str(e)}")
    finally:
        twitter_client.close()

    # 3. Takip edilen hesapların tweetlerine yorum yap
    try:
        twitter_client._setup_browser()
        # ...ilgili fonksiyonları çağır...
    except Exception as e:
        logger.error(f"Yorum yaparken hata: {str(e)}")
    finally:
        twitter_client.close()

if __name__ == "__main__":
    threading.Thread(target=start_web, daemon=True).start()
    main()
    while True:
        run_bot()
        time.sleep(60 * 60)  # Her saat başı çalıştır