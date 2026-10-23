/* Write AlterBBN's own forward rate of reaction INDEX as a table (T9, rate, fu) on a log grid,
 * fu = high/central (AlterBBN err=1), fl = central/low (err=2). Used for the baseline ("default rates") and to test
 * rate_override with a round trip.   dump_rates.x INDEX [NPTS] > table */
#include "src/include.h"
int main(int argc, char **argv)
{
    int idx = atoi(argv[1]), n = argc > 2 ? atoi(argv[2]) : 301;
    struct relicparam p; struct errorparam e; memset(&e, 0, sizeof e);
    Init_cosmomodel(&p);
    unsetenv("ALTERBBN_RATES");
    printf("# AlterBBN v2.2 built-in forward rate, reaction %d; T9  N_A<sv> (cm^3/mol/s)  fu=high/central  fl=central/low\n", idx);
    for (int i = 0; i < n; i++) {
        double T9 = pow(10., -3. + 4. * i / (n - 1));   /* 1e-3 .. 10 */
        double f0[NNUCREACMAX + 1] = {0}, f1[NNUCREACMAX + 1] = {0}, f2[NNUCREACMAX + 1] = {0};
        p.err = 0; rate_all(f0, T9, &p, &e);
        p.err = 1; rate_all(f1, T9, &p, &e);
        p.err = 2; rate_all(f2, T9, &p, &e);
        if (f0[idx] > 0) printf("%.6e %.8e %.6f %.6f\n", T9, f0[idx], f1[idx] / f0[idx], f0[idx] / f2[idx]);
    }
    return 0;
}
