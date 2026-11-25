"""Named motions for a four-servo desktop robot.

Servos, all in degrees from 0 to 180:
  base     — turntable
  shoulder — upper arm
  elbow    — forearm
  gripper  — 0 closed, 180 open
"""


def frame(base, shoulder, elbow, gripper, duration_ms, label):
    return {
        "label": label,
        "duration_ms": duration_ms,
        "servos": {
            "base": base,
            "shoulder": shoulder,
            "elbow": elbow,
            "gripper": gripper,
        },
    }


def home_frame(duration_ms=350, label="Return home"):
    return frame(90, 90, 90, 40, duration_ms, label)


PRIMITIVES = [
    {
        "id": "wave",
        "title": "Wave",
        "description": (
            "wave hello, greet a person, say hi, goodbye wave, "
            "friendly wave of the hand or arm"
        ),
        "frames": [
            frame(90, 48, 40, 20, 400, "Raise the arm"),
            frame(68, 46, 36, 20, 280, "Wave left"),
            frame(112, 46, 36, 20, 280, "Wave right"),
            frame(68, 46, 36, 20, 280, "Wave left again"),
            frame(90, 55, 48, 24, 320, "Settle the wave"),
        ],
    },
    {
        "id": "pick",
        "title": "Pick up",
        "description": (
            "pick up. grab and lift. grasp the object and raise it upward."
        ),
        "frames": [
            frame(90, 122, 42, 90, 450, "Reach and open"),
            frame(90, 128, 36, 12, 350, "Close the gripper"),
            frame(90, 62, 52, 12, 450, "Lift the object"),
        ],
    },
    {
        "id": "place",
        "title": "Place",
        "description": (
            "put down. place down. lower the object and release it onto the table."
        ),
        "frames": [
            frame(90, 120, 40, 12, 420, "Lower the object"),
            frame(90, 124, 38, 90, 320, "Open and release"),
            frame(90, 84, 78, 40, 380, "Pull the arm back"),
        ],
    },
    {
        "id": "point",
        "title": "Point",
        "description": (
            "point at something, indicate a direction, show where to look, "
            "extend one arm toward a target"
        ),
        "frames": [
            frame(48, 72, 24, 16, 420, "Extend and point"),
            frame(48, 70, 22, 16, 500, "Hold the point"),
            home_frame(360, "Lower the arm"),
        ],
    },
    {
        "id": "bow",
        "title": "Bow",
        "description": (
            "bow, take a bow, polite greeting, bend forward to show respect"
        ),
        "frames": [
            frame(90, 132, 108, 30, 500, "Bow forward"),
            frame(90, 136, 112, 30, 450, "Hold the bow"),
            home_frame(420, "Rise"),
        ],
    },
    {
        "id": "nod",
        "title": "Nod",
        "description": "nod yes, agree, nod the head up and down to say yes",
        "frames": [
            frame(90, 70, 112, 40, 260, "Nod down"),
            frame(90, 102, 78, 40, 260, "Nod up"),
            frame(90, 70, 112, 40, 260, "Nod down again"),
            home_frame(280, "Center"),
        ],
    },
    {
        "id": "shake",
        "title": "Shake no",
        "description": "shake head no, disagree, turn from side to side to say no",
        "frames": [
            frame(58, 90, 90, 40, 260, "Turn left"),
            frame(122, 90, 90, 40, 260, "Turn right"),
            frame(58, 90, 90, 40, 260, "Turn left again"),
            home_frame(280, "Face forward"),
        ],
    },
    {
        "id": "handshake",
        "title": "Handshake",
        "description": (
            "handshake, shake hands with someone, offer a hand, greet with a clasp"
        ),
        "frames": [
            frame(90, 82, 32, 78, 400, "Offer an open hand"),
            frame(90, 84, 30, 14, 280, "Close for the clasp"),
            frame(82, 86, 34, 14, 220, "Pump down"),
            frame(98, 80, 28, 14, 220, "Pump up"),
            frame(90, 88, 70, 40, 360, "Release"),
        ],
    },
    {
        "id": "scan",
        "title": "Scan",
        "description": (
            "look around, scan the room, search the area, turn and inspect"
        ),
        "frames": [
            frame(42, 78, 70, 40, 420, "Look left"),
            frame(90, 74, 66, 40, 360, "Look ahead"),
            frame(138, 78, 70, 40, 420, "Look right"),
            home_frame(340, "Face forward"),
        ],
    },
    {
        "id": "celebrate",
        "title": "Celebrate",
        "description": (
            "celebrate, cheer, victory, dance, raise both the mood and the arm"
        ),
        "frames": [
            frame(90, 38, 28, 18, 280, "Throw the arm up"),
            frame(62, 44, 36, 16, 240, "Cheer left"),
            frame(118, 44, 36, 16, 240, "Cheer right"),
            frame(90, 34, 24, 12, 280, "Hold the celebration"),
        ],
    },
    {
        "id": "push",
        "title": "Push",
        "description": (
            "push an object, press a button, poke forward, nudge something away"
        ),
        "frames": [
            frame(90, 100, 50, 18, 320, "Line up the hand"),
            frame(90, 118, 28, 14, 280, "Push forward"),
            frame(90, 88, 80, 40, 340, "Retract"),
        ],
    },
    {
        "id": "rest",
        "title": "Rest",
        "description": (
            "go home. return home. rest. stop moving and hold still"
        ),
        "frames": [
            home_frame(480, "Rest at home"),
        ],
    },
]


# Webcam actions. Kept separate from the typed catalog so a punch is not
# matched against "wave" or "pick up".
FIGHT_ACTIONS = [
    {
        "id": "punch",
        "title": "Punch",
        "description": "a person throws a punch, fist flying forward",
        "frames": [
            frame(90, 78, 70, 8, 160, "Chamber the fist"),
            frame(90, 118, 18, 6, 140, "Punch forward"),
            frame(90, 120, 14, 6, 160, "Hold the punch"),
            frame(90, 90, 90, 40, 260, "Pull the fist back"),
        ],
    },
    {
        "id": "block",
        "title": "Block",
        "description": "a person blocks a hit with a forearm raised in guard",
        "frames": [
            frame(72, 42, 48, 18, 200, "Raise the guard"),
            frame(64, 36, 40, 14, 340, "Hold the block"),
            home_frame(260, "Lower the guard"),
        ],
    },
    {
        "id": "dodge",
        "title": "Dodge",
        "description": "a person dodges sideways and leans out of the way",
        "frames": [
            frame(38, 102, 82, 30, 160, "Slip to the side"),
            frame(32, 108, 88, 30, 260, "Stay out of the line"),
            home_frame(260, "Return to center"),
        ],
    },
    {
        "id": "idle",
        "title": "Still",
        "description": "a person standing still with arms down, not moving",
        "frames": [
            home_frame(480, "Hold still"),
        ],
    },
]
