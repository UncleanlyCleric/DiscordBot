import random

HOSTS = {
    "snarky_ai": {
        "intro": [
            "Oh great. Another round of questionable intelligence."
        ],
        "correct": [
            "Wow. That was disturbingly correct."
        ],
        "wrong": [
            "Nope. That was confidently incorrect."
        ]
    },

    "wizard": {
        "intro": [
            "A mystical question appears before thee..."
        ],
        "correct": [
            "The arcane forces approve."
        ],
        "wrong": [
            "The council of wizards is disappointed."
        ]
    },

    "corporate": {
        "intro": [
            "Let’s measure your cognitive ROI."
        ],
        "correct": [
            "Performance acceptable."
        ],
        "wrong": [
            "This will be noted in your file."
        ]
    }
}

def pick_host():
    return random.choice(list(HOSTS.keys()))