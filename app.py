import os
import sqlite3
from datetime import datetime
from functools import wraps
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from projects import PROJECTS, PROJECTS_BY_SLUG

# ===========================================================================
#  ⚠️  CTF CHALLENGE — INTENTIONALLY VULNERABLE  ⚠️
#  This application is a deliberately insecure target built for the
#  "hslu_cw_ctf_stage1" exercise. It contains THREE planted vulnerabilities
#  (SQL injection, insecure file upload, server-side template injection /
#  RCE). Do NOT deploy it on anything reachable from an untrusted network,
#  and never reuse this code in a real project. Each planted flaw is marked
#  with a `CTF VULN` comment. See ctf/SOLUTION.md for the intended path.
# ===========================================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["DATABASE"] = os.path.join(app.instance_path, "stielvoll.db")
app.config["UPLOAD_DIR"] = os.path.join(app.static_folder, "uploads")
# Cache static files (images, CSS, JS) in the browser for a week so repeat
# visits don't re-download them — less bandwidth on a constrained host.
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 7 * 24 * 3600

TIMEZONE = ZoneInfo("Europe/Zurich")
MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]
COMMENT_NAME_MAX = 60
COMMENT_TEXT_MAX = 2000

# Seed account that lives in the DB and is the goal of the SQL injection.
ADMIN_USER = "tom-admin"
ADMIN_PASSWORD = "@ndAouGot1t!"

NAV_ITEMS = [
    ("index", "Home"),
    ("projects", "Vergangene Projekte"),
    ("about", "Über uns"),
    ("contact", "Kontakt"),
]

# day: 1 = Montag … 7 = Sonntag (used to highlight today's row)
OPENING_HOURS = [
    {"day": 1, "label": "Montag", "hours": "08:00 – 18:30"},
    {"day": 2, "label": "Dienstag", "hours": "08:00 – 18:30"},
    {"day": 3, "label": "Mittwoch", "hours": "08:00 – 18:30"},
    {"day": 4, "label": "Donnerstag", "hours": "08:00 – 20:00"},
    {"day": 5, "label": "Freitag", "hours": "08:00 – 18:30"},
    {"day": 6, "label": "Samstag", "hours": "08:00 – 17:00"},
    {"day": 7, "label": "Sonntag", "hours": "geschlossen"},
]

SERVICES = [
    {
        "title": "Gartengestaltung",
        "text": "Von der ersten Skizze bis zur fertigen Bepflanzung – wir planen und bauen Ihren Traumgarten.",
        "icon": "design",
    },
    {
        "title": "Gartenpflege",
        "text": "Regelmässige oder saisonale Pflege: Rasen, Beete, Laub und Winterschutz.",
        "icon": "care",
    },
    {
        "title": "Pool- & Teichbau",
        "text": "Schwimmbecken, Naturpools und Gartenteiche – harmonisch in Ihren Garten eingebettet.",
        "icon": "water",
    },
    {
        "title": "Baum- & Heckenschnitt",
        "text": "Fachgerechter Schnitt für gesunde Bäume, dichte Hecken und schöne Formen.",
        "icon": "trim",
    },
]

SORTIMENT = [
    {
        "title": "Zimmerpflanzen",
        "text": "Grünes für drinnen – von pflegeleicht bis ausgefallen.",
        "image": "img/zimmerpflanzen.jpg",
    },
    {
        "title": "Sukkulenten & Kakteen",
        "text": "Genügsame Schönheiten für sonnige Fensterbänke.",
        "image": "img/sukkulenten.jpg",
    },
    {
        "title": "Blumen & Stauden",
        "text": "Saisonale Blütenpracht für Balkon, Terrasse und Beet.",
        "image": "img/blumen.jpg",
    },
    {
        "title": "Gemüse- & Kräutersetzlinge",
        "text": "Jungpflanzen aus der Region für Ihren eigenen Garten.",
        "image": "img/setzlinge.jpg",
    },
    {
        "title": "Gehölze & Formschnitt",
        "text": "Sträucher, Hecken und kunstvoll geschnittene Bäumchen.",
        "image": "img/gehoelze.jpg",
    },
    {
        "title": "Erde & Zubehör",
        "text": "Torffreie Erden, Werkzeug und Töpfe für jedes Projekt.",
        "image": "img/zubehoer.jpg",
    },
]


