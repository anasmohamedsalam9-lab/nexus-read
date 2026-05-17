import re
import os

def proxy_urls():
    with open('data.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to find img URLs starting with specific patterns and not already proxied
    # Skip if already contains weserv
    pattern = r'img:\s*\"(https://(s4\.anilist\.co|static\.mangadex\.org).+?)\"'
    
    def replacer(match):
        original_url = match.group(1)
        if "weserv.nl" in original_url:
            return match.group(0)
        return f'img: "https://images.weserv.nl/?url={original_url}"'
    
    new_content = re.sub(pattern, replacer, content)
    
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully applied image proxy to data.js")

if __name__ == "__main__":
    proxy_urls()
