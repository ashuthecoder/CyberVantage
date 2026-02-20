# CyberVantage Design System Prompt for GitHub Copilot

Use this prompt when creating new pages to match the existing design system.

---

## 🎨 DESIGN SYSTEM OVERVIEW

Create a modern, glassmorphic cybersecurity-themed page with the following design system:

### COLOR PALETTE
```css
--bg-color: #0a0a1a;              /* Deep dark blue background */
--text-color: #ffffff;             /* White text */
--accent-primary: #00f2ff;         /* Cyan - main brand */
--accent-secondary: #7000ff;       /* Purple - depth */
--accent-tertiary: #ff006e;        /* Pink - energy */
--accent-glow: #00ffaa;            /* Mint - highlights */
--glass-bg: rgba(255, 255, 255, 0.03);
--glass-border: rgba(255, 255, 255, 0.1);
```

### TYPOGRAPHY
- **Display Font**: 'Syne' (800 weight for headings)
- **Body Font**: 'DM Sans' (400, 500, 700 weights)
- **Monospace**: 'Space Mono' (for code/tech elements)
- **Hero Title**: 7rem (112px), letter-spacing: -3px
- **Section Titles**: 4.5rem (72px), letter-spacing: -2px
- **Body Text**: 1rem (16px), line-height: 1.7

### SPACING SYSTEM
- Section padding: 4-6rem vertical, 10% horizontal
- Card padding: 2.5-3rem
- Gap between elements: 1.5-2.5rem
- Margin between sections: 4rem

---

## 🎭 VISUAL ELEMENTS

### 1. ANIMATED GRADIENT MESH BACKGROUND
Always include 4 floating gradient blobs:
```html
<div class="gradient-mesh">
    <div class="mesh-gradient mesh-1"></div>
    <div class="mesh-gradient mesh-2"></div>
    <div class="mesh-gradient mesh-3"></div>
    <div class="mesh-gradient mesh-4"></div>
</div>
```

CSS: 600-800px wide blurs, `filter: blur(120px)`, opacity 0.6, 20s float animation

### 2. NOISE OVERLAY
```html
<div class="noise-overlay"></div>
```
Fixed position, SVG noise texture, opacity 0.5, mix-blend-mode: overlay

### 3. CUSTOM CURSOR
```html
<div class="custom-cursor"></div>
<div class="cursor-dot"></div>
```
Z-index: 999999, `cursor: none !important` on body, expands on hover

### 4. GLASSMORPHISM CARDS
- Background: `rgba(255, 255, 255, 0.03)`
- Border: `1px solid rgba(255, 255, 255, 0.1)`
- Backdrop-filter: `blur(20-30px)`
- Border-radius: 20-30px
- Box-shadow: Multi-layer with color tints
- Hover: Lift up (`translateY(-10px)`), scale(1.02-1.03), enhanced glow

---

## ⚡ ANIMATION SYSTEM

### SCROLL ANIMATIONS (Apple-style)
- Easing: `cubic-bezier(0.25, 0.46, 0.45, 0.94)` (smooth, elegant)
- Duration: 1.2s (slower, more refined)
- Initial state: `opacity: 0`, `translateY(80px)`
- Use Intersection Observer with `threshold: 0.15`
- Stagger cards with 200ms delay between each

### HOVER EFFECTS
- 3D Parallax: `perspective(1000px)` with `rotateX/Y` based on mouse position
- Transition: 0.6s with cubic-bezier easing
- Scale: 1.02-1.05 on hover
- Glow: Increase box-shadow with accent colors
- Border: Shift from transparent to accent-primary

### MAGNETIC BUTTONS
- Track mouse position within 80px range
- Move button proportionally toward cursor: `translate(x, y)`
- Smooth spring-back on mouse leave
- Combined with scale and glow effects

---

## 📐 LAYOUT PATTERNS

### NAVIGATION BAR
```html
<nav class="glass-nav">
    <div class="logo">CyberVantage</div>
    <div class="nav-links">
        <a href="#section">Link</a>
        <a href="#" class="btn-primary">CTA Button</a>
    </div>
</nav>
```
- Fixed position, backdrop-blur
- Changes on scroll (add `.scrolled` class at 100px)
- Gradient text logo

