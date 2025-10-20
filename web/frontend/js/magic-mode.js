// ⚡️ ARCANE MODE: THE GRAND RITUAL EDITION ⚡️
// Magical functionality for the living spellbook

// 🌠 Particle Wisps of Energy
function summonParticles(count = 20) {
    for (let i = 0; i < count; i++) {
        const spark = document.createElement('div');
        spark.className = 'arcane-spark';
        document.body.appendChild(spark);
        animateSpark(spark);
    }
}

function animateSpark(el) {
    const x = Math.random() * window.innerWidth;
    const y = Math.random() * window.innerHeight;
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
    el.style.animationDuration = `${5 + Math.random() * 5}s`;
    el.addEventListener('animationend', () => el.remove());
}

// 🌈 Arcane Cursor Trail
let cursorTrailEnabled = false;

function enableCursorTrail() {
    if (cursorTrailEnabled) return;
    cursorTrailEnabled = true;
    
    document.addEventListener('mousemove', createWisp);
}

function disableCursorTrail() {
    cursorTrailEnabled = false;
    document.removeEventListener('mousemove', createWisp);
}

function createWisp(e) {
    const wisp = document.createElement('div');
    wisp.className = 'wisp';
    wisp.style.left = `${e.pageX}px`;
    wisp.style.top = `${e.pageY}px`;
    document.body.appendChild(wisp);
    setTimeout(() => wisp.remove(), 1000);
}

// 🌌 Dynamic Constellation Effects
function createConstellationLines() {
    if (!document.body.classList.contains('magic-mode')) return;
    
    const canvas = document.createElement('canvas');
    canvas.id = 'constellation-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '1';
    canvas.style.opacity = '0.3';
    
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const stars = [];
    
    // Create star positions
    for (let i = 0; i < 50; i++) {
        stars.push({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            brightness: Math.random()
        });
    }
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    function animateConstellation() {
        if (!document.body.classList.contains('magic-mode')) {
            canvas.remove();
            return;
        }
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Update and draw stars
        stars.forEach(star => {
            star.x += star.vx;
            star.y += star.vy;
            star.brightness += (Math.random() - 0.5) * 0.02;
            star.brightness = Math.max(0.3, Math.min(1, star.brightness));
            
            // Wrap around screen
            if (star.x < 0) star.x = canvas.width;
            if (star.x > canvas.width) star.x = 0;
            if (star.y < 0) star.y = canvas.height;
            if (star.y > canvas.height) star.y = 0;
            
            // Draw star
            ctx.beginPath();
            ctx.arc(star.x, star.y, star.brightness * 2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(234, 163, 66, ${star.brightness})`;
            ctx.fill();
        });
        
        // Draw constellation lines between nearby stars
        stars.forEach((star, i) => {
            stars.slice(i + 1).forEach(otherStar => {
                const dx = star.x - otherStar.x;
                const dy = star.y - otherStar.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 150) {
                    const opacity = (1 - distance / 150) * 0.3;
                    ctx.beginPath();
                    ctx.moveTo(star.x, star.y);
                    ctx.lineTo(otherStar.x, otherStar.y);
                    ctx.strokeStyle = `rgba(234, 163, 66, ${opacity})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            });
        });
        
        requestAnimationFrame(animateConstellation);
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    animateConstellation();
}

function removeConstellationLines() {
    const canvas = document.getElementById('constellation-canvas');
    if (canvas) {
        canvas.remove();
    }
}

// 🪄 Magic Mode Toggle
function toggleMagicMode() {
    const body = document.body;
    
    if (body.classList.contains('magic-mode')) {
        // Dispel Magic
        body.classList.remove('magic-mode');
        
        // Clean up magical effects
        document.querySelectorAll('.arcane-spark, .wisp').forEach(el => el.remove());
        disableCursorTrail();
        removeConstellationLines();
        
        console.log("%c🪄 The Weave settles... Arcane Mode dispelled.", "color:#756AA2; font-weight:bold");
    } else {
        // Invoke Magic
        body.classList.add('magic-mode');
        
        // Activate magical effects
        summonParticles();
        enableCursorTrail();
        createConstellationLines();
        
        console.log("%c✨ The Weave stirs... Arcane Mode enabled.", "color:#EAA342; font-weight:bold");
        
        // Show magical achievement toast
        showArcaneToast("✨ The Grand Ritual begins... The Weave awakens!");
    }
}

// 🔔 Arcane Achievement Toasts
function showArcaneToast(message) {
    const toast = document.createElement('div');
    toast.className = 'arcane-toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 🪄 Keyboard Incantation (Konami-style combo)
const spell = ['Alt', 'Shift', 'M']; // "Alt + Shift + M" for Magic
let buffer = [];

document.addEventListener('keydown', e => {
    buffer.push(e.key);
    if (buffer.length > spell.length) {
        buffer.shift();
    }
    
    if (buffer.slice(-spell.length).join('') === spell.join('')) {
        toggleMagicMode();
        buffer = [];
    }
});

// Enhanced analysis completion with magical flair
export function showMagicalAnalysisComplete(result) {
    if (document.body.classList.contains('magic-mode')) {
        const totalFindings = result.findings.length;
        const actionCount = result.summary?.by_severity?.action || 0;
        const adviceCount = result.summary?.by_severity?.advice || 0;
        
        let message = `✨ Divination Complete — The Weave reveals ${totalFindings} portents`;
        if (actionCount > 0) {
            message += ` (${actionCount} urgent omens)`;
        }
        if (adviceCount > 0) {
            message += ` (${adviceCount} wise counsel)`;
        }
        
        showArcaneToast(message);
        
        // Summon extra particles for celebration
        setTimeout(() => summonParticles(10), 500);
    }
}

// Initialize Magic Mode functionality
document.addEventListener('DOMContentLoaded', function() {
    // Magic Mode initialization - no initial greeting for normal users
});
