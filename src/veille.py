import feedparser
import json
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Configuration des flux et mots-clés
RSS_FEEDS = [
    "https://www.zdnet.fr/feeds/rss/actualites/",
    "https://www.lemondeinformatique.fr/flux-rss/thematique/toutes-les-actualites/rss.xml",
    "https://techcrunch.com/feed/",
]

KEYWORDS = [
    "cybersécurité", "ransomware", "zero trust", "cloud", "aws", "azure", "gcp",
    "ia", "intelligence artificielle", "llm", "openai", "mistral",
    "devops", "kubernetes", "docker", "linux", "windows", "android",
]

# Chemins (automatiques grâce à Pathlib)
BASE_DIR = Path(__file__).parent.parent
OUT_DIR = BASE_DIR / "output"
ARCHIVE_DIR = OUT_DIR / "archives"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

def get_image(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''): return link.href
    return "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=500&auto=format&fit=crop"

def main():
    print("Démarrage de la collecte...")
    rows = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            title, summary = e.get("title", ""), e.get("summary", "")
            if any(k.lower() in (title + " " + summary).lower() for k in KEYWORDS):
                rows.append({
                    "date": e.get("published", "") or e.get("updated", ""),
                    "title": title,
                    "link": e.get("link", ""),
                    "source": feed.feed.get("title", "Info Tech"),
                    "image": get_image(e)
                })

    if not rows:
        print("Aucun article trouvé."); return

    df = pd.DataFrame(rows).drop_duplicates(subset=["title", "link"])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # 1. Sauvegarde l'archive JSON
    json_filename = f"veille_{today}.json"
    df.to_json(ARCHIVE_DIR / json_filename, orient="records", force_ascii=False, indent=4)

    # 2. Met à jour l'index central
    index_path = OUT_DIR / "index.json"
    index_data = []
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
    
    if not any(item['date'] == today for item in index_data):
        index_data.insert(0, {"date": today, "file": f"archives/{json_filename}"})
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data[:20], f, ensure_ascii=False, indent=4)
    print("Veille terminée avec succès.")

if __name__ == "__main__":
    main()
