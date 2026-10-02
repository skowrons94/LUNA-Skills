#!/usr/bin/env python3
"""Independent kinematics and single-process slab checks, not a transport simulator.

All masses are rest energies in MeV (c=1), momenta MeV/c and kinetic energies MeV.
Supply consistent nuclear masses; no nuclide masses or cross sections are guessed.
Outputs are reference predictions for comparison with generated truth, not Edep.
"""

import argparse
import json
import math
from pathlib import Path


def finite(*values):
    if not all(math.isfinite(x) for x in values):
        raise ValueError("Inputs must be finite")


def boost_z(energy, px, py, pz, beta):
    """Boost a CM four-vector to a lab moving along +z relative to CM."""
    finite(energy, px, py, pz, beta)
    if abs(beta) >= 1:
        raise ValueError("Require |beta| < 1")
    gamma = 1 / math.sqrt(1 - beta * beta)
    return [gamma * (energy + beta * pz), px, py, gamma * (pz + beta * energy)]


def two_body(
    projectile_mass_MeV,
    target_mass_MeV,
    beam_kinetic_MeV,
    product_mass_MeV,
    residual_mass_MeV,
    theta_cm_deg,
    phi_cm_deg=0,
):
    """a+A -> b+B, target at rest and beam along +z; B includes its excitation.

    Select CM direction of b. B is exactly opposite before the common lab boost.
    Massless b supports radiative capture; no cross-section/angular law is assumed.
    """
    ma, mA, T, mb, mB = (
        projectile_mass_MeV,
        target_mass_MeV,
        beam_kinetic_MeV,
        product_mass_MeV,
        residual_mass_MeV,
    )
    finite(ma, mA, T, mb, mB, theta_cm_deg, phi_cm_deg)
    if min(ma, mA) <= 0 or min(T, mb, mB) < 0 or not 0 <= theta_cm_deg <= 180:
        raise ValueError(
            "Positive incident masses, nonnegative final masses/energy, theta in [0,180] required"
        )
    total = ma + mA + T
    incident_p = math.sqrt(T * (T + 2 * ma))
    s = (ma + mA) ** 2 + 2 * mA * T
    W = math.sqrt(s)
    if W < mb + mB:
        raise ValueError("Channel is below threshold for supplied final masses")
    # Factored Kallen expression avoids subtracting several large fourth powers.
    p = math.sqrt(
        max(0.0, (W - mb - mB) * (W + mb + mB) * (W - mb + mB) * (W + mb - mB))
    ) / (2 * W)
    eb, eB = math.hypot(mb, p), math.hypot(mB, p)
    theta, phi = math.radians(theta_cm_deg), math.radians(phi_cm_deg)
    px, py, pz = (
        p * math.sin(theta) * math.cos(phi),
        p * math.sin(theta) * math.sin(phi),
        p * math.cos(theta),
    )
    beta = incident_p / total
    b = boost_z(eb, px, py, pz, beta)
    B = boost_z(eB, -px, -py, -pz, beta)
    residual = [b[0] + B[0] - total, b[1] + B[1], b[2] + B[2], b[3] + B[3] - incident_p]
    return {
        "Q_MeV": ma + mA - mb - mB,
        "sqrt_s_MeV": W,
        "cm_kinetic_available_MeV": W - mb - mB,
        "beta_cm": beta,
        "product_cm_energy_MeV": eb,
        "product_cm_momentum_MeV_c": p,
        "four_vector_order": ["energy_MeV", "px_MeV_c", "py_MeV_c", "pz_MeV_c"],
        "product_lab": b,
        "residual_lab": B,
        "product_lab_kinetic_MeV": b[0] - mb,
        "residual_lab_kinetic_MeV": B[0] - mB,
        "conservation_residual_MeV": residual,
        "scope": "Two-body vertex only; target at rest, beam +z; no stopping, branching or transport",
    }


def doppler(rest_energy_keV, beta, lab_angle_deg):
    """Photon energy for a lab-frame angle to the actual emitting recoil velocity."""
    finite(rest_energy_keV, beta, lab_angle_deg)
    if rest_energy_keV <= 0 or not 0 <= beta < 1 or not 0 <= lab_angle_deg <= 180:
        raise ValueError("Require E>0, 0<=beta<1 and lab angle in [0,180]")
    gamma = 1 / math.sqrt(1 - beta * beta)
    energy = rest_energy_keV / (
        gamma * (1 - beta * math.cos(math.radians(lab_angle_deg)))
    )
    return {
        "lab_energy_keV": energy,
        "rest_energy_keV": rest_energy_keV,
        "beta": beta,
        "lab_angle_deg": lab_angle_deg,
        "scope": "Fixed recoil velocity at emission; no slowing, lifetime or angular acceptance",
    }


def slab(optical_depth, bias_factor, interaction_depth_fraction=None):
    """One absorbing process in a homogeneous slab: exact analog/biased probabilities.

    tau = n*sigma*L; no energy loss, competing processes, scattering or reinjection.
    Interaction-history weight is exp((b-1)*tau*x/L)/b, not generally 1/b.
    """
    finite(optical_depth, bias_factor)
    tau, b = optical_depth, bias_factor
    if tau <= 0 or b <= 0:
        raise ValueError("Positive optical depth and bias factor required")
    analog = -math.expm1(-tau)
    biased = -math.expm1(-b * tau)
    result = {
        "analog_probability": analog,
        "biased_probability": biased,
        "naive_divide_by_bias": biased / b,
        "naive_relative_error": (biased / b) / analog - 1,
        "conditional_reaction_probability_ratio": analog / biased,
        "log_survivor_weight": (b - 1) * tau,
        "scope": "Constant-energy single-process absorbing slab only; not a SimLUNA event reweighter",
    }
    if interaction_depth_fraction is not None:
        finite(interaction_depth_fraction)
        if not 0 <= interaction_depth_fraction <= 1:
            raise ValueError("Interaction depth fraction must lie in [0,1]")
        # Log form remains usable when an extreme bias creates large weights.
        result["log_interaction_weight"] = (
            b - 1
        ) * tau * interaction_depth_fraction - math.log(b)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    kin = sub.add_parser(
        "two-body", help="JSON input keys match the two_body function arguments"
    )
    kin.add_argument("config", type=Path)
    dop = sub.add_parser("doppler")
    dop.add_argument("--rest-energy-keV", type=float, required=True)
    dop.add_argument("--beta", type=float, required=True)
    dop.add_argument("--lab-angle-deg", type=float, required=True)
    bias = sub.add_parser("slab")
    bias.add_argument("--optical-depth", type=float, required=True)
    bias.add_argument("--bias-factor", type=float, required=True)
    bias.add_argument("--interaction-depth-fraction", type=float)
    for p in [kin, dop, bias]:
        p.add_argument("--out", type=Path, help="New JSON file; otherwise print")
    args = parser.parse_args()
    kwargs = vars(args).copy()
    kwargs.pop("mode")
    out = kwargs.pop("out")
    if args.mode == "two-body":
        cfg = json.loads(kwargs["config"].read_text())
        result = two_body(**cfg)
        result["inputs"] = cfg
    elif args.mode == "doppler":
        result = doppler(**kwargs)
    else:
        result = slab(**kwargs)
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if out:
        with out.open("x") as stream:
            stream.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
