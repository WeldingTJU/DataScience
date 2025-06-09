import os
import xml.etree.ElementTree as ET

def extract_full_text(entry):
    texts = []
    if entry.text:
        texts.append(entry.text.strip())
    for child in entry.iter():
        if child is not entry and child.text:
            texts.append(child.text.strip())
    return ' '.join(texts)

def extract_math_text(entry):
    texts = []
    for child in entry.iter():
        if child.tag.endswith('mi') or child.tag.endswith('mn') or child.tag.endswith('mo') or child.tag.endswith('msup') or child.tag.endswith('msub'):
            if child.text:
                texts.append(child.text.strip())
    return ' '.join(texts)

def extract_footnotes(table, namespace_common):
    footnotes = []

    footnote = table.findall(f'.//{{{namespace_common}}}footnote')
    for note in footnote:
        footnotes.append(f'Footnote: {extract_full_text(note)}')

    table_footnote = table.find(f'.//{{{namespace_common}}}table-footnote')
    if table_footnote is not None:
        footnotes.append(f'Table footnotes: {extract_full_text(table_footnote)}')

    return footnotes

source_folder = r'F:\elsevier-xml'
target_folder = r'F:\table-xml'

namespace_common = 'http://www.elsevier.com/xml/common/dtd'
namespace_cals = 'http://www.elsevier.com/xml/common/cals/dtd'

for filename in os.listdir(source_folder):
    if filename.endswith('.xml'):
        source_file_path = os.path.join(source_folder, filename)
        target_file_path = os.path.join(target_folder, filename.replace('.xml', '.txt'))

        if os.path.exists(target_file_path):
            tree = ET.parse(source_file_path)
            root = tree.getroot()
            tables = root.findall(f'.//{{{namespace_common}}}table')

            with open(target_file_path, 'a', encoding='utf-8') as f:
                f.write('\n')
                for table in tables:
                    label = table.find(f'.//{{{namespace_common}}}label')
                    if label is not None:
                        table_title = extract_full_text(label)

                    footnotes = extract_footnotes(table, namespace_common)
                    for note in footnotes:
                        f.write(note + '\n')

                    caption = table.find(f'.//{{{namespace_common}}}caption')
                    if caption is not None:
                        simple_para = caption.find(f'.//{{{namespace_common}}}simple-para')
                        if simple_para is not None:
                            title_text = extract_full_text(simple_para)
                            f.write(f'{table_title} : {title_text}\n')

                    thead = table.find(f'.//{{{namespace_cals}}}thead')
                    if thead is not None:
                        headers = []
                        units = []

                        for row in thead.findall(f'{{{namespace_cals}}}row'):
                            row_headers = [extract_full_text(entry) for entry in
                                           row.findall(f'{{{namespace_common}}}entry')]
                            headers.extend(row_headers)

                        combined_headers = []
                        for header in headers:
                            combined_headers.append(header)

                        f.write('Header row: ' + ' | '.join(combined_headers) + '\n')

                    tbody = table.find(f'.//{{{namespace_cals}}}tbody')
                    if tbody is not None:
                        for row in tbody.findall(f'{{{namespace_cals}}}row'):
                            row_data = []
                            for entry in row.findall(f'{{{namespace_common}}}entry'):
                                full_text = extract_full_text(entry)
                                if entry.find('.//{http://www.w3.org/1998/Math/MathML}math') is not None:
                                    math_text = extract_math_text(entry)
                                    row_data.append(math_text)
                                else:
                                    row_data.append(full_text)
                            f.write('Data row: ' + ' | '.join(row_data) + '\n')

                    f.write('\n')

print(f'Table information has been extracted and appended to the corresponding TXT file.')
