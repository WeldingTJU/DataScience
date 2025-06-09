# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import os
import json

def ifskip(string):
    flag = 0
    stop = ['abbre', 'Bib', 'Ack', 'author', 'affiliation', 'corresponding',
            'editor', 'right', 'info', 'cite', 'url']
    for sw in stop:
        if sw in string:
            flag = 1
            break
    return flag


def ifskip_section(string):
    flag = 0
    stop = ['abbreviation', 'references', 'acknow', 'author information', 'editor information',
            'rights and permissions', 'copyright information', 'about this paper', 'abstract',
            'additional information', 'ethics', 'funding', 'notes', 'supplementary', 'about this article',
            'avail']
    string = string.lower()
    for sw in stop:
        if sw in string:
            flag = 1
            break
    return flag


def parse_paragraph(doc):
    return doc.text.replace('\n', '').strip()


def parse_ol(doc):
    idlst = []
    textlst = []
    for child in doc.children:
        if not (child.name is None):
            idlst.append(child.name)
            textlst.append(child.text.replace('\n', ''))
    return idlst, textlst


def parse_section(doc):
    textlst = []
    idlst = []
    for child in doc.children:
        if (child.name == 'div') and ('class' in child.attrs) and ('NLM_sec' in child.attrs['class']):
            ids, texts = parse_section(child)
            idlst.extend(ids)
            textlst.extend(texts)
        elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            idlst.append(child.name)
            textlst.append(child.text.strip())
        elif child.name in ['p', 'ul']:
            idlst.append('p')
            textlst.append(child.text.replace('\n', '').strip())
    return idlst, textlst


def parse_abstract(abst):
    abstract = ''
    tmp = abst.find_all('p')
    for para in tmp:
        if hasattr(para, 'attrs') and ('class' in para.attrs) and ('summary-title' in para.attrs['class']):
            continue
        abstract += para.text.replace('\n', '').strip()
    return abstract


def parse_keywords(para):
    keywords = []
    if len(para) == 1:
        tmp = para[0].find_all('a')
        for t in tmp:
            keywords.append(t.text.strip())
    else:
        print('Keyword error')
    return keywords

def parse_doc(doc):
    idlst = []
    textlst = []
    title = ''
    abstract = ''
    keywords = []

    # title
    tmp = doc.find_all('span', class_='hlFld-title')
    if len(tmp) == 1:
        title = tmp[0].text.strip()
    elif len(tmp) == 0:
        print("Warning: no title")
    else:
        title = tmp[0].text.strip()
        print("Warning: multi title")

    # abstract
    tmp0 = doc.find_all('div', class_='abstractSection')
    abstract = parse_abstract(tmp0[0]) if tmp0 else ''

    # keywords
    tmp0 = doc.find_all('div', class_='abstractKeywords')
    keywords = parse_keywords(tmp0) if tmp0 else []

    # sections
    tmp0 = doc.find_all('div', class_='hlFld-Fulltext')
    if tmp0:
        for child in tmp0[0].children:
            if hasattr(child, 'attrs') and ('class' in child.attrs) and ('NLM_sec' in child.attrs['class']):
                tmp_id, tmp_text = parse_section(child)
                idlst.append(tmp_id)
                textlst.append(tmp_text)

    return title, abstract, keywords, idlst, textlst


def section_struct(ids, texts):
    sec = {'sec_title': '', 'content': []}
    minid = 100
    record = []
    for i in range(len(ids)):
        if ids[i][0] == 'h':
            current = int(ids[i][1:])
            if current < minid:
                minid = current

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
            sec['content'].append(section_struct(ids[record[i]:record[i + 1]], texts[record[i]:record[i + 1]]))
        sec['content'].append(section_struct(ids[record[-1]:], texts[record[-1]:]))
    return sec


def doc_struct(title, abstract, keywords, ids, texts, path, file, doi):
    return {
        'title': title,
        'abstract': abstract,
        'keywords': keywords,
        'path': path,
        'file': file,
        'doi': doi,
        'content': [section_struct(ids[i], texts[i]) for i in range(len(ids))]
    }


# === 主程序 ===
path = r'F:\html\taylor'  # input
txtpath = r'F:\prase-html\taylor'  # output
logpath = os.path.join(txtpath, 'parse.log')
iftxt = 1  # Set to 1 if you want to export text files

filelist = os.listdir(path)
doc_dict = {}

with open(logpath, 'w', encoding='utf-8') as log:
    for file in filelist:
        if not file.endswith('.html'):
            continue

        filename = file[:-5]
        doi = filename.replace('_', '/')
        print(file)
        log.write(file)

        try:
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                doc = BeautifulSoup(f, "lxml")
            title, abstract, keywords, ids, texts = parse_doc(doc)
            ifsuccess = True
        except Exception as e:
            print("PARSE ERROR:", e)
            log.write(' PARSE ERROR\n')
            ifsuccess = False

        if iftxt:
            with open(os.path.join(txtpath, filename + '.txt'), 'w', encoding='utf-8') as fout:
                if ifsuccess:
                    doc_dict[doi] = doc_struct(title, abstract, keywords, ids, texts, path, file, doi)
                    log.write('\n')
                    fout.write(f'E:/Data/Literature Data/AM fatigue/{filename}.pdf\n')
                    fout.write(title + '\n')
                    fout.write('Abstract\n' + abstract + '\n')
                    fout.write('Keywords\n' + ', '.join(keywords) + '\n')
                    for i in range(len(texts)):
                        fout.write(f'[Section {i + 1}]\n')
                        for j in range(len(texts[i])):
                            fout.write(f'[{ids[i][j]}]\n{texts[i][j]}\n')
                else:
                    fout.write(file + ' PARSE ERROR\n')

with open(os.path.join(path, 'data.json'), 'w', encoding='utf-8') as f:
    json.dump(doc_dict, f, ensure_ascii=False, indent=2)
