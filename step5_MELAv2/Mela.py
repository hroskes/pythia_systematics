import array
from collections import Counter, Iterator, OrderedDict
import contextlib
from math import copysign
import os
import ROOT
import subprocess
import tempfile

@contextlib.contextmanager
def cd(newdir):
    """http://stackoverflow.com/a/24176022/5228524"""
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

ROOT.gROOT.Macro("$CMSSW_BASE/src/ZZMatrixElement/MELA/test/loadMELA.C")
ROOT.gROOT.LoadMacro("MelaWrapper.cc")
ROOT.gROOT.LoadMacro("Category.cc")
ROOT.gSystem.Load('libCondFormatsBTauObjects')
TVar = ROOT.TVar

mela = ROOT.Mela(13, 125, TVar.ERROR)

ROOT.SimpleParticle_t.id = property(lambda self: self.first)
ROOT.SimpleParticle_t.momentum = property(lambda self: self.second)
ROOT.SimpleParticle_t.pt = property(lambda self: self.momentum.Pt())
ROOT.SimpleParticle_t.eta = property(lambda self: self.momentum.Eta())

csvfile = "CSVv2_4invfb.csv"
CSVFile = ROOT.BTagCalibration("csvv2",csvfile)
btaggers = {}
for systematic in "central", "up", "down":
    btaggers[0,systematic] = btaggers[1,systematic] = ROOT.BTagCalibrationReader(CSVFile, 1, "mujets", systematic)
    btaggers[2,systematic] = ROOT.BTagCalibrationReader(CSVFile, 1, "incl", systematic)

def isbtagged(self, systematic):
    if abs(self.id) == 5:
        FLAV = 0
    elif abs(self.id) == 4:
        FLAV = 1
    elif 1 <= abs(self.id) <= 3 or self.id == 21:
        FLAV = 2
    result = btaggers[FLAV,systematic].eval(FLAV, copysign(min(abs(self.eta), 2.35), self.eta), min(self.pt, 669))
    print self.id, result
    return result
ROOT.SimpleParticle_t.isbtagged = isbtagged


