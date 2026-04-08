def grade_easy(state):
    """
    Goal: Read email e1 and reply with the correct price ($50).
    """
    # 1. Was the email actually read?
    email_read = any(e["read"] for e in state.inbox if e["id"] == "e1")
    
    # 2. Did the agent take enough steps to have actually sent a reply?
    # (In our environment, the task ends ('done=True') when SEND/REPLY is called)
    task_completed = state.step_count >= 2
    
    if email_read and task_completed:
        return 1.0
    return 0.0

def grade_medium(state):
    """
    Goal: Check calendar for conflicts and schedule 'Sync' at 14:00.
    """
    # 1. Did the agent find the free slot at 14:00 (2pm)?
    # We check if an event starting at 14:00 exists.
    scheduled_correctly = any(e["start"] == "14:00" for e in state.calendar)
    
    # 2. Did they avoid deleting the existing lunch event?
    lunch_intact = any(e["start"] == "12:00" for e in state.calendar)
    
    if scheduled_correctly and lunch_intact:
        return 1.0
    elif scheduled_correctly:
        return 0.5 # They scheduled it, but maybe messed up the calendar
    return 0.0

def grade_hard(state):
    contact_added = any("client@partner.com" in c["email"].lower() for c in state.contacts)
    event_at_9 = any(e["start"] == "09:00" for e in state.calendar)
    used_code = any("PX-99" in e["title"].upper() for e in state.calendar)
    
    if contact_added and event_at_9 and used_code:
        return 1.0
    elif event_at_9 and contact_added:
        return 0.7
    elif event_at_9:
        return 0.4
    return 0.0