### SECTION STRUCTURE
```html
<section class="section-name">
    <h2 class="section-title">Title with Gradient</h2>
    <div class="content-grid">
        <!-- Cards or content -->
    </div>
</section>
```

### CARD GRID LAYOUTS

**Standard Grid:**
```css
display: grid;
grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
gap: 2.5rem;
```

**Bento Grid (Asymmetric):**
```css
grid-template-columns: repeat(4, 1fr);
/* Then span cards differently: */
.card:nth-child(1) { grid-column: span 2; }
.card:nth-child(3) { grid-column: span 2; grid-row: span 2; }
```

---

## 🎯 INTERACTIVE ELEMENTS

### BUTTONS

**Glass Button:**
```html
<button class="btn-glass">Action</button>
```
- Glass effect, magnetic interaction
- Ripple effect from center on hover
- Transform: translate + scale

**Outline Button:**
```html
<button class="btn-outline">Action</button>
```
- Transparent with border
- Fill with gradient on hover

**Primary Button:**
```html
<button class="btn-primary">Action</button>
```
- Gradient background
- Shimmer effect on hover

### CARDS

**Phase Card (with number):**
```html
<div class="phase-card">
    <div class="phase-number">01</div>
    <span class="phase-icon">🛡️</span>
    <h3>Card Title</h3>
    <p>Description text...</p>
</div>
```

**Glass Panel:**
```html
<div class="glass-panel">
    <h3>Feature Title</h3>
    <p>Feature description...</p>
</div>
```

---

## 📱 RESPONSIVE DESIGN

### Breakpoints:
- Desktop: > 1200px (full experience)
- Tablet: 900-1200px (2-column layouts)
- Mobile: < 900px (single column, stack everything)
- Small Mobile: < 480px (larger touch targets)

### Mobile Adjustments:
- Hide custom cursor on touch devices
- Reduce hero title from 7rem → 4rem → 3rem
- Stack hero layout (column direction)
- Single column grids
- Larger button padding (touch-friendly)
- Reduce animation complexity

---

## 🎨 STYLING CONVENTIONS

### Section Title Pattern:
```css
.section-title {
    font-size: 4.5rem;
    font-weight: 800;
    letter-spacing: -2px;
    background: linear-gradient(135deg, var(--accent-primary) 0%, 
                var(--accent-glow) 50%, var(--accent-tertiary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
```

### Card Hover Pattern:
```css
.card {
    transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.card:hover {
    transform: perspective(1000px) rotateX(Xdeg) rotateY(Ydeg) 
                translateY(-15px) scale(1.02);
    border-color: var(--accent-primary);
    box-shadow: 0 20px 60px rgba(0, 242, 255, 0.3);
}
```

### Gradient Overlay Pattern:
```css
.element::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, 
        rgba(0, 242, 255, 0.05) 0%, 
        rgba(112, 0, 255, 0.05) 100%);
    opacity: 0;
    transition: opacity 0.5s ease;
}

.element:hover::before {
    opacity: 1;
}
```

---

## 🔧 JAVASCRIPT PATTERNS

### Scroll Observer:
```javascript
const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);
```

