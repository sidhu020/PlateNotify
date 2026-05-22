// static/js/dark-mode.js
// I moved this script here because Flask-Talisman's Content Security Policy (CSP) 
// blocks inline scripts by default. I could have used 'unsafe-inline' in config, but 
// Gemini told me that is bad for security (XSS attacks)! So I made it a separate file.
// It feels so much more professional now.

const toggle = document.getElementById('darkModeToggle');
const saved = localStorage.getItem('darkMode');

if (saved === 'true') {
    document.body.classList.add('dark-mode');
}

if (toggle) {
    toggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDark);
    });
}
