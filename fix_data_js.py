"""Fix the corrupted data.js file by:
1. Removing orphaned chapter blocks between first manga entry and markers
2. Moving White Dragon Duke inside the markers  
3. Fixing mojibake descriptions
"""
import json
import re
import os

data_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.js')

with open(data_js_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to reconstruct data.js properly
# The structure should be:
# const SITE_DATA = {
#     manhwa: {
#         topSlider: [],
#         trending: [],
#         latest: [
#             /* LATEST_MANHWA_START */
#             { ...manga1... },
#             { ...manga2... }
#             /* LATEST_MANHWA_END */
#         ],
#         popular: []
#     },
#     ...
# };

# Extract the data between LATEST_MANHWA_START and LATEST_MANHWA_END
start_marker = "/* LATEST_MANHWA_START */"
end_marker = "/* LATEST_MANHWA_END */"

if start_marker not in content or end_marker not in content:
    print("ERROR: Markers not found!")
    exit(1)

# Get the content between markers
_, after_start = content.split(start_marker, 1)
between_markers, _ = after_start.split(end_marker, 1)

# Parse the existing manga entries between markers
between_stripped = between_markers.strip().rstrip(',')
try:
    marker_items = json.loads(f"[{between_stripped}]")
    print(f"Found {len(marker_items)} items between markers")
except:
    print("Failed to parse items between markers, trying to fix...")
    # Try removing trailing commas
    fixed = re.sub(r',\s*([}\]])', r'\\1', between_stripped)
    marker_items = json.loads(f"[{fixed}]")

# Now we need to also find the White Dragon Duke entry that's BEFORE the markers
# It's the first entry in the `latest: [` array but outside the markers
# We need to extract it and add it to the marker items

# Find the chapters data for White Dragon Duke from the content before the marker
# The first entry starts at "latest: [" and ends at the start marker
latest_start = content.find('latest: [')
before_markers = content[latest_start+len('latest: ['):content.find(start_marker)]

# Try to extract the White Dragon Duke object - it's everything from the first { to the matching }
# This is tricky because there are orphaned chapter blocks. Let's find it by looking for the title
# and extracting through brace matching

# Actually, let's check if White Dragon already exists in marker items
has_white_dragon = any(
    item.get('title', '').lower() == 'white dragon duke: pendragon' 
    for item in marker_items
)

# Let's also find chapter data from the pre-marker content
# We know the chapters for White Dragon Duke are in the assets/chapters/white-dragon-duke-pendragon/ folder
# Let's find all valid chapter folders
chapters_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'chapters', 'white-dragon-duke-pendragon')
white_dragon_chapters = []

