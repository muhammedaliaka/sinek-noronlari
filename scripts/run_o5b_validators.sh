#!/bin/bash
# O5b doğrulayıcı kuyruğu (docs/odor_o5b_plani.md §8). Yeniden başlatmaya dayanıklı: bitenler atlanır, kesilen iş parça kontrol noktasından AYNI hesapla sürer.
# Aşama 0: yeni popülasyonlar için ön-eğitim (tohum 202-205, R-1: bu betik ön-kayıt commit'inden SONRA çalıştırılır). Aşama 1: kol × parça işçileri. Aşama 2: değerlendirme.
#   scripts/run_o5b_validators.sh [işçi_sayısı]      # varsayılan 4; çıktı results/o5_val/b_s<tohum>
set -u
cd "$(dirname "$0")/.."
W=${1:-4}
OUT=results/o5_val
mkdir -p $OUT results/odor_val
CH=8

pre_job() {  # pop
  pop=$1; f=results/odor_val/pre_s$pop.npz
  [ -f $f ] && { echo "atla ön-eğitim $pop (var)"; return; }
  echo "başla ön-eğitim $pop $(date +%T)"
  python3 -I -m sinek.experiments.odor_pretrain --seed $pop --threads 1 --out $f > results/odor_val/pre_s$pop.log 2>&1
  echo "bitti ön-eğitim $pop $(date +%T) çıkış=$?"
}
arm_job() {  # tohum pop kol parça
  seed=$1; pop=$2; arm=$3; ch=$4
  d=$OUT/b_s$seed
  [ -f $d/results.json ] && { echo "atla $seed $arm $ch (bitti)"; return; }
  mkdir -p $d
  only="--only-arms $arm"; [ "$ch" != all ] && only="$only --only-chunks $ch"
  python3 -I -m sinek.experiments.odor_validate_o5 --o5b --pre results/odor_val/pre_s$pop.npz --seed $seed --threads 1 $only --out $d >> $d.$arm.$ch.log 2>&1
  echo "bitti $seed $arm $ch $(date +%T) çıkış=$?"
}
eval_job() {  # tohum pop
  seed=$1; pop=$2; d=$OUT/b_s$seed
  [ -f $d/results.json ] && { echo "atla değerlendirme $seed (bitti)"; return; }
  python3 -I -m sinek.experiments.odor_validate_o5 --o5b --pre results/odor_val/pre_s$pop.npz --seed $seed --threads 1 --out $d > $d.log 2>&1
  echo "değerlendirme $seed bitti $(date +%T) çıkış=$?"
}
export -f pre_job arm_job eval_job; export OUT CH

printf '%s\n' 202 203 204 205 | xargs -P "$W" -I{} bash -c 'pre_job {}'
{
  for arm in plastic_ens plastic frozen; do
    for c in $(seq 0 $((CH - 1))); do
      for sp in "270 202" "271 203" "272 204" "273 205"; do echo "$sp $arm $c"; done
    done
  done
  for sp in "270 202" "271 203" "272 204" "273 205"; do echo "$sp reference all"; done
} | xargs -P "$W" -I{} bash -c 'arm_job {}'
printf '%s\n' "270 202" "271 203" "272 204" "273 205" | xargs -P 4 -I{} bash -c 'eval_job {}'
