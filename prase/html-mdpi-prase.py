# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import os
import json
from openpyxl import load_workbook, Workbook
import chardet


def ifskip(string):
    flag = 0
    stop = ['abbre', 'Bib', 'Ack', 'author', 'affiliation', 'corresponding', \
            'editor', 'right', 'info', 'cite', 'url']
    for sw in stop:
        if sw in string:
            flag = 1
            break
    return flag


def ifskip_section(string):
    flag = 0
    stop = ['abbreviation', 'references', 'acknow', 'author information', 'editor information', \
            'rights and permissions', 'copyright information', 'about this paper', 'abstract', \
            'additional information', 'ethics', 'funding', 'notes', 'supplementary', 'about this article', \
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
    title = ''
    for i, child in enumerate(doc.children):
        if (child.name == 'section'):
            ids = []
            texts = []
            ids, texts = parse_section(child)
            idlst.extend(ids)
            textlst.extend(texts)
        elif child.name == 'h1' or child.name == 'h2' or child.name == 'h3' or \
                child.name == 'h4' or child.name == 'h5' or child.name == 'h6':
            title = child.text
            idlst.append(child.name)
            textlst.append(title)
        elif (child.name == 'div') and ('class' in child.attrs.keys()) and ('html-p' in child.attrs['class']):
            texts = child.text.replace('\n', '')
            idlst.append('p')
            textlst.append(texts)

    return idlst, textlst


def parse_abstract(abst):
    abstract = ''
    for para in abst:
        abstract += para.text.replace('\n', '')
    return abstract


def parse_keywords(para):
    keywords = []
    if len(para) == 1:
        tmp = para[0].find('span', {'itemprop': ['keywords']})
        if len(tmp) > 0:
            keywords = tmp.text.split(';')
        for i in range(0, len(keywords)):
            keywords[i] = keywords[i].strip()
    else:
        print('Keyword error')
    return keywords


def parse_doc(doc):
    idlst = []
    textlst = []
    title = ''
    abstract = ''
    keywords = []

    # get title
    tmp = doc.find_all('h1', class_='title hypothesis_container')
    if len(tmp) == 1:
        title = tmp[0].text.strip()
    elif len(tmp) == 0:
        print("Warning: no title")
    else:
        title = tmp[0].text.strip()
        print("Warning: multi title")

    # get abstract
    tmp0 = doc.find_all('div', class_='art-abstract')
    abst = parse_abstract(tmp0)
    abstract = abst
    tmp0 = doc.find_all('div', class_='art-keywords')
    kw = parse_keywords(tmp0)
    keywords = kw

    # get sections
    tmp0 = doc.find_all('div', class_='html-body')
    if len(tmp0) > 0:
        tmp = tmp0[0].find_all('section')
        for sec in tmp:
            tmp1 = sec.find('h2', {'data-nested': ['1', ]})
            if not tmp1 is None:
                tmp_id, tmp_text = parse_section(sec)
                idlst.append(tmp_id)
                textlst.append(tmp_text)

    return title, abstract, keywords, idlst, textlst


def section_struct(ids, texts):
    sec = {'sec_title': '', 'content': []}
    minid = 100
    record = []

    # Get the minimum id of paragraph
    for i in range(0, len(ids)):
        if ids[i][0] == 'h':
            current = int(ids[i][1:])
            if current < minid:
                minid = current

    for i in range(0, len(ids)):
        if ids[i][0] == 'h':
            current = int(ids[i][1:])
            if current == minid:
                record.append(i)

    if len(record) <= 1:
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

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding']


def parse_html_file(file_path):
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as f:
        soup = BeautifulSoup(f, 'lxml')
    return soup


def process_directory(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.html'):
            input_file_path = os.path.join(input_dir, filename)
            output_file_path = os.path.join(output_dir, f"{filename}.txt")

            print(f"Processing: {filename}")

            try:
                doc = parse_html_file(input_file_path)
                title, abstract, keywords, ids, texts = parse_doc(doc)
                ifsuccess = 1
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue

            # 保存解析结果
            with open(output_file_path, 'w', encoding='utf-8') as fout:
                fout.write(title + '\n\n')
                fout.write('Abstract\n\n')
                fout.write(abstract + '\n\n')
                fout.write('Keywords\n\n')
                fout.write(', '.join(keywords) + '\n\n')
                fout.write('Content\n\n')
                for i in range(0, len(texts)):
                    for j in range(0, len(texts[i])):
                        fout.write(texts[i][j] + '\n\n')


if __name__ == "__main__":
    input_directory = r"F:\html\10.3390"  # input
    output_directory = r"F:\prase-html\10.3390"  # output

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    process_directory(input_directory, output_directory)
    print("Parsing completed.")
