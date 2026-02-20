import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// ⚠️ PEGA TUS CREDENCIALES AQUÍ
const firebaseConfig = {
  apiKey: "AIzaSyAVo2SPz804FTZCSf0E5bPbJqt8_G7Gyjc",
  authDomain: "web-ia-b366c.firebaseapp.com",
  projectId: "web-ia-b366c",
  storageBucket: "web-ia-b366c.firebasestorage.app",
  messagingSenderId: "405041950906",
  appId: "1:405041950906:web:2b225d61def2a7f0125283"
};

let app;
let auth: any;
let googleProvider: any;

try {
    if (Object.keys(firebaseConfig).length > 0) {
        app = initializeApp(firebaseConfig);
        auth = getAuth(app);
        googleProvider = new GoogleAuthProvider();
    }
} catch (e) {
    console.error("Error Firebase Config:", e);
}

export { auth, googleProvider };