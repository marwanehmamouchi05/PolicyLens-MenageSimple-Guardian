#!/bin/sh
# Existing Guardian service only. Run as the host administrator after approval.
set -eu
REV=${1:?commit SHA required}
SHA=${2:?archive SHA256 required}
case "$REV" in *[!a-f0-9]*|'') exit 2;; esac
case "$SHA" in *[!a-f0-9]*|'') exit 2;; esac
test ${#REV} -eq 40
test ${#SHA} -eq 64
ROOT=/opt/policylens-guardian
OLD=$(readlink -f "$ROOT/current")
case "$OLD" in "$ROOT"/releases/*) ;; *) exit 3;; esac
TARGET="$ROOT/releases/$REV"
test ! -e "$TARGET"
systemctl is-active --quiet policylens-guardian.service
systemctl is-active --quiet policylens-expire.timer
mkdir "$TARGET"
curl -fsSL --max-time 90 "https://api.github.com/repos/marwanehmamouchi05/PolicyLens-MenageSimple-Guardian/tarball/$REV" -o "$ROOT/release-$REV.tar.gz"
printf '%s  %s\n' "$SHA" "$ROOT/release-$REV.tar.gz" | sha256sum -c -
tar -xzf "$ROOT/release-$REV.tar.gz" --strip-components=1 -C "$TARGET"
chmod -R a+rX "$TARGET"
(cd "$TARGET" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v) > "$ROOT/validation-$REV.txt" 2>&1
tail -5 "$ROOT/validation-$REV.txt"
printf '%s\n' "$OLD" > "$ROOT/rollback-$REV.txt"
ln -s "$TARGET" "$ROOT/.current-$REV"
mv -Tf "$ROOT/.current-$REV" "$ROOT/current"
ok=0
if systemctl restart policylens-guardian.service; then
 attempt=0
 while test "$attempt" -lt 90; do
  attempt=$((attempt+1))
  if curl -fsS --max-time 3 http://127.0.0.1:8889/api/health; then ok=1; break; fi
  sleep 1
 done
fi
if test "$ok" -ne 1; then
 ln -s "$OLD" "$ROOT/.rollback-$REV"
 mv -Tf "$ROOT/.rollback-$REV" "$ROOT/current"
 systemctl restart policylens-guardian.service
 echo 'Guardian rollback performed.'
 exit 1
fi
readlink -f "$ROOT/current"
systemctl show policylens-guardian.service -p MemoryCurrent -p MemoryMax -p CPUQuotaPerSecUSec
systemctl list-timers policylens-expire.timer --no-pager
docker ps --format '{{.Names}} {{.Status}}'
curl -fsS --max-time 20 -o /dev/null -w 'Nodum HTTPS %{http_code}\n' https://nodum.54-173-165-46.sslip.io/app/
