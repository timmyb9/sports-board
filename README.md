# sports-board

Compact game board for a DAKboard slot (~310x665): last result plus next two games for each team,
away team first. Data comes from ESPN's public site API, refreshed by a GitHub Action every 30 minutes
and served as a static page by GitHub Pages.

- `scripts/fetch_scores.py` - pulls schedules/scores, writes `docs/data.json` (only when something changed)
- `docs/index.html` - the widget; reads `data.json`, re-reads it every 5 minutes, transparent background
- `.github/workflows/update.yml` - cron job that runs the script and commits changes

## Setup
1. Create a GitHub repo (public, so free Pages works) and push this folder.
2. Settings > Pages > Deploy from a branch > `main` / `/docs`.
3. Settings > Actions > General > Workflow permissions > Read and write.
4. Actions tab > Update scores > Run workflow (optional; a current data.json is already included).
5. DAKboard: add an iFrame block pointing at `https://<user>.github.io/<repo>/`, sized to the right-hand slot,
   with block background/border set to none.

## Customize
- Teams: edit `TEAMS` in `scripts/fetch_scores.py` (ESPN sport path + team id).
- Rows per team: `PAST` / `SLOTS` in the same file.
- Timezone: `TZ` at the top of the script block in `docs/index.html`.

Note: GitHub pauses scheduled workflows on repos with no activity for 60 days. In the off-season, re-enable
it from the Actions tab if that happens.
