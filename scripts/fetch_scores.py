#!/usr/bin/env python3
"""Pull schedules and scores from ESPN's public site API and write docs/data.json.

Only rewrites the file when something changed, so the Action commits only on real updates.
Edit TEAMS below to add or remove teams (sport path + ESPN team id).
"""
import json, os, sys, datetime as dt, urllib.request

TEAMS = [  # key, display name, ESPN sport path, ESPN team id, header color override (optional)
    ("IOWA", "Hawkeyes", "football/college-football", "2294", "#b38f00"),
    ("KC",   "Chiefs",   "football/nfl",              "12",   None),
    ("NJD",  "Devils",   "hockey/nhl",                "11",   "#c8102e"),
    ("SF",   "49ers",    "football/nfl",              "25",   None),
]
PAST, SLOTS = 1, 3   # 1 finished game + up to 2 live/upcoming = 3 rows per team
URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/teams/{id}/schedule{q}"
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "data.json")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sports-board/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def logo(team):
    logos = team.get("logos") or []
    for l in logos:
        if "default" in l.get("rel", []):
            return l["href"]
    return logos[0]["href"] if logos else ""


def score(c):
    s = c.get("score")
    if isinstance(s, dict):
        s = s.get("displayValue", s.get("value"))
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None


def side(c):
    t = c["team"]
    return {"id": t["id"], "abbr": t.get("abbreviation", ""), "logo": logo(t),
            "score": score(c), "winner": bool(c.get("winner"))}


def parse_event(ev):
    comp = ev["competitions"][0]
    st = comp["status"]["type"]
    by = {c.get("homeAway"): c for c in comp["competitors"]}
    if "away" not in by or "home" not in by:          # safety net, e.g. neutral site
        by = {"home": comp["competitors"][0], "away": comp["competitors"][1]}
    return {"id": ev["id"], "date": ev["date"], "state": st["state"],   # pre | in | post
            "detail": st.get("shortDetail", ""),
            "away": side(by["away"]), "home": side(by["home"])}


def team_block(key, label, sport, tid, color):
    events, info = {}, {}
    for q in ("", "?seasontype=3"):                   # regular season, then postseason
        try:
            d = get(URL.format(sport=sport, id=tid, q=q))
        except Exception as e:
            print(f"warn {key} {q or 'regular'}: {e}", file=sys.stderr)
            continue
        info = info or d.get("team", {})
        for ev in d.get("events", []):
            events[ev["id"]] = parse_event(ev)
    games = sorted(events.values(), key=lambda g: g["date"])
    past = [g for g in games if g["state"] == "post"][-PAST:]
    live = [g for g in games if g["state"] == "in"]
    pre = [g for g in games if g["state"] == "pre"]
    ahead = (live + pre)[:SLOTS - 1]
    team_logo = logo(info)
    for g in games:                                   # schedule endpoint may omit the team's own logo
        for sd in (g["away"], g["home"]):
            if not team_logo and sd["id"] == tid:
                team_logo = sd["logo"]
    return {"key": key, "id": tid, "name": label, "full": info.get("displayName", label),
            "record": info.get("recordSummary", ""), "logo": team_logo,
            "color": color or "#" + (info.get("color") or "444444"),
            "games": past + ahead}


def main():
    teams = [team_block(*t) for t in TEAMS]
    if not any(t["games"] for t in teams):
        sys.exit("no data fetched; leaving data.json untouched")
    try:
        old = json.load(open(OUT))
    except Exception:
        old = {}
    if old.get("teams") == teams:
        print("no changes")
        return
    out = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "teams": teams}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print("data.json updated")


if __name__ == "__main__":
    main()
