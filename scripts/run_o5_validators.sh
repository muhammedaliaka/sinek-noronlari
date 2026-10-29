#!/bin/bash
# O5 doğrulayıcı kuyruğu (docs/odor_o5_plani.md §8). Yeniden başlatmaya dayanıklı: biten iş (results.json var) atlanır,
# kesilen iş kol × parça kontrol noktalarından AYNI hesapla sürer. Ölçüt/eşik KEŞFETMEZ.
#
#   scripts/run_o5_validators.sh [işçi_sayısı]      # varsayılan 4; çıktı results/o5_val/
set -u
cd "$(dirname "$0")/.."
W=${1:-4}
OUT=results/o5_val
mkdir -p $OUT

arm_job() {  # tohum kol pop
  seed=$1; arm=$2; pop=$3
  d=$OUT/s$seed
  [ -f $d/results.json ] && { echo "atla $seed $arm (bitti)"; return; }
  mkdir -p $d
  echo "başla $seed $arm $(date +%T)"
  python3 -I -m sinek.experiments.odor_validate_o5 --pre results/odor_val/pre_s$pop.npz --seed $seed --threads 1 --only-arms $arm --out $d >> $d.$arm.log 2>&1
  echo "bitti $seed $arm $(date +%T) çıkış=$?"
}
eval_job() {  # tohum pop
  seed=$1; pop=$2
  d=$OUT/s$seed
  [ -f $d/results.json ] && { echo "atla değerlendirme $seed (bitti)"; return; }
  python3 -I -m sinek.experiments.odor_validate_o5 --pre results/odor_val/pre_s$pop.npz --seed $seed --threads 1 --out $d > $d.log 2>&1
  echo "değerlendirme $seed bitti $(date +%T) çıkış=$?"
}
export -f arm_job eval_job; export OUT

printf '%s\n' "260 plastic 200" "261 plastic 201" "260 frozen 200" "261 frozen 201" "260 reference 200" "261 reference 201" | xargs -P "$W" -I{} bash -c 'arm_job {}'
printf '%s\n' "260 200" "261 201" | xargs -P 2 -I{} bash -c 'eval_job {}'
