import requests
import feedparser
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÕES DE EMAIL ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "peixoto1987ca@gmail.com"
EMAIL_PASSWORD = "gasf fkoc gpth njkv"
TO_EMAIL = "peixoto1987ca@gmail.com"  # Substitua pelo e-mail de destino

# --- PALAVRAS-CHAVE ---
KEYWORDS = [
    "FDA approved", "approval", "approved", "cleared", "authorized", "green light", "allowed",
    "fast track", "priority review", "breakthrough therapy", "orphan drug", "RMAT", "expanded indication",
    "clinical trial success", "clinical trial positive", "clinical trial results",
    "phase 1 success", "phase 2 success", "phase 3 success",
    "phase 1 data", "phase 2 data", "phase 3 data",
    "market authorization", "NDA approval", "BLA approval",
    "accelerated approval", "conditional approval", "emergency use authorization", "EUA granted",
    "clearance granted", "label expansion", "indication approved",
    "product launch", "launch approved", "regulatory approval", "marketing approval",
    "positive feedback from FDA", "FDA breakthrough designation", "FDA fast track designation",
    "FDA priority review", "approval recommended", "submission accepted", "submission granted",
    "license granted", "patent approved", "stock surge", "stock rally", "shares jump",
    "shares rally", "shares surge", "investor confidence", "partnership agreement",
    "collaboration agreement", "deal signed", "licensing agreement", "royalty agreement"
]

SEEN_FILE = "seen_links.txt"

# --- FUNÇÃO PARA ENVIAR EMAIL ---
def send_email(subject, body, to_email):
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
        print("✅ E-mail enviado com todas as notícias.")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

# --- FUNÇÃO PARA BUSCAR E FILTRAR NOTÍCIAS ---
def get_yahoo_finance_rss():
    rss_url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL,MSFT,GOOG&region=US&lang=en-US"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(rss_url, headers=headers)
    response.raise_for_status()
    feed = feedparser.parse(response.content)

    news_list = []
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        title_lower = title.lower()

        if any(keyword.lower() in title_lower for keyword in KEYWORDS):
            news_list.append((title, link))
    return news_list

# --- FUNÇÕES PARA GERENCIAR LINKS JÁ ENVIADOS ---
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
    seen_links = load_seen_links()
    news = get_yahoo_finance_rss()
    new_items = []

    for title, link in news:
        if link not in seen_links:
            new_items.append((title, link))

    if new_items:
        email_body = "📰 Novas notícias encontradas:\n\n"
        for title, link in new_items:
            email_body += f"• {title}\n{link}\n\n"

        print("🖥️ Notícias encontradas:")
        for title, link in new_items:
            print(f"• {title}\n{link}\n")

        send_email("Novas notícias encontradas", email_body, TO_EMAIL)
        save_seen_links([link for _, link in new_items])
    else:
        print("📭 Nenhuma notícia nova no momento.")

# --- LOOP INFINITO COM INTERVALO DE 5 MINUTOS ---
if __name__ == "__main__":
    while True:
        print("🔁 Verificando notícias...")
        main()
        print("🕒 Aguardando 5 minutos...\n")
        time.sleep(300)  # 300 segundos = 5 minutos
