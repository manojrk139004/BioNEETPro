with open('BioNeet-Pro.html', 'r', encoding='utf-8') as f:
    content = f.read()
import re
for match in re.finditer(r'(js/|css/)[^"\' >]+', content):
    print(match.group())