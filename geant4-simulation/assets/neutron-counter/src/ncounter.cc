// ncounter: minimal Geant4 application for a moderated neutron counter.
//
// Geometry : moderator box (polyethylene or water, with thermal-scattering H), an axial
//            source channel, a ring of gas proportional tubes (3He at a given pressure),
//            and an optional borated-polyethylene shell. All dimensions set from macros.
// Source   : point source; mono, Watt fission, thermal Maxwellian, histogram file or event list;
//            isotropic or Legendre (a2, a4) angular distribution about +z.
// Scoring  : stepping action. Gas captures (neutron step producing p + t), energy deposit per
//            tube, first-capture time (die-away), and neutron absorptions anywhere (any hadronic
//            end of a neutron without an outgoing neutron: r^2 from the source and time, for
//            diffusion-length and capture-time checks). One JSON summary per run, optional CSV.
//
// Usage : ncounter MACRO --seeds S1 S2 [--phys QGSP_BIC_HP] [--no-tsl]
//         Seeds are required on the command line and must not be set again in the macro.

#include "G4Box.hh"
#include "G4Element.hh"
#include "G4Event.hh"
#include "G4GenericMessenger.hh"
#include "G4Isotope.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4Neutron.hh"
#include "G4NistManager.hh"
#include "G4ParticleGun.hh"
#include "G4PhysListFactory.hh"
#include "G4PhysicalConstants.hh"
#include "G4PrimaryVertex.hh"
#include "G4PVPlacement.hh"
#include "G4Proton.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4RunManagerFactory.hh"
#include "G4Step.hh"
#include "G4SubtractionSolid.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThermalNeutrons.hh"
#include "G4Track.hh"
#include "G4Triton.hh"
#include "G4Tubs.hh"
#include "G4UImanager.hh"
#include "G4UserEventAction.hh"
#include "G4UserRunAction.hh"
#include "G4UserSteppingAction.hh"
#include "G4VModularPhysicsList.hh"
#include "G4VProcess.hh"
#include "G4ProcessType.hh"
#include "G4VUserActionInitialization.hh"
#include "G4VUserDetectorConstruction.hh"
#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4Version.hh"
#include "Randomize.hh"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <sys/stat.h>
#include <vector>

// ------------------------------------------------------------------ configuration
// Geant4 internal units throughout (set with units from the macro).
struct Config {
  // geometry
  G4String moderator = "PE";            // PE | water
  G4double modX = 30 * cm, modY = 30 * cm, modZ = 40 * cm;
  G4double modDensity = 0.95 * g / cm3; // PE only; water uses G4_WATER-like 1.0
  G4double holeR = 2.0 * cm;            // axial source channel radius (0 = none)
  G4int nTubes = 8;
  G4double ringR = 9 * cm, ringPhase = 0 * deg;
  G4double tubeR = 1.25 * cm, tubeWall = 0.05 * cm, tubeActive = 30 * cm;
  G4double gasPressure = 4 * bar, gasTemperature = 293.15 * kelvin;
  G4double bpeThick = 0;                // borated-PE shell outside the moderator (0 = none)
  G4double bpeBoron = 0.05;             // natural-B mass fraction
  G4double bpeDensity = 1.0 * g / cm3;
  // source
  G4String spectrum = "mono";           // mono | watt | thermal | hist | list
  G4double energy = 1 * MeV;            // mono
  G4double wattA = 1.18 * MeV, wattB = 1.034 / MeV;  // Watt parameters (check against your source)
  G4double kT = 0.0253 * eV;            // thermal Maxwellian flux spectrum
  G4String file = "";                   // hist: E_low_MeV,E_high_MeV,weight ; list: E_MeV,ux,uy,uz[,w]
  G4ThreeVector position;               // source position
  G4double a2 = 0, a4 = 0;              // W(theta) = 1 + a2 P2 + a4 P4 about +z
  // output
  G4String outDir = ".", tag = "run";
  G4double threshold = 150 * keV;       // per-tube deposit threshold for a "count"
  G4bool csv = false;                   // per-capture CSV
  size_t listRows = 0;                  // list source: rows read, and whether they were reused
  G4bool listWrapped = false;
};
static Config CFG;
static G4LogicalVolume* gGasLV = nullptr;
static std::vector<G4ThreeVector> gTubeXY;
static G4String gPhysName = "QGSP_BIC_HP";
static G4bool gTSL = true;
static long gSeeds[2] = {-1, -1};
static G4String gRunManagerType = "";

