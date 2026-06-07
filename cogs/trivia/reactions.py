import random
import time


def clamp(n, a, b):
    return max(a, min(b, n))


HOST_REACTIONS = {
    "snark": {
        "correct": [
            "Fine. You got it right. Don’t let it go to your head.",
            "Correct. I’m filing this under ‘accidental competence.’",
            "Wow. A functioning brain cell appeared."
        ],
        "wrong": [
            "Nope. That was confidently incorrect.",
            "I admire your commitment to being wrong.",
            "That answer should be studied. And avoided."
        ],
        "fast": [
            "Speedy, but unfortunately still wrong.",
            "You answered that like your keyboard was on fire."
        ],
        "slow_correct": [
            "You got it… eventually.",
            "That delay was emotionally concerning, but correct."
        ]
    },

    "wizard": {
        "correct": [
            "The arcane forces nod in approval.",
            "The scroll of wisdom glows faintly… correct."
        ],
        "wrong": [
            "The spirits recoil from that answer.",
            "A curse has been placed upon your confidence."
        ],
        "fast": [
            "Impulsive magic rarely ends well…"
        ]
    },

    "corporate": {
        "correct": [
            "Meets expectations.",
            "Performance acceptable.",
            "Logged as ‘correct response.’"
        ],
        "wrong": [
            "This will be noted in your file.",
            "Deviation from expected output detected."
        ],
        "fast": [
            "Rapid response noted."
        ]
    }
}