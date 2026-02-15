# CyberVantage React UI

This directory contains the React/Vite-based frontend for CyberVantage's new UI components.

## Overview

The new UI includes:
- **Landing Page**: Modern SOC-themed landing page with terminal aesthetics
- **Dashboard**: Themeable dashboard with SOC and Modern themes

## Architecture

- **Framework**: React 19+ with Vite build tool
- **UI Library**: Lucide React for icons
- **Styling**: Inline styles with dynamic theme switching
- **Build Output**: Static files generated to `../static/react-build/`

## Development

### Install Dependencies
```bash
npm install
```

### Build for Production
```bash
npm run build
```

This generates optimized JavaScript and CSS files in `../static/react-build/`.

## Flask Integration

The React components are integrated with Flask via templates:

- `/landing-new` → `templates/landing_new.html` → Loads React landing page
- `/dashboard-new` → `templates/dashboard_new.html` → Loads React dashboard (auth required)

## Features

### Landing Page
- Terminal-style SOC theme with scanlines and grid effects
- Animated typing effect and cursor blink
- Real-time UTC clock display
- Responsive four-phase training protocol cards
- Enterprise features showcase

### Dashboard
- **Dual Themes**: SOC Mode (dark/terminal) and Modern Mode (light/clean)
- Theme toggle button with instant switching
- Real-time stat cards with hover effects
- Sidebar navigation with icons

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
