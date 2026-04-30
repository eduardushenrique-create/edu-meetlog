import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\src\App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    anchor_archive = """  const handleBulkArchive = async (ids: string[]) => {
    try {"""
    replacement_archive = """  const handleBulkArchive = async (ids: string[]) => {
    if (!window.confirm(`Tem certeza que deseja arquivar ${ids.length} transcrição(ões)?`)) return;
    try {"""
    
    anchor_delete = """  const handleBulkDelete = async (ids: string[]) => {
    try {"""
    replacement_delete = """  const handleBulkDelete = async (ids: string[]) => {
    if (!window.confirm(`ATENÇÃO: A exclusão é definitiva! Tem certeza que deseja deletar ${ids.length} transcrição(ões)?`)) return;
    try {"""
    
    if anchor_archive in content:
        content = content.replace(anchor_archive, replacement_archive)
    if anchor_delete in content:
        content = content.replace(anchor_delete, replacement_delete)
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Confirms successfully added to bulk actions.")

if __name__ == "__main__":
    main()
