import requests
import feedparser
import time
import smtplib
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÕES DE EMAIL ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "peixoto1987ca@gmail.com"
EMAIL_PASSWORD = "gasf fkoc gpth njkv"
TO_EMAIL = "peixoto1987ca@gmail.com"

# --- DICIONÁRIO COMPLETO EMPRESA-TICKER ---
COMPANY_TICKERS = {
    # Big Pharma (original)
    "Pfizer": "PFE",
    "Moderna": "MRNA",
    "BioNTech": "BNTX",
    "Novartis": "NVS",
    "Merck": "MRK",
    "Johnson & Johnson": "JNJ",
    "Roche": "RHHBY",
    "Sanofi": "SNY",
    "AstraZeneca": "AZN",
    "GlaxoSmithKline": "GSK",
    "Eli Lilly": "LLY",
    "AbbVie": "ABBV",
    "Bristol-Myers Squibb": "BMY",
    "Gilead Sciences": "GILD",
    "Amgen": "AMGN",
    
    # Biotech (original)
    "Bionano Genomics": "BNGO",
    "CRISPR Therapeutics": "CRSP",
    "Editas Medicine": "EDIT",
    "Intellia Therapeutics": "NTLA",
    "Regeneron": "REGN",
    "Vertex Pharmaceuticals": "VRTX",
    "Alnylam Pharmaceuticals": "ALNY",
    "Biogen": "BIIB",
    "Illumina": "ILMN",
    "Exact Sciences": "EXAS",
    "Guardant Health": "GH",
    "Invitae": "NVTA",
    "Pacific Biosciences": "PACB",
    
    # Nuclear/Energy (original)
    "NuScale Power": "SMR",
    "General Electric": "GE",
    
    # Tech Giants (original)
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Google": "GOOG",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Nvidia": "NVDA",
    "Meta": "META",
    "Intel": "INTC",
    
    # Healthcare Tech (original)
    "Teladoc": "TDOC",
    "Livongo": "LVGO",
    "Veeva Systems": "VEEV",
    
    # --- ADIÇÃO: CRIPTOMOEDAS (ROBINHOOD) ---
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Dogecoin": "DOGE-USD",
    "Shiba Inu": "SHIB-USD",
    "Litecoin": "LTC-USD",
    "Solana": "SOL-USD",
    "Polygon": "MATIC-USD",
    "Avalanche": "AVAX-USD",
    "Chainlink": "LINK-USD",
    "Uniswap": "UNI-USD",
    "Stellar": "XLM-USD",
    "Algorand": "ALGO-USD",
    "Filecoin": "FIL-USD",
    "Tezos": "XTZ-USD",
    "Decentraland": "MANA-USD",
    "The Sandbox": "SAND-USD",
    "USD Coin": "USDC-USD"
}

# --- PALAVRAS-CHAVE ATUALIZADAS (ORIGINAIS + CRIPTO) ---
KEYWORDS = [
    # --- SUAS PALAVRAS-CHAVE ORIGINAIS ---
    "FDA approved", "approval", "approved", "cleared", "authorized", "fast track",
    "priority review", "breakthrough therapy", "orphan drug", "RMAT", "PMA approval",
    "BLA approval", "NDA approval", "accelerated approval", "emergency use authorization", "EUA",
    "phase 1 success", "phase 2 success", "phase 3 success", "phase 3", "phase 3 data",
    "clinical trial success", "clinical trial results", "positive data", "efficacy data",
    "earnings beat", "revenue growth", "profit surge", "raised guidance", "upside potential",
    "blockbuster drug", "sales jump", "beat estimates",
    "acquisition", "merger", "takeover", "buyout", "strategic partnership",
    "stock surge", "stock rally", "shares jump", "short squeeze",
    
    # --- PALAVRAS-CHAVE DE CRIPTO ADICIONADAS ---
    # Fundamentos
    "adoption", "partnership", "listing", "burn", "scarcity", "halving",
    # Mercado
    "bullish", "breakout", "rally", "surge", "soaring", "price increase", 
    "uptrend", "bull run", "all-time high", "ATH", "recovery",
    # Tecnologia
    "upgrade", "mainnet", "staking", "yield farming", "protocol upgrade",
    # Eventos
    "airdrop", "buyback", "supply reduction", 
    # Indicadores
    "volume spike", "liquidity", "whale accumulation",
    # Projeções
    "price target", "upside potential",
    # Sentimento
    "optimism", "market confidence", "FOMO"
]

