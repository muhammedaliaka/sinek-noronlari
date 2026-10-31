#!/bin/bash
# Kontrol sunucusunu başlatır (docs/uzak_kontrol.md). Varsayılan: yalnız bu bilgisayardan erişim (127.0.0.1); uzaktan erişim git yayını ile (--relay).
#   scripts/ops_baslat.sh --relay origin:ops-relay   # ÖNERİLEN: dışarıya port açmadan, imzalı komut + durum GitHub dalı üzerinden
#   scripts/ops_baslat.sh                            # yalnız yerel panel
#   scripts/ops_baslat.sh --host 0.0.0.0             # ağdan erişim (TLS yok; yalnız güvenilir ağ/VPN)
set -u
cd "$(dirname "$0")/.."
exec python3 -I -m sinek.ops.server "$@"
