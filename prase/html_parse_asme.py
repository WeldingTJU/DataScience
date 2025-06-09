# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import os, json

def clean(t: str) -> str:
    return ' '.join(t.strip().split())

def parse_doc_asme(soup: BeautifulSoup):
    h1 = soup.find('h1', class_='article-title-main')
    title = clean(h1.text) if h1 else ''

    abs_sec  = soup.find('section', class_='abstract')
    abstract = ' '.join(clean(p.text) for p in abs_sec.find_all('p')) if abs_sec else ''

    kw_div   = soup.find('div', class_='content-metadata-keywords')
    keywords = [a.text.strip() for a in kw_div.find_all('a')] if kw_div else []
    if not keywords:
        for meta in soup.find_all('meta', attrs={'name':'citation_keyword'}):
            kw = meta.get('content', '').strip()
            if kw: keywords.append(kw)

    idlst, textlst = [], []
    for wrap in soup.select('div.article-section-wrapper'):
        if wrap.find('section', class_='abstract'):
            continue

        sec_ids, sec_txts = [], []

        h_tag = wrap.find(['h2','h3','h4','h5','h6'])
        if h_tag:
            sec_ids.append(h_tag.name)
            sec_txts.append(clean(h_tag.text))

        for p in wrap.find_all('p'):
            txt = clean(p.text)
            if txt:
                sec_ids.append('p'); sec_txts.append(txt)

        if sec_ids:
            idlst.append(sec_ids)
            textlst.append(sec_txts)

    return title, abstract, keywords, idlst, textlst

def section_struct(ids, txts):
    node = {'sec_title':'', 'content':[]}
    heads = [int(i[1]) for i in ids if i.startswith('h')] or [7]
    top   = min(heads)
    splits= [i for i,x in enumerate(ids) if x.startswith('h') and int(x[1])==top] + [len(ids)]
    for a, b in zip(splits[:-1], splits[1:]):
        title = txts[a]
        sub_id, sub_txt = ids[a+1:b], txts[a+1:b]
        if any(i.startswith('h') for i in sub_id):
            node['content'].append(section_struct(sub_id, sub_txt) | {'sec_title': title})
        else:
            node['content'].append({'sec_title': title, 'content': sub_txt})
    return node

def doc_struct(title, abstract, keywords, ids, txts, path, file, doi):
    return {
        'title': title,
        'abstract': abstract,
        'keywords': keywords,
        'path': path,
        'file': file,
        'doi': doi,
        'content': [section_struct(ids[i], txts[i]) for i in range(len(ids))]
    }

path    = r"F:\html\asme" # input
txtpath = r"F:\prase-html\asme" # output
logpath = os.path.join(txtpath, "parse.log")
iftxt   = 1 # Set to 1 if you want to export text files
ifjson  = 1 # Set to 1 if you want to export JSON files

os.makedirs(txtpath, exist_ok=True)
doc_dict = {}

with open(logpath, 'w', encoding='utf-8') as log:
    for file in os.listdir(path):
        if not file.endswith('.html'):
            continue
        filename = file[:-5]
        doi = filename.replace('_', '/')
        try:
            with open(os.path.join(path, file), 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'lxml')
            title, abstract, kw, ids, txts = parse_doc_asme(soup)
            ok = True
            log.write(file + '\n')
        except Exception as e:
            ok = False
            log.write(f"{file} PARSE ERROR: {e}\n")

        # —— TXT
        if iftxt:
            with open(os.path.join(txtpath, filename + '.txt'), 'w', encoding='utf-8') as out:
                if ok:
                    out.write(f"{title}\n\nAbstract\n{abstract}\n\nKeywords\n")
                    out.write(', '.join(kw) + '\n\n')
                    for tags, paras in zip(ids, txts):
                        for tag, txt in zip(tags, paras):
                            out.write(f"[{tag}]\n{txt}\n")
                else:
                    out.write(f"{file} PARSE ERROR\n")

        # —— JSON
        if ok:
            doc_dict[doi] = doc_struct(title, abstract, kw, ids, txts,
                                       path, file, doi)

if ifjson:
    with open(os.path.join(path, 'data.json'), 'w', encoding='utf-8') as jf:
        json.dump(doc_dict, jf, ensure_ascii=False, indent=2)
