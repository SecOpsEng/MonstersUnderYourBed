# Import dependencies
import requests
from bs4 import BeautifulSoup
import sqlite3
import re

def start_session(http_port = 9051, https_port = 9051):
    # Create tor session
    ses = requests.session()
    ses.proxies = {}
    ses.proxies['http'] = 'socks5h://localhost:{}'.format(http_port)
    ses.proxies['https'] = 'socks5h://localhost:{}'.format(https_port)
    return ses

def scan_onion_service(url, depth):
    print("Scanning {}".format(url))
    if depth == 0:
        return
    try:
        session = start_session()
        response = session.get(url)
    except:
        return
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        # Find all onion links        
        links = re.findall(r'http[s]?://[a-zA-Z0-9\-\.]+\.onion', text)
        findings = sum(len(re.findall(pattern, text)) for pattern in patterns)

        # Insert or update the service in the database        
        c.execute('INSERT OR IGNORE INTO services (url, inbound, outbound, findings) VALUES (?, 0, 0, ?)', (url, findings))
        c.execute('UPDATE services SET findings = ? WHERE url = ?', (findings, url))
        for link in links:
            c.execute('INSERT OR IGNORE INTO services (url, inbound, outbound, findings) VALUES (?, 0, 0, 0)', (link,))
            c.execute('INSERT INTO connections (source, target) VALUES (?, ?)', (url, link))
            c.execute('UPDATE services SET outbound = outbound + 1 WHERE url = ?', (url,))
            c.execute('UPDATE services SET inbound = inbound + 1 WHERE url = ?', (link,))

            # Recursive scan            
            scan_onion_service(link, depth - 1)
        # Find all btc addresses
        btc_addresses = soup.findAll(text=re.compile(r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b'))
        # Add btc findings to db
        for address in btc_addresses:
            c.execute('INSERT OR IGNORE INTO bitcoin_addresses (address, url) VALUES (?,?)', (re.search(r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b',address)[0],url))

        conn.commit()    
    except Exception as e:
        print(f"Failed to scan {url}: {e}")

# Sample patterns to scan for in each URL
patterns = [r'Western Union', r'western union', r'money order', r'Money Order']
# Initialize SQLite database
conn = sqlite3.connect('onion_services.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS services
             (url TEXT PRIMARY KEY, inbound INTEGER, outbound INTEGER, findings INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS connections
             (source TEXT, target TEXT, FOREIGN KEY(source) REFERENCES services(url), FOREIGN KEY(target) REFERENCES services(url))''')
c.execute('''CREATE TABLE IF NOT EXISTS bitcoin_addresses
             (address TEXT, url TEXT, FOREIGN KEY(url) REFERENCES services(url))''')
conn.commit()

# Start scanning from a given onion service URL
seed_urls = [
    'http://deepmlzxkh7tpnuiv32nzzg6oxza4nvpd6b7ukujwxzgxj2f33johuqd.onion/',
    'http://2fd6cemt4gmccflhm6imvdfvli3nf7zn6rfrwpsy7uhxrgbypvwf5fad.onion/search/Western-Union'
]
for url in seed_urls:
    scan_depth = 5
    scan_onion_service(url, scan_depth)