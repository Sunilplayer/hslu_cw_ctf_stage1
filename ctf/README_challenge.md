# Stielvoll — CTF Stage 1 (Setup)

A deliberately vulnerable Flask web app. The intended path chains three planted
web vulnerabilities into remote code execution, from which the player reads a
user flag on the host.

> ⚠️ **Deploy only on an isolated lab/VM.** This app contains real RCE by
> design. Never expose it to an untrusted network and never reuse the code.

## Attack path (overview)

1. **SQL injection** in the *Kommentare durchsuchen* search (GET param `q`) on
   any project page → leaks the admin credentials `tom-admin` / `@ndAouGot1t!`
   from the `users` table. Reflected and GET-based, so it is exploitable by
   hand (UNION) and detectable by sqlmap. (Posting a comment is parameterised
   and safe.)
2. **Login** at `/admin` with those credentials.
3. **Insecure upload + SSTI/RCE**: the admin "Blogbeitrag erstellen" form
   accepts any file as a "Titelbild". When the post is opened, the uploaded
   file is rendered as a Jinja template → code execution as the web user.
4. From the shell, read the **user flag** (out of scope of the web app itself).

Full walkthrough with payloads: [SOLUTION.md](SOLUTION.md).

## Host provisioning (run on the challenge VM, as root)

The foothold user and the flag live on the operating system, not in the repo.
Run the provided script once on the target VM:

```bash
sudo bash ctf/setup_challenge.sh
```

It creates the `analyst` account (password `analystpw123!`), drops the user
flag into `/home/analyst/user.txt`, and prints how to run the app **as that
user** so the RCE foothold lands as `analyst`.

Place your own root/second flag wherever "out of scope" should be (e.g.
`/root/root.txt`) — that part is left to the challenge author.

## Running the app

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_hex(32))')" \
  .venv/bin/python app.py      # listens on 127.0.0.1:5015
```

For the challenge, bind it so players can reach it (e.g. behind a reverse proxy,
or change the host in `app.py` to `0.0.0.0`) and run the process **as the
`analyst` user** so a shell from the RCE has the foothold identity.

## Resetting between attempts

- Comments / blog posts: delete `instance/stielvoll.db` (it is recreated on
  start, re-seeding the `tom-admin` account).
- Uploaded payloads: empty `static/uploads/` (the `.gitignore` there keeps the
  directory but ignores its contents).
