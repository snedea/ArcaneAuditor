// theme-manager.js
export class ThemeManager {
    constructor() {
        this.storageKey = 'arcane-auditor-theme';
    }

    initialize() {
        // Check for saved theme preference or default to dark mode
        const savedTheme = localStorage.getItem(this.storageKey) || 'dark';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        const themeButton = document.getElementById('theme-toggle');
        
        if (theme === 'dark') {
            if (themeIcon) themeIcon.textContent = '☀️';
            if (themeText) themeText.textContent = 'Cast Light';
            if (themeButton) themeButton.setAttribute('aria-label', 'Cast Light');
        } else {
            if (themeIcon) themeIcon.textContent = '🌙';
            if (themeText) themeText.textContent = 'Cast Darkness';
            if (themeButton) themeButton.setAttribute('aria-label', 'Cast Darkness');
        }
        
        // Save preference
        localStorage.setItem(this.storageKey, theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
}