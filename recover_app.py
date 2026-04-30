import os
import re

log_path = r"C:\Users\eduar\.gemini\antigravity\brain\1a36e58f-5435-47f8-87a0-54f1629b0caf\.system_generated\logs\overview.txt"

with open(log_path, 'r', encoding='utf-8') as f:
    log_content = f.read()

# We need to extract the view_file blocks for src/App.tsx
# The output starts with "File Path: `file:///c:/PROJETOS/edu-meetlog/src/App.tsx`"
# And then lines like "1: import { useState, useEffect, useRef } from 'react';"

blocks = []
in_block = False
current_block = []

for line in log_content.split('\n'):
    if "File Path: `file:///c:/PROJETOS/edu-meetlog/src/App.tsx`" in line:
        in_block = True
        current_block = []
        continue
    
    if in_block:
        if line.startswith("The above content shows") or line.startswith("The above content does NOT show"):
            in_block = False
            blocks.append(current_block)
            continue
            
        # Match lines like "1: import ..."
        m = re.match(r'^(\d+): (.*)$', line)
        if m:
            current_block.append((int(m.group(1)), m.group(2)))

if not blocks:
    print("Could not find blocks in log.")
    exit(1)

# Sort all lines by line number to ensure proper reconstruction
all_lines = {}
for block in blocks:
    for line_num, content in block:
        all_lines[line_num] = content

if not all_lines:
    print("No lines extracted.")
    exit(1)

max_line = max(all_lines.keys())
print(f"Recovered {len(all_lines)} unique lines out of max {max_line}")

with open(r"c:\PROJETOS\edu-meetlog\src\App.tsx", 'w', encoding='utf-8') as f:
    for i in range(1, max_line + 1):
        # We assume there are no gaps, but if there are we write empty string (shouldn't happen)
        f.write(all_lines.get(i, '') + '\n')

print("Recovery complete.")
