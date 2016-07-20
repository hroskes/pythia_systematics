import os
import ROOT
import style

t = ROOT.TChain("SelectedTree")
for filename in os.listdir("."):
    if filename.endswith(".root"):
        t.Add(filename)

c_Mela2j = 1.1310070753097534

c1 = ROOT.TCanvas()
h = ROOT.TH1F("h", "h", 100, 0, 1)

totalwt = 0
length = t.GetEntries()
for i, entry in enumerate(t, start=1):
    totalwt += entry.isSelected*entry.MC_weight
    if entry.isSelected and t.nCleanedJetsPt30 >= 2:
        h.Fill(1/(1 + c_Mela2j * entry.phjj_VAJHU_highestPTJets / entry.pvbf_VAJHU_highestPTJets))
    if i % 10000 == 0:
        print i, "/", length

h.Scale(1/totalwt)

h.Draw()

for ext in "png eps root pdf".split():
    c1.SaveAs("Djet_{}.{}".format(os.path.basename(os.getcwd()), ext))
