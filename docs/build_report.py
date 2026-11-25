"""Build the Milestone 1 diagram, database evidence, and two-page report."""

import sqlite3
from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(__file__).resolve().parent
DB = ROOT / "backend" / "instance" / "motionmind.db"

INK = (28, 24, 20)
MUTED = (90, 78, 66)
PAPER = (246, 241, 231)
COPPER = (184, 101, 46)
SAGE = (70, 110, 86)
LINE = (210, 198, 180)
WHITE = (255, 252, 247)


def font(size, bold=False):
    name = "Supplemental/Arial Bold.ttf" if bold else "Supplemental/Arial.ttf"
    path = Path("/System/Library/Fonts") / name
    if not path.exists():
        return ImageFont.load_default()
    return ImageFont.truetype(str(path), size)


def architecture():
    image = Image.new("RGB", (1400, 760), PAPER)
    draw = ImageDraw.Draw(image)
    title = font(36, True)
    label = font(26, True)
    small = font(20)
    draw.text((48, 36), "MotionMind — Milestone 1 architecture", fill=INK, font=title)
    draw.text(
        (48, 86),
        "Two origins. Auth, planning, admin, and the model are modules inside the API.",
        fill=MUTED,
        font=small,
    )

    def box(xy, wh, heading, lines, fill=WHITE):
        x, y = xy
        w, h = wh
        draw.rounded_rectangle((x, y, x + w, y + h), radius=22, fill=fill, outline=LINE, width=3)
        draw.text((x + 24, y + 20), heading, fill=INK, font=label)
        cursor = y + 64
        for line in lines:
            draw.text((x + 24, cursor), line, fill=MUTED, font=small)
            cursor += 30

    box(
        (48, 160),
        (360, 250),
        "Client  :5173",
        ["Separate origin", "Register and login", "User lab", "Administrator desk"],
    )
    box(
        (500, 140),
        (430, 430),
        "API server  :5001",
        [
            "Separate origin",
            "",
            "Modules in this process:",
            "• Authentication (bcrypt, JWT cookie)",
            "• Motion plans",
            "• Administrator checks",
            "• Usage tracker",
            "• VideoPrism text encoder",
        ],
    )
    box((1020, 160), (332, 180), "SQLite", ["Separate data store", "users", "motion_plans", "api_usage"])
    box(
        (1020, 390),
        (332, 180),
        "Local model files",
        ["VideoPrism-LvT-B", "backend/models/", "flax .npz weights", "Loaded in-process"],
    )

    def arrow(start, end):
        draw.line((start, end), fill=COPPER, width=5)
        ex, ey = end
        draw.polygon([(ex, ey), (ex - 16, ey - 8), (ex - 16, ey + 8)], fill=COPPER)

    arrow((408, 280), (500, 280))
    draw.text((418, 220), "JSON + cookie", fill=COPPER, font=small)
    arrow((930, 250), (1020, 250))
    draw.text((944, 214), "SQL", fill=COPPER, font=small)
    arrow((930, 470), (1020, 470))
    draw.text((934, 434), "embed", fill=COPPER, font=small)

    path = DOCS / "architecture.png"
    image.save(path)
    return path


def erd():
    image = Image.new("RGB", (1400, 620), PAPER)
    draw = ImageDraw.Draw(image)
    title = font(36, True)
    label = font(26, True)
    small = font(20)
    draw.text((48, 32), "MotionMind tables", fill=INK, font=title)

    tables = [
        (
            48,
            "users",
            ["id  PK", "email  unique", "password_hash", "role", "created_at"],
        ),
        (
            500,
            "motion_plans",
            ["id  PK", "user_id  FK", "prompt", "summary", "plan_json", "model_name", "created_at"],
        ),
        (
            980,
            "api_usage",
            ["id  PK", "user_id  FK", "endpoint", "method", "status_code", "created_at"],
        ),
    ]
    for x, name, fields in tables:
        height = 80 + 34 * len(fields)
        draw.rounded_rectangle((x, 120, x + 370, 120 + height), radius=18, fill=WHITE, outline=LINE, width=3)
        draw.rectangle((x, 120, x + 370, 172), fill=(243, 232, 216))
        draw.text((x + 20, 134), name, fill=INK, font=label)
        for index, field in enumerate(fields):
            draw.text((x + 20, 188 + index * 34), field, fill=MUTED, font=small)

    draw.line((418, 250, 500, 250), fill=COPPER, width=4)
    draw.line((870, 250, 980, 320), fill=COPPER, width=4)
    draw.text((424, 210), "1 to many", fill=COPPER, font=small)
    draw.text((888, 348), "1 to many", fill=COPPER, font=small)
    path = DOCS / "erd.png"
    image.save(path)
    return path


