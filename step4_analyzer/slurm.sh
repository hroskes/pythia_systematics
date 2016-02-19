#!/bin/bash
#SBATCH --time=6:0:0
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --partition=shared
#SBATCH --mem=24000
#SBATCH --mail-type=end
#SBATCH --mail-user=heshyslurm@gmail.com

totalevents=200000
eventsperfile=10000

if [ ${SLURM_SUBMIT_DIR} ]; then cd ${SLURM_SUBMIT_DIR}; fi				&&
echo "SLURM job running in: " `pwd`							&&
source /work-zfs/lhc/installations/addtopath.sh						&&   #sets LHAPDF environment variables
eval $(scram ru -sh)									&&
indir="$(pwd | sed 's/step4_analyzer/step3_pythia/')"					&&

skipevents=$(echo "
i=$1;
if i == 0:
    print '(0.1)'
else:
    print '[0.%i]' % (i*$eventsperfile - 1)
" | python)										&&

echo $skipevents									&&

cmd="./analyzer indir=$indir $(ls $indir | grep [.]root ) outdir=$(pwd) outfile=analyzed_$1.root includeGenDecayProb=g1 includeRecoDecayProb=g1 includeGenProdProb=g1 includeRecoProdProb=g1 computeVBFProdAngles=1 sampleProductionId=JJVBF,JHUGen maxevents=$eventsperfile skipevents=$skipevents fileLevel=1"	&&
echo $cmd										&&

cd ../../../../CMSJHU_AnalysisMacros/JHUSpinWidthPaper_2015/LHEAnalyzer/		&&

$cmd
