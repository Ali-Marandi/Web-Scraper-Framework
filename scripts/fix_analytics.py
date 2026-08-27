with open('/home/z/my-project/Web-Scraper-Framework/WebScraperPro/ui/panels/analytics_panel.py', 'r') as f:
    lines = f.readlines()

result = []
i = 0
changed = 0
while i < len(lines):
    line = lines[i]
    if i + 1 < len(lines):
        qcount = line.count('"')
        is_odd = qcount % 2 == 1
        next_stripped = lines[i + 1].strip()
        # Next line should be just a closing quote and paren: ") or just "
        if is_odd and next_stripped in ('"', '")'):
            result.append(line.rstrip() + '\n"\n')
            i += 2
            changed += 1
            continue
    result.append(line)
    i += 1

with open('/home/z/my-project/Web-Scraper-Framework/WebScraperPro/ui/panels/analytics_panel.py', 'w') as f:
    f.writelines(result)

print(f'Processed {len(lines)} lines, fixed {changed}')