// ------------------------------------------------------------------ accumulators
static const int NT = 60;  // log10(t/us) from -1 to 5, 10 bins per decade
struct Event {
  std::vector<G4double> edep;
  G4int nGasCap = 0, capTube = -1;
  G4double capTime = -1, w = 1, e0 = 0;
};
struct Run {
  long nGen = 0;
  G4double sumW = 0, sumW2 = 0, wGasCap = 0, wGasCap2 = 0, wCount = 0, wCount2 = 0, sumT = 0, sumT2 = 0;
  G4double wAbs = 0, sumR2 = 0, sumTAbs = 0;  // neutron absorptions anywhere: r^2 (cm^2), time (us)
  G4double sumE0 = 0;
  std::vector<G4double> tube, tHist;
};
static Event EV;
static Run RUN;

// ------------------------------------------------------------------ geometry
class Detector : public G4VUserDetectorConstruction {
 public:
  Detector() {
    fM = new G4GenericMessenger(this, "/nc/geo/", "geometry (set before /run/initialize)");
    fM->DeclareProperty("moderator", CFG.moderator, "PE | water");
    fM->DeclarePropertyWithUnit("modX", "cm", CFG.modX);
    fM->DeclarePropertyWithUnit("modY", "cm", CFG.modY);
    fM->DeclarePropertyWithUnit("modZ", "cm", CFG.modZ);
    fM->DeclarePropertyWithUnit("modDensity", "g/cm3", CFG.modDensity);
    fM->DeclarePropertyWithUnit("holeR", "cm", CFG.holeR);
    fM->DeclareProperty("nTubes", CFG.nTubes);
    fM->DeclarePropertyWithUnit("ringR", "cm", CFG.ringR);
    fM->DeclarePropertyWithUnit("ringPhase", "deg", CFG.ringPhase);
    fM->DeclarePropertyWithUnit("tubeR", "cm", CFG.tubeR);
    fM->DeclarePropertyWithUnit("tubeWall", "cm", CFG.tubeWall);
    fM->DeclarePropertyWithUnit("tubeActive", "cm", CFG.tubeActive);
    fM->DeclarePropertyWithUnit("gasPressure", "bar", CFG.gasPressure);
    fM->DeclarePropertyWithUnit("gasTemperature", "kelvin", CFG.gasTemperature);
    fM->DeclarePropertyWithUnit("bpeThick", "cm", CFG.bpeThick);
    fM->DeclareProperty("bpeBoron", CFG.bpeBoron, "natural-B mass fraction");
    fM->DeclarePropertyWithUnit("bpeDensity", "g/cm3", CFG.bpeDensity);
  }

