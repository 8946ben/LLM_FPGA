"""Fetch original author PDFs and pin metadata. Does not run model/EDA/board work."""
from pathlib import Path
import concurrent.futures, hashlib, html, json, re, urllib.request
from datetime import datetime, timezone
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "LMHead-v4b-literature-review/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read(), response.geturl()

def fetch(p):
    meta_path = ROOT / (p['id'] + '_source.html')
    if not meta_path.exists():
        raw, _ = get('https://arxiv.org/abs/' + p['arxiv'])
        meta_path.write_bytes(raw)
    raw = meta_path.read_text(encoding='utf-8')
    def meta(name):
        return [html.unescape(x) for x in re.findall(r'<meta\s+name="'+re.escape(name)+r'"\s+content="([^"]+)"', raw)]
    title = meta('citation_title')[0]
    authors = meta('citation_author')
    # Pin the latest version observed at collection time, using the abs page.
    versions = re.findall(re.escape(p['arxiv']) + r'v(\d+)', raw)
    version = max(map(int, versions)) if versions else 1
    identifier = p['arxiv'] + 'v' + str(version)
    url = 'https://arxiv.org/pdf/' + identifier
    target = ROOT / (p['id'] + '_' + p['slug'] + '_' + identifier + '.pdf')
    if not target.exists():
        data, final_url = get(url)
        if not data.startswith(b'%PDF-'):
            raise ValueError('Not a PDF: ' + url)
        target.write_bytes(data)
    data = target.read_bytes()
    reader = PdfReader(target)
    first = reader.pages[0].extract_text() or ''
    # Full text is retained for reproducible review; PDFs are never rewritten.
    text = '\n\n'.join(f'--- PAGE {i+1} ---\n'+(page.extract_text() or '') for i,page in enumerate(reader.pages))
    (ROOT / (p['id'] + '_extracted.txt')).write_text(text, encoding='utf-8')
    return dict(p, title=title, authors=authors, version=identifier,
                source_url='https://arxiv.org/abs/'+identifier, pdf_url=url,
                file=target.name, bytes=len(data), pages=len(reader.pages),
                sha256=hashlib.sha256(data).hexdigest(),
                metadata_sha256=hashlib.sha256(meta_path.read_bytes()).hexdigest(),
                first_page_excerpt=first[:220])

def main():
    papers = json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))['papers']
    records, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch,p):p for p in papers}
        for future in concurrent.futures.as_completed(futures):
            p = futures[future]
            try:
                record = future.result()
                records.append(record)
                print(p['id'], record['version'], record['pages'], 'pages', flush=True)
            except Exception as exc:
                errors.append(dict(id=p['id'], error=str(exc)))
                print(p['id'], 'FAILED', str(exc), flush=True)
    records.sort(key=lambda x:x['id'])
    manifest = dict(collected_at_utc=datetime.now(timezone.utc).isoformat(),
                    scope='Original PDFs for local research; no redistribution license inferred',
                    papers=records, errors=errors)
    (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'SHA256SUMS.txt').write_text(''.join(f"{p['sha256']}  {p['file']}\n" for p in records),encoding='utf-8')
    bib = []
    for p in records:
        bib.append('@misc{v4b_'+p['id']+',\n  title={'+p['title']+'},\n  author={'+ ' and '.join(p['authors'])+'},\n  year={20'+p['arxiv'][:2]+'},\n  eprint={'+p['arxiv']+'},\n  archivePrefix={arXiv},\n  note={Local PDF '+p['version']+'},\n  url={'+p['source_url']+'}\n}\n')
    (ROOT/'sources.bib').write_text('\n'.join(bib),encoding='utf-8')
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
