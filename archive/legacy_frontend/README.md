# Archived Legacy Frontend Assets

These files were moved from `js/` and `css/` to `archive/legacy_frontend/` on 2026-09-04 as part of the BioNEET-Pro cleanup (Phase 1 Bug Fix 9).

## Reason for Archival

These files had **zero references** from `BioNeet-Pro.html` (the single-file frontend). The HTML file uses:
- Inline CSS styles (no external stylesheet)
- Firebase JS SDK loaded from CDN (`https://www.gstatic.com/firebasejs/11.0.0/...`)
- All application logic embedded in the HTML file itself

## Archived Files

- `js/auth.js` (8 KB) - Local Firebase auth wrapper, unused
- `js/config.js` (16 KB) - Configuration module, unused
- `js/utils.js` (11 KB) - Utility functions, unused
- `css/styles.css` (62 KB) - Stylesheet, unused (all styles are inline in HTML)

## Retained Frontend

- `BioNeet-Pro.html` - The single-file production frontend (236 KB) with all CSS/JS inlined.

## Restoration

If a modular frontend architecture is adopted in the future, these files can be restored from this archive directory.