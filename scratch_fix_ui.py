import re

def fix_app_tsx():
    with open('c:/Users/eduar/OneDrive/Desktop/Edu MeetLog/src/App.tsx', 'r', encoding='utf-8') as f:
        content = f.read()

    target = "          {['#ef4444', '#f59e0b', '#22c55e'].map((color) => (\n            <span key={color} className=\"traffic-light\" style={{ background: color }} />\n          ))}"

    replacement = """          {['#ef4444', '#f59e0b', '#22c55e'].map((color) => {
            const isClose = color === '#ef4444';
            const isMinimize = color === '#f59e0b';
            const isMaximize = color === '#22c55e';
            const action = isClose ? window.electronAPI?.closeWindow :
                           isMinimize ? window.electronAPI?.minimizeWindow :
                           isMaximize ? window.electronAPI?.maximizeWindow : undefined;
            return <span key={color} className="traffic-light" style={{ background: color, cursor: 'pointer' }} onClick={action} />
          })}"""

    content = content.replace(target, replacement)
    content = content.replace(target.replace('\n', '\r\n'), replacement)

    with open('c:/Users/eduar/OneDrive/Desktop/Edu MeetLog/src/App.tsx', 'w', encoding='utf-8') as f:
        f.write(content)

fix_app_tsx()
print("Fixed App.tsx")
