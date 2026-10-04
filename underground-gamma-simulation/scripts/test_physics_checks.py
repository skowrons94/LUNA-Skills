#!/usr/bin/env python3
"""Analytic regression checks; all masses below are synthetic, not nuclear evaluations."""

import math
import unittest
from physics_checks import two_body, boost_z, doppler, slab


class PhysicsChecks(unittest.TestCase):
    def test_equal_mass_elastic_partition(self):
        r = two_body(1, 1, 1, 1, 1, 90)
        self.assertAlmostEqual(r["product_lab_kinetic_MeV"], 0.5)
        self.assertAlmostEqual(r["residual_lab_kinetic_MeV"], 0.5)

    def test_capture_at_rest(self):
        r = two_body(1, 10, 0, 0, 10, 42)
        self.assertAlmostEqual(r["product_cm_energy_MeV"], 21 / 22)
        # Excited residual mass is inserted before, not subtracted after, recoil correction.
        r = two_body(1, 10, 0, 0, 10.5, 42)
        self.assertAlmostEqual(r["product_cm_energy_MeV"], (121 - 10.5**2) / 22)

    def test_conservation_and_mass_shells(self):
        for theta in [0, 47, 90, 180]:
            r = two_body(938, 15000, 3, 0, 15930, theta, 21)
            for residual in r["conservation_residual_MeV"]:
                self.assertLess(abs(residual), 1e-9)
            for key, mass in [("product_lab", 0), ("residual_lab", 15930)]:
                E, px, py, pz = r[key]
                self.assertAlmostEqual(
                    E * E - px * px - py * py - pz * pz, mass * mass, delta=1e-6
                )

    def test_threshold_and_invalid_inputs(self):
        with self.assertRaises(ValueError):
            two_body(1, 1, 0, 1, 2, 0)
        with self.assertRaises(ValueError):
            two_body(1, 1, float("nan"), 0, 1, 0)
        with self.assertRaises(ValueError):
            doppler(1, 1, 0)
        with self.assertRaises(ValueError):
            slab(0.1, 0)
        with self.assertRaises(ValueError):
            slab(0.1, 2, 1.1)

    def test_doppler_angles_and_inverse(self):
        self.assertEqual(doppler(1000, 0, 37)["lab_energy_keV"], 1000)
        beta = 0.01
        self.assertAlmostEqual(
            doppler(1000, beta, 0)["lab_energy_keV"],
            1000 * math.sqrt((1 + beta) / (1 - beta)),
        )
        self.assertAlmostEqual(
            doppler(1000, beta, 180)["lab_energy_keV"],
            1000 * math.sqrt((1 - beta) / (1 + beta)),
        )
        theta = math.radians(52)
        E, px, py, pz = boost_z(1, math.sin(theta), 0, math.cos(theta), beta)
        angle = math.degrees(math.atan2(math.hypot(px, py), pz))
        self.assertAlmostEqual(doppler(1000, beta, angle)["lab_energy_keV"], 1000 * E)
        restored = boost_z(E, px, py, pz, -beta)
        self.assertAlmostEqual(restored[0], 1)
        self.assertAlmostEqual(restored[3], math.cos(theta))

    def test_bias_limits(self):
        r = slab(0.2, 1)
        self.assertEqual(r["analog_probability"], r["biased_probability"])
        self.assertAlmostEqual(slab(1e-9, 10)["naive_relative_error"], 0, delta=1e-8)
        self.assertLess(slab(0.001, 1000)["naive_relative_error"], -0.36)

    def test_weighted_slab_integral(self):
        # Integrate biased event density times exact history weight; include survivors.
        tau, b = 0.2, 8
        N = 10000

        def integrand(x):
            log_weight = slab(tau, b, x)["log_interaction_weight"]
            return b * tau * math.exp(-b * tau * x + log_weight)

        dx = 1 / N
        estimate = dx * (
            0.5 * integrand(0)
            + sum(integrand(i * dx) for i in range(1, N))
            + 0.5 * integrand(1)
        )
        r = slab(tau, b)
        self.assertAlmostEqual(estimate, r["analog_probability"], delta=1e-10)
        weighted_survivors = math.exp(-b * tau + r["log_survivor_weight"])
        self.assertAlmostEqual(estimate + weighted_survivors, 1, delta=1e-10)


if __name__ == "__main__":
    unittest.main()