if os.path.exists(chapters_dir):
    for ch_dir in sorted(os.listdir(chapters_dir), key=lambda x: float(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0, reverse=True):
        ch_path = os.path.join(chapters_dir, ch_dir)
        if os.path.isdir(ch_path):
            ch_num_match = re.search(r'ch-(\d+)', ch_dir)
            if ch_num_match:
                ch_num = ch_num_match.group(1)
                pages = []
                for img in sorted(os.listdir(ch_path), key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0):
                    if img.endswith('.webp'):
                        pages.append(f"assets/chapters/white-dragon-duke-pendragon/{ch_dir}/{img}")
                if pages:
                    white_dragon_chapters.append({
                        "n": ch_num,
                        "d": "اليوم",
                        "pages": pages
                    })

if white_dragon_chapters:
    print(f"Found {len(white_dragon_chapters)} White Dragon chapters on disk")

# Build the White Dragon Duke entry from disk data
if not has_white_dragon and white_dragon_chapters:
    white_dragon_entry = {
        "title": "White Dragon Duke: Pendragon",
        "img": "",
        "rating": "9.5",
        "genres": ["Action", "Fantasy"],
        "description": "اكتشف العناصر الحصرية والجديدة التي تمت إضافتها للتو. لا تفوت الفرصة!",
        "chapters": white_dragon_chapters
    }
    marker_items.insert(0, white_dragon_entry)
    print("Added White Dragon Duke: Pendragon to marker items")
elif has_white_dragon:
    print("White Dragon Duke already exists in marker items, updating chapters...")
    for item in marker_items:
        if item.get('title', '').lower() == 'white dragon duke: pendragon' and white_dragon_chapters:
            item['chapters'] = white_dragon_chapters
            item['description'] = "اكتشف العناصر الحصرية والجديدة التي تمت إضافتها للتو. لا تفوت الفرصة!"

# Fix mojibake descriptions in all items
for item in marker_items:
    desc = item.get('description', '')
    # Check for mojibake (UTF-8 interpreted as Latin-1)
    if 'Ø' in desc or 'Ù' in desc:
        item['description'] = "اكتشف العناصر الحصرية والجديدة التي تمت إضافتها للتو. لا تفوت الفرصة!"

# Also check Spare Me chapters from disk
spare_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'chapters', 'spare-me-great-lord')
if os.path.exists(spare_dir):
    spare_chapters = []
    for ch_dir in sorted(os.listdir(spare_dir), key=lambda x: float(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0, reverse=True):
        ch_path = os.path.join(spare_dir, ch_dir)
        if os.path.isdir(ch_path):
            ch_num_match = re.search(r'ch-(\d+)', ch_dir)
            if ch_num_match:
                ch_num = ch_num_match.group(1)
                pages = []
                for img in sorted(os.listdir(ch_path), key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0):
                    if img.endswith('.webp'):
                        pages.append(f"assets/chapters/spare-me-great-lord/{ch_dir}/{img}")
                spare_chapters.append({
                    "n": ch_num,
                    "d": "اليوم",
                    "pages": pages
                })
    
    if spare_chapters:
        for item in marker_items:
            if 'spare' in item.get('title', '').lower():
                item['chapters'] = spare_chapters
                print(f"Updated Spare Me Great Lord with {len(spare_chapters)} chapters from disk")

# Now rebuild data.js
items_json = []
for item in marker_items:
    items_json.append(json.dumps(item, ensure_ascii=False, indent=4))

items_str = ",\n".join(items_json)

new_content = f"""/* =========================================================
   Nexus - Shared Data Store (2026)
   ========================================================= */

const SITE_DATA = {{
    manhwa: {{
        topSlider: [],
        trending: [],
        latest: [
{start_marker}
{items_str}
{end_marker}
        ],
        popular: []
    }},
    manga: {{ topSlider: [], trending: [], latest: [], popular: [] }},
    comics: {{ topSlider: [], trending: [], latest: [], popular: [] }},
    novels: {{ topSlider: [], trending: [], latest: [], popular: [] }}
}};

function enrichSiteData() {{
    Object.keys(SITE_DATA).forEach(categoryKey => {{
        const categoryData = SITE_DATA[categoryKey];
        ['topSlider', 'trending', 'latest', 'popular'].forEach(sectionKey => {{
            if(categoryData[sectionKey]) {{
                categoryData[sectionKey].forEach((item, index) => {{
                    if (!item.description) item.description = "بطل القصة يجد نفسه في موقف لا يُحسد عليه...";
                    if (!item.chapters) item.chapters = []; 
                    if (!item.rating) item.rating = "9.5";
                    if (!item.status) item.status = "مستمر";
                    if (item.chapters && item.chapters.length > 0) {{
                        item.ch = item.chapters[0].n; // Set display chapter
                    }}
                }});
            }}
        }});
    }});
}}

function titleToSlug(title) {{ 
    if(!title) return "";
    return title.toLowerCase().trim().replace(/[^a-z0-9\\u0600-\\u06FF]+/g, '-').replace(/^-|-$/g, ''); 
}}

function findSeriesBySlug(slug) {{
    if(!slug) return null;
    for (const catKey of Object.keys(SITE_DATA)) {{
        const catData = SITE_DATA[catKey];
        for (const section of ['trending', 'popular', 'topSlider', 'latest']) {{
            if (catData[section]) {{
                const found = catData[section].find(i => titleToSlug(i.title) === slug);
                if (found) return {{ item: found, category: catKey }};
            }}
        }}
    }}
    return null;
}}

function goToSeries(title, category) {{
    const slug = titleToSlug(title);
    window.location.href = `series.html?name=${{encodeURIComponent(slug)}}&cat=${{category}}`;
}}
"""

with open(data_js_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"\n✅ data.js تم إصلاحه بنجاح! ({len(marker_items)} مانها)")
for item in marker_items:
    ch_count = len(item.get('chapters', []))
    print(f"  - {item['title']}: {ch_count} فصول")



