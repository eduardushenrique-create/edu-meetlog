import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    anchor = """  const [suggestedLabels, setSuggestedLabels] = useState<any[]>([]);
  const [isSuggesting, setIsSuggesting] = useState(false);"""
  
    replacement = """  const [suggestedLabels, setSuggestedLabels] = useState<any[]>([]);
  const [isSuggesting, setIsSuggesting] = useState(false);

  useEffect(() => {
    if (meeting?.suggested_labels && labels) {
      const found = labels.filter(l => meeting.suggested_labels!.includes(l.id));
      const newSuggestions = found.filter(l => !(meeting.labels || []).includes(l.id));
      setSuggestedLabels(newSuggestions);
    } else {
      setSuggestedLabels([]);
    }
  }, [meeting?.id, meeting?.suggested_labels, meeting?.labels, labels]);"""
    
    if anchor in content:
        content = content.replace(anchor, replacement)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated Transcription component with auto-suggested labels effect.")
    else:
        print("Anchor not found!")

if __name__ == "__main__":
    main()
