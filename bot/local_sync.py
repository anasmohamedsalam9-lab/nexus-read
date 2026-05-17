import os
import json
import re

class LocalSync:
    def __init__(self, data_js_path):
        self.data_js_path = data_js_path

    def _parse_json_array_between_markers(self, content, start_marker, end_marker):
        """Safely extract and parse JSON array content between markers."""
        if start_marker not in content or end_marker not in content:
            return None, None, None

        parts = content.split(start_marker)
        if len(parts) < 2: return None, None, None
        
        head = parts[0]
        mid_and_tail = parts[1]
        
        if end_marker not in mid_and_tail:
            return None, None, None
            
        parts_sub = mid_and_tail.split(end_marker)
        mid = parts_sub[0]
        tail = end_marker.join(parts_sub[1:])

        # Clean-up segment
        mid_stripped = mid.strip().strip(',')
        if not mid_stripped:
            return head, [], tail

        try:
            items = json.loads(f"[{mid_stripped}]")
            return head, items, tail
        except json.JSONDecodeError:
            try:
                # Attempt recovery for trailing commas
                fixed = re.sub(r',\s*$', '', mid_stripped)
                items = json.loads(f"[{fixed}]")
                return head, items, tail
            except:
                print(f"[error] فشل تحليل JSON بين العلامات حتى بعد محاولة الإصلاح.")
                return head, None, tail

    def get_existing_manga_info(self, title, category='manhwa'):
        """يبحث عن المانجا في الموقع ليتأكد إذا كانت موجودة، ويرجع عدد فصولها."""
        if not os.path.exists(self.data_js_path):
            return False, 0
            
        with open(self.data_js_path, 'r', encoding='utf-8') as f:
            full_content = f.read()

        start_marker = f"/* LATEST_{category.upper()}_START */"
        end_marker = f"/* LATEST_{category.upper()}_END */"
        
        _, existing_items, _ = self._parse_json_array_between_markers(full_content, start_marker, end_marker)
        
        if existing_items:
            for item in existing_items:
                if isinstance(item, dict) and item.get('title', '').strip().lower() == title.strip().lower():
                    # Calculate max chapter number
                    max_ch = 0
                    for ch in item.get('chapters', []):
                        try:
                            ch_num = float(re.findall(r'\d+\.?\d*', str(ch.get('n', '0')))[0])
                            if ch_num > max_ch:
                                max_ch = ch_num
                        except:
                            pass
                    return True, max_ch
                
        # Try checking the other category if not found
        if category == 'manhwa':
            return self.get_existing_manga_info(title, 'manga')
            
        return False, 0

    async def update_data_js(self, manga_data, category='manhwa'):
        if not os.path.exists(self.data_js_path):
            print(f"[error] ملف {self.data_js_path} غير موجود.")
            return

        with open(self.data_js_path, 'r', encoding='utf-8') as f:
            full_content = f.read()

        # Markers
        start_marker = f"/* LATEST_{category.upper()}_START */"
        end_marker = f"/* LATEST_{category.upper()}_END */"

        if start_marker not in full_content or end_marker not in full_content:
            print(f"[error] العلامات الجوهرية مفقودة في data.js: {start_marker} / {end_marker}")
            return

        head, existing_items, tail = self._parse_json_array_between_markers(
            full_content, start_marker, end_marker
        )

        if existing_items is None:
            print("[error] تعذر تحليل البيانات الموجودة في data.js. لن يتم الكتابة.")
            return

        # Prepare the new/updated entry
        title = manga_data.get('title', 'Unknown')
        chapters = manga_data.get('chapters', [])

        # Sort chapters descending by number
        def get_ch_num(ch):
            try:
                return float(re.findall(r'\d+\.?\d*', str(ch.get('n', '0')))[0])
            except:
                return 0
        chapters.sort(key=get_ch_num, reverse=True)

        new_entry = {
            "title": title,
            "img": manga_data.get('cover', manga_data.get('img', '')),
            "rating": manga_data.get('rating', '9.5'),
            "genres": manga_data.get('genres', ["Action", "Fantasy"]),
            "description": manga_data.get('description', "اكتشف العناصر الحصرية والجديدة التي تمت إضافتها للتو. لا تفوت الفرصة!"),
            "chapters": chapters
        }

        # Merge: update existing entry or insert new
        found = False
        for i, item in enumerate(existing_items):
            if isinstance(item, dict) and item.get('title', '').lower() == title.lower():
                # Merge chapters: keep existing + add new
                existing_chapters = {str(ch.get('n', '')): ch for ch in item.get('chapters', []) if isinstance(ch, dict)}
                for ch in chapters:
                    existing_chapters[str(ch.get('n', ''))] = ch  # Overwrite or add
                
                merged_chapters = list(existing_chapters.values())
                merged_chapters.sort(key=get_ch_num, reverse=True)
                
                new_entry['chapters'] = merged_chapters
                # Preserve existing cover if new one is empty
                if not new_entry['img'] and item.get('img'):
                    new_entry['img'] = item['img']
                
                existing_items[i] = new_entry
                found = True
                break

        if not found:
            existing_items.insert(0, new_entry)

        # Serialize each item with proper indentation
        item_strings = []
        for item in existing_items:
            item_str = json.dumps(item, ensure_ascii=False, indent=4)
            item_strings.append(item_str)

        new_mid = ",\n".join(item_strings)

        # Write back with preserved markers
        updated_content = f"{head}{start_marker}\n{new_mid}\n{end_marker}{tail}"

        with open(self.data_js_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"[success] تم تحديث {self.data_js_path} بالعمل: {title}")
