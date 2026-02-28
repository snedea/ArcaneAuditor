# Frontend Guidelines

## Stack

Vanilla JavaScript with ES6 modules. No framework, no build step, no npm.

- `web/frontend/index.html` — single-page app
- `web/frontend/js/app.js` — main `ArcaneAuditorApp` class
- `web/frontend/js/results-renderer.js` — findings display, summary counters, export
- `web/frontend/js/config-manager.js` — theme, config selection
- `web/frontend/js/utils.js` — helpers, severity icons, sorting
- `web/frontend/js/magic-mode.js` — arcane visual effects
- `web/frontend/style.css` — CSS variables for light/dark theming

## Patterns

- State lives in `ArcaneAuditorApp` instance (global `app` variable)
- DOM updates via `innerHTML` template literals — no virtual DOM
- Theme and sort preferences stored in `localStorage`
- File uploads go to FastAPI endpoints, results stored in `app.currentResult`
- `filteredFindings` is the display array — must be refreshed from `currentResult.findings` after mutations
- `resolvedFindings` is a `Set<number>` of finding indices marked as fixed
- `editedFileContents` is a `Map<string, string>` of file paths to fixed content

## Live Summary Counters

`renderSummary()` computes Issues Found, Actions, and Advices from unresolved findings only. It's called from `renderFindings()` so counters update in real-time as findings get auto-fixed.

## Auto-Fix Flow

1. `autofix(findingIndex)` — POST to `/api/autofix`, stores fixed content, calls `revalidate()`
2. `autofixFile(filePath)` — Fix All: sorts additive fixes before removals, up to 3 convergence passes
3. `revalidate()` — POST to `/api/revalidate`, calls `diffFindings()` to merge new findings
4. `diffFindings()` — compares revalidation results against tracked findings, merges NEW findings
5. Export gated on `lastRevalidationFindingCount === 0`
