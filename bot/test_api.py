import cloudscraper
import json

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

def test_api(slug):
    print(f"Testing API for: {slug}")
    m_res = scraper.get(f"https://mangatek.com/api/manga/{slug}", headers=headers)
    if m_res.status_code == 200:
        m_data = m_res.json()
        manga_id = m_data.get('id')
        print(f"Manga ID: {manga_id}")
        
        if manga_id:
            api_url = f"https://mangatek.com/api/chapters?filters[manga][id][$eq]={manga_id}&pagination[limit]=500&sort[0]=number:desc"
            print(f"Fetching from: {api_url}")
            api_res = scraper.get(api_url, headers=headers)
            if api_res.status_code == 200:
                data = api_res.json()
                ch_list = data.get('data', [])
                print(f"Total Chapters from API: {len(ch_list)}")
                if ch_list:
                    print(f"Latest: {ch_list[0]['attributes']['number']}")
                    print(f"Oldest: {ch_list[-1]['attributes']['number']}")
            else:
                print(f"API Failed: {api_res.status_code}")
    else:
        print(f"Manga Res Failed: {m_res.status_code}")

test_api('white-dragon-duke-pendragon')
