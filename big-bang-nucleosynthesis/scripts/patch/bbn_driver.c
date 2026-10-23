/* Case-07 driver for AlterBBN (built against the patched libbbn.a by build_alterbbn.sh).
 *   bbn_driver.x central ETA [FAILSAFE]          -> one JSON line: central abundances
 *   bbn_driver.x mc ETA N SEED [FAILSAFE]         -> one JSON line per sample (AlterBBN err=4 sampling,
 *                                                   every rate incl. weak rates and neutron lifetime,
 *                                                   with a reproducible per-sample seed)
 * Rates replaced through ALTERBBN_RATES (patch/rate_override.c). Abundances: Yp = 4He mass fraction,
 * others number ratios to H; Li7/H includes 7Be decay (AlterBBN convention). */
#include "src/include.h"
#include <stdint.h>

static void print_json(const char *tag, long k, double eta, int fs, const double *r)
{
    printf("{\"mode\":\"%s\",\"sample\":%ld,\"eta\":%.6e,\"failsafe\":%d,\"Yp\":%.8e,\"D_H\":%.8e,"
           "\"He3_H\":%.8e,\"Li7_H\":%.8e,\"Li6_H\":%.8e,\"Be7_H\":%.8e}\n",
           tag, k, eta, fs, r[6], r[3], r[5], r[8], r[7], r[9]);
}

/* Box-Muller with erand48, independent state per sample: reproducible and thread-safe */
static double gauss48(unsigned short st[3])
{
    double u1 = erand48(st), u2 = erand48(st);
    if (u1 < 1e-300) u1 = 1e-300;
    return sqrt(-2. * log(u1)) * cos(2. * M_PI * u2);
}

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: central ETA [FS] | mc ETA N SEED [FS]\n"); return 1; }
    struct relicparam p;
    double eta = atof(argv[2]);
    int mc = !strcmp(argv[1], "mc");
    int fs = mc ? (argc > 5 ? atoi(argv[5]) : 1) : (argc > 3 ? atoi(argv[3]) : 1);
    Init_cosmomodel(&p);
    Init_cosmomodel_param(eta, p.Nnu, 0., p.life_neutron, p.life_neutron_error, 0., 0., 0., &p);
    p.failsafe = fs;
    if (!mc) {
        double r[NNUC + 1];
        p.err = 0;
        if (nucl(&p, r) != 0) { fprintf(stderr, "nucl failed\n"); return 2; }
        print_json("central", 0, eta, fs, r);
        return 0;
    }
    long n = atol(argv[3]);
    unsigned long seed = strtoul(argv[4], NULL, 10);
    p.err = 4;
    double (*res)[NNUC + 1] = malloc(sizeof(double[NNUC + 1]) * n);
    int *fail = calloc(n, sizeof(int));
#pragma omp parallel for schedule(dynamic)
    for (long k = 0; k < n; k++) {
        struct errorparam e;
        unsigned long s = seed * 1000003UL + (unsigned long)k;
        unsigned short st[3] = {(unsigned short)s, (unsigned short)(s >> 16), (unsigned short)(s >> 32)};
        for (int j = 0; j <= NNUCREAC + 1; j++) e.random[j] = gauss48(st);
        for (int j = 1; j <= NNUC; j++) res[k][j] = 0.;
        fail[k] = nucl_single(&p, res[k], &e) > 0;
    }
    for (long k = 0; k < n; k++) {
        if (fail[k]) { printf("{\"mode\":\"mc\",\"sample\":%ld,\"failed\":true}\n", k); continue; }
        print_json("mc", k, eta, fs, res[k]);
    }
    return 0;
}
