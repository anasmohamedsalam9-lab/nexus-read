# bot/issue_healer.py
import os
import sys
import re
import json
import asyncio
import requests

# Setup path
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.insert(0, bot_dir)

import main as bot_main
from tracker import MangaTracker
from data_manager import load_db, save_db, find_entry

# GitHub API Setup
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")  # format: owner/repo
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER")

def post_comment_and_close(comment_text):
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY or not ISSUE_NUMBER:
        print("[Healer] Local testing: comment not posted to GitHub.")
        print(f"[Healer] Comment text: {comment_text}")
        return
        
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Post comment
    comment_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{ISSUE_NUMBER}/comments"
    r = requests.post(comment_url, json={"body": comment_text}, headers=headers)
    if r.status_code == 201:
        print("[Healer] Successfully posted comment.")
    else:
        print(f"[Healer] Failed to post comment: {r.status_code} - {r.text}")

    # 2. Close issue
    issue_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{ISSUE_NUMBER}"
    r = requests.patch(issue_url, json={"state": "closed", "labels": ["resolved", "auto-fixed"]}, headers=headers)
    if r.status_code == 200:
        print("[Healer] Successfully closed issue.")
    else:
        print(f"[Healer] Failed to close issue: {r.status_code} - {r.text}")

async def heal_issue():
    title = os.environ.get("ISSUE_TITLE", "")
    body = os.environ.get("ISSUE_BODY", "")
    
    print(f"[Healer] Processing issue #{ISSUE_NUMBER}")
    print(f"[Healer] Title: {title}")
    
    # Pattern to match: [BUG] Broken Chapter: Manga Title - Chapter ChapterNum
    # or look in the body for Manga: ... and Chapter: ...
    manga_title = None
    chapter_num = None
    
    # Try parsing title first
    match = re.search(r"Broken\s+Chapter:\s*(.+?)\s*-\s*Chapter\s*([\d\.]+)", title, re.IGNORECASE)
    if match:
        manga_title = match.group(1).strip()
        chapter_num = match.group(2).strip()
    else:
        # Try parsing body
        manga_match = re.search(r"Manga:\s*(.+)", body, re.IGNORECASE)
        chapter_match = re.search(r"Chapter:\s*([\d\.]+)", body, re.IGNORECASE)
        if manga_match:
            manga_title = manga_match.group(1).strip()
        if chapter_match:
            chapter_num = chapter_match.group(1).strip()

    if not manga_title or not chapter_num:
        print("[Healer] Could not parse Manga title or Chapter number from issue.")
        post_comment_and_close("❌ عذراً، لم يتمكن بوت الإصلاح التلقائي من قراءة اسم المانهوا أو رقم الفصل من البلاغ. يرجى التأكد من عدم تعديل عنوان البلاغ التلقائي.")
        return

    print(f"[Healer] Targeting Manga: '{manga_title}', Chapter: {chapter_num}")
    
    # Find manga URL
    tracker = MangaTracker()
    url = tracker.get_url(manga_title)
    
    if not url:
        # Try fuzzy match in database
        db = load_db()
        idx, entry = find_entry(db, manga_title)
        if entry:
            # If we find it in DB, check if we have a tracked url
            url = tracker.get_url(entry.get('title'))
            manga_title = entry.get('title') # sync title casing
            
    if not url:
        print(f"[Healer] Manga '{manga_title}' is not in tracking.")
        post_comment_and_close(f"❌ البوت الذكي لم يعثر على رابط للمانهوا '{manga_title}' في نظام المتابعة. يرجى إضافتها أولاً.")
        return

    # Delete chapter from database to force clean re-scraping
    db = load_db()
    idx, entry = find_entry(db, manga_title)
    if entry:
        chapters = entry.get("chapters", [])
        # Filter out the reported chapter
        clean_chapters = [ch for ch in chapters if str(ch.get("n")) != str(chapter_num)]
        if len(clean_chapters) < len(chapters):
            entry["chapters"] = clean_chapters
            db[idx] = entry
            save_db(db)
            print(f"[Healer] Removed broken chapter {chapter_num} from DB to force re-scrape.")
    
    # Try scraping this chapter
    try:
        print(f"[Healer] Scraping {manga_title} chapter {chapter_num} from {url}...")
        # Convert chapter_num to float or int for start_ch/end_ch
        ch_val = float(chapter_num)
        if ch_val.is_integer():
            ch_val = int(ch_val)
            
        await bot_main.scrape_manga(url, start_ch=ch_val, end_ch=ch_val)
        
        # Verify it was written successfully
        db_after = load_db()
        _, entry_after = find_entry(db_after, manga_title)
        success = False
        if entry_after:
            success = any(str(ch.get("n")) == str(chapter_num) for ch in entry_after.get("chapters", []))
            
        if success:
            post_comment_and_close(f"🎉 **تم الإصلاح بنجاح!**\n\nقام البوت الذكي بإعادة سحب الفصل {chapter_num} من مانهوا '{manga_title}' وتصحيح الصور المعطوبة وتحديث الموقع تلقائياً. يمكنك مراجعته الآن! 🚀")
        else:
            post_comment_and_close(f"⚠️ البوت حاول سحب الفصل {chapter_num} ولكن لم يجد صوراً صالحة أو الفصل غير متوفر في المصدر الأصلي حالياً. يرجى التحقق يدوياً.")
            
    except Exception as e:
        print(f"[Healer] Error during self-healing: {e}")
        post_comment_and_close(f"❌ حدث خطأ غير متوقع أثناء محاولة البوت لإصلاح الفصل:\n```\n{str(e)}\n```\nيرجى مراجعة المشكلة يدوياً.")

if __name__ == "__main__":
    asyncio.run(heal_issue())
