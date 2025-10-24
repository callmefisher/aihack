import requests
from bs4 import BeautifulSoup
from typing import Optional


class URLFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_text_from_url(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            paragraphs = soup.find_all(['p', 'div'])
            text_content = []
            
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 20:
                    text_content.append(text)
            
            return '\n\n'.join(text_content)
            
        except Exception as e:
            raise Exception(f"获取URL内容失败: {str(e)}")
