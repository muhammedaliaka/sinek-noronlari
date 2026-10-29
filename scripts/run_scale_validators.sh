#!/bin/bash
# Ölçek ekseni doğrulayıcı kuyruğu (docs/olcek_plani.md §7). Yeniden başlatmaya dayanıklı: biten iş (results.json var) atlanır,
# kesilen iş kol-kol kontrol noktalarından AYNI hesapla sürer. Ölçüt/eşik KEŞFETMEZ.
#
#   scripts/run_scale_validators.sh [işçi_sayısı]      # varsayılan 4; çıktı results/scale_val/
set -u
cd "$(dirname "$0")/.."
W=${1:-4}
OUT=results/scale_val
mkdir -p $OUT

job() {  # oyun tohum pop
  game=$1; seed=$2; pop=$3
  d=$OUT/${game}_s$seed
  [ -f $d/results.json ] && { echo "atla $game $seed (bitti)"; return; }
  echo "başla $game $seed $(date +%T)"
  python3 -I -m sinek.experiments.odor_validate_scale --pre results/odor_val/pre_s$pop.npz --game $game --seed $seed --threads 1 --out $d > $d.log 2>&1
  echo "bitti $game $seed $(date +%T) çıkış=$?"
}
export -f job; export OUT

printf '%s\n' "O1a 250 200" "O1a 251 201" "O1b 252 200" "O1b 253 201" | xargs -P "$W" -I{} bash -c 'job {}'
