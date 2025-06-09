# -*- coding: utf-8 -*-
import os, json, re, sys
from io import StringIO
from urllib.parse import urljoin, urlparse

import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_max_column(table):
    return max((len(r) for r in table), default=0)

def fill_column(table, maxcol):
    for r in table:
        r.extend([''] * (maxcol - len(r)))
    return table

def add_data(data, table, nr, nc, rs, cs):
    while len(table) <= nr:
        table.append([])
    row = table[nr]
    while nc < len(row) and row[nc] != '':
        nc += 1
    for r in range(nr, nr + rs):
        while len(table) <= r:
            table.append([])
        for c in range(nc, nc + cs):
            while len(table[r]) <= c:
                table[r].append('')
            table[r][c] = data
    return table, nc + cs

def parse_rows(parent, tag):
    data = []; nr = 0
    for tr in parent.find_all('tr'):
        nc = 0
        for cell in tr.find_all(tag):
            txt = ' '.join(cell.stripped_strings)
            rs = int(cell.get('rowspan', 1))
            cs = int(cell.get('colspan', 1))
            data, nc = add_data(txt, data, nr, nc, rs, cs)
        nr += 1
    return data

def join_table(parts):
    if len(parts) <= 1:
        return parts
    merged = [parts[0]]
    for tb in parts[1:]:
        last = merged[-1]
        if (len(tb['head']) == len(last['head'])
                and len(tb['body']) == len(last['body'])):
            for r in range(len(tb['head'])):
                last['head'][r].extend(tb['head'][r])
            for r in range(len(tb['body'])):
                last['body'][r].extend(tb['body'][r])
        else:
            merged.append(tb)
    return merged

def parse_single_table(tables, title):
    out = []
    for tbl in tables:
        head = parse_rows(tbl.thead, 'th') if tbl.thead else []
        body = parse_rows(tbl.tbody or tbl, 'td')
        width = max(get_max_column(head), get_max_column(body))
        head, body = fill_column(head, width), fill_column(body, width)
        out.append({'title': title, 'head': head, 'body': body})
    return join_table(out)

def _fetch_remote(a_tag, base):
    if not a_tag or not a_tag.has_attr('href'):
        return []
    url = urljoin(base, a_tag['href'])
    try:
        html = requests.get(url, timeout=15).text
        sub = BeautifulSoup(html, 'lxml')
        caption = sub.find('figcaption')
        title = caption.get_text(strip=True) if caption else url
        return parse_single_table(sub.find_all('table'), title)
    except Exception as e:
        print(f'WARNING  {url}: {e}', file=sys.stderr)
        return []

def parse_table_springer(doc):
    art_title = (doc.find('h1') or
                 doc.find('meta', attrs={'name':'dc.title'}))
    art_title = art_title.get_text(strip=True) if art_title else 'Untitled'
    tables = []

    for box in doc.find_all(
            lambda t: t.name in ('div','figure')
            and t.get('class')
            and any('article-table' in c for c in t['class'])):

        caption = box.find('figcaption')
        ttl = caption.get_text(strip=True) if caption else art_title
        inner = box.find_all('table')
        if inner:
            tables.extend(parse_single_table(inner, ttl))
        else:
            pill = box.find('a', class_=lambda c:c and 'pill-button' in c)
            base = urlparse(doc.find('meta', property='og:url')['content'])
            base = f'{base.scheme}://{base.netloc}'
            tables.extend(_fetch_remote(pill, base))

    if not tables:
        tables.extend(parse_single_table(doc.find_all('table'), art_title))

    if not tables:
        sio = StringIO(str(doc))
        for flav in ('lxml','bs4'):
            try:
                for i,df in enumerate(pd.read_html(sio, flavor=flav),1):
                    tables.append({'title':f'{art_title} (fallback {i})',
                                   'head':[list(df.columns)],
                                   'body':df.values.tolist()})
                break
            except ValueError:
                sio.seek(0)
    return tables

def parse_table_wiley(doc):
    res = []
    for div in doc.find_all('div', class_='article-table-content'):
        ttl = ' '.join(div.header.stripped_strings) if div.header else 'Untitled'
        res.extend(parse_single_table(div.find_all('table'), ttl))
    return res

def parse_table_mdpi(doc):
    res = []
    for div in doc.find_all('div', class_='html-table_show'):
        cap = div.find('div', class_='html-caption') or div.find('caption')
        ttl = cap.get_text(strip=True) if cap else 'Untitled'
        res.extend(parse_single_table(div.find_all('table'), ttl))
    return res

def table_to_markdown(tb):
    """dict → markdown"""
    md = [f'#### {tb["title"]}\n']
    rows = []
    if tb['head']:
        rows.extend(tb['head'])
    rows.extend(tb['body'])

    if not rows:
        md.append('*(空表)*\n')
        return '\n'.join(md)

    header = rows[0]
    md.append('| ' + ' | '.join(header) + ' |')
    md.append('| ' + ' | '.join(['---']*len(header)) + ' |')

    for r in rows[1:]:
        md.append('| ' + ' | '.join(r) + ' |')
    md.append('')
    return '\n'.join(md)

def dump_markdown(data:dict, out_path:str):
    lines = ['# Tables Extracted\n']
    for paper_id, item in data.items():
        lines.append(f'## {paper_id}')
        if not item['tables']:
            lines.append('*No tables found.*\n')
            continue
        for tb in item['tables']:
            lines.append(table_to_markdown(tb))
    with open(out_path, 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(lines))
    print(f'Markdown saved → {out_path}')

def process_html(dir_path, parser):
    data = {}
    for fn in os.listdir(dir_path):
        if not fn.endswith('.html'):
            continue
        with open(os.path.join(dir_path, fn), encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
        try:
            tables = parser(soup)
            data[os.path.splitext(fn)[0]] = {
                'path': dir_path, 'file': fn, 'tables': tables}
            print(f'{fn}: {len(tables)} tables')
        except Exception as e:
            print(f'{fn}: PARSE ERROR {e}', file=sys.stderr)
    return data

if __name__ == '__main__':
    ROOT = r'F:\html\springer'   # ← Replace with your directory
    DATA_JSON = os.path.join(ROOT, 'data_table.json')
    DATA_MD   = os.path.join(ROOT, 'data_table.md.txt')

    data = process_html(ROOT, parse_table_springer)   # Switching the parser allows parsing of Wiley/MDPI.

    # Save JSON
    with open(DATA_JSON, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    print(f'JSON saved → {DATA_JSON}')

    # Save Markdown
    dump_markdown(data, DATA_MD)