  G4VPhysicalVolume* Construct() override {
    auto nist = G4NistManager::Instance();
    // Hydrogen bound in the moderator: the element name selects the thermal-scattering
    // (S(alpha,beta)) table in G4ThermalNeutrons. A plain "H" would be treated as free gas.
    const bool water = CFG.moderator == "water";
    auto hTS = new G4Element(water ? "TS_H_of_Water" : "TS_H_of_Polyethylene", "H", 1., 1.00794 * g / mole);
    auto elC = nist->FindOrBuildElement("C");
    G4Material* mod;
    if (water) {
      mod = new G4Material("Water_TS", 1.0 * g / cm3, 2, kStateLiquid);
      mod->AddElement(hTS, 2);
      mod->AddElement(nist->FindOrBuildElement("O"), 1);
    } else if (CFG.moderator == "PE") {
      mod = new G4Material("PE_TS", CFG.modDensity, 2);
      mod->AddElement(elC, 1);
      mod->AddElement(hTS, 2);
    } else {
      G4Exception("Detector", "nc001", FatalException, "moderator must be PE or water");
      return nullptr;
    }
    // 3He gas: density from the ideal gas law, rho = p M / (R T).
    const G4double M3 = 3.0160293 * g / mole;
    auto he3iso = new G4Isotope("He3", 2, 3, M3);
    auto he3el = new G4Element("Helium3", "He3", 1);
    he3el->AddIsotope(he3iso, 1.0);
    const G4double rhoGas = CFG.gasPressure * M3 / (k_Boltzmann * Avogadro * CFG.gasTemperature);
    auto gas = new G4Material("He3_gas", rhoGas, 1, kStateGas, CFG.gasTemperature, CFG.gasPressure);
    gas->AddElement(he3el, 1);
    auto steel = nist->FindOrBuildMaterial("G4_STAINLESS-STEEL");
    auto vacuum = nist->FindOrBuildMaterial("G4_Galactic");
    auto air = nist->FindOrBuildMaterial("G4_AIR");

    const G4double hx = CFG.modX / 2, hy = CFG.modY / 2, hz = CFG.modZ / 2, t = CFG.bpeThick;
    auto world = new G4LogicalVolume(new G4Box("World", hx + t + 50 * cm, hy + t + 50 * cm, hz + t + 50 * cm),
                                     air, "World");
    auto worldPV = new G4PVPlacement(nullptr, {}, world, "World", nullptr, false, 0);

    auto modLV = new G4LogicalVolume(new G4Box("Moderator", hx, hy, hz), mod, "Moderator");
    Place(new G4PVPlacement(nullptr, {}, modLV, "Moderator", world, false, 0));

    if (t > 0) {  // borated-PE shell = outer box - inner box - source channel
      auto bpe = new G4Material("BPE", CFG.bpeDensity, 3);
      const G4double fH = 2 * 1.00794 / (2 * 1.00794 + 12.0107), fPE = 1 - CFG.bpeBoron;
      bpe->AddElement(hTS, fPE * fH);
      bpe->AddElement(elC, fPE * (1 - fH));
      bpe->AddElement(nist->FindOrBuildElement("B"), CFG.bpeBoron);
      G4VSolid* shell = new G4SubtractionSolid("BPE_box", new G4Box("BPE_o", hx + t, hy + t, hz + t),
                                           new G4Box("BPE_i", hx, hy, hz));
      if (CFG.holeR > 0) shell = new G4SubtractionSolid("BPE", shell, new G4Tubs("BPE_c", 0, CFG.holeR, hz + t + 1 * cm, 0, twopi));
      Place(new G4PVPlacement(nullptr, {}, new G4LogicalVolume(shell, bpe, "BPE"), "BPE", world, false, 0));
    }
    if (CFG.holeR > 0)
      Place(new G4PVPlacement(nullptr, {}, new G4LogicalVolume(new G4Tubs("Channel", 0, CFG.holeR, hz, 0, twopi),
                                                               vacuum, "Channel"), "Channel", modLV, false, 0));

    auto tubeLV = new G4LogicalVolume(new G4Tubs("Tube", 0, CFG.tubeR, CFG.tubeActive / 2 + CFG.tubeWall, 0, twopi),
                                      steel, "Tube");
    gGasLV = new G4LogicalVolume(new G4Tubs("Gas", 0, CFG.tubeR - CFG.tubeWall, CFG.tubeActive / 2, 0, twopi), gas, "Gas");
    Place(new G4PVPlacement(nullptr, {}, gGasLV, "Gas", tubeLV, false, 0));
    gTubeXY.clear();
    for (G4int i = 0; i < CFG.nTubes; ++i) {
      const G4double phi = CFG.ringPhase + twopi * i / CFG.nTubes;
      gTubeXY.emplace_back(CFG.ringR * std::cos(phi), CFG.ringR * std::sin(phi), 0);
      Place(new G4PVPlacement(nullptr, gTubeXY.back(), tubeLV, "Tube", modLV, false, i));
    }
    if (fOverlaps) G4Exception("Detector", "nc002", FatalException, "overlapping volumes: fix the geometry");
    G4cout << "NCGEOM moderator=" << CFG.moderator << " tubes=" << CFG.nTubes
           << " gas_density_g_cm3=" << rhoGas / (g / cm3) << " overlaps=" << fOverlaps << G4endl;
    return worldPV;
  }

 private:
  void Place(G4PVPlacement* pv) { fOverlaps += pv->CheckOverlaps(2000, 0., false) ? 1 : 0; }
  G4GenericMessenger* fM;
  G4int fOverlaps = 0;
};

