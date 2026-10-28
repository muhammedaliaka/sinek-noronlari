#!/bin/bash
# Yeniden başlatmaya dayanıklı doğrulayıcı kuyruğu (V-03'ün ilk adımı: oyun düzeyinde devam).
# Ön-kayıt belgeleri: docs/odor_o1_plani.md, odor_o2_plani.md, odor_o3_plani.md, odor_o4_plani.md (komutlar orada dondurulmuştur).
# Bu betik ölçüt/eşik KEŞFETMEZ; yalnızca ön-kayıtlı komutları sırayla çalıştırır. Biten iş (results.json var) atlanır.
#
#   scripts/run_validators.sh [işçi_sayısı]      # varsayılan 4; çıktı results/odor_val/
set -u
cd "$(dirname "$0")/.."
W=${1:-4}
OUT=results/odor_val
mkdir -p $OUT

job() {  # oyun tohum pop [ek bayraklar...]
  game=$1; seed=$2; pop=$3; shift 3
  d=$OUT/${game}_s$seed
  [ -f $d/results.json ] && { echo "atla $game $seed (bitti)"; return; }
  echo "başla $game $seed $(date +%T)"
  case $game in
    O1a|O1b) mod=odor_validate; ex="--ref-min 0.80";;
    O2near|O2full) mod=odor_validate; ex="--ref-min 0.70";;
    O3) mod=odor_validate_s; ex="";;
    O4a|O4c) mod=odor_validate_s; ex="--test-reps 16 --attract-mult 1.0";;
  esac
  python3 -I -m sinek.experiments.$mod --pre $OUT/pre_s$pop.npz --game $game --seed $seed $ex --threads 1 --out $d > $d.log 2>&1
  echo "bitti $game $seed $(date +%T) çıkış=$?"
}
export -f job; export OUT

# önce en uzun işler (O3), sonra O2, O4; ön-eğitim dosyaları hazır olmalı
printf '%s\n' "O3 230 200" "O3 231 201" "O2near 220 200" "O2near 221 201" "O2full 222 200" "O2full 223 201" \
  "O4a 240 200" "O4a 241 201" "O4c 242 200" "O4c 243 201" \
  | xargs -P "$W" -I{} bash -c 'job {}'
