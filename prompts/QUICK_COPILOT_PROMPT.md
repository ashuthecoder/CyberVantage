# Quick Copilot Prompt - CyberVantage Design

## 🎯 COPY-PASTE PROMPT FOR GITHUB COPILOT

Use this when creating new pages:

---

**"Create a [page type] using this design system:**

**VISUAL:**
- Dark background (#0a0a1a) with 4 animated gradient blobs (cyan, purple, pink, mint)
- SVG noise overlay (opacity 0.5, mix-blend-mode: overlay)
- Custom cursor (ring + dot) with z-index 999999
- Glass navigation bar (fixed, backdrop-blur, changes on scroll)

**COLORS:**
```
Primary: #00f2ff (cyan)
Secondary: #7000ff (purple)
Tertiary: #ff006e (pink)
Glow: #00ffaa (mint)
Glass: rgba(255,255,255,0.03)
```

**TYPOGRAPHY:**
- Headings: 'Syne' 800 weight, 4.5-7rem, gradient text
- Body: 'DM Sans' 400-700, 1rem, line-height 1.7

**CARDS:**
- Glassmorphism: rgba(255,255,255,0.03), backdrop-blur(20-30px)
- Border-radius: 24-30px
- Hover: 3D tilt (perspective 1000px, rotateX/Y), lift up, scale 1.02, glow shadow

**ANIMATIONS:**
- Scroll reveals: 1.2s, cubic-bezier(0.25,0.46,0.45,0.94), translateY(80px) → 0
- Stagger cards: 200ms delay between each
- Hover transitions: 0.6s smooth easing
- Magnetic buttons: pull toward cursor within 80px

**INTERACTIONS:**
- 3D card tilt on mouse move (sensitivity: /20)
- Magnetic buttons (translate toward cursor)
- Scroll-triggered animations (Intersection Observer, threshold 0.15)
- Parallax gradient mesh (slow scroll)

**LAYOUT:**
- Sections: 4-6rem vertical padding, 10% horizontal
- Grid: repeat(auto-fit, minmax(350px, 1fr)), gap 2.5rem
- Responsive: 1200px, 900px, 480px breakpoints

**CYBERSECURITY THEME:**
- Use shield shapes, lock icons, network nodes, scan effects
- Pulsing glows (4s), floating particles, connection lines
- Color coding: cyan=secure, purple=advanced, pink=alert, mint=success

**REQUIRED ELEMENTS:**
1. Gradient mesh background (4 blobs)
2. Noise overlay
3. Custom cursor
4. Glass nav
5. Section titles with gradients
6. Glass cards with 3D hover
7. Smooth Apple-style animations
8. Responsive mobile layout

Apply consistently for polished, premium cybersecurity aesthetic."

---

## ⚡ ULTRA-SHORT VERSION

**"CyberVantage style: Dark bg (#0a0a1a), 4 gradient blobs (cyan/purple/pink/mint), custom cursor, glassmorphism cards (blur 20px), 3D tilt hover, 1.2s smooth animations, Syne headings + DM Sans body, magnetic buttons, scroll reveals with 200ms stagger. Cybersecurity theme with shields/locks/nodes. Responsive. Apple-quality polish."**

---

## 📋 COMPONENT TEMPLATES

### Quick Glass Card:
```html
<div class="glass-panel">
    <h3>Title</h3>
    <p>Content</p>
</div>
```

### Quick Section:
```html
<section class="content-section">
    <h2 class="section-title">Gradient Title</h2>
    <div class="card-grid">
        <!-- Cards here -->
    </div>
</section>
```

### Quick Button:
```html
<button class="btn-glass">Click Me</button>
```

---

## 🎨 CSS QUICK REFERENCE

```css
/* Glass Card */
.glass-panel {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 3rem;
    transition: all 0.6s cubic-bezier(0.25,0.46,0.45,0.94);
}

.glass-panel:hover {
    transform: translateY(-10px) scale(1.03);
    border-color: #00f2ff;
    box-shadow: 0 20px 60px rgba(0,242,255,0.25);
}

/* Gradient Title */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 4.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00f2ff 0%, #00ffaa 50%, #ff006e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Smooth Animation */
.animated-element {
    opacity: 0;
    transform: translateY(80px);
    transition: all 1.2s cubic-bezier(0.25,0.46,0.45,0.94);
}

.animated-element.visible {
    opacity: 1;
    transform: translateY(0);
}
```

---

## 🔥 EXAMPLE PROMPTS

**Dashboard Page:**
*"Create a dashboard page in CyberVantage style with gradient mesh, custom cursor, 6 glass stat cards in bento grid (2 large, 4 small), smooth scroll animations, 3D card tilt, magnetic CTAs. Colors: cyan/purple/pink/mint. Syne headings, DM Sans body."*

**Login Page:**
*"Create centered login form in CyberVantage style. Glass card (500px wide), gradient mesh background, custom cursor, floating shield icon, magnetic submit button, smooth focus states. Dark theme with cyan accents."*

**Feature Page:**
*"Create features page: hero with gradient title, 9 glass cards (3x3 grid), each with icon, 3D hover tilt, scroll-triggered stagger (200ms), magnetic 'Learn More' buttons. Full CyberVantage design system."*

---

**Use these prompts with GitHub Copilot to quickly generate consistent pages!** 🚀
