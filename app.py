import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from projects import PROJECTS, PROJECTS_BY_SLUG

app = Flask(__name__)
# Set SECRET_KEY in the environment for production deployments.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["DATABASE"] = os.path.join(app.instance_path, "stielvoll.db")

TIMEZONE = ZoneInfo("Europe/Zurich")
MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]
COMMENT_NAME_MAX = 60
COMMENT_TEXT_MAX = 2000

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


# ---------- Database (comments) ----------

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
    return {"nav_items": NAV_ITEMS}


# ---------- Routes ----------

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
    counts = dict(
        get_db().execute(
            "SELECT project_slug, COUNT(*) FROM comments GROUP BY project_slug"
        ).fetchall()
    )
    return render_template("projects.html", projects=PROJECTS, comment_counts=counts)


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

        # Hidden honeypot field: humans leave it empty, simple spam bots fill it in.
        if request.form.get("website"):
            return redirect(url_for("projects_detail", slug=slug))

        errors = []
        if not form["name"]:
            errors.append("Bitte geben Sie Ihren Namen an.")
        elif len(form["name"]) > COMMENT_NAME_MAX:
            errors.append(f"Der Name darf höchstens {COMMENT_NAME_MAX} Zeichen lang sein.")
        if not form["text"]:
            errors.append("Bitte schreiben Sie einen Kommentar.")
        elif len(form["text"]) > COMMENT_TEXT_MAX:
            errors.append(f"Der Kommentar darf höchstens {COMMENT_TEXT_MAX} Zeichen lang sein.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            db.execute(
                "INSERT INTO comments (project_slug, name, text, created_at) VALUES (?, ?, ?, ?)",
                (slug, form["name"], form["text"], datetime.now(TIMEZONE).isoformat()),
            )
            db.commit()
            flash("Vielen Dank für Ihren Kommentar!", "success")
            return redirect(url_for("projects_detail", slug=slug) + "#kommentare")

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
        newer=PROJECTS[index - 1] if index > 0 else None,
        older=PROJECTS[index + 1] if index + 1 < len(PROJECTS) else None,
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html", opening_hours=OPENING_HOURS)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5015, debug=True)
