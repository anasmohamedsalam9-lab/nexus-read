"""
translator.py - Nexus Image Translator (CPU-Friendly)
============================================================
يترجم صور المانهوا من الإنجليزية إلى العربية بدون الحاجة لـ GPU.

Pipeline:
  1. EasyOCR → كشف النصوص وإحداثياتها في الصورة
  2. Google Translate (مجاني) → ترجمة النص إلى العربية
  3. Pillow → مسح النص الأصلي وكتابة الترجمة العربية

الاستخدام:
  translator = MangaTranslator()
  translated_paths = translator.translate_chapter(image_paths, output_dir)
"""

import os
import sys
import requests
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Lazy imports for heavy modules
_easyocr_reader = None
_translator_instance = None


def _get_ocr_reader():
    """Lazy-load EasyOCR to avoid startup overhead."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            print("[Translator] جاري تحميل نموذج EasyOCR (المرة الأولى فقط)...")
            _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("[Translator] ✅ تم تحميل EasyOCR بنجاح")
        except ImportError:
            print("[Translator] ❌ EasyOCR غير مثبت. شغّل: pip install easyocr")
            return None
        except Exception as e:
            print(f"[Translator] ❌ خطأ في تحميل EasyOCR: {e}")
            return None
    return _easyocr_reader


def _get_translator():
    """Lazy-load Google Translator."""
    global _translator_instance
    if _translator_instance is None:
        try:
            from deep_translator import GoogleTranslator
            _translator_instance = GoogleTranslator(source='en', target='ar')
            print("[Translator] ✅ تم تفعيل Google Translate")
        except ImportError:
            print("[Translator] ❌ deep-translator غير مثبت. شغّل: pip install deep-translator")
            return None
    return _translator_instance


def _reshape_arabic(text):
    """Reshape Arabic text for correct rendering in Pillow."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except ImportError:
        # Fallback: return as-is (may display incorrectly)
        return text


import re

def _contains_english(text):
    """Check if a string contains any English alphabetical characters."""
    if not text:
        return False
    return bool(re.search(r'[a-zA-Z]', text))


def _clean_and_translate_fallback(text):
    """Fallback translation dictionary for common manga/comic exclamations and names."""
    if not text:
        return ""
    
    t_clean = text.strip().upper().replace("!", "").replace("?", "").replace(".", "").replace(",", "")
    
    fallbacks = {
        "FREEDOM": "حرية!",
        "SHANKS": "شانكس",
        "LUFFY": "لوفي",
        "ZORO": "زورو",
        "NAMI": "نامي",
        "USOPP": "يوسوب",
        "SANJI": "سانجي",
        "CHOPPER": "تشوبر",
        "ROBIN": "روبين",
        "FRANKY": "فرانكي",
        "BROOK": "بروك",
        "JINBE": "جينبي",
        "ONE PIECE": "ون بيس",
        "GOL D ROGER": "غول دي روجر",
        "MARINES": "البحرية",
        "PIRATES": "القراصنة",
        "HUH": "هاه؟",
        "WHAT": "ماذا؟",
        "YEAH": "أجل!",
        "YES": "نعم!",
        "NO": "لا!",
        "OH": "أوه!",
        "HEY": "مهلاً!",
        "WAIT": "انتظر!",
        "HELP": "النجدة!",
        "REALLY": "حقاً؟",
        "SERIOUSLY": "بجدية؟",
        "IMPOSSIBLE": "مستحيل!",
        "DAMN": "سحقاً!",
        "SHIT": "تباً!",
        "DIE": "مت!",
        "FIRE": "نار!",
        "WATER": "ماء!",
        "ATTACK": "هجوم!",
        "STOP": "توقف!",
        "GO": "اذهب!",
        "RUN": "اركض!",
        "LOOK": "انظر!"
    }
    
    for k, v in fallbacks.items():
        if k in t_clean:
            return v
            
    # If it is pure English sound effect/word, return clean or empty to erase from the bubble
    if re.match(r'^[A-Za-z\s\!\?\.\,]+$', text):
        return ""
        
    return text


