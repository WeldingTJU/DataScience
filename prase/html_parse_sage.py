# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import os
import json
import re

def ifskip(string):
    flag = 0
    stop = [
        'abbre', 'Bib', 'Ack', 'author', 'affiliation', 'corresponding',
        'editor', 'right', 'info', 'cite', 'url'
    ]
    for sw in stop:
        if sw in string:
            flag = 1
            break
    return flag


def ifskip_section(string):
    stop = [
        'abbreviation', 'references', 'acknow', 'author information',
        'editor information', 'rights and permissions', 'copyright',
        'about this paper', 'abstract', 'additional information', 'ethics',
        'funding', 'notes', 'supplementary', 'about this article', 'avail'
    ]
    string = string.lower()
    for sw in stop:
        if sw in string:
            return 1
    return 0

def parse_paragraph(tag):

    return tag.get_text(separator=' ', strip=True)

def parse_sage_section(sec):

    idlst, textlst = [], []

    heading = sec.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
    if heading:
        idlst.append(heading.name)
        textlst.append(heading.get_text(strip=True))

    for child in sec.children:
        if child == heading:
            continue
        if child.name == 'section':
            # 递归子节
            sub_ids, sub_txts = parse_sage_section(child)
            idlst.extend(sub_ids)
            textlst.extend(sub_txts)
        elif child.name == 'p':
            idlst.append('p')
            textlst.append(parse_paragraph(child))
        elif child.name == 'div' and child.get('role') == 'paragraph':
            idlst.append('p')
            textlst.append(parse_paragraph(child))

    return idlst, textlst

def parse_abstract(article_root):
    abstract, keywords = '', []

    abst_sec = article_root.find('section', id='abstract')
    if abst_sec:
        paras = abst_sec.find_all(['p', 'div'], recursive=False)
        abstract = ' '.join([parse_paragraph(p) for p in paras])

    if not abstract:
        meta_desc = article_root.find('meta', attrs={'name': 'description'})
        if meta_desc:
            abstract = meta_desc.get('content', '').strip()

    kw_sec = article_root.find('section', id='keywords')
    if kw_sec:
        keywords = [a.get_text(strip=True) for a in kw_sec.find_all('a')]
    if not keywords:
        meta_kw = article_root.find('meta', attrs={'name': 'keywords'})
        if meta_kw:
            keywords = [x.strip() for x in meta_kw['content'].split(',') if x.strip()]

    return abstract, keywords

def parse_doc(doc):

    idlst_all, textlst_all = [], []

    article = doc.find('article')
    if not article:
        raise RuntimeError('not find <article>')

    title_tag = article.find('h1')
    if title_tag:
        title = title_tag.get_text(strip=True)
    else:
        tmp = doc.find('div', class_='publicationContentTitle')
        title = tmp.get_text(strip=True) if tmp else doc.title.string

    abstract, keywords = parse_abstract(doc)

    top_secs = article.find_all('section', id=re.compile(r'^sec-\d+$'))
    for sec in top_secs:
        h = sec.find(['h2', 'h3', 'h4', 'h5', 'h6'])
        if h and ifskip_section(h.get_text()):
            continue
        ids, txts = parse_sage_section(sec)
        if ids and txts:
            idlst_all.append(ids)
            textlst_all.append(txts)

    return title, abstract, keywords, idlst_all, textlst_all

def section_struct(ids, texts):
    sec = {'sec_title': '', 'content': []}
    minid = 100
    record = []

    # get the minimum id of paragraph
    for i in range(len(ids)):
        if ids[i][0] == 'h':
            current = int(ids[i][1:])
            minid = min(minid, current)

    for i in range(len(ids)):
        if ids[i][0] == 'h' and int(ids[i][1:]) == minid:
            record.append(i)

    if len(record) <= 1:
        for i in range(len(ids)):
            if ids[i][0] == 'h' and int(ids[i][1:]) == minid:
                sec['sec_title'] = texts[i]
            elif ids[i][0] == 'h' and int(ids[i][1:]) > minid:
                tmp = section_struct(ids[i:], texts[i:])
                sec['content'].append(tmp['content'])
                return sec
            else:
                sec['content'].append(texts[i])
        return sec
    else:
        for i in range(len(record) - 1):
            sec['content'].append(
                section_struct(ids[record[i]:record[i + 1]], texts[record[i]:record[i + 1]]))
        sec['content'].append(
            section_struct(ids[record[-1]:], texts[record[-1]:]))
    return sec


def doc_struct(title, abstract, keywords, ids, texts, path, file, doi):
    doc = {
        'title': title,
        'abstract': abstract,
        'keywords': keywords,
        'path': path,
        'file': file,
        'doi': doi,
        'content': []
    }
    for i in range(len(ids)):
        doc['content'].append(section_struct(ids[i], texts[i]))
    return doc


path = r'F:\html\sage' # input
txtpath = r'F:\prase-html\sage' # output
logpath = os.path.join(txtpath, 'parse.log')
iftxt = 1  # Set to 1 if you want to export text files
ifjson = 1  # Set to 1 if you want to export JSON files

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
            title, abstract, kw, ids, txts = parse_doc(soup)
            ok = True
            log.write(file + '\n')
        except Exception as e:
            ok = False
            log.write(f"{file} PARSE ERROR: {e}\n")

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
