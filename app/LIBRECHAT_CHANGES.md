# LibreChat Overlay Changes

Track every modification made to LibreChat's upstream code via the overlay.
This file is a **rebase checklist** — review it before updating the LibreChat submodule.

| File | Change | Method | Risk on Upgrade |
|------|--------|--------|-----------------|
| `client/src/style.css` | Appended theme CSS | Dockerfile `cat >>` | Low — append is additive |
| `client/public/assets/logo.png` | Replaced logo | Dockerfile `cp` | Low — file replacement |
| `client/index.html` | Title, meta description | Dockerfile `sed` | Medium — target strings may change |
| `manifest.webmanifest` | PWA app name, colors | Dockerfile `sed` | Medium — target strings may change |

## After Submodule Update

1. Run `./scripts/validate-overlay.sh` to check all sed targets still exist
2. Run `make build` and verify branding is applied
3. Update this table if any changes were added or removed
