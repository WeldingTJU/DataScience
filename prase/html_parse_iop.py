# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import os, json

def ifskip(string):
    return any(sw in string for sw in [
        'abbre','Bib','Ack','author','affiliation','corresponding',
        'editor','right','info','cite','url'])

def parse_paragraph(tag):
    return tag.text.replace('\n', '')

def parse_section(div):
    idlst, txtlst = [], []
    for child in div.children:
        if child.name in ['h1','h2','h3','h4','h5','h6']:
            idlst.append(child.name)
            txtlst.append(child.text.strip())
        elif child.name == 'p':
            idlst.append('p')
            txtlst.append(parse_paragraph(child))
        elif child.name == 'div' and 'article-text' in child.get('class', []):
            ids, txts = parse_section(child)
            idlst.extend(ids); txtlst.extend(txts)
    return idlst, txtlst

def parse_doc_iop(soup):
    meta_t = soup.find('meta', {'name': 'citation_title'})
    title  = meta_t['content'].strip() if meta_t else ''

    abs_div = soup.find('div', class_='wd-jnl-art-abstract')
    abstract = ' '.join(p.text.strip() for p in abs_div.find_all('p')) if abs_div else ''

    keywords = []

    idlst, txtlst = [], []
    body = soup.find('div', itemprop='articleBody')
    if body:
        for child in body.children:
            if child.name == 'h2':
                idlst.append([]); txtlst.append([])
                idlst[-1].append('h2'); txtlst[-1].append(child.text.strip())
            elif child.name in ['h3','h4','h5','h6']:
                if not idlst:
                    idlst.append([]); txtlst.append([])
                idlst[-1].append(child.name); txtlst[-1].append(child.text.strip())
            elif child.name == 'div' and 'article-text' in child.get('class', []):
                ids, txts = parse_section(child)
                if ids:
                    idlst[-1].extend(ids); txtlst[-1].extend(txts)
    return title, abstract, keywords, idlst, txtlst

def section_struct(ids, txts):
    node = {'sec_title':'', 'content':[]}
    heads = [int(i[1]) for i in ids if i.startswith('h')] or [7]
    top   = min(heads)
    idxs  = [i for i,x in enumerate(ids) if x.startswith('h') and int(x[1])==top] + [len(ids)]
    for a,b in zip(idxs[:-1], idxs[1:]):
        title = txts[a]
        sub_id, sub_txt = ids[a+1:b], txts[a+1:b]
        if any(i.startswith('h') for i in sub_id):
            node['content'].append(section_struct(sub_id, sub_txt)|{'sec_title':title})
        else:
            node['content'].append({'sec_title':title, 'content':sub_txt})
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

path    = r'F:\html\iop'  # input
txtpath = r'F:prase-html\iop'  # output
logpath = os.path.join(txtpath, 'parse.log')
iftxt   = 1  # Set to 1 if you want to export text files
ifjson  = 1  # Set to 1 if you want to export JSON files

os.makedirs(txtpath, exist_ok=True)
doc_dict = {}

with open(logpath, 'w', encoding='utf-8') as log:
    for file in os.listdir(path):
        if not file.endswith('.html'):
            continue

        filename = file[:-5]
        doi = filename.replace('_', '/')

        print(file); log.write(file)
        try:
            with open(os.path.join(path, file), 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'lxml')

            title, abstract, kw, ids, txts = parse_doc_iop(soup)
            ok = True
            log.write('\n')
        except Exception as e:
            ok = False
            log.write(f' PARSE ERROR: {e}\n')

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

        if ok:
            doc_dict[doi] = doc_struct(title, abstract, kw, ids, txts,
                                       path, file, doi)

if ifjson:
    with open(os.path.join(path, 'data.json'), 'w', encoding='utf-8') as jf:
        json.dump(doc_dict, jf, ensure_ascii=False, indent=2)
