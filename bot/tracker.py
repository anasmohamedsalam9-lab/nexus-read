import json
import os

TRACKER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracked_mangas.json')

class MangaTracker:
    def __init__(self):
        self.tracker_file = TRACKER_FILE
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.tracker_file):
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def load_tracked(self):
        try:
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_tracked(self, data):
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_tracking(self, title, url):
        """يحفظ أو يحدث رابط المانجا."""
        data = self.load_tracked()
        title_lower = title.strip().lower()
        data[title_lower] = {
            "title": title.strip(),
            "url": url,
        }
        self.save_tracked(data)

    def get_url(self, title):
        data = self.load_tracked()
        return data.get(title.strip().lower(), {}).get('url')

    def get_all_tracked(self):
        """يرجع جميع المانهوات المتابعة حاليا"""
        return self.load_tracked()