SEEN_FILE = "seen_links.txt"
RSS_FEEDS = [
    # (Mantenha seus feeds RSS originais aqui)
]


# --- FUNÇÃO PARA ENCONTRAR PALAVRA-CHAVE ---
def find_keyword_in_text(text, keywords):
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return keyword
    return None


# --- FUNÇÃO PARA EXTRAIR TICKERS ---
def extract_tickers(text):
    found_tickers = set()
    text_lower = text.lower()

    for company, ticker in COMPANY_TICKERS.items():
        if company.lower() in text_lower and ticker != "Private":
            found_tickers.add(ticker)

    ticker_matches = re.findall(r'\b[A-Z]{2,5}\b', text)
    for match in ticker_matches:
        if match in COMPANY_TICKERS.values():
            found_tickers.add(match)

    return list(found_tickers)


# --- FUNÇÃO PARA ENVIAR EMAIL ---
def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    # Formata como HTML para negrito
    html_body = f"""
    <html>
        <body>
            <pre style="font-family: monospace;">
{body}
            </pre>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        print("✅ Email enviado com formatação!")
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")


# --- FUNÇÃO PARA BUSCAR NOTÍCIAS ---
def get_finance_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    news_list = []

    for rss_url in RSS_FEEDS:
        try:
            print(f"\n🔍 Verificando feed: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if not feed.entries:
                print(f"⚠️ Nenhuma notícia encontrada em {rss_url}")
                continue

            for entry in feed.entries:
                title = entry.get('title', 'Sem título')
                link = entry.get('link', '#')
                news_list.append((title, link))

        except Exception as e:
            print(f"⚠️ Erro no feed {rss_url}: {str(e)}")

    return news_list


# --- GERENCIAMENTO DE LINKS ---
def load_seen_links():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(line.strip() for line in f)


def save_seen_links(links):
    with open(SEEN_FILE, "a") as f:
        for link in links:
            f.write(link + "\n")


# --- FUNÇÃO PRINCIPAL ---
def main():
    print("\n" + "=" * 50)
    print("🔎 Iniciando busca por notícias relevantes...")
    print("=" * 50 + "\n")

    seen_links = load_seen_links()
    news = get_finance_news()
    new_items = []

    for title, link in news:
        if link not in seen_links:
            keyword = find_keyword_in_text(title, KEYWORDS)
            tickers = extract_tickers(title)

            if keyword or tickers:  # Só adiciona se encontrar palavra-chave ou ticker
                new_items.append((title, link, keyword, tickers))

    if new_items:
        print("\n✅ Novas notícias encontradas:")
        email_body = "📰 Notícias financeiras relevantes:\n\n"

        for title, link, keyword, tickers in new_items:
            ticker_str = f"[{', '.join(tickers)}] " if tickers else ""
            keyword_str = f"<b>{keyword}</b>" if keyword else ""

            email_body += (
                f"• {ticker_str}{title}\n"
                f"   🔑 Palavra-chave: {keyword_str}\n"
                f"   🔗 Link: {link}\n\n"
            )
            print(f"• {ticker_str}{title}")

        send_email("🚨 Alertas de Investimento", email_body, TO_EMAIL)
        save_seen_links([link for _, link, _, _ in new_items])
    else:
        print("\n📭 Nenhuma notícia nova encontrada.")


if __name__ == "__main__":
    while True:
        try:
            main()
            print("\n⏳ Aguardando próxima verificação (5 minutos)...")
            time.sleep(300)
        except KeyboardInterrupt:
            print("\n🛑 Script interrompido pelo usuário")
            break
        except Exception as e:
            print(f"\n⚠️ Erro inesperado: {str(e)}")
            print("Reiniciando em 10 segundos...")
            time.sleep(10)
