# Screenshots

> Placeholder folder. Capture these and drop the PNGs here, then they'll render
> in the main README's Screenshots section. (Images can't be generated
> programmatically — capture them from a running instance.)

## Recommended captures

| Filename | What to show |
|---|---|
| `dashboard-dark.png` | Full dashboard, dark theme, with several threats in the feed |
| `dashboard-light.png` | Same, light theme |
| `live-detection.png` | A new HIGH SQL Injection row just after triggering an attack |
| `block-action.png` | A row mid-action (Block/Ignore buttons) or a blocked status |
| `chart-stats.png` | Threats-by-type chart + stat cards |
| `demo-site.png` | The IntraPortal demo page with the Attack Simulator panel |
| `swagger.png` | `http://localhost:8000/docs` showing the endpoint list |

## How to capture

1. `docker compose up --build` (or run the stack manually).
2. Generate data: `python simulate_traffic.py` for ~20 s, or click attacks on
   the demo site.
3. Capture at ~1440px width for crisp README rendering.
4. Save as PNG with the filenames above.

## Reference in the README

```md
![Dashboard](docs/screenshots/dashboard-dark.png)
```