def _find_arabic_font(size=20):
    """Find a suitable Arabic font on the system, or download one."""
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(bot_dir, 'fonts')
    os.makedirs(fonts_dir, exist_ok=True)

    font_path = os.path.join(fonts_dir, 'Cairo-Bold.ttf')

    # Check if we already have it
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except:
            pass

    # Try to download Cairo font from Google Fonts
    try:
        print("[Translator] جاري تحميل خط Cairo العربي...")
        url = "https://github.com/google/fonts/raw/main/ofl/cairo/Cairo%5Bslnt%2Cwght%5D.ttf"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            with open(font_path, 'wb') as f:
                f.write(resp.content)
            print("[Translator] ✅ تم تحميل خط Cairo")
            return ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"[Translator] ⚠️ فشل تحميل الخط: {e}")

    # Try system Arabic fonts (Windows)
    system_fonts = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for sf in system_fonts:
        if os.path.exists(sf):
            try:
                return ImageFont.truetype(sf, size)
            except:
                continue

    # Ultimate fallback: default font
    print("[Translator] ⚠️ لم يُعثر على خط عربي، سيتم استخدام الخط الافتراضي")
    return ImageFont.load_default()


def _estimate_bg_color(img_array, bbox):
    """Estimate the background color around a text region."""
    x_min = max(0, int(min(p[0] for p in bbox)) - 5)
    y_min = max(0, int(min(p[1] for p in bbox)) - 5)
    x_max = min(img_array.shape[1], int(max(p[0] for p in bbox)) + 5)
    y_max = min(img_array.shape[0], int(max(p[1] for p in bbox)) + 5)

    if x_max <= x_min or y_max <= y_min:
        return (255, 255, 255)

    # Sample border pixels
    region = img_array[y_min:y_max, x_min:x_max]
    if region.size == 0:
        return (255, 255, 255)

    # Get edge pixels (likely background)
    edge_pixels = []
    h, w = region.shape[:2]
    if h > 2 and w > 2:
        edge_pixels.extend(region[0, :].tolist())     # top row
        edge_pixels.extend(region[-1, :].tolist())    # bottom row
        edge_pixels.extend(region[:, 0].tolist())     # left col
        edge_pixels.extend(region[:, -1].tolist())    # right col
    else:
        edge_pixels = region.reshape(-1, region.shape[-1] if len(region.shape) > 2 else 1).tolist()

    if not edge_pixels:
        return (255, 255, 255)

    # Average background color
    avg = np.mean(edge_pixels, axis=0)
    if len(avg.shape) == 0 or len(avg) < 3:
        return (255, 255, 255)

    return (int(avg[0]), int(avg[1]), int(avg[2]))


