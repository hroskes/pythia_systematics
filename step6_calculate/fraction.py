from __future__ import division
from collections import OrderedDict
import os
import ROOT
import rootoverloads
import style

def fraction(folder):
    rootfile = os.path.join("..", "step5_MELAv2", folder, folder+".root")
    f = ROOT.TFile(rootfile)
    c = f.c1
    h = c[1]
    total = h.Integral()
    fractions = OrderedDict()
    for i in range(1, h.GetNbinsX()+1):
        fractions[h.GetXaxis().GetBinLabel(i)] = h.GetBinContent(i) / total
    return fractions

def table():
    row = "{:>17}"*7
    nominal = fraction("nominal")
    print row.format("", *nominal.keys())
    print row.format("nominal", *("{:.2f}%".format(value*100) for value in nominal.values()))
    for sys in "scaleup", "scaledown", "tuneup", "tunedown":
        fractions = fraction(sys)
        toformat = ["(abs) "+sys]
        for key in fractions:
            toformat.append("{:+6.2f}%".format((fractions[key] - nominal[key]) * 100))
        print row.format(*toformat)
    print
    for sys in "scaleup", "scaledown", "tuneup", "tunedown":
        fractions = fraction(sys)
        toformat = ["(rel) "+sys]
        for key in fractions:
            toformat.append("{:+6.2f}%".format((fractions[key] - nominal[key]) / nominal[key] * 100))
        print row.format(*toformat)

if __name__ == "__main__":
    table()
