import csv,json,statistics
from collections import defaultdict
from urllib.request import urlopen
from pathlib import Path
base="https://raw.githubusercontent.com/hudl/open-data/master/data/"
def load(path):
 with urlopen(base+path,timeout=90) as r:return json.load(r)
matches=load("matches/43/106.json"); rows=[]
for i,m in enumerate(matches):
 mid=m["match_id"]; events=load(f"events/{mid}.json")
 poss=defaultdict(list)
 for e in events:
  if e.get("period")!=5:poss[e.get("possession")].append(e)
 for p,g in poss.items():
  g.sort(key=lambda e:e.get("index",0))
  shots=[e for e in g if e.get("type",{}).get("name")=="Shot" and e.get("play_pattern",{}).get("name") in ("Regular Play","From Counter") and e.get("shot",{}).get("type",{}).get("name")!="Penalty"]
  if not shots:continue
  shot=shots[0]; xg=shot.get("shot",{}).get("statsbomb_xg")
  if xg is None:continue
  n=sum(e.get("type",{}).get("name")=="Pass" and "outcome" not in e.get("pass",{}) for e in g if e.get("index",0)<shot["index"])
  b="0-2" if n<=2 else "3-5" if n<=5 else "6-9" if n<=9 else "10+"
  rows.append(dict(match_id=mid,possession=p,passes=n,bin=b,xg=xg,pattern=shot["play_pattern"]["name"]))
 print(i+1,len(matches),mid,flush=True)
out=Path("results");out.mkdir(exist_ok=True)
with (out/"shots.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
summary=[]
for b in ("0-2","3-5","6-9","10+"):
 x=[r["xg"] for r in rows if r["bin"]==b]
 summary.append(dict(bin=b,count=len(x),mean_xg=statistics.mean(x),variance_xg=statistics.variance(x),cdf_at_0_1=sum(v<=.1 for v in x)/len(x),high_xg_share=sum(v>=.2 for v in x)/len(x)))
with (out/"summary.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
print(json.dumps(summary,indent=2),flush=True)
