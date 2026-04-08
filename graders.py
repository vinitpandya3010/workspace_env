def grade_easy(state):
    """Goal: Read email e1 and reply with $50."""
    email_read = any(e["read"] for e in state.inbox if e["id"] == "e1")
    if email_read and state.step_count >= 2:
        return 0.9  # Success (must be < 1.0)
    if email_read:
        return 0.4  # Partial progress
    return 0.1      # Failure/Start (must be > 0.0)

def grade_medium(state):
    """Goal: Schedule at 14:00 without conflict."""
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
    elif event_at_9:
        return 0.4
    return 0.1