import os
import sys
import threading
import requests
import re
import json
from PIL import Image, ImageTk
from io import BytesIO
import customtkinter as ctk

# Ensure we can import from the bot directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the existing scraper
try:
    from bot.scraper import MangaScraper
except ImportError:
    # Fallback or error if not in correct dir
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.withdraw()
    from tkinter import messagebox
    messagebox.showerror("Error", "Please place this script in the root of nile-manhwa directory.")
    sys.exit()

# Re-use or adapt data injector logic
def inject_to_data_js(manga_obj):
    data_path = os.path.join(current_dir, 'data.js')
    if not os.path.exists(data_path):
        return False, "data.js file not found!"
    
    with open(data_path, 'r', encoding='utf-8') as f:
        content = f.read()

    title = manga_obj['title']
    # Check if exists
    pattern_exists = r'\{\s*["\']title["\']:\s*["\']' + re.escape(title) + r'["\']'
    if re.search(pattern_exists, content, re.IGNORECASE):
        return False, f"'{title}' already exists in data.js!"

    # Prepare JSON
    manga_json = json.dumps(manga_obj, ensure_ascii=False, indent=4)
    manga_json = '\n'.join('    ' + line for line in manga_json.split('\n'))

    # Find insertion point (latest array)
    insert_marker = r'latest:\s*\['
    match = re.search(insert_marker, content)
    if not match:
        return False, "Could not find 'latest: [' array in data.js"
    
    pos = match.end()
    rest = content[pos:].lstrip()
    comma = ",\n" if rest.startswith("{") else "\n"
    insertion = "\n" + manga_json.strip() + comma
    
    new_content = content[:pos] + insertion + content[pos:]
    
    with open(data_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True, "Successfully added to data.js"

class NileManhwaBot(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window settings
        self.title("Nexus - Content Assistant")
        self.geometry("1000x700")
        
        # Theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue") # We will use custom colors
        
        self.accent_color = "#E4B1F0" # A nice purple/pink accent like Nexus
        self.bg_color = "#1A1A1D"
        self.card_color = "#2D2E32"

        self.scraper = MangaScraper()
        self.results = []
        self.selected_manga = None

        self.configure(fg_color=self.bg_color)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Sidebar (Logo & Stats)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#121214")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="NILE", font=ctk.CTkFont(size=28, weight="bold"), text_color="white")
        self.logo_label.pack(pady=(30, 0))
        self.logo_sub = ctk.CTkLabel(self.sidebar, text="MANHWA", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.accent_color)
        self.logo_sub.pack(pady=(0, 30))

        self.info_label = ctk.CTkLabel(self.sidebar, text="Desktop Bot v1.0\nStatus: Ready", font=ctk.CTkFont(size=12), text_color="gray")
        self.info_label.pack(side="bottom", pady=20)

        # Main Content Area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Search Bar
        self.search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Enter Manhwa Name...", height=45, font=("Arial", 16))
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.start_search())

        self.search_btn = ctk.CTkButton(self.search_frame, text="Search", command=self.start_search, height=45, fg_color=self.accent_color, hover_color="#C68FE6", text_color="black", font=("Arial", 14, "bold"))
        self.search_btn.grid(row=0, column=1)

        # Results & Preview Split
        self.interaction_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.interaction_frame.grid(row=1, column=0, sticky="nsew")
        self.interaction_frame.grid_columnconfigure(0, weight=2)
        self.interaction_frame.grid_columnconfigure(1, weight=1)
        self.interaction_frame.grid_rowconfigure(0, weight=1)

        # Results List
        self.results_scroll = ctk.CTkScrollableFrame(self.interaction_frame, label_text="Search Results", fg_color=self.card_color)
        self.results_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Preview Sidebar
        self.preview_frame = ctk.CTkFrame(self.interaction_frame, fg_color=self.card_color)
        self.preview_frame.grid(row=0, column=1, sticky="nsew")
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Preview", font=("Arial", 18, "bold"))
        self.preview_label.pack(pady=10)

        self.cover_canvas = ctk.CTkLabel(self.preview_frame, text="No Image", width=200, height=300, fg_color="#121214", corner_radius=10)
        self.cover_canvas.pack(pady=10, padx=20)

        self.preview_title = ctk.CTkLabel(self.preview_frame, text="Select a manga", font=("Arial", 16, "bold"), wraplength=250)
        self.preview_title.pack(pady=(10, 5), padx=10)

        self.preview_desc = ctk.CTkTextbox(self.preview_frame, height=200, fg_color="transparent", activate_scrollbars=True)
        self.preview_desc.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_desc.insert("0.0", "Description will appear here...")
        self.preview_desc.configure(state="disabled")

        self.inject_btn = ctk.CTkButton(self.preview_frame, text="Add to Nexus", state="disabled", fg_color="#27AE60", hover_color="#2ECC71", command=self.inject_manga, height=40, font=("Arial", 14, "bold"))
        self.inject_btn.pack(pady=20, padx=20, fill="x")

        # Status
        self.status_bar = ctk.CTkLabel(self, text="Ready", anchor="w", padx=10, fg_color="#121214")
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def update_status(self, text, color="white"):
        self.status_bar.configure(text=text, text_color=color)

    def start_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return
        
        self.search_btn.configure(state="disabled", text="Searching...")
        self.update_status(f"Searching for '{query}'...")
        
        # Clear results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        threading.Thread(target=self.run_search, args=(query,), daemon=True).start()

    def run_search(self, query):
        try:
            results = self.scraper.search_manga(query)
            self.after(0, lambda: self.display_results(results))
        except Exception as e:
            self.after(0, lambda: self.update_status(f"Error: {str(e)}", "red"))
            self.after(0, lambda: self.search_btn.configure(state="normal", text="Search"))

    def display_results(self, results):
        self.results = results
        self.search_btn.configure(state="normal", text="Search")
        
        if not results:
            self.update_status("No results found.", "yellow")
            return

        self.update_status(f"Found {len(results)} results.")

        for i, res in enumerate(results):
            btn = ctk.CTkButton(self.results_scroll, 
                               text=f"{res['title']} ({res['source']})",
                               anchor="w",
                               fg_color="transparent",
                               text_color="white",
                               hover_color="#3F3F45",
                               command=lambda r=res: self.select_manga(r))
            btn.pack(fill="x", pady=2)

    def select_manga(self, res):
        self.selected_manga = res
        self.update_status(f"Loading details for '{res['title']}'...")
        self.preview_title.configure(text=res['title'])
        self.inject_btn.configure(state="disabled")
        
        threading.Thread(target=self.fetch_details, args=(res['url'],), daemon=True).start()

    def fetch_details(self, url):
        try:
            details = self.scraper.get_manga_details(url)
            self.after(0, lambda: self.show_details(details))
        except Exception as e:
            self.after(0, lambda: self.update_status(f"Error fetching details: {str(e)}", "red"))

    def show_details(self, details):
        self.selected_manga.update(details)
        
        # Update text
        self.preview_desc.configure(state="normal")
        self.preview_desc.delete("0.0", "end")
        self.preview_desc.insert("0.0", details.get('description', 'No description available.'))
        self.preview_desc.configure(state="disabled")
        
        self.inject_btn.configure(state="normal")
        self.update_status("Ready to add.")

        # Update Image
        if details.get('cover'):
            threading.Thread(target=self.load_preview_image, args=(details['cover'],), daemon=True).start()

    def load_preview_image(self, url):
        try:
            response = requests.get(url, timeout=10)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img.thumbnail((200, 300))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 300))
            self.after(0, lambda: self.cover_canvas.configure(image=ctk_img, text=""))
        except:
            self.after(0, lambda: self.cover_canvas.configure(image=None, text="Failed to load image"))

    def inject_manga(self):
        if not self.selected_manga:
            return

        m = self.selected_manga
        self.inject_btn.configure(state="disabled", text="Adding...")
        self.update_status("Downloading cover and updating data.js...")

        def run_injection():
            try:
                # 1. Download cover
                slug = re.sub(r'[^a-z0-9]+', '-', m['title'].lower()).strip('-')
                cover_dir = os.path.join(current_dir, 'assets', 'covers')
                os.makedirs(cover_dir, exist_ok=True)
                
                ext = '.webp'
                cover_filename = f"{slug}{ext}"
                cover_path = os.path.join(cover_dir, cover_filename)
                
                resp = requests.get(m['cover'], timeout=20)
                if resp.status_code == 200:
                    with open(cover_path, 'wb') as f:
                        f.write(resp.content)
                
                local_img_path = f"assets/covers/{cover_filename}"
                
                # 2. Build object
                manga_obj = {
                    "title": m['title'],
                    "img": local_img_path,
                    "rating": m.get('rating', '9.0'),
                    "genres": m.get('genres', ["Action", "Fantasy"]),
                    "status": "مستمر",
                    "description": m.get('description', ''),
                    "chapters": [] # User specifically asked for Name, Desc, and Cover ONLY
                }
                
                success, msg = inject_to_data_js(manga_obj)
                
                if success:
                    self.after(0, lambda: self.update_status(f"Success! {m['title']} added.", "green"))
                else:
                    self.after(0, lambda: self.update_status(f"Failed: {msg}", "red"))
                
                self.after(0, lambda: self.inject_btn.configure(state="normal", text="Add to Nexus"))
                
            except Exception as e:
                self.after(0, lambda: self.update_status(f"Fatal Error: {str(e)}", "red"))
                self.after(0, lambda: self.inject_btn.configure(state="normal", text="Add to Nexus"))

        threading.Thread(target=run_injection, daemon=True).start()

if __name__ == "__main__":
    app = NileManhwaBot()
    app.mainloop()