// ------------------------------------------------------------------ source
class Source : public G4VUserPrimaryGeneratorAction {
 public:
  Source() : fGun(new G4ParticleGun(1)) {
    fGun->SetParticleDefinition(G4Neutron::Definition());
    fM = new G4GenericMessenger(this, "/nc/gun/", "point neutron source");
    fM->DeclareProperty("spectrum", CFG.spectrum, "mono | watt | thermal | hist | list");
    fM->DeclarePropertyWithUnit("energy", "MeV", CFG.energy);
    fM->DeclarePropertyWithUnit("wattA", "MeV", CFG.wattA);
    fM->DeclareProperty("wattB", fWattB, "Watt b in 1/MeV");
    fM->DeclarePropertyWithUnit("kT", "eV", CFG.kT);
    fM->DeclareProperty("file", CFG.file, "hist or list input file");
    fM->DeclarePropertyWithUnit("position", "cm", CFG.position);
    fM->DeclareProperty("a2", CFG.a2);
    fM->DeclareProperty("a4", CFG.a4);
  }
  ~Source() override { delete fGun; delete fM; }

  void GeneratePrimaries(G4Event* ev) override {
    CFG.wattB = fWattB / MeV;
    G4double E = 0, w = 1;
    G4ThreeVector dir = Direction();
    if (CFG.spectrum == "mono") E = CFG.energy;
    else if (CFG.spectrum == "thermal") E = -CFG.kT * std::log(G4UniformRand() * G4UniformRand());
    else if (CFG.spectrum == "watt") E = Watt(CFG.wattA, CFG.wattB);
    else if (CFG.spectrum == "hist") E = FromHistogram();
    else if (CFG.spectrum == "list") FromList(E, dir, w);
    else G4Exception("Source", "nc010", FatalException, ("unknown spectrum " + CFG.spectrum).c_str());
    fGun->SetParticleEnergy(E);
    fGun->SetParticleMomentumDirection(dir);
    fGun->SetParticlePosition(CFG.position);
    fGun->GeneratePrimaryVertex(ev);
    ev->GetPrimaryVertex()->SetWeight(w);
    EV.w = w;
    EV.e0 = E;
  }

 private:
  // Maxwellian with temperature T: E = -T (ln u1 + ln u2 cos^2(pi u3 / 2)).
  static G4double Maxwell(G4double T) {
    const G4double c = std::cos(halfpi * G4UniformRand());
    return -T * (std::log(G4UniformRand()) + std::log(G4UniformRand()) * c * c);
  }
  // Watt spectrum exp(-E/a) sinh(sqrt(bE)), sampled as a Maxwellian plus a boost.
  static G4double Watt(G4double a, G4double b) {
    const G4double w = Maxwell(a);
    return w + 0.25 * a * a * b + (2 * G4UniformRand() - 1) * std::sqrt(a * a * b * w);
  }
  // Isotropic, or W(cos) = 1 + a2 P2 + a4 P4 about +z by rejection.
  G4ThreeVector Direction() {
    const G4double wmax = 1 + std::fabs(CFG.a2) + std::fabs(CFG.a4);
    if (CFG.a2 != fCheckedA2 || CFG.a4 != fCheckedA4) {  // W must be non-negative everywhere
      for (int i = 0; i <= 2000; ++i) {
        const G4double x = -1 + i / 1000.0, q2 = 0.5 * (3 * x * x - 1), q4 = (35 * x * x * x * x - 30 * x * x + 3) / 8;
        if (1 + CFG.a2 * q2 + CFG.a4 * q4 < 0)
          G4Exception("Source", "nc014", FatalException, "a2, a4 give W(theta) < 0 somewhere");
      }
      fCheckedA2 = CFG.a2; fCheckedA4 = CFG.a4;
    }
    G4double c;
    while (true) {
      c = 2 * G4UniformRand() - 1;
      const G4double p2 = 0.5 * (3 * c * c - 1), p4 = (35 * c * c * c * c - 30 * c * c + 3) / 8;
      if (G4UniformRand() * wmax <= 1 + CFG.a2 * p2 + CFG.a4 * p4) break;
    }
    const G4double sinT = std::sqrt(1 - c * c), phi = twopi * G4UniformRand();
    return {sinT * std::cos(phi), sinT * std::sin(phi), c};
  }
  static std::vector<std::vector<G4double>> ReadCsv(const G4String& path, size_t ncol) {
    std::ifstream in(path);
    if (!in) G4Exception("Source", "nc011", FatalException, ("cannot open " + path).c_str());
    std::vector<std::vector<G4double>> rows;
    std::string line;
    while (std::getline(in, line)) {
      if (line.empty() || line[0] == '#') continue;
      std::replace(line.begin(), line.end(), ',', ' ');
      std::istringstream ss(line);
      std::vector<G4double> r;
      G4double x;
      while (ss >> x) r.push_back(x);
      if (r.size() >= ncol) rows.push_back(r);
    }
    if (rows.empty()) G4Exception("Source", "nc012", FatalException, ("no data rows in " + path).c_str());
    return rows;
  }
  G4double FromHistogram() {  // uniform within each bin
    if (fCdf.empty()) {
      fBins = ReadCsv(CFG.file, 3);
      G4double sum = 0;
      for (auto& r : fBins) fCdf.push_back(sum += r[2]);
      for (auto& c : fCdf) c /= sum;
    }
    const size_t i = std::lower_bound(fCdf.begin(), fCdf.end(), G4UniformRand()) - fCdf.begin();
    const auto& r = fBins[std::min(i, fBins.size() - 1)];
    return (r[0] + G4UniformRand() * (r[1] - r[0])) * MeV;
  }
  void FromList(G4double& E, G4ThreeVector& dir, G4double& w) {  // cycles through the file
    if (fList.empty()) fList = ReadCsv(CFG.file, 4);
    if (fNext == fList.size() && !fWrapped) {
      fWrapped = true;
      G4Exception("Source", "nc013", JustWarning,
                  "event list exhausted: rows are reused, so events are no longer independent");
    }
    CFG.listRows = fList.size();
    CFG.listWrapped = fWrapped;
    const auto& r = fList[fNext++ % fList.size()];
    E = r[0] * MeV;
    dir = G4ThreeVector(r[1], r[2], r[3]).unit();
    w = r.size() > 4 ? r[4] : 1.0;
  }
  G4ParticleGun* fGun;
  G4GenericMessenger* fM;
  G4double fWattB = 1.034;  // 1/MeV
  G4double fCheckedA2 = 0, fCheckedA4 = 0;
  std::vector<std::vector<G4double>> fBins, fList;
  std::vector<G4double> fCdf;
  size_t fNext = 0;
  G4bool fWrapped = false;
};