class TreeWrapper(Iterator):
    def __init__(self, filename, newfilename, minevent=0, maxevent=None):
        self.filename = filename
        self.newfilename = newfilename
        self.minevent = minevent
        self.maxevent = maxevent

    def __enter__(self):
        assert not os.path.exists(self.newfilename)

        self.f = ROOT.TFile.Open(self.filename)
        try:
            tree = self.tree = self.f.SelectedTree
        except AttributeError:
            self.empty = True
            return self
        self.empty = False

        self.newf = ROOT.TFile.Open(self.newfilename, "recreate")
        self.newt = tree.CloneTree(0)

        if self.maxevent is None or self.maxevent >= tree.GetEntries():
            self.length = tree.GetEntries() - self.minevent
        else:
            self.length = self.maxevent - self.minevent + 1

        self.branches = OrderedDict()
        for branchname in self.floats:
            a = array.array("f", [0])
            self.branches[branchname] = a
            self.newt.Branch(branchname, a, branchname+"/F")
        for branchname in self.ints:
            a = array.array("i", [0])
            self.branches[branchname] = a
            self.newt.Branch(branchname, a, branchname+"/I")

        return self

    def __exit__(self, *args):
        if not self.empty:
            self.newt.Write()
            self.newf.Close()
        self.f.Close()

    def __iter__(self):
        self.__i = 0                               #at the beginning of next self.__i and self.__treeentry are
        self.__treeentry = self.minevent-1         # incremented, so they start at 1 and self.minevent
        return super(TreeWrapper, self).__iter__() # for the first entry

    def next(self):
        if self.empty: raise StopIteration
        while True:
            self.__i += 1
            self.__treeentry += 1
            i, t = self.__i, self.tree
            t.GetEntry(self.__treeentry)
            if i > self.length:
                raise StopIteration
            if i % 1000 == 0 or i == self.length:
                print i, "/", self.length
            if t.isSelected:
                break

    def associatedparticles(self):
        t = self.tree
        result = ROOT.SimpleParticleCollection_t()
        genaps = []
        for id, pt, eta, phi, m in zip(t.GenAssociatedParticleId, t.GenAssociatedParticlePt, t.GenAssociatedParticleEta, t.GenAssociatedParticlePhi, t.GenAssociatedParticleMass):
            p = ROOT.TLorentzVector()
            p.SetPtEtaPhiM(pt, eta, phi, m)
            genaps.append((id, p))

        for id, pt, eta, phi, m in zip(t.AssociatedParticleId, t.AssociatedParticlePt, t.AssociatedParticleEta, t.AssociatedParticlePhi, t.AssociatedParticleMass):
            p = ROOT.TLorentzVector()
            p.SetPtEtaPhiM(pt, eta, phi, m)
            mindr = float("infinity")
            if id == 0:
                for genid, genp in genaps:
                    dr = genp.DeltaR(p)
                    if dr < mindr:
                        id, mindr = genid, dr
            result.push_back(ROOT.SimpleParticle_t(id, p))
        return result

    def leptons(self):
        t = self.tree
        result = ROOT.SimpleParticleCollection_t()
        for i in range(1, 5):
            l = "Lep{}".format(i)
            id, pt, eta, phi, m = (getattr(t, l+v) for v in ("Id", "Pt", "Eta", "Phi", "Mass"))
            p = ROOT.TLorentzVector()
            p.SetPtEtaPhiM(pt, eta, phi, m)
            result.push_back(ROOT.SimpleParticle_t(id, p))
        return result

    def fillnewt(self):
        associatedparticles = self.associatedparticles()
        leptons = self.leptons()

        associatedleptons = [particle for particle in associatedparticles if abs(particle.id) in (11, 13, 15)]
        associatedleptonscounter = Counter(associatedleptons)
        associatedjets = [particle for particle in associatedparticles if abs(particle.id) in (1, 2, 3, 4, 5, 21)]

        self.nExtraLep = len(associatedleptons)
        self.nExtraZ = sum(min(associatedleptonscounter[i], associatedleptonscounter[-i]) for i in (11, 13, 15))
        cleanedJetsPt30 = [jet for jet in associatedjets if jet.pt >= 30]
        self.nCleanedJetsPt30 = len(cleanedJetsPt30)
        cleanedJetsPt30BTagged = [jet for jet in cleanedJetsPt30 if jet.isbtagged("central")]
        self.nCleanedJetsPt30BTagged = len(cleanedJetsPt30BTagged)

        leadingjets = ROOT.SimpleParticleCollection_t()
        if self.nCleanedJetsPt30 >= 1:
            leadingjets.push_back(ROOT.SimpleParticle_t(0, associatedjets[0].momentum))
        if self.nCleanedJetsPt30 >= 2:
            leadingjets.push_back(ROOT.SimpleParticle_t(0, associatedjets[1].momentum))
        mela.setInputEvent(leptons, leadingjets, 0, False)

        p_tmp = array.array('f', [0])

        useQGTagging = False
        jetQGLikelihood = array.array('f', [0]*self.nCleanedJetsPt30)

        self.pvbf_VAJHU_highestPTJets = self.phjj_VAJHU_highestPTJets = self.pwh_hadronic_VAJHU = self.pzh_hadronic_VAJHU = self.phj_VAJHU = self.pAux_vbf_VAJHU = None

        if self.nCleanedJetsPt30 >= 2:
            assert len(leadingjets) == 2
            mela.setProcess(TVar.HSMHiggs, TVar.JHUGen, TVar.JJVBF)
            mela.computeProdP(p_tmp, True)
            self.pvbf_VAJHU_highestPTJets = p_tmp[0]

            mela.setProcess(TVar.HSMHiggs, TVar.JHUGen, TVar.JJQCD)
            mela.computeProdP(p_tmp, True)
            self.phjj_VAJHU_highestPTJets = p_tmp[0]

            mela.setProcess(TVar.HSMHiggs, TVar.JHUGen, TVar.Had_WH);
            mela.computeProdP(p_tmp, True)
            self.pwh_hadronic_VAJHU = p_tmp[0]

            mela.setProcess(TVar.HSMHiggs, TVar.JHUGen, TVar.Had_ZH);
            mela.computeProdP(p_tmp, True)
            self.pzh_hadronic_VAJHU = p_tmp[0]

            self.phj_VAJHU = self.pAux_vbf_VAJHU = 0

        elif self.nCleanedJetsPt30 == 1:
            mela.setProcess(TVar.HSMHiggs, TVar.JHUGen, TVar.JQCD)
            mela.computeProdP(p_tmp, True)
            self.phj_VAJHU = p_tmp[0]

            mela.setProcess(TVar.HSMHiggs, TVar.JHUGen, TVar.JJVBF);
            mela.computeProdP(p_tmp, True); #Un-integrated ME
            self.pvbf_VAJHU_highestPTJets = p_tmp[0]
            mela.getPAux(p_tmp);         #= Integrated / un-integrated
            self.pAux_vbf_VAJHU = p_tmp[0]

            self.phjj_VAJHU_highestPTJets = self.pwh_hadronic_VAJHU = self.pzh_hadronic_VAJHU = 0

        else:
            self.pvbf_VAJHU_highestPTJets = self.phj_VAJHU = self.pAux_vbf_VAJHU = self.phjj_VAJHU_highestPTJets = self.pwh_hadronic_VAJHU = self.pzh_hadronic_VAJHU = 0

        mela.resetInputEvent()

        self.category = ROOT.categoryIchep16_noextern(
                                                      self.nExtraLep,
                                                      self.nExtraZ,
                                                      self.nCleanedJetsPt30,
                                                      self.nCleanedJetsPt30BTagged,
                                                      #jetQGLikelihood,
                                                      self.phjj_VAJHU_highestPTJets,
                                                      self.phj_VAJHU,
                                                      self.pvbf_VAJHU_highestPTJets,
                                                      self.pAux_vbf_VAJHU,
                                                      self.pwh_hadronic_VAJHU,
                                                      self.pzh_hadronic_VAJHU,
                                                      useQGTagging,
                                                     )

        for branchname, ptr in self.branches.iteritems():
            ptr[0] = getattr(self, branchname)
        self.newt.Fill()

    floats = [
              "phjj_VAJHU_highestPTJets",
              "phj_VAJHU",
              "pvbf_VAJHU_highestPTJets",
              "pAux_vbf_VAJHU",
              "pwh_hadronic_VAJHU",
              "pzh_hadronic_VAJHU",
             ]
    ints = [
            "nExtraLep",
            "nExtraZ",
            "nCleanedJetsPt30",
            "nCleanedJetsPt30BTagged",
            "category",
           ]

if __name__ == "__main__":
    for folder in "nominal", "scaleup", "scaledown", "tuneup", "tunedown":
        for filename in os.listdir(os.path.join("..", "step4_analyzer", folder)):
            if not filename.endswith(".root"): continue
            newfilename = os.path.join(folder, filename)
            filename = os.path.join("..", "step4_analyzer", folder, filename)
            assert os.path.exists(filename)
            if os.path.exists(newfilename): continue

            with TreeWrapper(filename, newfilename) as treewrapper:
                for entry in treewrapper:
                    treewrapper.fillnewt()