# ---------- Database ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_slug TEXT NOT NULL,
                name TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_comments_slug ON comments (project_slug)"
        )
        # Admin account — this is what the SQL injection is meant to reveal.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin'
            )
            """
        )
        db.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, 'admin')",
            (ADMIN_USER, ADMIN_PASSWORD),
        )
        # Blog posts created through the admin area.
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS blogposts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                image TEXT,
                author TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


init_db()


# ---------- Template helpers ----------

@app.template_filter("date_de")
def date_de(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value).astimezone(TIMEZONE)
    text = f"{value.day}. {MONTHS_DE[value.month - 1]} {value.year}"
    if isinstance(value, datetime):
        text += f", {value:%H:%M} Uhr"
    return text


@app.context_processor
def inject_globals():
    return {"nav_items": NAV_ITEMS, "logged_in": bool(session.get("user"))}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


# ---------- Public routes ----------

@app.route("/")
def index():
    return render_template(
        "index.html",
        opening_hours=OPENING_HOURS,
        services=SERVICES,
        sortiment=SORTIMENT,
    )


@app.route("/projekte")
def projects():
    db = get_db()
    counts = dict(
        db.execute(
            "SELECT project_slug, COUNT(*) FROM comments GROUP BY project_slug"
        ).fetchall()
    )
    posts = db.execute(
        "SELECT id, title, body, image, author, created_at FROM blogposts ORDER BY id DESC"
    ).fetchall()
    return render_template(
        "projects.html", projects=PROJECTS, comment_counts=counts, posts=posts
    )


@app.route("/projekte/<slug>", methods=["GET", "POST"])
def projects_detail(slug):
    project = PROJECTS_BY_SLUG.get(slug)
    if project is None:
        abort(404)

    db = get_db()
    form = {"name": "", "text": ""}

    if request.method == "POST":
        form["name"] = request.form.get("name", "").strip()
        form["text"] = request.form.get("text", "").strip()

        errors = []
        if not form["name"]:
            errors.append("Bitte geben Sie Ihren Namen an.")
        if not form["text"]:
            errors.append("Bitte schreiben Sie einen Kommentar.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            # Posting a comment is SAFE (parameterised) — the planted SQL
            # injection lives in the comment SEARCH below, not here.
            db.execute(
                "INSERT INTO comments (project_slug, name, text, created_at) "
                "VALUES (?, ?, ?, ?)",
                (slug, form["name"], form["text"], datetime.now(TIMEZONE).isoformat()),
            )
            db.commit()
            flash("Vielen Dank für Ihren Kommentar!", "success")
            return redirect(url_for("projects_detail", slug=slug) + "#kommentare")

    # ====================================================================
    # CTF VULN #1 — SQL INJECTION (Kommentar-Suche, GET-Parameter `q`)
    # The "Kommentare durchsuchen" box builds its query by string
    # interpolation instead of a parameterised query, and renders the
    # matching rows straight back onto the page. Because the sink is a
    # reflected SELECT, it is injectable by hand AND detectable by sqlmap
    # (UNION / boolean-based on SQLite). The query returns 3 columns
    # (name, text, created_at), so a union such as:
    #     %' UNION SELECT username, password, role FROM users-- -
    # lists the admin credentials in the results.
    # The safe version would pass `q` as a bound parameter.
    # ====================================================================
    search_query = request.args.get("q")
    search_results = None
    if search_query is not None:
        sql = (
            "SELECT name, text, created_at FROM comments "
            f"WHERE project_slug = '{slug}' AND text LIKE '%{search_query}%' "
            "ORDER BY id"
        )
        try:
            search_results = db.execute(sql).fetchall()
        except sqlite3.Error as exc:
            # Verbose DB errors on purpose: they help players tune a payload.
            flash(f"Suche fehlgeschlagen: {exc}", "error")
            search_results = []

    comments = db.execute(
        "SELECT name, text, created_at FROM comments WHERE project_slug = ? ORDER BY id",
        (slug,),
    ).fetchall()

    index = PROJECTS.index(project)
    return render_template(
        "project_detail.html",
        project=project,
        comments=comments,
        form=form,
        name_max=COMMENT_NAME_MAX,
        text_max=COMMENT_TEXT_MAX,
        search_query=search_query or "",
        search_results=search_results,
        newer=PROJECTS[index - 1] if index > 0 else None,
        older=PROJECTS[index + 1] if index + 1 < len(PROJECTS) else None,
    )


@app.route("/blog/<int:post_id>")
def blog_post(post_id):
    db = get_db()
    post = db.execute(
        "SELECT id, title, body, image, author, created_at FROM blogposts WHERE id = ?",
        (post_id,),
    ).fetchone()
    if post is None:
        abort(404)

    # ====================================================================
    # CTF VULN #3 — SERVER-SIDE TEMPLATE INJECTION → RCE (on blog open)
    # The uploaded "cover image" is read back and rendered through Jinja's
    # render_template_string when the post is opened. A file uploaded via the
    # admin area whose bytes are a Jinja/SSTI payload is therefore executed
    # server-side the moment someone views the blog post, e.g.:
    #   {{ cycler.__init__.__globals__.os.popen('id').read() }}
    # Normal image bytes render to harmless noise. This is deliberately insecure.
    # ====================================================================
    widget = ""
    if post["image"]:
        path = os.path.join(app.config["UPLOAD_DIR"], post["image"])
        try:
            with open(path, "r", errors="ignore") as fh:
                widget = render_template_string(fh.read())
        except Exception as exc:  # noqa: BLE001 — show errors to help players
            widget = f"[Widget-Fehler: {exc}]"

    return render_template("blog_post.html", post=post, widget=widget)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html", opening_hours=OPENING_HOURS)


# ---------- Admin area ----------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("user"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        db = get_db()
        # Login itself uses a parameterised query — the credentials are meant
        # to be obtained through VULN #1 (the comment SQL injection), not by
        # bypassing this check.
        row = db.execute(
            "SELECT username, role FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        if row:
            session["user"] = row["username"]
            session["role"] = row["role"]
            flash("Willkommen im Admin-Bereich.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Falscher Benutzername oder falsches Passwort.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Abgemeldet.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    db = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        upload = request.files.get("image")

        filename = None
        if upload and upload.filename:
            # ================================================================
            # CTF VULN #2 — INSECURE FILE UPLOAD
            # No validation of extension or content type. Any file the admin
            # chooses is written straight into static/uploads/ under (a
            # sanitised version of) its own name. Combined with VULN #3 this
            # gives remote code execution.
            # ================================================================
            filename = secure_filename(upload.filename) or "upload.bin"
            upload.save(os.path.join(app.config["UPLOAD_DIR"], filename))

        if not title or not body:
            flash("Titel und Text sind erforderlich.", "error")
        else:
            db.execute(
                "INSERT INTO blogposts (title, body, image, author, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (title, body, filename, session["user"], datetime.now(TIMEZONE).isoformat()),
            )
            db.commit()
            flash("Blogbeitrag veröffentlicht.", "success")
            return redirect(url_for("admin_dashboard"))

    posts = db.execute(
        "SELECT id, title, author, created_at FROM blogposts ORDER BY id DESC"
    ).fetchall()
    return render_template("admin_dashboard.html", posts=posts)


if __name__ == "__main__":
    # Lean by default: no debugger, no reloader (the reloader runs a second
    # process and watches files). Set FLASK_DEBUG=1 for local development only.
    # Bind address is configurable so you don't have to edit code to expose it
    # on the LAN: HOST=0.0.0.0 python app.py
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5015")),
        debug=debug,
    )
