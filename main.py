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
    # Big Pharma
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

    # Biotech
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

    # Nuclear/Energy
    "NuScale Power": "SMR",
    "TerraPower": "Private",
    "General Electric": "GE",

    # Tech Giants
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Google": "GOOG",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Nvidia": "NVDA",
    "Meta": "META",
    "Intel": "INTC",

    # Healthcare Tech
    "Teladoc": "TDOC",
    "Livongo": "LVGO",
    "Veeva Systems": "VEEV"
}

# --- PALAVRAS-CHAVE ATUALIZADAS ---
KEYWORDS = [
    # Aprovações Regulatórias
    "FDA approved", "approval", "approved", "cleared", "authorized", "fast track",
    "priority review", "breakthrough therapy", "orphan drug", "RMAT", "PMA approval",
    "BLA approval", "NDA approval", "accelerated approval", "emergency use authorization", "EUA",

    # Resultados Clínicos
    "phase 1 success", "phase 2 success", "phase 3 success", "phase 3", "phase 3 data",
    "clinical trial success", "clinical trial results", "positive data", "efficacy data",

    # Desempenho Financeiro
    "earnings beat", "revenue growth", "profit surge", "raised guidance", "upside potential",
    "blockbuster drug", "sales jump", "beat estimates",

    # Fusões & Aquisições
    "acquisition", "merger", "takeover", "buyout", "strategic partnership",

    # Movimentação de Ações
    "stock surge", "stock rally", "shares jump", "short squeeze"
]

SEEN_FILE = "seen_links.txt"

# --- FONTES DE NOTÍCIAS CONFIÁVEIS ---
RSS_FEEDS = [
    f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={','.join([ticker for ticker in COMPANY_TICKERS.values() if ticker != 'Private'])}&region=US&lang=en-US",
    "https://www.fiercebiotech.com/rss.xml",
    "https://endpts.com/feed/",
    "http://feeds.feedburner.com/biospace"
]


# --- FUNÇÃO PARA EXTRAIR TICKERS DAS NOTÍCIAS ---
def extract_tickers(text):
    found_tickers = set()
    text_lower = text.lower()

    for company, ticker in COMPANY_TICKERS.items():
        if company.lower() in text_lower and ticker != "Private":
            found_tickers.add(ticker)

    # Procura por padrões de ticker no texto (ex: "NASDAQ: AAPL")
    ticker_matches = re.findall(r'\b[A-Z]{2,5}\b', text)
    for match in ticker_matches:
        if match in COMPANY_TICKERS.values():
            found_tickers.add(match)

    return list(found_tickers)


# --- FUNÇÃO PARA ENVIAR EMAIL (COM TICKERS) ---
def send_email(subject, body, to_email):
    # Extrai tickers do corpo do email
    related_tickers = extract_tickers(body)

    # Adiciona seção de tickers ao email
    if related_tickers:
        tickers_section = "\n🔍 Ações Relacionadas: " + ", ".join(related_tickers)
        body += tickers_section

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")


# --- FUNÇÃO PARA BUSCAR NOTÍCIAS COM TRATAMENTO DE ERROS ---
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
                description = entry.get('description', '').lower()
                title_lower = title.lower()

                if any(keyword.lower() in title_lower or keyword.lower() in description for keyword in KEYWORDS):
                    news_list.append((title, link))
                    print(f"👉 Notícia relevante: {title}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao acessar {rss_url}: {str(e)}")
        except Exception as e:
            print(f"⚠️ Erro inesperado em {rss_url}: {str(e)}")

    return news_list


# --- GERENCIAMENTO DE LINKS JÁ VISTOS ---
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
            new_items.append((title, link))

    if new_items:
        print("\n✅ Novas notícias encontradas:")
        email_body = "📰 Notícias financeiras relevantes:\n\n"
        for title, link in new_items:
            print(f"• {title}\n   {link}\n")
            email_body += f"• {title}\n   {link}\n\n"

        send_email("🚨 Alertas de Investimento", email_body, TO_EMAIL)
        save_seen_links([link for _, link in new_items])
    else:
        print("\n📭 Nenhuma notícia nova encontrada.")


# --- EXECUÇÃO ---
if __name__ == "__main__":
    while True:
        main()
        print("\n⏳ Aguardando 5 minutos para próxima verificação...")
        time.sleep(300)
