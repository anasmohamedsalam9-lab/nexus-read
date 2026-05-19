// firebase-config.js
// لتشغيل قاعدة البيانات وتفعيل الحسابات، قم بإنشاء مشروع مجاني في Firebase وضع مفاتيحك هنا.
// إذا تركتها فارغة، سيعمل الموقع تلقائياً على نظام (الذاكرة المحلية localStorage) المؤقت.

const firebaseConfig = {
  apiKey: "YOUR_API_KEY_HERE",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

let app, db, auth;
let isFirebaseEnabled = false;

try {
    if (firebaseConfig.apiKey !== "YOUR_API_KEY_HERE") {
        // Initialize Firebase
        app = firebase.initializeApp(firebaseConfig);
        db = firebase.firestore();
        auth = firebase.auth();
        isFirebaseEnabled = true;
        console.log("[Firebase] تم تفعيل النظام السحابي بنجاح ☁️");
    } else {
        console.warn("[Firebase] النظام السحابي غير مفعل. يتم استخدام الذاكرة المحلية (localStorage) مؤقتاً.");
    }
} catch (e) {
    console.error("[Firebase] خطأ في التشغيل: ", e);
}

// Wrapper Functions for Database/Auth
window.NexusDB = {
    async saveHistory(userEmail, historyArray) {
        if (!isFirebaseEnabled) return;
        try {
            await db.collection("users").doc(userEmail).set({ history: historyArray }, { merge: true });
        } catch (e) { console.error("Error saving history:", e); }
    },
    
    async getHistory(userEmail) {
        if (!isFirebaseEnabled) return null;
        try {
            const doc = await db.collection("users").doc(userEmail).get();
            return doc.exists ? doc.data().history : null;
        } catch (e) { return null; }
    },
    
    async loginWithGoogle() {
        if (!isFirebaseEnabled) {
            // Fallback mock login
            const mockUser = {
                name: "قارئ نيكسس",
                email: "reader@nexus.com",
                avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=nexus",
                uid: "mock_123"
            };
            localStorage.setItem('nile_user', JSON.stringify(mockUser));
            return mockUser;
        }
        
        try {
            const provider = new firebase.auth.GoogleAuthProvider();
            const result = await auth.signInWithPopup(provider);
            const user = {
                name: result.user.displayName,
                email: result.user.email,
                avatar: result.user.photoURL,
                uid: result.user.uid
            };
            localStorage.setItem('nile_user', JSON.stringify(user));
            
            // Sync history on login
            const cloudHistory = await this.getHistory(user.email);
            if (cloudHistory && cloudHistory.length > 0) {
                localStorage.setItem('nile_history', JSON.stringify(cloudHistory));
            }
            
            return user;
        } catch (error) {
            console.error("Login failed:", error);
            throw error;
        }
    },
    
    logout() {
        if (isFirebaseEnabled) {
            auth.signOut();
        }
        localStorage.removeItem('nile_user');
    }
};