// ------------------------------------------------------------------ scoring
class Stepping : public G4UserSteppingAction {
 public:
  void UserSteppingAction(const G4Step* step) override {
    auto pre = step->GetPreStepPoint();
    auto track = step->GetTrack();
    const bool neutron = track->GetDefinition() == G4Neutron::Definition();
    if (neutron && track->GetTrackStatus() == fStopAndKill) {
      // Absorption: the neutron ends in a hadronic process without an outgoing neutron
      // (radiative capture, 3He(n,p)t, 10B(n,a)7Li, ...). Process names differ between versions.
      auto proc = step->GetPostStepPoint()->GetProcessDefinedStep();
      if (proc && proc->GetProcessType() == fHadronic) {
        bool nOut = false;
        for (auto sec : *step->GetSecondaryInCurrentStep()) nOut |= sec->GetDefinition() == G4Neutron::Definition();
        if (!nOut) {
          RUN.wAbs += EV.w;
          RUN.sumR2 += EV.w * (step->GetPostStepPoint()->GetPosition() - CFG.position).mag2() / (cm * cm);
          RUN.sumTAbs += EV.w * step->GetPostStepPoint()->GetGlobalTime() / microsecond;
        }
      }
    }
    if (pre->GetPhysicalVolume()->GetLogicalVolume() != gGasLV) return;
    const G4int tube = pre->GetTouchable()->GetCopyNumber(1);  // copy number of the mother tube
    EV.edep[tube] += step->GetTotalEnergyDeposit();
    if (!neutron) return;
    bool p = false, t = false;  // 3He(n,p)t: identify by the secondaries of this step
    for (auto sec : *step->GetSecondaryInCurrentStep()) {
      p |= sec->GetDefinition() == G4Proton::Definition();
      t |= sec->GetDefinition() == G4Triton::Definition();
    }
    if (p && t && EV.nGasCap++ == 0) {
      EV.capTube = tube;
      EV.capTime = step->GetPostStepPoint()->GetGlobalTime();
    }
  }
};

