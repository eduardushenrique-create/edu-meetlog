import os

def main():
    file_path = r"c:\PROJETOS\edu-meetlog\backend\main.py"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Import audit log
    import_anchor = "from transcription.merge_engine import TranscriptMergeEngine"
    import_replacement = "from transcription.merge_engine import TranscriptMergeEngine\nfrom audit_log import log_audit_event"
    
    if import_anchor in content and "from audit_log import log_audit_event" not in content:
        content = content.replace(import_anchor, import_replacement)

    # 1. Labels Create
    lbl_create_anchor = """    labels.append(label.dict())
    save_labels(labels)
    return {"success": True}"""
    lbl_create_repl = """    labels.append(label.dict())
    save_labels(labels)
    log_audit_event("CREATE_LABEL", {"label_id": label.id, "name": label.name})
    return {"success": True}"""
    if lbl_create_anchor in content: content = content.replace(lbl_create_anchor, lbl_create_repl)

    # 2. Labels Delete
    lbl_del_anchor = """    save_labels([l for l in load_labels() if l["id"] != label_id])
    return {"success": True}"""
    lbl_del_repl = """    save_labels([l for l in load_labels() if l["id"] != label_id])
    log_audit_event("DELETE_LABEL", {"label_id": label_id})
    return {"success": True}"""
    if lbl_del_anchor in content: content = content.replace(lbl_del_anchor, lbl_del_repl)

    # 3. Update Meeting Labels
    mtg_lbl_anchor = """    save_meetings(meetings)
    return {"success": True}"""
    mtg_lbl_repl = """    save_meetings(meetings)
    log_audit_event("UPDATE_MEETING_LABELS", {"meeting_id": meeting_id, "labels": update.label_ids})
    return {"success": True}"""
    # Wait, there are multiple `save_meetings(meetings); return {"success": True}` blocks!
    # Let's be more specific.
    mtg_lbl_specific_anchor = """def update_meeting_labels(meeting_id: str, update: MeetingLabelsUpdate):
    meetings = load_meetings()
    for m in meetings:
        if m["id"] == meeting_id:
            m["labels"] = update.label_ids
            break
    save_meetings(meetings)
    return {"success": True}"""
    mtg_lbl_specific_repl = """def update_meeting_labels(meeting_id: str, update: MeetingLabelsUpdate):
    meetings = load_meetings()
    for m in meetings:
        if m["id"] == meeting_id:
            m["labels"] = update.label_ids
            break
    save_meetings(meetings)
    log_audit_event("UPDATE_MEETING_LABELS", {"meeting_id": meeting_id, "labels": update.label_ids})
    return {"success": True}"""
    if mtg_lbl_specific_anchor in content: content = content.replace(mtg_lbl_specific_anchor, mtg_lbl_specific_repl)

    # 4. Bulk Delete
    bulk_del_anchor = """    save_meetings([m for m in meetings if m["id"] not in to_delete])
    return {"success": True, "deleted": len(to_delete)}"""
    bulk_del_repl = """    save_meetings([m for m in meetings if m["id"] not in to_delete])
    log_audit_event("BULK_DELETE_MEETINGS", {"count": len(to_delete), "meeting_ids": list(to_delete)})
    return {"success": True, "deleted": len(to_delete)}"""
    if bulk_del_anchor in content: content = content.replace(bulk_del_anchor, bulk_del_repl)

    # 5. Bulk Archive
    bulk_arch_anchor = """    save_meetings(meetings)
    return {"success": True, "archived": len(to_archive)}"""
    bulk_arch_repl = """    save_meetings(meetings)
    log_audit_event("BULK_ARCHIVE_MEETINGS", {"count": len(to_archive), "meeting_ids": list(to_archive)})
    return {"success": True, "archived": len(to_archive)}"""
    if bulk_arch_anchor in content: content = content.replace(bulk_arch_anchor, bulk_arch_repl)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Audit logging applied to main.py")

if __name__ == "__main__":
    main()
