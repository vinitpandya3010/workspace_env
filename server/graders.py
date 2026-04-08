# server/graders.py

def grade_easy(state):
    """Goal: Read email e1 and reply."""
    email_read = any(e["read"] for e in state.inbox if e["id"] == "e1")
    if email_read and state.step_count >= 2:
        return 0.9  # Success
    if email_read:
        return 0.4  # Progress
    return 0.1      # Started

def grade_medium(state):
    """Goal: Schedule at 14:00."""
    scheduled_correctly = any(e["start"] == "14:00" for e in state.calendar)
    lunch_intact = any(e["start"] == "12:00" for e in state.calendar)
    if scheduled_correctly and lunch_intact:
        return 0.9
    elif scheduled_correctly:
        return 0.5
    return 0.1

def grade_hard(state):
    """Goal: Contact + Code + Event."""
    contact_added = any("client@partner.com" in c["email"].lower() for c in state.contacts)
    event_at_9 = any(e["start"] == "09:00" for e in state.calendar)
    used_code = any("PX-99" in e["title"].upper() for e in state.calendar)
    if contact_added and event_at_9 and used_code:
        return 0.9
    elif event_at_9 and contact_added:
        return 0.7
    return 0.1