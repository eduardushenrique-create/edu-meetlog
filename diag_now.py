import json, os
from pathlib import Path
from datetime import datetime

app = Path(os.environ['APPDATA']) / 'Edu MeetLog'
q = app / 'queue'

print('=== QUEUE STATE NOW ===')
for d in ['pending','processing','done','failed']:
    p = q / d
    files = sorted(p.glob('*'))
    print(d + '/ (' + str(len(files)) + ' files):')
    for f in files:
        age_min = (datetime.now().timestamp() - f.stat().st_mtime) / 60
        print('  ' + f.name + '  (' + str(f.stat().st_size) + ' bytes, ' + str(int(age_min)) + ' min ago)')

print()
print('=== MEETINGS.JSON ===')
mf = app / 'config' / 'meetings.json'
meetings = json.loads(mf.read_text(encoding='utf-8'))
for m in meetings:
    mid = m.get('id','?')
    status = m.get('status','?')
    name = m.get('name','?')
    print('  ' + mid + '  status=' + status + '  name=' + name)

print()
print('=== SETTINGS ===')
sf = app / 'config' / 'settings.json'
s = json.loads(sf.read_text(encoding='utf-8'))
for k,v in s.items():
    print('  ' + k + '=' + str(v))

print()
print('=== RECORDINGS DIR ===')
rec = app / 'recordings'
for f in sorted(rec.glob('*.wav')):
    age_min = (datetime.now().timestamp() - f.stat().st_mtime) / 60
    size_kb = f.stat().st_size / 1024
    print('  ' + f.name + '  (' + str(int(size_kb)) + 'KB, ' + str(int(age_min)) + ' min ago)')

print()
print('=== TRANSCRIPTS OUTPUT DIR ===')
out = s.get('output_folder','')
if out:
    op = Path(out)
    if op.exists():
        for f in sorted(op.glob('*.json')):
            print('  ' + f.name + '  (' + str(f.stat().st_size) + ' bytes)')
    else:
        print('  DIR DOES NOT EXIST: ' + out)
else:
    print('  No custom output_folder set')
