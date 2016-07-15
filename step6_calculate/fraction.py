from collections import namedtuple
import os
import ROOT
import style
import sys

Plot = namedtuple("Plot", ["dir", "title", "color"])

def fraction(*plots):

    bins = 50

    h, npass, nless, nnojets = {}, {}, {}, {}
    hstack = ROOT.THStack("Djet", "Djet")
    legend = ROOT.TLegend(.6, .6, .9, .9)
    legend.SetLineWidth(0)
    legend.SetLineColor(0)
    legend.SetFillStyle(0)
    for plot in plots:
        t = ROOT.TChain("SelectedTree", "SelectedTree")
        for f in os.listdir(os.path.join("../step4_analyzer", plot.dir)):
            if ".root" in f:
                t.Add(os.path.join("../step4_analyzer", plot.dir, f))

        h[plot] = ROOT.TH1F(plot.dir, plot.title, bins, 0, 1)
        h[plot].SetLineColor(plot.color)
        h[plot].SetLineWidth(3)
        hstack.Add(h[plot])
        legend.AddEntry(h[plot], plot.title, "l")

        length = t.GetEntries()
        npass[plot] = 0
        nless[plot] = 0
        nnojets[plot] = 0
        for i, entry in enumerate(t):
            if entry.isSelected:
                pvbf = entry.vbf_p0plus_VAJHU
                phjj = entry.hjj_p0plus_VAJHU
                if pvbf == 0 or phjj == 0:
                    nnojets[plot] += 1
                else:
                    Djet = pvbf / (pvbf+phjj)
                    h[plot].Fill(Djet)
                    if Djet > 0.5:
                        npass[plot] += 1
                    else:
                        nless[plot] += 1
            if i % 10000 == 0:
                print i, "/", length

        print "Djet > 0.5:\t", npass[plot]
        print "Djet < 0.5:\t", nless[plot]
        print "not 2 jets:\t", nnojets[plot]
        print
        h[plot].Scale(1.0/(npass[plot]+nless[plot]+nnojets[plot]))

    fraction, error = {}, {}
    for plot in plots:
        n = {True: float(npass[plot]), False: float(nless[plot]+nnojets[plot])}
        error = {key: value**.5 for key, value in n.iteritems()}

        fraction[plot.dir] = n[True] / (n[True]+n[False])
        error[plot.dir] = (
                              (1/(n[True]+n[False]) - n[True] / (n[True]+n[False])**2) ** 2  *  error[True]**2
                            + (                     - n[True] / (n[True]+n[False])**2) ** 2  *  error[False]**2
                          )**.5

        print "%s: (%f +/- %f)%%" % (plot.dir, fraction[plot.dir]*100, error[plot.dir]*100)
    print

    for a in "scale", "tune":
        print "%s:"%a
        for b in "up", "down":
            if fraction[a+b] >= fraction["nominal"]:
                print "    +%f%%" % ((fraction[a+b] / fraction["nominal"] - 1)*100)
        for b in "up", "down":
            if fraction[a+b] < fraction["nominal"]:
                print "    -%f%%" % ((1 - fraction[a+b] / fraction["nominal"])*100)

    c1 = ROOT.TCanvas()
    hstack.Draw("nostack")
    hstack.GetXaxis().SetTitle("D_{jet}")
    hstack.GetYaxis().SetTitle("fraction of events / %s"%(1.0/bins))
    legend.Draw()
    c1.SaveAs("test.png")
    c1.SaveAs("test.pdf")
    c1.SaveAs("test.eps")
    c1.SaveAs("test.root")

if __name__ == "__main__":
    plots = (
             Plot("nominal", "nominal", 1),
             Plot("scaleup", "scale up", 418),
             Plot("scaledown", "scale down", 3),
             Plot("tuneup", "tune up", 4),
             Plot("tunedown", "tune down", 7),
            )
    fraction(*plots)
