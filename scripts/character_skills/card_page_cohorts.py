"""Freeze old CSV membership without recomputing description counts."""
import csv
import hashlib
import json
import random
from pathlib import Path


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze(root,out):
    source=root/'output/character_skills/profiles/characters.csv'
    payload=source.read_bytes();target=out/'cohorts/characters.csv';target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and target.read_bytes()!=payload:raise ValueError('Frozen roster differs; use a new preparation directory')
    target.write_bytes(payload)
    rows=list(csv.DictReader(payload.decode('utf-8-sig').splitlines()));members=[]
    for r in rows:
        n=int(r['descriptions']);cohort='ge60' if n>=60 else '40to59' if n>=40 else '20to39' if n>=20 else 'remaining'
        members.append(dict(cid=int(r['cid']),name=r['name'],old_descriptions=n,cohort=cohort))
    members.sort(key=lambda r:r['cid']);assert len(members)==len({r['cid'] for r in members})==2236
    cohorts={k:[r['cid'] for r in members if r['cohort']==k] for k in ('ge60','40to59','20to39','remaining')}
    assert sum(len(cohorts[k]) for k in ('ge60','40to59','20to39'))==760 and len(cohorts['remaining'])==1476
    chosen=random.Random(20261019).sample(cohorts['remaining'],30)
    result=dict(schema='card-page-cohort-1',source='output/character_skills/profiles/characters.csv',source_sha256=sha(source),
                frozen_csv='characters.csv',seed=20261019,members=members,cohorts=cohorts,
                ordered_remaining_pool=cohorts['remaining'],random_remaining_30=chosen,
                review_cids=[r['cid'] for r in members if r['cohort']!='remaining']+chosen,
                review_policy='All 760 complex cards plus seeded 30; at least 10 distinct real rows each, or all when fewer; actual review decisions required')
    path=target.parent/'manifest.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result
