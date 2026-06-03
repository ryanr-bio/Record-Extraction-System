import json

def check_progress(jsonfile):
    try:
        with open(jsonfile, "r") as f:
            data = json.load(f)
            completed = set(data.get("completed_ids", []))
    except (json.JSONDecodeError, FileNotFoundError):
        completed = set()
    return completed

def save_progress(jsonfile, comp_id):
    completed = check_progress(jsonfile)
    completed.add(int(comp_id))
    with open(jsonfile, "w") as f:
        json.dump({"completed_ids": list(completed)}, f)
