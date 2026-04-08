def grade_easy(state):
    email_read = any(e["read"] for e in state.inbox if e["id"] == "e1")
    if email_read and state.step_count >= 2:
        return 0.95
    return 0.2

def grade_medium(state):
    scheduled = any(e["start"] == "14:00" for e in state.calendar)
    lunch_ok = any(e["start"] == "12:00" for e in state.calendar)
    if scheduled and lunch_ok:
        return 0.95
    return 0.2

def grade_hard(state):
    # Domain changed to match reset data (@pt.com)
    contact_ok = any("client@pt.com" in c["email"].lower() for c in state.contacts)
    event_ok = any(e["start"] == "09:00" for e in state.calendar)
    code_ok = any("PX-99" in e["title"].upper() for e in state.calendar)
    
    if contact_ok and event_ok and code_ok:
        return 0.95
    if event_ok and contact_ok:
        return 0.6
    return 0.2