class EventAction : public G4UserEventAction {
 public:
  void BeginOfEventAction(const G4Event*) override {
    const G4double w = EV.w, e0 = EV.e0;  // set by the generator just before
    EV = Event();
    EV.w = w; EV.e0 = e0;
    EV.edep.assign(std::max<G4int>(CFG.nTubes, 1), 0.);
  }
  void EndOfEventAction(const G4Event* ev) override {
    RUN.nGen++;
    RUN.sumW += EV.w;
    RUN.sumW2 += EV.w * EV.w;
    RUN.sumE0 += EV.w * EV.e0;
    G4double emax = 0;
    for (auto e : EV.edep) emax = std::max(emax, e);
    if (emax > CFG.threshold) { RUN.wCount += EV.w; RUN.wCount2 += EV.w * EV.w; }
    if (EV.nGasCap == 0) return;
    RUN.wGasCap += EV.w; RUN.wGasCap2 += EV.w * EV.w;
    RUN.tube[EV.capTube] += EV.w;
    const G4double tus = EV.capTime / microsecond;
    RUN.sumT += EV.w * tus; RUN.sumT2 += EV.w * tus * tus;
    // [0] underflow (< 0.1 us), [1..NT] log bins, [NT+1] overflow (>= 1e5 us)
    const int b = tus < 0.1 ? 0 : (tus >= 1e5 ? NT + 1 : 1 + std::min(NT - 1, (int)((std::log10(tus) + 1) * 10)));
    RUN.tHist[b] += EV.w;
    if (fCsv) *fCsv << ev->GetEventID() << "," << EV.capTube << "," << tus << "," << emax / keV << ","
                    << EV.e0 / MeV << "," << EV.w << "\n";
  }
  std::ofstream* fCsv = nullptr;
};

class RunAction : public G4UserRunAction {
 public:
  explicit RunAction(EventAction* ea) : fEA(ea) {
    fM = new G4GenericMessenger(this, "/nc/out/", "output");
    fM->DeclareProperty("dir", CFG.outDir);
    fM->DeclareProperty("tag", CFG.tag);
    fM->DeclarePropertyWithUnit("threshold", "keV", CFG.threshold);
    fM->DeclareProperty("csv", CFG.csv, "write one CSV row per event with a gas capture");
  }
  void BeginOfRunAction(const G4Run* run) override {
    RUN = Run();
    RUN.tube.assign(std::max<G4int>(CFG.nTubes, 1), 0.);
    RUN.tHist.assign(NT + 2, 0.);
    if (CFG.csv) {
      fCsv.open(Name(run, "_captures.csv"));
      fCsv << "event,tube,t_us,edep_max_keV,E0_MeV,weight\n";
      fEA->fCsv = &fCsv;
    }
  }
  void EndOfRunAction(const G4Run* run) override {
    if (fCsv.is_open()) { fCsv.close(); fEA->fCsv = nullptr; }
    const G4double W = RUN.sumW > 0 ? RUN.sumW : 1;
    const G4double tm = RUN.wGasCap > 0 ? RUN.sumT / RUN.wGasCap : 0;
    std::ofstream f(Name(run, ".json"));
    f.precision(10);
    f << "{\n  \"run\": " << run->GetRunID() << ", \"tag\": " << Q(CFG.tag) << ",\n"
      << "  \"geant4\": \"" << G4Version << "\", \"physics_list\": \"" << gPhysName << "\", \"thermal_scattering\": "
      << (gTSL ? "true" : "false") << ",\n"
      << "  \"seeds\": [" << gSeeds[0] << ", " << gSeeds[1] << "], \"engine\": \""
      << G4Random::getTheEngine()->name() << "\", \"run_manager\": " << Q(gRunManagerType) << ",\n"
      << "  \"geometry\": {\"moderator\": \"" << CFG.moderator << "\", \"mod_cm\": [" << CFG.modX / cm << ", "
      << CFG.modY / cm << ", " << CFG.modZ / cm << "], \"mod_density_g_cm3\": " << CFG.modDensity / (g / cm3)
      << ", \"hole_r_cm\": " << CFG.holeR / cm << ", \"n_tubes\": " << CFG.nTubes << ", \"ring_r_cm\": " << CFG.ringR / cm
      << ", \"tube_r_cm\": " << CFG.tubeR / cm << ", \"tube_wall_cm\": " << CFG.tubeWall / cm << ", \"tube_active_cm\": "
      << CFG.tubeActive / cm << ", \"gas_pressure_bar\": " << CFG.gasPressure / bar << ", \"bpe_thick_cm\": "
      << CFG.bpeThick / cm << ", \"bpe_boron\": " << CFG.bpeBoron << "},\n"
      << "  \"source\": {\"spectrum\": \"" << CFG.spectrum << "\", \"energy_MeV\": " << CFG.energy / MeV
      << ", \"watt_a_MeV\": " << CFG.wattA / MeV << ", \"watt_b_per_MeV\": " << CFG.wattB * MeV << ", \"kT_eV\": "
      << CFG.kT / eV << ", \"file\": " << Q(CFG.file) << ", \"list_rows\": " << CFG.listRows
      << ", \"list_wrapped\": " << (CFG.listWrapped ? "true" : "false") << ", \"position_cm\": [" << CFG.position.x() / cm << ", "
      << CFG.position.y() / cm << ", " << CFG.position.z() / cm << "], \"a2\": " << CFG.a2 << ", \"a4\": " << CFG.a4
      << ", \"mean_E0_MeV\": " << RUN.sumE0 / W / MeV << "},\n"
      << "  \"n_generated\": " << RUN.nGen << ", \"sum_weights\": " << RUN.sumW << ", \"sum_weights2\": " << RUN.sumW2 << ",\n"
      << "  \"gas_captures\": " << RUN.wGasCap << ", \"gas_captures_w2\": " << RUN.wGasCap2
      << ", \"efficiency_capture\": " << RUN.wGasCap / W << ",\n"
      << "  \"threshold_keV\": " << CFG.threshold / keV << ", \"counts_above_threshold\": " << RUN.wCount
      << ", \"counts_above_threshold_w2\": " << RUN.wCount2 << ", \"efficiency_threshold\": " << RUN.wCount / W << ",\n"
      << "  \"captures_per_tube\": " << Arr(RUN.tube) << ",\n"
      << "  \"capture_time_mean_us\": " << tm << ", \"capture_time_rms_us\": "
      << (RUN.wGasCap > 0 ? std::sqrt(std::max(0., RUN.sumT2 / RUN.wGasCap - tm * tm)) : 0) << ",\n"
      << "  \"capture_time_hist\": {\"edges\": \"log10(t/us) from -1 to 5, 10 bins per decade; first entry underflow, last overflow\", \"counts\": "
      << Arr(RUN.tHist) << "},\n"
      << "  \"neutron_absorptions_anywhere\": " << RUN.wAbs << ", \"mean_r2_absorption_cm2\": "
      << (RUN.wAbs > 0 ? RUN.sumR2 / RUN.wAbs : 0) << ", \"absorption_time_mean_us\": "
      << (RUN.wAbs > 0 ? RUN.sumTAbs / RUN.wAbs : 0) << "\n}\n";
    G4cout << "NCSUMMARY tag=" << CFG.tag << " run=" << run->GetRunID() << " events=" << RUN.nGen
           << " gas_captures=" << RUN.wGasCap << " eff=" << RUN.wGasCap / W << " t_mean_us=" << tm
           << " absorptions_anywhere=" << RUN.wAbs << G4endl;
  }

