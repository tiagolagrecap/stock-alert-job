import requests
import feedparser
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÕES DE EMAIL ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "peixoto1987ca@gmail.com"
EMAIL_PASSWORD = "gasf fkoc gpth njkv"
TO_EMAIL = "destinatario@gmail.com"  # Substitua pelo e-mail de destino

# --- PALAVRAS-CHAVE ---
KEYWORDS = [
    "FDA approved", "approval", "approved", "cleared", "authorized", "green light", "allowed",
    "fast track", "priority review", "breakthrough therapy", "orphan drug", "RMAT", "expanded indication",
    "clinical trial success", "phase 1", "phase 2", "phase 3", "market authorization", "CEO"
]

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

# --- MAIN LOOP ---
def main():
    news = get_yahoo_finance_rss()
    new_items = []

    for title, link in news:
        # Aqui você pode salvar os links já enviados em um arquivo .txt se quiser
        new_items.append((title, link))

    if new_items:
        email_body = "📰 Novas notícias encontradas:\n\n"
        for title, link in new_items:
            email_body += f"• {title}\n{link}\n\n"
        send_email("Novas notícias encontradas", email_body, TO_EMAIL)
    else:
        print("📭 Nenhuma notícia nova no momento.")

if __name__ == "__main__":
    main()

