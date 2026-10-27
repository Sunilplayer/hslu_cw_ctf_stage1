#!/usr/bin/env bash
#
# Stielvoll CTF — host provisioning. Run ONCE on the challenge VM as root.
#   sudo bash ctf/setup_challenge.sh
#
# Creates the foothold account "analyst" and plants the user flag. Intended for
# an isolated lab VM only.

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

FOOTHOLD_USER="analyst"
FOOTHOLD_PASS='analystpw123!'
USER_FLAG="${USER_FLAG:-CWHS2026{rooted_like_a_begonia}}"

# --- create the foothold user (idempotent) ---
if id "$FOOTHOLD_USER" &>/dev/null; then
  echo "[*] User '$FOOTHOLD_USER' already exists."
else
  useradd -m -s /bin/bash "$FOOTHOLD_USER"
  echo "[+] Created user '$FOOTHOLD_USER'."
fi
echo "${FOOTHOLD_USER}:${FOOTHOLD_PASS}" | chpasswd
echo "[+] Password set for '$FOOTHOLD_USER'."

# --- plant the user flag, readable only by the foothold user ---
FLAG_PATH="/home/${FOOTHOLD_USER}/user.txt"
printf '%s\n' "$USER_FLAG" > "$FLAG_PATH"
chown "${FOOTHOLD_USER}:${FOOTHOLD_USER}" "$FLAG_PATH"
chmod 640 "$FLAG_PATH"
echo "[+] User flag written to $FLAG_PATH"

cat <<EOF

Done.

Run the web app AS the foothold user so RCE lands as '$FOOTHOLD_USER':

    sudo -u $FOOTHOLD_USER bash -lc '
        cd /path/to/ClaudeCode_Test &&
        python3 -m venv .venv &&
        .venv/bin/pip install -r requirements.txt &&
        SECRET_KEY="\$(python3 -c "import secrets;print(secrets.token_hex(32))")" \\
          .venv/bin/python app.py
    '

Place a second / root flag out of scope yourself, e.g.:

    printf 'CWHS2026{...}\n' > /root/root.txt && chmod 600 /root/root.txt
EOF
