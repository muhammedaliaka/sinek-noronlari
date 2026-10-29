#!/bin/bash
# O5 GELİŞTİRME paneli (kanıt değil; tohum < 200): plastic, frozen, reference, plastic_ens (K=4, τ=0,04), parça paralel, yeniden başlatmaya dayanıklı.
#   scripts/run_o5_dev_panel.sh <pre.npz> <tohum> [işçi_sayısı]      # çıktı results/o5_val/dev_s<tohum>
set -u
cd "$(dirname "$0")/.."
PRE=$1; SEED=$2; W=${3:-4}
D=results/o5_val/dev_s$SEED
mkdir -p $D
job() {  # kol [parça]
  arm=$1; ch=${2:-}
  extra=""; [ "$arm" = plastic_ens ] && extra="--ens-k 4 --ens-tau 0.04"
  [ -n "$ch" ] && extra="$extra --only-chunks $ch"
  python3 -I -m sinek.experiments.odor_validate_o5 --pilot --pre $PRE --seed $SEED --threads 1 --only-arms $arm $extra --out $D >> $D.$arm${ch:+_c$ch}.log 2>&1
  echo "bitti $arm $ch $(date +%T) çıkış=$?"
}
export -f job; export PRE SEED D
printf '%s\n' "plastic_ens 0" "plastic_ens 1" "plastic_ens 2" "plastic_ens 3" "plastic" "frozen" "reference" | xargs -P "$W" -I{} bash -c 'job {}'
python3 -I -m sinek.experiments.odor_validate_o5 --pilot --pre $PRE --seed $SEED --threads 1 --ens-k 4 --ens-tau 0.04 --out $D > $D.log 2>&1
echo "değerlendirme bitti $(date +%T)"
