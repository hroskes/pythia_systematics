from itertools import product
import subprocess

cmd = "(scancel %(oldjob)i; cd %(c)s && sbatch --job-name=%(c)s_%(a)i_%(b)i slurm.sh %(a)i %(b)i)"
cc = ["nominal", "scaleup", "scaledown", "tuneup", "tunedown"]
aa = range(14)
aa.remove(6)
aa.remove(11)
bb = range(10)

bjobs = subprocess.check_output(["squeue", "-u", "jroskes1@jhu.edu", "-o", "%.7i %.9P %.20j %.8u %.2t %.10M %.6D %R"])
jobs = []
for job in bjobs.split("\n"):
    if "launch failed requeued held" in job:
        jobs.append((int(job.split()[0]), job.split()[2]))

print jobs, len(aa) * len(bb) * len(cc)

for a, b, c in product(aa, bb, cc):
    repmap = {"a": a, "b": b, "c": c}
    for job in jobs:
        if "%(c)s_%(a)i_%(b)i"%repmap == job[1]:
            repmap["oldjob"] = job[0]
            print cmd%repmap
