// ═══════════════════════════════════════════════════════════
//  BIONEET PRO — Authentication Module
// ═══════════════════════════════════════════════════════════

import { DB, save, db, auth, collection, getDocs, query, where, doc, setDoc, getDoc } from './config.js';
import { toast, go } from './utils.js';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  updateProfile
} from "https://www.gstatic.com/firebasejs/11.0.0/firebase-auth.js";

// ─── Navigation State Update ───────────────────────────────
export function updateNav() {
  const gNav = document.getElementById('gNav');
  const sNav = document.getElementById('sNav');
  const aNav = document.getElementById('aNav');
  const gBtns = document.getElementById('gBtns');
  const uBtns = document.getElementById('uBtns');

  if (DB.isAdmin) {
    if (gNav) gNav.classList.add('hidden');
    if (sNav) sNav.classList.add('hidden');
    if (aNav) aNav.classList.remove('hidden');
    if (gBtns) gBtns.classList.add('hidden');
    if (uBtns) uBtns.classList.remove('hidden');
    const navAv = document.getElementById('navAv');
    const navName = document.getElementById('navName');
    if (navAv) navAv.textContent = 'A';
    if (navName) navName.textContent = 'Admin';
  } else if (DB.currentUser) {
    if (gNav) gNav.classList.add('hidden');
    if (sNav) sNav.classList.remove('hidden');
    if (aNav) aNav.classList.add('hidden');
    if (gBtns) gBtns.classList.add('hidden');
    if (uBtns) uBtns.classList.remove('hidden');
    const navAv = document.getElementById('navAv');
    const navName = document.getElementById('navName');
    if (navAv) navAv.textContent = (DB.currentUser.name || 'S')[0].toUpperCase();
    if (navName) navName.textContent = (DB.currentUser.name || 'Student').split(' ')[0];
  } else {
    if (gNav) gNav.classList.remove('hidden');
    if (sNav) sNav.classList.add('hidden');
    if (aNav) aNav.classList.add('hidden');
    if (gBtns) gBtns.classList.remove('hidden');
    if (uBtns) uBtns.classList.add('hidden');
  }
}

// ─── Register ──────────────────────────────────────────────
export async function doRegister() {
  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const pass = document.getElementById('regPass').value;
  const target = document.getElementById('regTarget')?.value || 'NEET 2026';

  if (!name || !email || !pass) {
    toast('Please fill all fields', 'e');
    return;
  }
  if (pass.length < 6) {
    toast('Password must be 6+ characters', 'e');
    return;
  }

  try {
    const cred = await createUserWithEmailAndPassword(auth, email, pass);
    await updateProfile(cred.user, { displayName: name });

    const userData = {
      id: cred.user.uid,
      name,
      email,
      target,
      role: 'student',
      joined: new Date().toISOString()
    };
    await setDoc(doc(db, "users", cred.user.uid), userData);

    DB.currentUser = userData;
    DB.isAdmin = false;
    localStorage.setItem('currentUser', JSON.stringify(DB.currentUser));
    localStorage.setItem('isAdmin', 'false');

    DB.users = DB.users.filter(u => u.id !== userData.id);
    DB.users.push(userData);
    save('users');

    updateNav();
    toast('Welcome to BioNEET Pro! 🎉', 's');
    go('dashboard');

  } catch (error) {
    console.error("Register error:", error);
    toast(readableAuthError(error), 'e');
  }
}

// ─── Login ─────────────────────────────────────────────────
export async function doLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const pass = document.getElementById('loginPass').value;

  if (!email || !pass) {
    toast('Enter email and password', 'e');
    return;
  }

  try {
    const cred = await signInWithEmailAndPassword(auth, email, pass);
    const found = await loadUserProfile(cred.user);

    DB.currentUser = found;
    DB.isAdmin = found.role === 'admin';
    localStorage.setItem('currentUser', JSON.stringify(DB.currentUser));
    localStorage.setItem('isAdmin', JSON.stringify(DB.isAdmin));

    updateNav();
    toast('Welcome back, ' + (found.name || 'Student') + '! 👋', 's');
    go(DB.isAdmin ? 'admin' : 'dashboard');

  } catch (error) {
    console.error("Login error:", error);
    toast(readableAuthError(error), 'e');
  }
}

// ─── Admin Login ───────────────────────────────────────────
export async function doAdminLogin() {
  const email = document.getElementById('adminEmail')?.value.trim();
  const pass = document.getElementById('adminPass')?.value;

  if (!email || !pass) {
    toast('Enter admin credentials', 'e');
    return;
  }

  try {
    const cred = await signInWithEmailAndPassword(auth, email, pass);
    const found = await loadUserProfile(cred.user);
    if (found.role !== 'admin') {
      await signOut(auth);
      toast('This account does not have admin access.', 'e');
      return;
    }

    DB.currentUser = found;
    DB.isAdmin = true;
    localStorage.setItem('currentUser', JSON.stringify(DB.currentUser));
    localStorage.setItem('isAdmin', 'true');

    updateNav();
    toast('Admin logged in! 🔐', 's');
    go('admin');

  } catch (error) {
    console.error("Admin login error:", error);
    toast(readableAuthError(error), 'e');
  }
}

// ─── Demo Login ────────────────────────────────────────────
export function demoLogin() {
  DB.currentUser = {
    id: 'demo-' + Date.now(),
    name: 'Demo Student',
    email: 'demo@bioneet.com',
    target: 'NEET 2026',
    role: 'student',
    joined: new Date().toISOString()
  };
  DB.isAdmin = false;
  localStorage.setItem('currentUser', JSON.stringify(DB.currentUser));
  localStorage.setItem('isAdmin', 'false');
  updateNav();
  toast('Demo mode active! 🎯', 's');
  go('dashboard');
}

// ─── Logout ────────────────────────────────────────────────
export async function logout() {
  try {
    await signOut(auth);
  } catch (error) {
    console.warn('Firebase sign-out skipped:', error);
  }
  DB.currentUser = null;
  DB.isAdmin = false;
  localStorage.removeItem('currentUser');
  localStorage.setItem('isAdmin', 'false');
  updateNav();
  toast('Logged out successfully', 's');
  go('home');
}

async function loadUserProfile(firebaseUser) {
  const ref = doc(db, "users", firebaseUser.uid);
  const snap = await getDoc(ref);
  if (snap.exists()) {
    const profile = { id: firebaseUser.uid, ...snap.data() };
    DB.users = DB.users.filter(u => u.id !== profile.id);
    DB.users.push(profile);
    save('users');
    return profile;
  }

  const fallback = {
    id: firebaseUser.uid,
    name: firebaseUser.displayName || firebaseUser.email.split('@')[0],
    email: firebaseUser.email,
    target: 'NEET 2026',
    role: 'student',
    joined: new Date().toISOString()
  };
  await setDoc(ref, fallback);
  return fallback;
}

function readableAuthError(error) {
  const code = error?.code || '';
  if (code.includes('email-already-in-use')) return 'Email already registered. Please log in.';
  if (code.includes('invalid-email')) return 'Enter a valid email address.';
  if (code.includes('weak-password')) return 'Password must be at least 6 characters.';
  if (code.includes('invalid-credential') || code.includes('wrong-password')) return 'Invalid email or password.';
  if (code.includes('user-not-found')) return 'No account found. Register first.';
  return 'Authentication failed. Please try again.';
}
