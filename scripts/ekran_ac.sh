#!/usr/bin/env bash
# Sinek TEST EKRANI (sunucu/port yok). Kullanım: scripts/ekran_ac.sh --relay origin:ops-relay --auto
cd "$(dirname "$0")/.." || exit 1
exec python3 -X utf8 -I -m sinek.ops.ekran "$@"
