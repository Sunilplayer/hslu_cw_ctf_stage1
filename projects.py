"""Blog entries for the "Vergangene Projekte" page (newest first)."""

from datetime import date

PROJECTS = [
    {
        "slug": "poolbau-mit-holzdeck",
        "title": "Poolbau mit Holzdeck in Küsnacht",
        "date": date(2026, 8, 21),
        "location": "Küsnacht ZH",
        "category": "Poolbau",
        "image": "img/projekte/poolbau.jpg",
        "summary": (
            "Ein schlichter Betonpool, eingefasst von einem warmen Holzdeck – "
            "und rundherum eine Bepflanzung, die auch im Herbst Freude macht."
        ),
        "body": [
            "Der Wunsch der Familie war klar: ein Pool, der sich ruhig in den "
            "bestehenden Garten einfügt und nicht wie ein Fremdkörper wirkt. "
            "Nach mehreren Planungsgesprächen haben wir uns für ein schlichtes, "
            "rechteckiges Becken mit grau-grüner Auskleidung entschieden.",
            "Für das Deck verwendeten wir thermisch behandeltes Eschenholz aus "
            "der Schweiz. Es ist langlebig, splitterarm und bekommt mit den "
            "Jahren eine schöne silbergraue Patina. Unter dem Deck verschwinden "
            "Technik und Abdeckung, sodass der Pool im Winter fast unsichtbar wird.",
            "Rund um die Wasserfläche pflanzten wir Gräser, Lavendel und "
            "Felsenbirnen. Sie vertragen die sonnige Lage, werfen kaum Laub "
            "ins Wasser und sorgen für Sichtschutz zum Nachbargrundstück.",
            "Bauzeit: rund zehn Wochen von der Baugrube bis zum ersten Sprung "
            "ins Wasser.",
        ],
    },
    {
        "slug": "gartenumgestaltung-rosengarten",
        "title": "Vom Rasen zum Rosengarten",
        "date": date(2026, 6, 3),
        "location": "Winterthur",
        "category": "Gartenumgestaltung",
        "image": "img/projekte/gartenumgestaltung.jpg",
        "summary": (
            "Aus einer pflegeintensiven Rasenfläche wurde ein duftender "
            "Rosengarten mit Buchshecken und einem einladenden Kiesweg."
        ),
        "body": [
            "Als wir den Garten zum ersten Mal sahen, bestand er fast nur aus "
            "Rasen – schön grün, aber viel Arbeit und wenig Leben. Die "
            "Besitzerin wünschte sich einen Ort zum Spazieren, Riechen und "
            "Verweilen.",
            "Wir haben einen geschwungenen Weg aus rotem Splitt angelegt, der "
            "den Garten in zwei Hälften teilt. Links und rechts davon setzen "
            "niedrige Hecken klare Linien, dahinter wachsen über 40 Rosen in "
            "verschiedenen Sorten – von robusten Strauchrosen bis zu "
            "duftenden Englischen Rosen.",
            "Damit sich der Pflegeaufwand in Grenzen hält, haben wir auf "
            "krankheitsresistente Sorten gesetzt und die Beete mit "
            "Rindenmulch abgedeckt. Eine Tropfbewässerung versorgt die "
            "Pflanzen auch in trockenen Sommern zuverlässig.",
        ],
    },
    {
        "slug": "naschgarten-mit-hochbeeten",
        "title": "Naschgarten mit Hochbeeten",
        "date": date(2026, 4, 15),
        "location": "Baden AG",
        "category": "Gemüsegarten",
        "image": "img/projekte/hochbeete.jpg",
        "summary": (
            "Rückenschonend gärtnern: Fünf Hochbeete aus Lärchenholz machen "
            "aus einer ungenutzten Ecke einen kleinen Selbstversorgergarten."
        ),
        "body": [
            "Eine junge Familie wollte ihr eigenes Gemüse ziehen – am liebsten "
            "so, dass auch die Kinder mithelfen können. Die ungenutzte, sonnige "
            "Ecke hinter dem Haus war dafür ideal.",
            "Wir bauten fünf Hochbeete aus unbehandeltem Schweizer Lärchenholz. "
            "Gefüllt sind sie nach dem klassischen Schichtprinzip: Äste und "
            "Zweige unten, darüber Laub, Kompost und zuoberst unsere torffreie "
            "Gemüseerde.",
            "Zum Start haben wir gemeinsam Mangold, Salate, Kräuter und "
            "Erdbeeren gepflanzt. Zwischen den Beeten liegt Holzschnitzel, "
            "damit man auch nach einem Regenschauer trockenen Fusses ernten kann.",
        ],
    },
]

PROJECTS_BY_SLUG = {p["slug"]: p for p in PROJECTS}
