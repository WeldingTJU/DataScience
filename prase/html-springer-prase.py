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
    text = doc.text.replace('\n', '')
    return text

def parse_ol(doc):
    idlst = []
    textlst = []
    for i, child in enumerate(doc.children):
        if not (child.name is None):
            idlst.append(child.name)
            textlst.append(child.text.replace('\n', ''))
    return idlst, textlst

def parse_section(doc):
    textlst = []
    idlst = []
    skip = []
    title = ''
    for i, child in enumerate(doc.children):
        if child.name == 'div':
            ids = []
            texts = []
            if 'class' in child.attrs.keys():
                if child.attrs['class'][0] == 'c-article-equation__number':
                    ids.append('eq_num')
                    texts.append(child.text)
                elif child.attrs['class'][0] == 'c-article-equation':
                    ids.append('eq')
                    texts.append(child.text)
                else:
                    ids, texts = parse_section(child)
            else:
                ids, texts = parse_section(child)
            idlst.extend(ids)
            textlst.extend(texts)
        elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            title = child.text
            idlst.append(child.name)
            textlst.append(title)
        elif child.name == 'p':
            texts = parse_paragraph(child)
            idlst.append('p')
            textlst.append(texts)
        elif child.name == 'ol':
            ids, texts = parse_ol(child)
            idlst.extend(ids)
            textlst.extend(texts)
    return idlst, textlst

def parse_abstract(abst):
    abstract = ''
    keywords = []
    tmp = abst.find_all('div', class_="c-article-section__content")
    para = tmp[0].find('p')
    abstract = para.text.replace('\n', '')
    kws = tmp[0].find_all('li', class_='c-article-subject-list__subject')
    for k in kws:
        keywords.append(k.text)

    return abstract, keywords

def parse_doc(doc):
    idlst = []
    textlst = []
    title = ''
    abstract = ''
    keywords = []
    tmp = doc.find_all('h1', class_='c-article-title')
    if len(tmp) == 1:
        title = tmp[0].text
    else:
        title = tmp[0].text
        print("Warning: multi title")

    tmp = doc.find_all('section')
    for sec in tmp:
        if 'data-title' in sec.attrs.keys() and not ifskip_section(sec.attrs['data-title']):
            tmp_id, tmp_text = parse_section(sec)
            idlst.append(tmp_id)
            textlst.append(tmp_text)
        elif 'data-title' in sec.attrs.keys() and 'Abstract' in sec.attrs['data-title']:
            abstract, keywords = parse_abstract(sec)

    return title, abstract, keywords, idlst, textlst

def section_struct(ids, texts):
    sec = {'sec_title': '', 'content': []}
    minid = 100
    record = []
    ct = 0
    for i in range(0, len(ids)):
        if ids[i][0] == 'h':
            ct += 1
            current = int(ids[i][1:])
            if current < minid:
                minid = current

    for i in range(0, len(ids)):
        if ids[i][0] == 'h':
            current = int(ids[i][1:])
            if current == minid:
                record.append(i)

    if len(record) == 1:
        for i in range(0, len(ids)):
            if (ids[i][0] == 'h') and (int(ids[i][1:]) == minid):
                sec['sec_title'] = texts[i]
            elif (ids[i][0] == 'h') and (int(ids[i][1:]) > minid):
                tmp = section_struct(ids[i:], texts[i:])
                sec['content'].append(tmp['content'])
                return sec
            else:
                sec['content'].append(texts[i])
        return sec
    else:
        for i in range(0, len(record) - 1):
            sec['content'].append(section_struct(ids[record[i]:record[i + 1]], texts[record[i]:record[i + 1]]))
        sec['content'].append(section_struct(ids[record[-1]:], texts[record[-1]:]))
    return sec

def doc_struct(title, abstract, keywords, ids, texts, path, file, doi):
    doc = {}
    doc['title'] = title
    doc['abstract'] = abstract
    doc['keywords'] = keywords
    doc['path'] = path
    doc['file'] = file
    doc['doi'] = doi
    doc['content'] = []
    for i in range(0, len(ids)):
        doc['content'].append(section_struct(ids[i], texts[i]))
    return doc


path = r'F:\html\10.1007' # input
txtpath = r'F:\prase-html\10.1007' # output
jsonpath = os.path.join(txtpath, 'json')
logpath = os.path.join(txtpath, 'parse.log')

if not os.path.exists(jsonpath):
    os.makedirs(jsonpath)

iftxt = 1  # Set to 1 if you want to export text files
ifjson = 1  # Set to 1 if you want to export JSON files

doc_dict = {}

log = open(logpath, 'w')

for file in os.listdir(path):
    leng = len(file)
    if leng > 5 and file[leng-5:leng] == '.html':
        filename = file[0:leng-5]
        doi = filename.replace("_", "/").replace(":", "_")
        print(file)
        log.write(file + '\n')
        try:
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                doc = BeautifulSoup(f, "lxml")
            title, abstract, keywords, ids, texts = parse_doc(doc)
            ifsuccess = 1
        except:
            ifsuccess = 0
        if iftxt:
            txt_filename = os.path.join(txtpath, filename + '.txt')
            with open(txt_filename, 'w', encoding='utf-8') as fout:
                if ifsuccess:
                    fout.write(title + '\n\n')
                    fout.write('Abstract\n\n')
                    fout.write(abstract + '\n\n')
                    fout.write('Keywords\n\n')
                    for kw in keywords:
                        fout.write(kw + ', ')
                    fout.write('\n\n')
                    for i in range(0, len(texts)):
                        for j in range(0, len(texts[i])):
                            fout.write(texts[i][j] + '\n\n')
                else:
                    fout.write(file + ' PARSE ERROR\n')
        if ifjson:
            doc_info = doc_struct(title, abstract, keywords, ids, texts, path, filename, doi)
            json_filename = os.path.join(jsonpath, filename + '.json')
            with open(json_filename, 'w', encoding='utf-8') as json_file:
                json.dump(doc_info, json_file, ensure_ascii=False, indent=4)
        log.write('\n' if ifsuccess else ' PARSE ERROR\n')

log.close()

if ifjson:
    with open(os.path.join(jsonpath, 'all_data.json'), 'w') as json_file:
        json.dump(doc_dict, json_file, ensure_ascii=False, indent=4)