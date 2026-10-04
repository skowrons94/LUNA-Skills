# Geometry

`-Path <dir>/` must contain: `asolid` (crystal shapes), `aclust` (crystals in each cluster type), `aeuler` (placement of clusters), `awalls` (cryostat/dead material), `aslice` (segmentation planes). Symlinks to `environment/agata/A180/` files are fine.

Standard A180 set: `asolid -> A180solid.list`, `aclust -> A180clustS2p.list`, `awalls -> A180wallsS2p.list`, `aslice -> A180slice.list`; `aeuler` chooses the configuration (e.g. `A180euler_LNL_2022.list`, 13 ATC; `A180euler1T.list`, one triplet at nominal 23.5 cm).

## aeuler format
```
#  cl  cl#   psi(Rz)  theta(Ry)  phi(Rz)   dx  dy  dz      (deg, mm)
    0    0    0.0      0.0        0.0      0   0   75.5
```
First column: cluster position index; second: cluster type in `aclust` (type 0 = ATC triplet in A180clustS2p). Rotation (0,0,0) puts the cluster axis along +z (beam direction), i.e. downstream of the target at 0°.

## One triplet at distance d (validated in the 14N(p,γ) triplet study)
In the cluster frame the Ge front faces are at z ≈ −49.7 mm and the cryostat front at z ≈ −55.5 mm (computed from A180solid/A180clustS2p/A180wallsS2p). For the endcap at distance d from the target: `dz = d + 55.5` mm; the Ge front is then at ≈ d + 5.8 mm. Nominal A180 placement radius is ~276.5 mm (Ge front ≈ 232 mm).
- At d = 20 mm one ATC gives a 7.4 MeV full-energy efficiency of ~1.5 % (addback), 1.2 % at 30 mm, 0.8 % at 50 mm; ~15 % of 7.4 MeV γ interact.
- A γ along exactly +z passes the junction of the three crystals (few or no hits): do not test with pencil beams on axis.
- Other orientations: set theta (Ry) to tilt the axis; check that the cryostat does not overlap the beam pipe.
