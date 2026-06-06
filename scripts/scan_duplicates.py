import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
SEARCH_DIRS = [
    os.path.join(ROOT, 'templates'),
    os.path.join(ROOT, 'exams', 'templates'),
]

def scan_files():
    report_lines = []
    id_map = defaultdict(list)
    script_includes = defaultdict(list)

    for base in SEARCH_DIRS:
        for dirpath, dirs, files in os.walk(base):
            for fn in files:
                if not fn.endswith(('.html', '.js', '.css')):
                    continue
                path = os.path.join(dirpath, fn)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                except Exception as e:
                    report_lines.append(f'ERROR reading {path}: {e}')
                    continue

                # consecutive duplicate lines
                for i in range(len(lines)-1):
                    if lines[i].strip() and lines[i].strip() == lines[i+1].strip():
                        report_lines.append(f'CONSECUTIVE DUPLICATE in {path} at lines {i+1}-{i+2}: "{lines[i].strip()}"')

                # ids
                for i, line in enumerate(lines, start=1):
                    for m in re.finditer(r'id\s*=\s*"([^"]+)"', line):
                        id_map[m.group(1)].append((path, i))
                    # script includes
                    for m in re.finditer(r'<script[^>]*src="([^"]+)"', line):
                        script_includes[m.group(1)].append((path, i))

    # report duplicate ids
    for _id, occ in id_map.items():
        if len(occ) > 1:
            report_lines.append(f'DUPLICATE ID "{_id}" used {len(occ)} times:')
            for p, ln in occ:
                report_lines.append(f'  - {p}#L{ln}')

    # report duplicate script includes
    for src, occ in script_includes.items():
        if len(occ) > 1:
            report_lines.append(f'DUPLICATE SCRIPT include "{src}" used {len(occ)} times:')
            for p, ln in occ:
                report_lines.append(f'  - {p}#L{ln}')

    out_path = os.path.join(ROOT, 'duplicates_report.txt')
    with open(out_path, 'w', encoding='utf-8') as outf:
        if not report_lines:
            outf.write('No duplicates found.\n')
        else:
            outf.write('\n'.join(report_lines))

    print('Scan complete. Report written to', out_path)

if __name__ == '__main__':
    scan_files()
