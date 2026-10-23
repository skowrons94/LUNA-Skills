"""KSHELL helpers: inputs, log parsing, spurious-state checks, calibration.

KSHELL (Shimizu et al., Comput. Phys. Commun. 244, 372 (2019)) gives energies,
<Hcm>, isospin, orbit occupancies and the hbar-omega decomposition of each
eigenstate in a square-integrable basis.  It gives no widths.

    write_input(...)        namelist input for kshell.exe (Lawson term on by default)
    parse_log(text)         every eigenstate of a log: E, J, parity, T, <Hcm>, occupancies, hw
    flag_spurious(states)   states whose <Hcm> marks a c.m. excitation
    sd_occupancy(state)     nucleons in the sd orbits (p + n)
    calibrate(residuals)    offset and scatter of (experiment - model) over calibration states
    relative_energy(E, E_ref)  energy referred to a threshold or a core state

Generalized from the 7Be study (YSOX interaction, p-sd shell, 4He core).
"""
import re

import numpy as np

STATE_RE = re.compile(r"^\s*(\d+)\s+<H>:\s*(-?[\d.]+)\s+<JJ>:\s*(-?[\d.]+)\s+J:\s*(\d+)/2\s+prty\s+(-?\d+)"
                      r"(.*?)(?=^-{10}|\Z)", re.S | re.M)
SD_ORBITS = ("0d_3/2", "0d_5/2", "1s_1/2")


def write_input(path, fn_int, fn_ptn, n_eigen, fn_wav=None, beta_cm=10.0, mtot=1,
                eff_charge=(1.5, 0.5), gl=(1.0, 0.0), gs=(5.585, -3.826), hw_type=2,
                max_lanc_vec=300, maxiter=600, n_restart_vec=30):
    """Write a KSHELL namelist.  mtot is 2*M (1 for odd A, 0 for even A); beta_cm > 0
    switches on the Lawson term beta_cm * (H_cm - 3/2 hbar omega)."""
    wav = fn_wav or path.rsplit("/", 1)[-1].replace(".input", ".wav")
    txt = f"""&input
  beta_cm = {beta_cm}
  eff_charge = {eff_charge[0]}, {eff_charge[1]}
  fn_int = "{fn_int}"
  fn_ptn = "{fn_ptn}"
  fn_save_wave = "{wav}"
  gl = {gl[0]}, {gl[1]}
  gs = {gs[0]}, {gs[1]}
  hw_type = {hw_type}
  is_double_j = .false.
  max_lanc_vec = {max_lanc_vec}
  maxiter = {maxiter}
  mode_lv_hdd = 0
  mtot = {mtot}
  n_block = 0
  n_eigen = {n_eigen}
  n_restart_vec = {n_restart_vec}
&end
"""
    with open(path, "w") as f:
        f.write(txt)
    return txt


def parse_log(text):
    """All eigenstates in a KSHELL log, sorted by energy.  J is a float (J: 3/2 -> 1.5)."""
    orbits = None
    m = re.search(r"n orbit\s+(.+)", text)
    if m:
        orbits = m.group(1).split()
    out = []
    for mm in STATE_RE.finditer(text):
        idx, E, _jj, j2, p, rest = mm.groups()
        st = dict(i=int(idx), E=float(E), J=int(j2) / 2, parity=int(p))
        h = re.search(r"<Hcm>:\s*(-?[\d.]+)", rest)
        t = re.search(r"T:\s*(\d+)/2", rest)
        st["Hcm"] = float(h.group(1)) if h else None
        st["T"] = int(t.group(1)) / 2 if t else None
        for nuc in ("p", "n"):
            o = re.search(rf"<{nuc} Nj>\s+([\d.\s-]+)", rest)
            if o and orbits:
                vals = [float(x) for x in o.group(1).split()][:len(orbits)]
                st[f"occ_{nuc}"] = dict(zip(orbits, vals))
        hw = re.search(r"^\s*hw:\s*(.*)$", rest, re.M)
        if hw:
            st["hw"] = {int(k): float(v) for k, v in (x.split(":") for x in hw.group(1).split())}
        out.append(st)
    out.sort(key=lambda s: s["E"])
    return out


def jpi(st):
    j = st["J"]
    js = f"{int(j)}" if j == int(j) else f"{int(2 * j)}/2"
    return js + ("+" if st["parity"] > 0 else "-")


def flag_spurious(states, hcm_max=0.5):
    """(physical, spurious): a state with <Hcm> above hcm_max (MeV, with beta_cm = 10
    the physical states carry ~0.0-0.1) is a centre-of-mass excitation."""
    phys = [s for s in states if s["Hcm"] is None or s["Hcm"] <= hcm_max]
    spur = [s for s in states if s["Hcm"] is not None and s["Hcm"] > hcm_max]
    return phys, spur


def sd_occupancy(st, orbits=SD_ORBITS):
    """Protons + neutrons in the sd orbits (1.00 = one nucleon promoted)."""
    return sum(st.get(f"occ_{n}", {}).get(o, 0.0) for n in ("p", "n") for o in orbits)


def relative_energy(E, E_ref):
    """Energy above a reference (core+nucleon threshold: E_ref = E(core g.s.) in the same run convention)."""
    return E - E_ref


def calibrate(residuals):
    """Offset (mean) and scatter (population rms about the mean) of exp - model residuals.
    The scatter is the systematic uncertainty carried to a prediction."""
    r = np.asarray(residuals, float)
    off = float(r.mean())
    return off, float(np.sqrt(np.mean((r - off) ** 2)))
