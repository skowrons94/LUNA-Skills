/* Replace AlterBBN forward rates by tables (project patch, case 07; applied by build_alterbbn.sh).
 *
 * ALTERBBN_RATES=FILE, each line "INDEX PATH" (INDEX = AlterBBN reaction number, e.g. 20 for
 * H2(p,g)He3). Each table has columns T9, N_A<sigma v> (cm^3 mol^-1 s^-1), fu (factor
 * uncertainty, lognormal); '#' lines are comments. Between table points the rate is interpolated
 * linearly in (log T9, log rate). Outside the table range the code's own rate is kept and the
 * count of such calls is printed at exit (ALTERBBN_RATES_VERBOSE=1), so a table that does not
 * cover the BBN range is visible. Uncertainties: ferrhigh = fu - 1, ferrlow = 1/fu - 1.
 * The reverse rates are computed by AlterBBN from the forward ones (detailed balance). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define OVR_MAXREAC 16
#define OVR_MAXPTS 5000

static int ovr_loaded = 0, ovr_n = 0;
static int ovr_idx[OVR_MAXREAC], ovr_np[OVR_MAXREAC];
static double ovr_lt[OVR_MAXREAC][OVR_MAXPTS], ovr_lr[OVR_MAXREAC][OVR_MAXPTS], ovr_fu[OVR_MAXREAC][OVR_MAXPTS];
static long ovr_outside[OVR_MAXREAC];

static void ovr_report(void)
{
    for (int k = 0; k < ovr_n; k++)
        fprintf(stderr, "rate_override: reaction %d, %ld calls outside table range (code rate used)\n",
                ovr_idx[k], ovr_outside[k]);
}

static void ovr_load(void)
{
    const char *list = getenv("ALTERBBN_RATES");
    ovr_loaded = 1;
    if (!list || !*list) return;
    FILE *fl = fopen(list, "r");
    if (!fl) { fprintf(stderr, "rate_override: cannot open %s\n", list); exit(2); }
    int idx; char path[4096];
    while (fscanf(fl, "%d %4095s", &idx, path) == 2) {
        if (ovr_n >= OVR_MAXREAC) { fprintf(stderr, "rate_override: too many reactions\n"); exit(2); }
        FILE *ft = fopen(path, "r");
        if (!ft) { fprintf(stderr, "rate_override: cannot open %s\n", path); exit(2); }
        char line[512]; int np = 0;
        while (fgets(line, sizeof line, ft)) {
            double t, r, fu;
            if (line[0] == '#') continue;
            if (sscanf(line, "%lf %lf %lf", &t, &r, &fu) != 3) continue;
            if (np >= OVR_MAXPTS || t <= 0 || r <= 0 || fu < 1) {
                fprintf(stderr, "rate_override: bad row in %s: %s", path, line); exit(2); }
            ovr_lt[ovr_n][np] = log(t); ovr_lr[ovr_n][np] = log(r); ovr_fu[ovr_n][np] = fu; np++;
        }
        fclose(ft);
        for (int i = 1; i < np; i++) if (ovr_lt[ovr_n][i] <= ovr_lt[ovr_n][i-1]) {
            fprintf(stderr, "rate_override: T9 not increasing in %s\n", path); exit(2); }
        if (np < 2) { fprintf(stderr, "rate_override: %s has < 2 rows\n", path); exit(2); }
        ovr_idx[ovr_n] = idx; ovr_np[ovr_n] = np; ovr_outside[ovr_n] = 0; ovr_n++;
        if (getenv("ALTERBBN_RATES_VERBOSE"))
            fprintf(stderr, "rate_override: reaction %d <- %s (%d points, T9 %.3g-%.3g)\n",
                    idx, path, np, exp(ovr_lt[ovr_n-1][0]), exp(ovr_lt[ovr_n-1][np-1]));
    }
    fclose(fl);
    if (getenv("ALTERBBN_RATES_VERBOSE")) atexit(ovr_report);
}

void rate_override(double f[], double ferrlow[], double ferrhigh[], double T9, int with_err)
{
    if (!ovr_loaded) {
#pragma omp critical(rate_override_load)
        { if (!ovr_loaded) ovr_load(); }
    }
    double lt = log(T9);
    for (int k = 0; k < ovr_n; k++) {
        int np = ovr_np[k];
        if (lt < ovr_lt[k][0] || lt > ovr_lt[k][np-1]) {
#pragma omp atomic
            ovr_outside[k]++;
            continue;
        }
        int i = 1;
        while (i < np - 1 && ovr_lt[k][i] < lt) i++;
        double w = (lt - ovr_lt[k][i-1]) / (ovr_lt[k][i] - ovr_lt[k][i-1]);
        f[ovr_idx[k]] = exp(ovr_lr[k][i-1] + w * (ovr_lr[k][i] - ovr_lr[k][i-1]));
        if (with_err) {
            double fu = ovr_fu[k][i-1] + w * (ovr_fu[k][i] - ovr_fu[k][i-1]);
            ferrhigh[ovr_idx[k]] = fu - 1.;
            ferrlow[ovr_idx[k]] = 1. / fu - 1.;
        }
    }
}
