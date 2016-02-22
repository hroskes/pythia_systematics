#!/bin/bash
#SBATCH --time=2:0:0
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --partition=shared
#SBATCH --mem=24000
#SBATCH --mail-type=end
#SBATCH --mail-user=heshyslurm@gmail.com

if [ ${SLURM_SUBMIT_DIR} ]; then cd ${SLURM_SUBMIT_DIR}; fi
echo "SLURM job running in: " `pwd`
source /work-zfs/lhc/installations/addtopath.sh    #sets LHAPDF environment variables
eval $(scram ru -sh)
rm Higgs0PMToZZTo4L_M-125_13TeV-powheg2-JHUgenV5_*.root
cmsRun ggH_125_LHEtoEDM_cfg.py 0
