"""
===============================================================================
NOME DEL PROGETTO : iOS-Style Top 4 News Widget
AUTORE            : Assistant & User
DATA              : 23 Agosto 2026
SCOPO             : Riproduce l'iconico widget iOS di aggregazione di 4 notizie 
                    fondamentali in una finestra compatta Tkinter.
LIBRERIE          : tkinter (GUI), urllib.request (HTTP), ssl (Bypass macOS SSL),
                    xml.etree (Parsing RSS), webbrowser (Apertura notizie)
===============================================================================
CRONOLOGIA AGGIORNAMENTI (CHANGELOG):
v1.0 - Versionamento iniziale tramite feed RSS Google News.
v2.0 - Passaggio a NewsAPI REST API.
v3.0 - Aggiunto fallback automatico.
v4.0 - Risolto errore 'nodename nor servname provided' su macOS Ventura
       tramite bypass contesto SSL nativo e alimentazione diretta RSS multi-sorgente.
===============================================================================
"""

import ssl
import tkinter as tk
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import webbrowser

# Bypass dei certificati SSL per evitare blocchi DNS/SSL tipici di Python su macOS
SSL_CONTEXT = ssl._create_unverified_context()

# Sorgenti notizie RSS ad alta affidabilità
RSS_SOURCES = [
    {
        "name": "Google News Italia",
        "url": "https://news.google.com/rss?hl=it&gl=IT&ceid=IT:it",
    },
    {"name": "ANSA", "url": "https://xml2.ansa.it/ansait_ric_rss.xml"},
]

# User-Agent nativo macOS Ventura / Safari
MAC_SAFARI_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)


# =============================================================================
# LOGICA DI RECUPERO DATI
# =============================================================================
def fetch_top_news(limit=4):
    """Recupera le notizie provando sequenzialmente le sorgenti disponibili."""
    for source in RSS_SOURCES:
        try:
            print(f"[INFO] Ttentativo di connessione a: {source['name']}...")
            req = urllib.request.Request(
                source["url"], headers={"User-Agent": MAC_SAFARI_USER_AGENT}
            )

            # Passiamo il contesto SSL disabilitato per macOS
            with urllib.request.urlopen(
                req, timeout=5, context=SSL_CONTEXT
            ) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)
            items = root.findall(".//item")

            if not items:
                continue

            news_list = []
            for item in items[:limit]:
                title = (
                    item.find("title").text
                    if item.find("title") is not None
                    else "Senza titolo"
                )
                link = (
                    item.find("link").text
                    if item.find("link") is not None
                    else ""
                )

                # Pulizia titolo (rimuove il nome fonte se già presente)
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    clean_title = parts[0]
                    src_label = parts[1]
                else:
                    clean_title = title
                    src_label = source["name"]

                news_list.append(
                    {"title": clean_title, "source": src_label, "link": link}
                )

            print(
                f"[SUCCESS] {len(news_list)} notizie caricate con successo!"
            )
            return news_list

        except Exception as e:
            print(f"[ERRORE {source['name']}] {e}")

    # Se tutte le sorgenti falliscono:
    return [
        {
            "title": "Verifica la connessione Wi-Fi del Mac e riprova.",
            "source": "NESSUNA CONNESSIONE",
            "link": "",
        }
    ]


# =============================================================================
# INTERFACCIA GRAFICA (TKINTER)
# =============================================================================
class NewsWidget(tk.Tk):
    """Finestra principale del widget in stile iOS Dark Mode."""

    def __init__(self):
        super().__init__()

        # Configurazione finestra principale
        self.title("Apple News Widget")
        self.geometry("380x380")
        self.resizable(False, False)
        self.configure(bg="#1C1C1E")  # Dark mode iOS background

        # Header del Widget
        header_frame = tk.Frame(self, bg="#1C1C1E")
        header_frame.pack(fill="x", padx=16, pady=(16, 10))

        # Iconico pallino rosso Apple News
        dot_label = tk.Label(
            header_frame,
            text="●",
            font=("Helvetica", 14, "bold"),
            fg="#FF2D55",
            bg="#1C1C1E",
        )
        dot_label.pack(side="left", padx=(0, 6))

        title_label = tk.Label(
            header_frame,
            text="NOTIZIE PRINCIPALI",
            font=("Helvetica", 12, "bold"),
            fg="#8E8E93",
            bg="#1C1C1E",
        )
        title_label.pack(side="left")

        # Pulsante di aggiornamento
        refresh_btn = tk.Label(
            header_frame,
            text="↻",
            font=("Helvetica", 14, "bold"),
            fg="#0A84FF",
            bg="#1C1C1E",
            cursor="hand2",
        )
        refresh_btn.pack(side="right")
        refresh_btn.bind("<Button-1>", lambda e: self.load_news())

        # Contenitore dinamico delle notizie
        self.news_container = tk.Frame(self, bg="#1C1C1E")
        self.news_container.pack(
            fill="both", expand=True, padx=16, pady=(0, 16)
        )

        # Carica le notizie al primo avvio
        self.load_news()

    def load_news(self):
        """Popola o aggiorna le 4 schede notizia."""
        for widget in self.news_container.winfo_children():
            widget.destroy()

        news_items = fetch_top_news(limit=4)

        for item in news_items:
            card = tk.Frame(self.news_container, bg="#2C2C2E", cursor="hand2")
            card.pack(fill="x", pady=4, ipady=6, ipadx=8)

            source_label = tk.Label(
                card,
                text=item["source"].upper(),
                font=("Helvetica", 8, "bold"),
                fg="#0A84FF",
                bg="#2C2C2E",
                anchor="w",
            )
            source_label.pack(fill="x")

            title_label = tk.Label(
                card,
                text=item["title"],
                font=("Helvetica", 12),
                fg="#FFFFFF",
                bg="#2C2C2E",
                anchor="w",
                justify="left",
                wraplength=340,
            )
            title_label.pack(fill="x")

            if item["link"]:
                link_url = item["link"]
                card.bind(
                    "<Button-1>", lambda e, url=link_url: webbrowser.open(url)
                )
                source_label.bind(
                    "<Button-1>", lambda e, url=link_url: webbrowser.open(url)
                )
                title_label.bind(
                    "<Button-1>", lambda e, url=link_url: webbrowser.open(url)
                )


# =============================================================================
# AVVIO APPLICAZIONE
# =============================================================================
if __name__ == "__main__":
    app = NewsWidget()
    app.mainloop()