 private:
  static std::string Q(const std::string& in) {  // JSON string with escaping
    std::ostringstream o;
    o << '"';
    for (char c : in) {
      if (c == '"' || c == '\\') o << '\\' << c;
      else if ((unsigned char)c < 0x20) o << "\\u" << std::hex << std::setw(4) << std::setfill('0') << (int)c << std::dec;
      else o << c;
    }
    o << '"';
    return o.str();
  }
  static std::string Arr(const std::vector<G4double>& v) {
    std::ostringstream o;
    o << "[";
    for (size_t i = 0; i < v.size(); ++i) o << (i ? ", " : "") << v[i];
    o << "]";
    return o.str();
  }
  static std::string Name(const G4Run* run, const char* ext) {
    mkdir(CFG.outDir.c_str(), 0755);
    std::ostringstream o;
    o << CFG.outDir << "/" << CFG.tag << "_r" << run->GetRunID() << ext;
    return o.str();
  }
  EventAction* fEA;
  G4GenericMessenger* fM;
  std::ofstream fCsv;
};

class Actions : public G4VUserActionInitialization {
 public:
  void Build() const override {
    auto ea = new EventAction;
    SetUserAction(new Source);
    SetUserAction(ea);
    SetUserAction(new RunAction(ea));
    SetUserAction(new Stepping);
  }
};

// ------------------------------------------------------------------ main
static bool IsDir(const char* p) { struct stat st; return p && stat(p, &st) == 0 && S_ISDIR(st.st_mode); }

