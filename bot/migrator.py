import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
import uuid

class FirebaseMigrator:
    def __init__(self, cert_path='serviceAccountKey.json'):
        """Initialize Firebase Admin SDK."""
        if not firebase_admin._apps:
            cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET', 'your-project-id.appspot.com')
            })
        
        self.db = firestore.client()
        self.bucket = storage.bucket()

    def upload_manga_meta(self, manga_data):
        """Upload or update manga metadata in Firestore."""
        manga_id = manga_data['title'].lower().replace(' ', '-').replace("'", "")
        doc_ref = self.db.collection('mangas').document(manga_id)
        
        # Prepare data for Firestore
        meta = {
            'title': manga_data['title'],
            'cover': manga_data.get('cover', ''),
            'description': manga_data.get('description', ''),
            'status': manga_data.get('status', 'Ongoing'),
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref.set(meta, merge=True)
        return manga_id

    def upload_chapter(self, manga_id, chapter_num, image_urls):
        """Upload chapter images to Storage and link them in Firestore."""
        chapter_id = f"ch-{chapter_num}"
        # Store as sub-collection
        doc_ref = self.db.collection('mangas').document(manga_id).collection('chapters').document(chapter_id)
        
        doc_ref.set({
            'number': chapter_num,
            'images': image_urls,
            'created_at': firestore.SERVER_TIMESTAMP
        }, merge=True)

    def upload_to_storage(self, image_bytes, destination_path):
        """Upload a single image to Firebase Storage and return public URL."""
        blob = self.bucket.blob(destination_path)
        blob.upload_from_string(image_bytes, content_type='image/webp')
        
        # Make the blob publicly viewable
        blob.make_public()
        return blob.public_url
