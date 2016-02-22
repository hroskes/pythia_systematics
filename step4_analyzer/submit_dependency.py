from itertools import product
import subprocess


cmd = "(cd %(c)s && sbatch --dependency=afterok:%(pythiajob)i --job-name=%(c)s_%(a)i_%(b)i slurm.sh %(a)i %(b)i)"
cc = ["tuneup", "tunedown"]
aa = range(15)
aa.remove(6)
aa.remove(11)
bb = range(10)

bjobs = subprocess.check_output(["squeue", "-u", "jroskes1@jhu.edu", "-o", "%.7i %.9P %.20j %.8u %.2t %.10M %.6D %R"])
jobs = []
runningjobs = []
for job in bjobs.split("\n"):
    if "pythia" in job:
        jobs.append((int(job.split()[0]), job.split()[2]))
    elif len(job.split()) > 2:
        runningjobs.append(job.split()[2])

for a, b, c in product(aa, bb, cc):
    repmap = {"a": a, "b": b, "c": c}
    if "%(c)s_%(a)i_%(b)i"%repmap in runningjobs:
        continue
    for job in jobs:
        if "%(c)s_pythia_%(a)i"%repmap == job[1]:
            repmap["pythiajob"] = job[0]
            print cmd%repmap
            break
    else:
        assert False

