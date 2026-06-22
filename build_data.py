import os
dir_path = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(dir_path, 'cards.json'), 'r', encoding='utf-8') as f:
    json_data = f.read()
with open(os.path.join(dir_path, 'data.js'), 'w', encoding='utf-8') as f:
    f.write('const EMBEDDED_DATA = ')
    f.write(json_data)
    f.write(';')
print('data.js created')