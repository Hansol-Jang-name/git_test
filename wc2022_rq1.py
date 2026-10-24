import csv,json,statistics,math
from collections import defaultdict
from pathlib import Path
from urllib.request import urlopen

BASE="https://raw.githubusercontent.com/hudl/open-data/master/data/"
PLAY={"Regular Play","From Counter"}
def load(path):
    with urlopen(BASE+path,timeout=90) as f: return json.load(f)
def group(n):
    return "0-2" if n<=2 else "3-5" if n<=5 else "6-9" if n<=9 else "10+"
def wilson(s,n,z=1.96):
    p=s/n
    den=1+z*z/n
    ctr=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return ctr-half,ctr+half
matches=load("matches/43/106.json")
rows=[]
for i,m in enumerate(matches):
    mid=m["match_id"]; ev=load(f"events/{mid}.json")
    poss=defaultdict(list)
    for e in ev:
        if e.get("period")!=5 and e.get("possession") is not None:
            poss[e["possession"]].append(e)
    for pid,es in poss.items():
        es.sort(key=lambda x:x.get("index",0))
        if not any(e.get("play_pattern",{}).get("name") in PLAY for e in es):continue
        shots=[e for e in es if e.get("type",{}).get("name")=="Shot"
               and e.get("play_pattern",{}).get("name") in PLAY
               and e.get("shot",{}).get("type",{}).get("name")!="Penalty"]
        first=shots[0] if shots else None
        cutoff=first["index"] if first else float("inf")
        n=sum(e.get("type",{}).get("name")=="Pass" and "outcome" not in e.get("pass",{})
              for e in es if e.get("index",0)<cutoff)
        rows.append(dict(match_id=mid,possession=pid,passes=n,bin=group(n),shot=int(first is not None)))
    print(i+1,len(matches),mid,flush=True)
out=Path("results");out.mkdir(exist_ok=True)
with (out/"rq1_possessions.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
summary=[]
for b in ("0-2","3-5","6-9","10+"):
    subset=[r for r in rows if r["bin"]==b]
    s=sum(r["shot"] for r in subset);n=len(subset)
    lo,hi=wilson(s,n)
    summary.append(dict(bin=b,possessions=n,shot_possessions=s,shot_probability=s/n,
                        bernoulli_variance=(s/n)*(1-s/n),ci95_low=lo,ci95_high=hi))
with (out/"rq1_summary.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
by_n=defaultdict(list)
for r in rows:by_n[r["passes"]].append(r["shot"])
exact=[dict(passes=n,possessions=len(a),shots=sum(a),probability=sum(a)/len(a))
       for n,a in sorted(by_n.items())]
with (out/"rq1_exact.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=exact[0]);w.writeheader();w.writerows(exact)
print(json.dumps(dict(total_possessions=len(rows),shot_possessions=sum(r["shot"] for r in rows),
                      summary=summary),ensure_ascii=False,indent=2),flush=True)
