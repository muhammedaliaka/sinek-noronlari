#!/bin/bash
# Kontrol sunucusunu başlatır (docs/uzak_kontrol.md). Varsayılan: yalnız bu bilgisayardan erişim (127.0.0.1) — tünel/VPN ile açılır.
#   scripts/ops_baslat.sh                  # yerel, jeton ~/.sinek_ops_token
#   scripts/ops_baslat.sh --host 0.0.0.0   # ağdan erişim (TLS yok; güvenilir ağ/VPN dışında açmayın)
#   scripts/ops_baslat.sh --relay origin:ops-relay   # bağlantı kabul edemiyorsa: GitHub dalı üzerinden komut/durum
set -u
cd "$(dirname "$0")/.."
exec python3 -I -m sinek.ops.server "$@"
