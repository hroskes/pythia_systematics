import os
import ROOT
import sys

def fraction(*dirs):
    npass, nless, nnojets = {}, {}, {}
    for dir in dirs:
        t = ROOT.TChain("SelectedTree", "SelectedTree")
        for f in os.listdir(os.path.join("../step4_analyzer", dir)):
            if ".root" in f:
                t.Add(os.path.join("../step4_analyzer", dir, f))

        length = t.GetEntries()
        npass[dir] = 0
        nless[dir] = 0
        nnojets[dir] = 0
        for i, entry in enumerate(t):
            if entry.isSelected:
                pvbf = entry.vbf_p0plus_VAJHU
                phjj = entry.hjj_p0plus_VAJHU
                if pvbf == 0 or phjj == 0:
                    nnojets[dir] += 1
                else:
                    Djet = pvbf / (pvbf+phjj)
                    if Djet > 0.5:
                        npass[dir] += 1
                    else:
                        nless[dir] += 1
            if i % 10000 == 0:
                print i, "/", length

        print "Djet > 0.5:\t", npass[dir]
        print "Djet < 0.5:\t", nless[dir]
        print "not 2 jets:\t", nnojets[dir]
        print

    fraction, error = {}, {}
    for dir in dirs:
        n = {True: float(npass[dir]), False: float(nless[dir]+nnojets[dir])}
        error = {key: value**.5 for key, value in n.iteritems()}

        fraction[dir] = n[True] / (n[True]+n[False])
        error[dir] = (
                         (1/(n[True]+n[False]) - n[True] / (n[True]+n[False])**2) ** 2  *  error[True]**2
                       + (                     - n[True] / (n[True]+n[False])**2) ** 2  *  error[False]**2
                     )**.5

        print "%s: (%f +/- %f)%%" % (dir, fraction[dir]*100, error[dir]*100)
    print

    for a in "scale", "tune":
        print "%s:"%a
        for b in "up", "down":
            if fraction[a+b] >= fraction["nominal"]:
                print "    +%f%%" % ((fraction[a+b] / fraction["nominal"] - 1)*100)
        for b in "up", "down":
            if fraction[a+b] < fraction["nominal"]:
                print "    -%f%%" % ((1 - fraction[a+b] / fraction["nominal"])*100)
    

if __name__ == "__main__":
    dirs = ("nominal", "scaleup", "scaledown", "tuneup", "tunedown")
    fraction(*dirs)
