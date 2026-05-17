import os
import re
from PIL import Image
from io import BytesIO

class ImageProcessor:
    @staticmethod
    def to_webp(image_data, quality=80):
        """Convert image bytes to WebP format."""
        try:
            img = Image.open(BytesIO(image_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            
            output = BytesIO()
            img.save(output, format="WebP", quality=quality)
            return output.getvalue()
        except Exception as e:
            print(f"Error processing image: {e}")
            return image_data

    def save_local_image(self, data, path):
        """Save bytes to a local relative path."""
        try:
            # Ensure path directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            print(f"Error saving file {path}: {e}")
            return False

    def slugify(self, text):
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

    def save_local_chapter(self, manga_title, chapter_num, page_num, image_data):
        """Save a specific page of a chapter to a slugified path."""
        slug = self.slugify(manga_title)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(project_root, "assets", "chapters", slug, f"ch-{chapter_num}", f"{page_num}.webp")
        return self.save_local_image(image_data, path)

    def save_local_cover(self, manga_title, image_data):
        """Save the cover image to the assets folder."""
        slug = self.slugify(manga_title)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(project_root, "assets", "covers", f"{slug}.webp")
        self.save_local_image(image_data, path)
        return f"assets/covers/{slug}.webp"

    @staticmethod
    def cleanup_filename(filename):
        """Ensure filenames are safe for storage."""
        return "".join(c for c in filename if c.isalnum() or c in ('.', '_', '-')).strip()
