#!/usr/bin/env python3
"""Render a GitHub contribution calendar + activity composition in two SVG themes.

Data comes from GitHub GraphQL. The API token is never written to an output file.
"""
import datetime
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount contributionLevel } }
      }
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
    }
  }
}"""

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
THEMES = {
    "light": dict(bg="#ffffff", border="#d0d7de", fg="#1f2328",
                  muted="#59636e", empty="#ebedf0",
                  levels=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
                  green="#2da44e", bar_bg="#eaeef2"),
    "dark": dict(bg="#0d1117", border="#30363d", fg="#e6edf3",
                 muted="#9198a1", empty="#161b22",
                 levels=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
                 green="#3fb950", bar_bg="#21262d"),
}

def request_collection(login, token):
    req = Request(
        "https://api.github.com/graphql",
        json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        {"Authorization": "Bearer " + token, "Content-Type": "application/json",
         "User-Agent": "profile-activity-overview"}, method="POST")
    with urlopen(req, timeout=35) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError("GitHub GraphQL returned errors: " + str(result["errors"]))
    user = (result.get("data") or {}).get("user")
    if not user:
        raise RuntimeError("GitHub user not found: " + login)
    return user["contributionsCollection"]

def render(data, t):
    a = []
    def rect(x,y,w,h,color,r=3,extra=""):
        a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{color}" {extra}/>')
    def label(x,y,s,size=16,color=None,weight=400,anchor="start"):
        a.append(f'<text x="{x}" y="{y}" fill="{color or t["fg"]}" font-size="{size}" '
                 f'font-weight="{weight}" text-anchor="{anchor}">{escape(str(s))}</text>')

    a.append('<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="635" '
             'viewBox="0 0 1160 635" role="img" '
             'aria-label="GitHub contributions calendar and activity overview">')
    a.append('<title>GitHub contribution activity, last year</title>')
    a.append('<style>text{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif}</style>')
    rect(1,1,1158,633,t["bg"],15,
         f'stroke="{t["border"]}" stroke-width="2"')
    calendar = data["contributionCalendar"]
    label(34,60,f'{calendar["totalContributions"]:,} contributions in the last year',28,weight=600)
    label(1126,59,"GITHUB ACTIVITY",13,t["muted"],600,"end")
    weeks = calendar["weeks"]
    x0,y0,step = 113,139,18
    seen = set()
    for i,week in enumerate(weeks):
        for day in week["contributionDays"]:
            ym = day["date"][:7]
            if ym not in seen:
                seen.add(ym)
                if i > 1 and i < len(weeks)-1:
                    mon = datetime.date.fromisoformat(day["date"]).strftime("%b")
                    label(x0+i*step,122,mon,14,t["muted"])
            x,y = x0+i*step,y0+day["weekday"]*step
            col = t["levels"][LEVELS.get(day["contributionLevel"],0)]
            a.append(f'<rect x="{x}" y="{y}" width="14" height="14" rx="3" fill="{col}">'
                     f'<title>{escape(day["date"])}: {day["contributionCount"]} contributions</title></rect>')
    for day,ix in [("Mon",1),("Wed",3),("Fri",5)]:
        label(72,y0+ix*step+11,day,14,t["muted"])
    label(49,304,"Less",13,t["muted"])
    for i,color in enumerate(t["levels"]):
        rect(93+i*20,289,15,15,color)
    label(199,304,"More",13,t["muted"])
    label(1126,304,"Daily contributions · GitHub GraphQL",12,t["muted"],anchor="end")
    a.append(f'<line x1="1" x2="1159" y1="334" y2="334" stroke="{t["border"]}"/>')
    label(34,377,"Activity overview",21,weight=600)
    label(34,416,"CONTRIBUTION TYPE",13,t["muted"],600)

    values = [("Commits",data["totalCommitContributions"]),
              ("Issues",data["totalIssueContributions"]),
              ("Pull requests",data["totalPullRequestContributions"]),
              ("Code reviews",data["totalPullRequestReviewContributions"])]
    total = sum(values[i][1] for i in range(4))
    portions = [v/total if total else 0 for _,v in values]
    for i,(name,value) in enumerate(values):
        y = 454+47*i
        label(34,y,name,17)
        label(510,y,f'{value:,}  ·  {portions[i]:.0%}',15,t["muted"],anchor="end")
        rect(34,y+10,476,7,t["bar_bg"])
        if value:
            rect(34,y+10,max(2,476*portions[i]),7,t["green"])
    a.append(f'<line x1="565" x2="565" y1="366" y2="604" stroke="{t["border"]}"/>')
    label(850,385,"ACTIVITY MIX",13,t["muted"],600,"middle")
    cx,cy,r=850,510,80
    dirs=[(0,-1),(1,0),(0,1),(-1,0)]
    for frac in (0.25,0.50,0.75,1):
        points=" ".join(f'{cx+dx*r*frac:.1f},{cy+dy*r*frac:.1f}' for dx,dy in dirs)
        a.append(f'<polygon points="{points}" fill="none" stroke="{t["border"]}" stroke-dasharray="3 5"/>')
    for dx,dy in dirs:
        a.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+dx*r}" y2="{cy+dy*r}" stroke="{t["border"]}"/>')
    points=" ".join(f'{cx+dx*r*portions[i]:.1f},{cy+dy*r*portions[i]:.1f}'
                    for i,(dx,dy) in enumerate(dirs))
    a.append(f'<polygon points="{points}" fill="{t["green"]}" fill-opacity=".26" '
             f'stroke="{t["green"]}" stroke-width="3" stroke-linejoin="round"/>')
    for i,(dx,dy) in enumerate(dirs):
        a.append(f'<circle cx="{cx+dx*r*portions[i]:.1f}" cy="{cy+dy*r*portions[i]:.1f}" '
                 f'r="4" fill="{t["bg"]}" stroke="{t["green"]}" stroke-width="3"/>')
    for x,y,i,anchor in [(850,423,0,"middle"),(947,515,1,"start"),
                         (850,620,2,"middle"),(753,515,3,"end")]:
        label(x,y,f'{portions[i]:.0%} {values[i][0]}',13,t["muted"],anchor=anchor)
    a.append("</svg>")
    return "\n".join(a)+"\n"

def main():
    token=os.getenv("GITHUB_TOKEN")
    login=os.getenv("GITHUB_REPOSITORY_OWNER") or os.getenv("GH_LOGIN")
    if not token or not login:
        raise SystemExit("GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER required")
    data=request_collection(login,token)
    output=Path("assets/contributions")
    output.mkdir(parents=True,exist_ok=True)
    for theme,palette in THEMES.items():
        path=output/f"activity-{theme}.svg"
        path.write_text(render(data,palette),encoding="utf-8")
        print(f"Wrote {path}")

if __name__=="__main__":
    main()