def records():
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    users = connection.execute(
        "SELECT id, email, password_hash, role, created_at FROM users ORDER BY id"
    ).fetchall()
    plans = connection.execute(
        "SELECT id, user_id, prompt, model_name, created_at FROM motion_plans ORDER BY id"
    ).fetchall()
    usage = connection.execute(
        "SELECT id, user_id, method, endpoint, status_code, created_at FROM api_usage ORDER BY id DESC LIMIT 6"
    ).fetchall()
    connection.close()

    image = Image.new("RGB", (1600, 980), PAPER)
    draw = ImageDraw.Draw(image)
    title = font(34, True)
    head = font(22, True)
    body = font(18)
    draw.text((40, 28), "Sample rows from backend/instance/motionmind.db", fill=INK, font=title)
    draw.text(
        (40, 74),
        "password_hash is a bcrypt string. The plaintext passwords are not stored.",
        fill=MUTED,
        font=body,
    )

    def fit(text, width, face):
        text = "—" if text is None else str(text)
        if face.getlength(text) <= width - 16:
            return text
        trimmed = text
        while trimmed and face.getlength(trimmed + "…") > width - 16:
            trimmed = trimmed[:-1]
        return trimmed + "…"

    def table(y, name, headers, rows, widths):
        draw.text((40, y), name, fill=INK, font=head)
        top = y + 40
        draw.rectangle((40, top, 40 + sum(widths), top + 36), fill=(243, 232, 216))
        x = 40
        for index, header in enumerate(headers):
            draw.text((x + 10, top + 8), fit(header, widths[index], head), fill=INK, font=head)
            x += widths[index]
        for rindex, row in enumerate(rows):
            row_y = top + 36 + rindex * 34
            if rindex % 2 == 0:
                draw.rectangle((40, row_y, 40 + sum(widths), row_y + 34), fill=WHITE)
            x = 40
            for index, value in enumerate(row):
                draw.text((x + 10, row_y + 6), fit(value, widths[index], body), fill=MUTED, font=body)
                x += widths[index]
        return top + 36 + max(len(rows), 1) * 34 + 28

    user_rows = []
    for row in users:
        digest = row["password_hash"]
        shown = digest[:28] + "…"
        user_rows.append((row["id"], row["email"], shown, row["role"], row["created_at"][:19]))
    y = table(
        120,
        "users",
        ["id", "email", "password_hash", "role", "created_at"],
        user_rows,
        [70, 280, 560, 140, 470],
    )
    plan_rows = [
        (row["id"], row["user_id"], row["prompt"], row["model_name"].split("/")[-1], row["created_at"][:19])
        for row in plans
    ] or [("—", "—", "none yet", "—", "—")]
    y = table(
        y,
        "motion_plans",
        ["id", "user_id", "prompt", "model", "created_at"],
        plan_rows,
        [70, 120, 560, 280, 490],
    )
    usage_rows = [
        (row["id"], row["user_id"], row["method"], row["endpoint"], row["status_code"], row["created_at"][:19])
        for row in usage
    ]
    table(
        y,
        "api_usage (newest first)",
        ["id", "user_id", "method", "endpoint", "status", "created_at"],
        usage_rows,
        [70, 120, 140, 460, 120, 610],
    )
    path = DOCS / "database-records.png"
    image.save(path)
    return path


def report(architecture_path):
    pdf = FPDF(format="Letter", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(16, 14, 16)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(
        0, 8, "MotionMind: AI Motion Planner for a Four-Servo Robot",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0, 6, "Milestone 1  |  Group Mr7",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Team", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        5.5,
        "Prabh - Client pages and the walkthrough a marker follows: registration, the user lab, and the administrator desk.\n"
        "Raj - API server, authentication, database design, and the local embedding model.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Project", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        5.4,
        "MotionMind continues our feasibility study for a four-servo desktop robot. A person describes a movement in ordinary language. The API embeds that sentence with a local copy of google/videoprism-lvt-base-f16r288 and compares it with a catalog of motions. The closest matches become timed angles for the base, shoulder, elbow, and gripper, which the client plays on a simple arm. Accounts, saved plans, and API calls live in separate tables. Passwords are bcrypt hashes. The session is an HttpOnly JWT cookie issued by our own server. We did not use OAuth, because this course requires our own authentication. Milestone 1 plans the motion. It does not drive the microcontroller yet.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Model, origins, and test accounts", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        5,
        "Model: https://huggingface.co/google/videoprism-lvt-base-f16r288\n"
        "Weights: backend/models/videoprism-lvt-base-f16r288/flax_lvt_base_f16r288_repeated.npz\n"
        "The API uses the text encoder in that checkpoint. GET /api/model shows the file.\n"
        "Client: http://localhost:5173     API: http://localhost:5001\n"
        "User: john@john.com / 123     Administrator: admin@admin.com / 111\n"
        "AI page after login: http://localhost:5173/user.html\n"
        "Administrator page: http://localhost:5173/admin.html",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Architecture", new_x="LMARGIN", new_y="NEXT")
    pdf.image(str(architecture_path), w=180)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        5.4,
        "The client and the API are deployed as different origins. For this milestone those origins are localhost ports 5173 and 5001. Authentication, motion planning, administrator authorization, usage tracking, and VideoPrism inference are modules inside the one API process. SQLite is a separate data store next to that process, with users, motion_plans, and api_usage kept as different tables. A later milestone can move the database or the model into its own service without changing the client's contract. Administrator checks run on the server: a normal user who opens the admin page receives 403.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    out = DOCS / "milestone1GroupMr7.pdf"
    pdf.output(str(out))
    return out, pdf.pages_count


if __name__ == "__main__":
    arch = architecture()
    erd()
    records()
    path, pages = report(arch)
    print(f"{path} ({pages} pages)")
