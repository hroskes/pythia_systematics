import os
import ROOT
import sys

t = ROOT.TChain("SelectedTree", "SelectedTree")
for f in os.listdir("."):
    if ".root" in f:
        t.Add(f)

for entry in t:
    if entry.hjj_p0plus_VAJHU != 0:
        entry.Show()
        break

