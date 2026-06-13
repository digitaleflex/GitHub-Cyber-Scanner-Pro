import requests
from bs4 import BeautifulSoup

url = "https://csrc.nist.gov/publications/sp800"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # On cherche des éléments qui pourraient contenir les publications
        # Typiquement des div avec des classes comme 'publication-item' ou dans un tableau
        print("--- TITRE DE LA PAGE ---")
        print(soup.title.string)
        
        # On cherche les lignes de tableau ou des divs de liste
        pubs = soup.find_all('tr', class_='publication-item')
        if not pubs:
            pubs = soup.find_all('div', class_='publication-item')
        
        if pubs:
            print(f"--- {len(pubs)} PUBLICATIONS TROUVÉES ---")
            for pub in pubs[:3]:
                print(pub.prettify()[:500])
        else:
            # Si on ne trouve pas par classe, on cherche les liens vers /publications/detail/
            links = soup.find_all('a', href=True)
            detail_links = [l for l in links if '/publications/detail/sp' in l['href']]
            print(f"--- {len(detail_links)} LIENS DE DÉTAIL TROUVÉS ---")
            for l in detail_links[:5]:
                print(f"Lien: {l['href']} - Texte: {l.text.strip()}")
    else:
        print(f"Status Code: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