def _fit_text_in_box(draw, text, font_func, box_width, box_height, min_size=10, max_size=28):
    """Find the best font size and wrap text to fit in a bounding box (unreshaped raw text)."""
    best_size = min_size
    best_lines = [text]

    # Bubble-safe horizontal padding to fit beautifully in curved speech bubbles
    usable_width = max(15, box_width - 12)

    for size in range(max_size, min_size - 1, -1):
        font = font_func(size)
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            # Measure using reshaped line so width estimates are extremely accurate
            reshaped_test = _reshape_arabic(test_line)
            bbox = draw.textbbox((0, 0), reshaped_test, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= usable_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Check total height
        total_height = len(lines) * (size + 6)
        if total_height <= box_height - 2:
            best_size = size
            best_lines = lines
            break

    return best_size, best_lines


class MangaTranslator:
    """
    Lightweight manga image translator for CPU.
    Translates English text in manga/manhwa images to Arabic.
    """

    def __init__(self, target_lang='ar'):
        self.target_lang = target_lang
        self._font_cache = {}

    def is_available(self):
        """Check if all translation dependencies are available."""
        try:
            import easyocr
            from deep_translator import GoogleTranslator
            return True
        except ImportError:
            return False

    def get_font(self, size):
        """Get font with caching."""
        if size not in self._font_cache:
            self._font_cache[size] = _find_arabic_font(size)
        return self._font_cache[size]

    def translate_image(self, image_path_or_url, output_path, log_func=None):
        """
        Translate a single manga page image.

        Args:
            image_path_or_url: Local path or URL of the image
            output_path: Where to save the translated image
            log_func: Optional logging function

        Returns:
            bool: True if translated successfully
        """
        log = log_func or print

        reader = _get_ocr_reader()
        translator = _get_translator()

        if not reader or not translator:
            log("[Translator] ❌ OCR أو المترجم غير متاح")
            return False

        try:
            # Load image
            if image_path_or_url.startswith(('http://', 'https://')):
                resp = requests.get(image_path_or_url, timeout=20, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': image_path_or_url
                })
                if resp.status_code != 200:
                    log(f"[Translator] ❌ فشل تحميل الصورة: HTTP {resp.status_code}")
                    return False
                img = Image.open(BytesIO(resp.content)).convert('RGB')
            else:
                img = Image.open(image_path_or_url).convert('RGB')

            img_array = np.array(img)

            # OCR: Detect text regions
            results = reader.readtext(img_array)

            if not results:
                # No text found, save as-is
                img.save(output_path, 'WEBP', quality=85)
                return True

            # Filter: only translate regions with sufficient confidence
            text_regions = []
            for (bbox, text, conf) in results:
                if conf > 0.3 and len(text.strip()) > 1:
                    text_regions.append((bbox, text, conf))

            if not text_regions:
                img.save(output_path, 'WEBP', quality=85)
                return True

            # Batch translate all texts
            original_texts = [r[1] for r in text_regions]
            try:
                # Translate in batch for efficiency
                translated_texts = []
                batch = []
                for t in original_texts:
                    batch.append(t)
                    if len(batch) >= 10:
                        translated_batch = translator.translate_batch(batch)
                        translated_texts.extend(translated_batch)
                        batch = []
                        time.sleep(0.5)  # Rate limit

                if batch:
                    translated_batch = translator.translate_batch(batch)
                    translated_texts.extend(translated_batch)

            except Exception as e:
                log(f"[Translator] ⚠️ خطأ في الترجمة: {e}")
                # Try one by one
                translated_texts = []
                for t in original_texts:
                    try:
                        tr = translator.translate(t)
                        translated_texts.append(tr or t)
                        time.sleep(0.3)
                    except:
                        translated_texts.append(t)

            # Draw translated text on image
            draw = ImageDraw.Draw(img)

            for i, (bbox, original_text, conf) in enumerate(text_regions):
                if i >= len(translated_texts):
                    break

                translated = translated_texts[i]
                
                # Check if it was not translated, or if it still contains English
                if not translated or translated == original_text or _contains_english(translated):
                    # Try a fallback clean/translate
                    translated = _clean_and_translate_fallback(original_text)

                # Calculate bounding box
                pts = np.array(bbox)
                x_min, y_min = int(pts[:, 0].min()), int(pts[:, 1].min())
                x_max, y_max = int(pts[:, 0].max()), int(pts[:, 1].max())

                box_w = x_max - x_min
                box_h = y_max - y_min

                if box_w < 10 or box_h < 8:
                    continue

                # Estimate background color
                bg_color = _estimate_bg_color(img_array, bbox)

                # Choose text color (dark on light bg, light on dark bg)
                brightness = (bg_color[0] * 299 + bg_color[1] * 587 + bg_color[2] * 114) / 1000
                
                # Clamping Background: if it's very light, it's a white speech bubble! Make it pure white!
                if brightness > 190:
                    bg_color = (255, 255, 255)
                    brightness = 255
                # If it's very dark, make it pure black!
                elif brightness < 65:
                    bg_color = (0, 0, 0)
                    brightness = 0

                text_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)

                # DO NOT draw a solid background rectangle to avoid ugly blocks on the art!
                # The user explicitly requested to NOT draw fake bubbles.
                # Instead, we will use a very thick text stroke (outline) to mask the original English text.

                # If after fallback we still have English or empty text, do NOT draw any text
                if not translated or _contains_english(translated):
                    continue

                # Fit text in box (passing RAW translated text now!)
                font_size, lines = _fit_text_in_box(
                    draw, translated, self.get_font,
                    box_w, box_h,
                    min_size=max(8, box_h // 4),
                    max_size=min(26, box_h - 2)
                )

                font = self.get_font(font_size)

                # Draw each line centered
                total_text_height = len(lines) * (font_size + 4)
                y_start = y_min + (box_h - total_text_height) // 2

                for line_idx, line in enumerate(lines):
                    # Reshape each line individually right before drawing to preserve bidirectional connectivity!
                    display_line = _reshape_arabic(line)
                    
                    line_bbox = draw.textbbox((0, 0), display_line, font=font)
                    line_w = line_bbox[2] - line_bbox[0]
                    x_pos = x_min + (box_w - line_w) // 2
                    y_pos = y_start + line_idx * (font_size + 4)

                    # Draw text with native thick stroke (outline) to mask original English text seamlessly
                    outline_color = (255, 255, 255) if text_color == (0, 0, 0) else (0, 0, 0)
                    draw.text((x_pos, y_pos), display_line, fill=text_color, font=font, stroke_width=3, stroke_fill=outline_color)

            # Save translated image
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path, 'WEBP', quality=85)
            return True

        except Exception as e:
            log(f"[Translator] ❌ خطأ في ترجمة الصورة: {e}")
            return False

    def translate_chapter(self, image_urls, output_dir, chapter_num="0", log_func=None):
        """
        Translate an entire chapter of manga images.

        Args:
            image_urls: List of image URLs or paths
            output_dir: Directory to save translated images
            chapter_num: Chapter number for logging
            log_func: Optional log function

        Returns:
            list: List of saved file paths (relative to project root)
        """
        log = log_func or print
        os.makedirs(output_dir, exist_ok=True)

        saved_paths = []
        total = len(image_urls)

        for idx, url in enumerate(image_urls):
            page_num = idx + 1
            output_filename = f"{page_num}.webp"
            output_path = os.path.join(output_dir, output_filename)

            log(f"    🔄 ترجمة الصفحة {page_num}/{total}...")

            success = self.translate_image(url, output_path, log_func=log)

            if success and os.path.exists(output_path):
                saved_paths.append(output_path)
                log(f"    ✅ تمت ترجمة الصفحة {page_num}")
            else:
                # Fallback: save original image without translation
                log(f"    ⚠️ فشلت الترجمة، سيتم حفظ الصورة الأصلية")
                try:
                    if url.startswith(('http://', 'https://')):
                        resp = requests.get(url, timeout=20, headers={
                            'User-Agent': 'Mozilla/5.0'
                        })
                        if resp.status_code == 200:
                            with open(output_path, 'wb') as f:
                                f.write(resp.content)
                            saved_paths.append(output_path)
                    elif os.path.exists(url):
                        from shutil import copy2
                        copy2(url, output_path)
                        saved_paths.append(output_path)
                except Exception as e:
                    log(f"    ❌ فشل حفظ الصورة الأصلية: {e}")

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        return saved_paths

    def download_and_save_original(self, image_urls, output_dir, log_func=None):
        """
        Download chapter images without translation (for when translation is disabled).

        Args:
            image_urls: List of image URLs
            output_dir: Directory to save images

        Returns:
            list: List of saved file paths
        """
        log = log_func or print
        os.makedirs(output_dir, exist_ok=True)

        saved_paths = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        for idx, url in enumerate(image_urls):
            page_num = idx + 1
            output_filename = f"{page_num}.webp"
            output_path = os.path.join(output_dir, output_filename)

            try:
                if url.startswith(('http://', 'https://')):
                    resp = requests.get(url, timeout=20, headers=headers)
                    if resp.status_code == 200:
                        # Convert to webp
                        try:
                            img = Image.open(BytesIO(resp.content)).convert('RGB')
                            img.save(output_path, 'WEBP', quality=85)
                        except:
                            with open(output_path, 'wb') as f:
                                f.write(resp.content)
                        saved_paths.append(output_path)
                elif os.path.exists(url):
                    from shutil import copy2
                    copy2(url, output_path)
                    saved_paths.append(output_path)
            except Exception as e:
                log(f"    ❌ فشل تحميل الصفحة {page_num}: {e}")

            time.sleep(0.3)

        return saved_paths


# Quick test
if __name__ == '__main__':
    t = MangaTranslator()
    print(f"المترجم متاح: {t.is_available()}")



