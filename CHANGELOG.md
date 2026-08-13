# Changelog

All material Hat in Ring product, evidence, and engineering changes are recorded here, newest first.

## 2026-08-13

### Accessibility

- Raised the Exploratory status color to WCAG AA contrast against white text.
- Replaced focusable table headers and rows with native sort and dossier buttons while retaining `aria-sort` on header cells.
- Standardized desktop and mobile interactive targets at 44px minimum with visible focus treatment.
- Removed the candidate-card headline clamp so WCAG text spacing and narrow-screen reflow no longer clip summaries.

## 2026-08-12

### Performance

- Added generator-owned 96px and 192px WebP portrait thumbnails for every referenced candidate image.
- Updated leaderboard, cards, dossier directory, and Wire avatar delivery with responsive srcset, explicit dimensions, lazy loading, and asynchronous decode.
- Retained the larger optimized portrait only for dossier and static candidate-page contexts that need it.

### Security and operations

- Added pinned dependency, secret, and configuration scanning.
- Enabled Dependabot vulnerability alerts, automated security fixes, and weekly Python and Actions updates.
