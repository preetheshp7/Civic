def get_department(issue):
    issue = issue.lower()

    if "pothole" in issue:
        return "road Maintenance"
    elif "garbage" in issue:
        return "sanitation"
    else:
        return "general services"