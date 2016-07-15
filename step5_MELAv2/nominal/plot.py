import os
import ROOT
import style

t = ROOT.TChain("SelectedTree")
for filename in os.listdir("."):
    if filename.endswith(".root"):
        t.Add(filename)

c1 = ROOT.TCanvas()
t.Draw("category>>h", "MC_weight && isSelected")
h = ROOT.h
a = h.GetXaxis()
a.SetBinLabel(1, "Untagged")
a.SetBinLabel(2, "VBF 1 jet")
a.SetBinLabel(3, "VBF 2 jets")
a.SetBinLabel(4, "VH leptonic")
a.SetBinLabel(5, "VH hadronic")
a.SetBinLabel(6, "ttH")
for ext in "png eps root pdf".split():
    c1.SaveAs("{}.{}".format(os.path.basename(os.getcwd()), ext))
