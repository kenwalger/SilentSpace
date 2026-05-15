"""
SilentSpace Guardian — Meeting Classification Engine

Translates numerical entropy scores into actionable enterprise terminology.
Recommendations are deterministic: same meeting title always yields the same result.
"""

import hashlib

CLASSIFICATIONS = [
    (20,  "Rare Gem: Genuine Human Interaction — Schedule another one next quarter."),
    (40,  "Marginally Justified: Could Be a Loom — We appreciate the effort."),
    (60,  "Calendar Debris: Occupies Space, Creates Little — A real recurring cost."),
    (80,  "Meeting-Shaped Void: Time's Natural Enemy — Cancel with prejudice."),
    (100, "Corporate Heat Death Event: Entropy Made Flesh — This meeting is why people quit."),
]

ASYNC_RECOMMENDATIONS = {
    "none": [
        "Send a well-structured email. People will skim it, but the information will exist.",
        "Post a Confluence page. It will be discovered during someone's offboarding.",
        "Drop a message in Slack. Acknowledge it will be read by 40% of attendees.",
    ],
    "low": [
        "Record a Loom video. Recipients will watch at 1.75x speed with their cameras off.",
        "Create a shared doc with a comment thread. Enables async debate about the agenda.",
        "Send a structured Slack message with clear headers and a 48-hour response window.",
    ],
    "medium": [
        "Convert to a monthly cadence and replace interim slots with a status doc.",
        "Implement a 15-minute stand-up and redirect the remaining time to actual work.",
        "Post a weekly update doc. Ask for thumbs-up reactions, not attendance confirmation.",
    ],
    "high": [
        "Cancel immediately. Send a Slack summary of what was going to be discussed.",
        "This meeting is a symptom. Address the underlying confusion in a written brief.",
        "Recommend the organizer complete an async communication fundamentals module.",
    ],
    "critical": [
        "This meeting should be studied, not attended. Forward to anthropology departments.",
        "Cancel and initiate a post-mortem on how this ended up on six calendars.",
        "Declare a calendar emergency. Block this timeslot for silent, focused work.",
    ],
}


def classify_meeting(waste_score: int) -> str:
    for threshold, label in CLASSIFICATIONS:
        if waste_score <= threshold:
            return label
    return CLASSIFICATIONS[-1][1]


def async_recommendation(meeting: dict, waste_score: int) -> str:
    seed = int(hashlib.md5(meeting.get("title", "").encode()).hexdigest(), 16)

    if waste_score <= 20:
        bucket = "none"
    elif waste_score <= 40:
        bucket = "low"
    elif waste_score <= 60:
        bucket = "medium"
    elif waste_score <= 80:
        bucket = "high"
    else:
        bucket = "critical"

    options = ASYNC_RECOMMENDATIONS[bucket]
    return options[seed % len(options)]