int main(int argc, char** argv) {
  if (argc < 2) {
    G4cerr << "usage: ncounter MACRO --seeds S1 S2 [--phys NAME] [--no-tsl]" << G4endl;
    return 2;
  }
  for (int i = 2; i < argc; ++i) {
    const std::string a = argv[i];
    if (a == "--no-tsl") gTSL = false;
    else if (a == "--phys" && i + 1 < argc) gPhysName = argv[++i];
    else if (a == "--seeds" && i + 2 < argc) {
      for (int k = 0; k < 2; ++k) {
        char* end = nullptr;
        const char* v = argv[++i];
        gSeeds[k] = std::strtol(v, &end, 10);
        if (end == v || *end || gSeeds[k] < 0) { G4cerr << "--seeds needs two non-negative integers" << G4endl; return 2; }
      }
    }
    else { G4cerr << "unknown option " << a << G4endl; return 2; }
  }
  if (gSeeds[0] < 0) { G4cerr << "explicit seeds are required: --seeds S1 S2" << G4endl; return 2; }
  {  // seeds set in the macro would silently replace the recorded ones
    std::ifstream mac(argv[1]);
    if (!mac) { G4cerr << "cannot open macro " << argv[1] << G4endl; return 2; }
    std::string line;
    while (std::getline(mac, line))
      if (line.find("/random/") != std::string::npos && line.find_first_not_of(" \t") == line.find("/random/")) {
        G4cerr << "the macro sets random-engine state; give seeds only with --seeds" << G4endl;
        return 2;
      }
  }
  // Neutron counting needs the HP neutron models; _HPT lists already contain thermal scattering.
  const bool hpt = gPhysName.size() > 4 && gPhysName.compare(gPhysName.size() - 4, 4, "_HPT") == 0;
  const bool hp = hpt || gPhysName.find("_HP") != std::string::npos || gPhysName.rfind("Shielding", 0) == 0;
  if (!hp) {
    G4cerr << "neutron counting needs an HP list (QGSP_BIC_HP, FTFP_BERT_HP, Shielding, or an _HPT list): "
           << gPhysName << G4endl;
    return 2;
  }
  if (hpt && !gTSL) { G4cerr << "--no-tsl contradicts an _HPT list" << G4endl; return 2; }
  // Fail early if the neutron data (and its thermal-scattering part) are not where Geant4 will look.
  const char* ndl = std::getenv("G4NEUTRONHPDATA");
  if (!IsDir(ndl) || (gTSL && !IsDir((std::string(ndl) + "/ThermalScattering").c_str()))) {
    G4cerr << "G4NEUTRONHPDATA is unset or lacks ThermalScattering/: " << (ndl ? ndl : "(unset)") << G4endl;
    return 3;
  }
  // Serial on purpose: the accumulators are not thread-safe. G4FORCE_RUN_MANAGER_TYPE could override
  // the factory's choice, so check the type actually created.
  auto rm = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);
  if (rm->GetRunManagerType() != G4RunManager::sequentialRM) {
    G4cerr << "this template needs the serial run manager (unset G4FORCE_RUN_MANAGER_TYPE)" << G4endl;
    return 2;
  }
  gRunManagerType = "Serial";
  rm->SetUserInitialization(new Detector);
  G4PhysListFactory factory;
  G4VModularPhysicsList* phys = factory.GetReferencePhysList(gPhysName);
  if (!phys) { G4cerr << "unknown physics list " << gPhysName << G4endl; return 2; }
  if (gTSL && !hpt) phys->RegisterPhysics(new G4ThermalNeutrons(0));  // never twice
  rm->SetUserInitialization(phys);
  rm->SetUserInitialization(new Actions);
  auto ui = G4UImanager::GetUIpointer();
  {
    std::ostringstream cmd;  // note: "s" is the Geant4 unit of time; do not reuse it as a name
    cmd << "/random/setSeeds " << gSeeds[0] << " " << gSeeds[1];
    if (ui->ApplyCommand(cmd.str()) != 0) { G4cerr << "/random/setSeeds failed" << G4endl; return 2; }
  }
  G4cout << "NCSTART geant4=" << G4Version << " run_manager=" << gRunManagerType << " physics=" << gPhysName << " tsl=" << gTSL
         << " seeds=" << gSeeds[0] << "," << gSeeds[1] << " G4NEUTRONHPDATA=" << ndl << G4endl;
  const G4int status = ui->ApplyCommand("/control/execute " + G4String(argv[1]));
  delete rm;
  return status == 0 ? 0 : 4;
}