### 3D Tilt Effect:
```javascript
element.addEventListener('mousemove', (e) => {
    const rect = element.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = (y - centerY) / 20;
    const rotateY = (centerX - x) / 20;
    
    element.style.transform = 
        `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
});
```

### Magnetic Button:
```javascript
button.addEventListener('mousemove', (e) => {
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    const distance = Math.sqrt(x * x + y * y);
    
    if (distance < 80) {
        const moveX = (x / 80) * 15;
        const moveY = (y / 80) * 15;
        button.style.transform = `translate(${moveX}px, ${moveY}px)`;
    }
});
```

---

## 🎪 CYBERSECURITY THEMED VISUALS

When creating security-related illustrations, use:

### Icons/Symbols:
- 🛡️ Shield shapes (hexagonal preferred)
- 🔒 Lock icons (with shackles)
- 🌐 Network nodes and connections
- ⚡ Data packets/particles
- 📡 Scanning effects
- 🔐 Encrypted data representations

### Animation Effects:
- Pulsing glows (4s cycle)
- Floating network nodes
- Connection lines between points
- Scan lines (vertical/horizontal)
- Orbiting particles
- Data stream effects

### Color Meanings:
- Cyan (#00f2ff): Active/secure
- Purple (#7000ff): Premium/advanced
- Pink (#ff006e): Alert/important
- Mint (#00ffaa): Success/verified

---

## 📋 IMPLEMENTATION CHECKLIST

When creating a new page, ensure:

- [ ] Gradient mesh background with 4 blobs
- [ ] Noise overlay for texture
- [ ] Custom cursor (hidden on mobile)
- [ ] Glass navigation bar
- [ ] Section title with gradient text
- [ ] Cards with glassmorphism
- [ ] 3D tilt effects on cards
- [ ] Smooth scroll animations (1.2s, Apple easing)
- [ ] Staggered card reveals (200ms delay)
- [ ] Magnetic button effects
- [ ] Responsive breakpoints (1200px, 900px, 480px)
- [ ] Hover states with glow effects
- [ ] Footer with gradient text

---

## 🎯 EXAMPLE USAGE PROMPT FOR COPILOT

**"Create a [page name] page using the CyberVantage design system. Include:**
- **Gradient mesh background** with 4 animated blobs
- **Custom cursor** (ring + dot)
- **Glass navigation** bar with logo and links
- **Hero section** with large gradient title (7rem)
- **[X number] glass cards** in a grid layout with 3D tilt effects
- **Smooth scroll animations** (1.2s, cubic-bezier easing)
- **Magnetic buttons** for CTAs
- **Responsive design** for mobile/tablet
- Use color palette: cyan (#00f2ff), purple (#7000ff), pink (#ff006e), mint (#00ffaa)
- Typography: Syne for headings, DM Sans for body
- All animations should feel Apple-smooth and polished"

---

## 💡 DESIGN PRINCIPLES

1. **Smooth over Snappy**: Longer durations (1.2s), elegant easing
2. **Depth over Flat**: Multiple layers, shadows, parallax
3. **Glow over Solid**: Use glowing effects for emphasis
4. **Glass over Opaque**: Transparent elements with blur
5. **Asymmetry over Uniformity**: Varied card sizes (bento grids)
6. **Bold over Subtle**: Large text, strong colors, dramatic effects
7. **Interactive over Static**: Hover states, 3D effects, magnetic pulls

---

## 🚀 QUICK START TEMPLATE

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="custom-cursor"></div>
    <div class="cursor-dot"></div>
    
    <div class="gradient-mesh">
        <div class="mesh-gradient mesh-1"></div>
        <div class="mesh-gradient mesh-2"></div>
        <div class="mesh-gradient mesh-3"></div>
        <div class="mesh-gradient mesh-4"></div>
    </div>
    
    <div class="noise-overlay"></div>
    
    <nav class="glass-nav">
        <div class="logo">CyberVantage</div>
        <div class="nav-links">
            <a href="#">Link</a>
        </div>
    </nav>
    
    <main>
        <section class="hero">
            <!-- Hero content -->
        </section>
        
        <section class="content-section">
            <h2 class="section-title">Section Title</h2>
            <div class="card-grid">
                <div class="glass-panel">Card content</div>
            </div>
        </section>
    </main>
    
    <footer class="custom-footer">
        <p>Footer content</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
```

---

## 📚 KEY FILES REFERENCE

If you need to reference the exact implementation:
- **CSS**: `landing.css` (23KB - full design system)
- **JS**: `landing.js` (10KB - all interactions)
- **HTML**: `index.html` (structure example)

---

This design system creates a premium, modern, cybersecurity-focused aesthetic with smooth Apple-quality interactions. Apply consistently across all pages for a cohesive brand experience.
