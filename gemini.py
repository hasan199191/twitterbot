import os
import time
import random
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class GeminiClient:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set. Please set it in your .env file.")
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash for more sophisticated content generation
        # It offers a larger context window and better reasoning capabilities than Flash, crucial for analytical tasks.
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Initialized Gemini 2.5 Flash model for enhanced content generation.")

    def generate_project_tweet(self, project):
        """
        Belirli bir proje hakkında analitik ve özgün bir tweet içeriği üretir.
        Tweetler, Web3 trendleriyle bağlantılı derinlemesine içgörüler sunar.
        """
        try:
            logger.info(f"Generating tweet content for project: {project.get('name', 'Unknown')}")
            
            # Daha zengin ve yönlendirici bir prompt oluşturuyoruz.
            # Analitik derinliği artırmak için spesifik yönergeler ekliyoruz.
            prompt = f"""
            You are a highly analytical and insightful Web3 and blockchain expert. Your goal is to generate an authentic, unique, and deeply analytical tweet (or thread) about the following project. Avoid generic statements and focus on providing real value and unique perspective.

            Project Details:
            - Project Name: {project.get('name', 'N/A')}
            - Twitter Handle: {project.get('twitter', 'N/A')}
            - Website: {project.get('website', 'N/A')}
            - Category: {project.get('category', 'N/A')}
            - Key Features/Description (if available, otherwise infer from category): {project.get('description', 'This project operates in the ' + project.get('category', 'blockchain') + ' space.')}

            Your tweet MUST adhere to these critical rules for authenticity and depth:
            1.  **Authenticity & Uniqueness**: The content must be entirely original, sound genuinely human-written, and reflect deep thought. No copy-paste sentences or generic phrases.
            2.  **Analytical & Interpretive**: Go beyond mere promotion. Analyze the project's potential impact, its unique selling proposition, challenges it addresses, or its position within the broader Web3 ecosystem. Compare it (briefly, implicitly, or explicitly) with other trends or projects if relevant.
            3.  **Insightful Questions/Highlights**: Include 1-2 thought-provoking questions or highlight a nuanced aspect that most people might miss. This shows depth of understanding.
            4.  **Web3 Trend Connection**: Relate the project to current or emerging Web3, blockchain, or crypto trends (e.g., modular blockchains, ZK-proofs, RWA tokenization, DePIN, account abstraction, specific L2 solutions, sustainable crypto, decentralized AI).
            5.  **Value Proposition**: Articulate what unique value this project brings or what problem it solves in an innovative way.
            6.  **Tone**: Professional, analytical, slightly inquisitive, and forward-looking. Avoid hype or overly promotional language.
            7.  **Length**: If the content exceeds 280 characters, it's encouraged to structure it as a natural Twitter thread (implying continuation, e.g., "1/N", but you don't need to add the numbers, just flow). Focus on content quality over strict character count for a single tweet.
            8.  **Emoji Use**: Limit to a maximum of 1 relevant emoji, used sparingly and effectively to enhance meaning, not decorate.
            9.  **Format**: Start with an insightful observation or analytical point, develop the thought, include a unique question or highlight, and end with the project's Twitter handle and/or website. Ensure smooth, coherent transitions if it's thread-like.

            Example structure for a single tweet (adapt for threads):
            "Deep dive into [Project Name]'s approach to [specific problem/area]. Their [unique feature/method] presents an interesting shift. How will this impact [related Web3 trend/area]? Check them out: {project.get('twitter', project.get('website'))}"

            Generate ONLY the tweet content. Do not include any preambles or explanations.
            """
            
            response = self.model.generate_content(prompt)
            tweet_content = response.text.strip()
            
            logger.info(f"Successfully generated tweet content for {project.get('name', 'Unknown')}.")
            return tweet_content
            
        except Exception as e:
            logger.error(f"Error generating tweet for {project.get('name', 'Unknown')}: {e}", exc_info=True)
            # Daha bilgilendirici bir fallback tweet.
            return f"Exploring the innovative work of {project.get('name', 'this project')} in the {project.get('category', 'Web3')} space. Their developments at {project.get('website', 'their website')} are worth a look! #Web3"
            
    def generate_comment(self, username, tweet_data):
        """
        Belirli bir tweet'e analitik, benzersiz ve insan benzeri bir yorum üretir.
        Yorumlar, çeşitli persona ve yazı stillerini kullanarak zenginleştirilmiştir.
        """
        logger.info(f"Generating comment for @{username}'s tweet: {tweet_data.get('text', 'No text provided')[:50]}...")

        # Daha detaylı ve özgün persona'lar
        personas = [
            "veteran Web3 architect with a focus on decentralization and scalability",
            "DeFi researcher specializing in yield strategies and risk management",
            "NFT historian and digital culture critic, analyzing market trends and artistic value",
            "tokenomics design expert, evaluating incentive models and sustainability",
            "blockchain security auditor, looking for potential vulnerabilities and robust solutions",
            "cross-chain interoperability evangelist, exploring seamless asset transfers and communication",
            "Web3 gaming economist, dissecting play-to-earn models and virtual economies",
            "privacy-preserving tech advocate, focusing on ZK-proofs and secure multi-party computation",
            "DAO governance specialist, analyzing decision-making frameworks and community engagement",
            "sustainable blockchain initiatives proponent, examining energy efficiency and environmental impact"
        ]
        
        # Daha spesifik ve yaratıcı yazı stilleri
        writing_styles = [
            "incisive and critical, but always constructive",
            "thought-provoking and philosophical, exploring underlying principles",
            "data-driven and evidence-based, citing potential metrics or trends",
            "comparative and contrastive, drawing parallels or distinctions with other concepts",
            "forward-looking and speculative, discussing future implications",
            "problem-solution oriented, identifying challenges and potential remedies",
            "question-driven, posing insightful queries that encourage deeper thought",
            "narrative-focused, framing the topic within a broader story of Web3 evolution",
            "strategically minded, evaluating market positioning and adoption pathways",
            "conceptually dense, breaking down complex ideas into understandable components"
        ]

        # Yorum yapılarını daha esnek hale getiriyoruz
        comment_strategies = [
            "Acknowledge the tweet, then present a nuanced counter-argument or an alternative perspective, concluding with a question about long-term viability.",
            "Identify a key assumption in the tweet and challenge it with an alternative insight, supported by a brief observation on market dynamics.",
            "Connect the tweet's content to a broader, less obvious Web3 trend or technological advancement, then ask how this connection might evolve.",
            "Analyze the tweet's subject through the lens of economic incentives or game theory, highlighting potential outcomes and posing a 'what if' scenario.",
            "Provide a brief historical context or evolution of the tweet's topic within Web3, then speculate on its next phase of development.",
            "Focus on a specific technical aspect mentioned or implied in the tweet, elaborate on its complexity or innovation, and ask about adoption challenges.",
            "Evaluate the tweet's implications for user experience or accessibility in Web3, suggesting improvements or discussing trade-offs.",
            "Draw a parallel between the tweet's subject and a concept from traditional finance or technology, then explore how Web3 diverges or improves upon it.",
            "Discuss the regulatory or governance implications of the tweet's topic, posing a question about future frameworks or community consensus.",
            "Highlight an often-overlooked risk or opportunity associated with the tweet's subject, offering a cautionary thought or an optimistic outlook."
        ]
        
        # Tonlar yorumun genel hissini belirleyecek
        response_tones = [
            "academically rigorous yet accessible",
            "pragmatically optimistic with a hint of realism",
            "skeptical but open-minded, seeking verifiable facts",
            "visionary and inspiring, focusing on potential breakthroughs",
            "critically constructive, aiming to improve understanding",
            "deeply contemplative, exploring ethical and societal impacts",
            "strategically analytical, assessing market fit and timing",
            "innovatively curious, exploring uncharted territories",
            "user-centric, focusing on how this impacts the end-user",
            "community-focused, considering collective impact and collaboration"
        ]
        
        # Random seçimler
        persona = random.choice(personas)
        style = random.choice(writing_styles)
        strategy = random.choice(comment_strategies)
        tone = random.choice(response_tones)
        
        # Yorumun derinliğini ve alaka düzeyini artırmak için prompt'u geliştiriyoruz.
        prompt = f"""
        You are a {persona} with a {style} writing style. Your task is to generate an insightful, unique, and genuinely analytical comment on the following tweet by @{username}. The comment should reflect your expertise and chosen style, aiming to add significant value to the conversation.

        Tweet Content: "{tweet_data.get('text', '')}"
        Tweet Author: @{username}

        Your comment MUST follow these instructions precisely:
        1.  **Perspective**: Adopt the viewpoint of the assigned persona, demonstrating genuine expertise.
        2.  **Originality**: Be completely unique and unplagiarized. Avoid any generic phrases.
        3.  **Depth**: Provide analytical depth. This means offering an insight, making a comparison, asking a truly penetrating question, or highlighting a non-obvious implication.
        4.  **Relevance**: Directly respond to the content of the tweet, showing you've understood it deeply.
        5.  **Conciseness**: Keep the comment under 280 characters. Every word must count.
        6.  **Engagement**: Formulate the comment according to this strategy: "{strategy}".
        7.  **Tone**: Maintain a {tone} tone.
        8.  **Emoji Use**: Use at most ONE highly relevant emoji if it adds significant value or clarity, otherwise omit. Place it thoughtfully.
        9.  **No Placeholders**: Do not include "[...]" or similar placeholders. Write the full, coherent comment.

        Generate ONLY the comment text. No other text, preambles, or explanations.
        """

        try:
            response = self.model.generate_content(prompt)
            comment = response.text.strip()
            
            # Yorumun Twitter karakter limitine uyduğundan emin ol
            if len(comment) > 280:
                # Akıllıca kısaltma yapmaya çalış, cümlenin ortasından kesmek yerine.
                # Genellikle son cümleden başlamak iyi bir stratejidir.
                truncated_comment = comment[:277] + "..."
                comment = truncated_comment
            
            logger.info(f"Successfully generated comment: {comment}")
            return comment
        except Exception as e:
            logger.error(f"Error generating comment for @{username}'s tweet: {e}", exc_info=True)
            # Daha özgün ve genel bir fallback yorum
            return f"The points @{username} raises are crucial for Web3's future. It sparks thought on how [mention a general relevant concept like 'scalability' or 'user adoption'] will evolve. Appreciate the insight!"

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # Bu kısmı test için kullanabiliriz. Gerçek bir Twitter entegrasyonu botunuzda olmalı.
    
    # Dummy project data for tweet generation
    sample_project = {
        "name": "Kaito AI",
        "twitter": "@KaitoInsights",
        "website": "https://kaito.ai/",
        "category": "AI, Crypto Analytics, Data Platform",
        "description": "Kaito is an AI-powered search and intelligence platform for crypto, providing institutional-grade insights and data for researchers and traders."
    }

    # Dummy tweet data for comment generation
    sample_tweet = {
        "text": "Scalability solutions in Web3 are reaching new frontiers with innovative L2s. But are we sacrificing decentralization for speed? #Blockchain #L2",
        "author_id": "12345",
        "id": "67890"
    }

    gemini_client = GeminiClient()

    print("--- Generating Project Tweet ---")
    generated_tweet = gemini_client.generate_project_tweet(sample_project)
    print(f"Generated Tweet:\n{generated_tweet}\n")

    print("--- Generating Tweet Comment ---")
    generated_comment = gemini_client.generate_comment("CryptoInsights", sample_tweet)
    print(f"Generated Comment:\n{generated_comment}\n")

    # Add a delay to avoid hitting rate limits during rapid testing if you were to loop this
    time.sleep(2)
    
    sample_tweet_2 = {
        "text": "The rise of Real World Asset (RWA) tokenization could bridge TradFi and DeFi. What are the biggest regulatory hurdles remaining? #RWA #DeFi",
        "author_id": "54321",
        "id": "09876"
    }
    print("--- Generating Another Tweet Comment ---")
    generated_comment_2 = gemini_client.generate_comment("DefiAnalyst", sample_tweet_2)
    print(f"Generated Comment:\n{generated_comment_2}\n")