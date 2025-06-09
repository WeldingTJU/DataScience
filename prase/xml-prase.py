import os
import xml.etree.ElementTree as ET
import json
import re

input_folder = r'F:\elsevier-xml'  # input
output_txt_folder = r'F:\prase-xml'  # output
output_json_folder = os.path.join(output_txt_folder, 'json')

os.makedirs(output_txt_folder, exist_ok=True)
os.makedirs(output_json_folder, exist_ok=True)

ns = {
    'dcterms': 'http://purl.org/dc/terms/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'ce': 'http://www.elsevier.com/xml/common/dtd',
    'xocs': 'http://www.elsevier.com/xml/xocs/dtd'
}

def clean_text(text):
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

for filename in os.listdir(input_folder):
    if filename.endswith('.xml'):
        input_file = os.path.join(input_folder, filename)

        tree = ET.parse(input_file)
        root = tree.getroot()

        title = root.find('.//dc:title', ns).text if root.find('.//dc:title', ns) is not None and root.find(
            './/dc:title', ns).text is not None else ''
        abstract = clean_text(root.find('.//dc:description', ns).text) if root.find('.//dc:description',
                                                                                    ns) is not None and root.find(
            './/dc:description', ns).text is not None else ''
        keywords = [kw.text for kw in root.findall('.//dcterms:subject', ns) if kw is not None and kw.text is not None]

        raw_text_elem = root.find('.//xocs:rawtext', ns)
        if raw_text_elem is not None and raw_text_elem.text is not None:
            body_content = clean_text(raw_text_elem.text)
        else:
            body_content_list = []
            for section in root.findall('.//ce:section', ns):
                section_text = ''.join(section.itertext()) if section is not None else ''
                if section_text:
                    body_content_list.append(clean_text(section_text))
            body_content = '\n\n'.join(body_content_list) if body_content_list else 'No body content found'



        output_txt_file = os.path.join(output_txt_folder, f"{os.path.splitext(filename)[0]}.txt")
        output_json_file = os.path.join(output_json_folder, f"{os.path.splitext(filename)[0]}.json")

        with open(output_txt_file, 'w', encoding='utf-8') as file:
            file.write(f"Title: {title}\n\n")
            file.write(f"Abstract: {abstract}\n\n")
            file.write("Keywords: " + ", ".join(keywords) + "\n\n")
            file.write(body_content)

        data = {"Title": title, "Abstract": abstract, "Keywords": keywords, "Body Content": body_content}

        with open(output_json_file, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        print(f"Parsing completed：{filename}")

print(f"Literature parsing completed and saved to {output_txt_folder} and {output_json_folder}")
