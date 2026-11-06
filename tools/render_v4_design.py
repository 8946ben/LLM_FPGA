"""Sync R4Sparse from the journal's single maintained design payload.

Uses the dev-log route snapshot contract; leaves the journal shell and every
other route untouched. No collection, EDA invocation, or board access.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def render():
    html = (ROOT / '开发日志.html').read_text(encoding='utf-8')
    data = json.loads(re.search(r'<script id="dev-log-data" type="application/json">(.*?)</script>', html, re.S)[1])
    route = next(r for r in data['exploration']['routes'] if r['id'] == 'R4Sparse')
    snapshot = dict(route={k: v for k, v in route.items() if k != 'design'},
                    design=route['design'], stages=data['exploration']['stages'],
                    back='../../开发日志.html#schedule-panel', updated=data['exploration']['updated'])
    template = (ROOT / 'doc/design/templates/R4Sparse.html').read_text(encoding='utf-8')
    payload = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False).replace('<', r'\u003c')
    (ROOT / route['design_page']).write_text(template.replace('__DESIGN_DATA__', payload), encoding='utf-8')


if __name__ == '__main__':
    render()
    print('R4Sparse snapshot synchronized from 开发日志.html')
