const themeToggle = document.getElementById('theme-toggle');
const html = document.documentElement;

// Verifica se já existe uma preferência salva
const savedTheme = localStorage.getItem('theme') || 'light';
html.setAttribute('data-theme', savedTheme);
updateIcon(savedTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateIcon(newTheme);
});

function updateIcon(theme) {
    document.getElementById('theme-icon').innerText = theme === 'light' ? '🌙' : '☀️';
}