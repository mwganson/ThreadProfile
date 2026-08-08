#!/usr/bin/env python3
"""Generate BSW / Whitworth (55°) internal/external profile tables.

British Standard Whitworth form (pitch normalized to 1):
  included angle 55°  ->  flank angle θ = 27.5°
  H = 1 / (2·tan(θ))           ≈ 0.960491
  h = (2/3)·H                  ≈ 0.640327   (thread depth)
  r = 0.137329                 (crest & root radius)
  e = H·sin(θ)/6               ≈ 0.073918   (arc height)

Tables use the ThreadProfile convention:
  radius = MinorDiameter/2 + table[i] · Pitch
with ~719 samples (k = 1..719 of 720), same as thread_builder / PG generator.

Internal: root fillet at 0 … flanks … crest fillet at h
External: same shape with a small root dip (default -0.018) for clearance

Usage:
  python Resources/assets/generate_bsw_profile_data.py
  python Resources/assets/generate_bsw_profile_data.py --check
  python Resources/assets/generate_bsw_profile_data.py --emit-cmd

See _bsw_validation/BSW_PROFILE_DATA_REPORT.md
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

RES = 720
THETA = math.radians(27.5)
H = 1.0 / (2.0 * math.tan(THETA))
DEPTH = (2.0 / 3.0) * H  # h
R = 0.137329083233
E = H * math.sin(THETA) / 6.0
ROOT_EXTERNAL = -0.018
SLOPE = 1.0 / math.tan(THETA)  # cot(27.5°) = dx/dz on flank

# Arc half-angle from bottom to flank tangent: 90° - 27.5° = 62.5°
ARC_HALF = math.radians(90.0 - 27.5)


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def whitworth_offset(z: float) -> float:
    """Radial offset from minor for one pitch, z in [0, 1).

    Layout (symmetric):
      root centre at z=0 (and z=1), crest centre at z=0.5
    """
    # fold to [0, 1), then to [0, 0.5] by mirroring
    z = z % 1.0
    if z > 0.5:
        z = 1.0 - z

    # Root arc: centre at (R, 0). Bottom at x=0.
    # Tangent points at angles ±ARC_HALF from the downward vertical.
    z_root_tan = R * math.sin(ARC_HALF)
    # Crest arc: centre at (DEPTH - R, 0.5). Top at x=DEPTH.
    z_crest_tan = 0.5 - R * math.sin(ARC_HALF)

    if z <= z_root_tan:
        # root fillet: x = R - sqrt(R^2 - z^2)
        return R - math.sqrt(max(R * R - z * z, 0.0))

    if z >= z_crest_tan:
        # crest fillet relative to crest centre at 0.5
        dz = z - 0.5
        # centre at x = DEPTH - R; point on circle toward outside
        return (DEPTH - R) + math.sqrt(max(R * R - dz * dz, 0.0))

    # straight flank through root tangent point
    x_tan = R - R * math.cos(ARC_HALF)  # = E
    # verify: R*(1-cos(ARC_HALF)) ... ARC_HALF=62.5°, cos(62.5°)≈0.4617, R*0.538≈0.074 ≈ E
    return x_tan + SLOPE * (z - z_root_tan)


def generate_bsw_tables(root_external: float = ROOT_EXTERNAL):
    """Return (internal_bsw_data, external_bsw_data)."""
    internal = []
    for k in range(1, RES):
        z = k / float(RES)
        internal.append(round(whitworth_offset(z), 12))

    # External: same flanks/crest, root shifted down by root_external (at valley)
    # Map: scale/shift so min goes to root_external and max stays DEPTH
    i_min = min(internal)
    i_max = max(internal)
    external = []
    for v in internal:
        if i_max == i_min:
            external.append(root_external)
        else:
            # keep crest at i_max, move root from i_min to root_external
            t = (v - i_min) / (i_max - i_min)
            external.append(round(root_external + t * (i_max - root_external), 12))
    return internal, external


def format_array(name: str, values) -> str:
    return f"{name} = [" + ",".join(str(v) for v in values) + "]"


def basic_minor(major_mm: float, pitch_mm: float) -> float:
    return major_mm - 2.0 * DEPTH * pitch_mm


def extract_from_cmd(src: str, name: str):
    import re

    m = re.search(rf"{name}\s*=\s*\[([^\]]+)\]", src)
    if not m:
        raise SystemExit(f"{name} not found in ThreadProfileCmd.py")
    return [float(x) for x in m.group(1).split(",") if x.strip()]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--check",
        action="store_true",
        help="geometry sanity + match ThreadProfileCmd.py arrays when present",
    )
    p.add_argument(
        "--cmd",
        type=Path,
        default=None,
        help="path to ThreadProfileCmd.py (for --check)",
    )
    p.add_argument(
        "--emit-cmd",
        action="store_true",
        help="print arrays suitable for pasting into ThreadProfileCmd.py",
    )
    p.add_argument("--quarter", action="store_true", help="print 1/4-20 BSW diameters")
    args = p.parse_args(argv)

    internal, external = generate_bsw_tables()

    if args.quarter:
        major = 0.25 * 25.4
        pitch = 25.4 / 20.0
        print(f"1/4-20 BSW major={major:.4f} P={pitch:.4f}")
        print(f"  basic minor={basic_minor(major, pitch):.4f} (chart ~4.72)")
        print(f"  h/P={DEPTH:.6f}  H/P={H:.6f}  r={R:.6f}  e={E:.6f}")

    if args.check:
        imin, imax = min(internal), max(internal)
        emin, emax = min(external), max(external)
        print(f"n={len(internal)}  internal [{imin:.6f} .. {imax:.6f}]")
        print(f"           external [{emin:.6f} .. {emax:.6f}]")
        print(f"H={H:.6f} h={DEPTH:.6f} r={R:.6f} e={E:.6f} slope={SLOPE:.6f}")
        ok = (
            len(internal) == RES - 1
            and abs(imax - DEPTH) < 1e-3
            and imin >= -1e-6
            and abs(emax - DEPTH) < 1e-3
            and abs(emin - ROOT_EXTERNAL) < 1e-6
        )
        z1, z2 = 0.15, 0.20
        slope = (whitworth_offset(z2) - whitworth_offset(z1)) / (z2 - z1)
        print(f"flank slope sample={slope:.6f}  expect cot(27.5°)={SLOPE:.6f}")
        ok = ok and abs(slope - SLOPE) < 0.05

        here = Path(__file__).resolve()
        cmd = args.cmd or here.parents[2] / "ThreadProfileCmd.py"
        if cmd.is_file() and "internal_bsw_data" in cmd.read_text(encoding="utf-8"):
            text = cmd.read_text(encoding="utf-8")
            ref_i = extract_from_cmd(text, "internal_bsw_data")
            ref_e = extract_from_cmd(text, "external_bsw_data")
            di = max(abs(a - b) for a, b in zip(internal, ref_i))
            de = max(abs(a - b) for a, b in zip(external, ref_e))
            match = (
                len(internal) == len(ref_i)
                and len(external) == len(ref_e)
                and di == 0.0
                and de == 0.0
            )
            print(f"vs ThreadProfileCmd: internal maxdiff={di} external maxdiff={de}")
            print("EMBEDDED MATCH" if match else "EMBEDDED MISMATCH")
            ok = ok and match
        else:
            print("ThreadProfileCmd.py arrays not yet present; geometry-only check")

        print("OK" if ok else "MISMATCH")
        return 0 if ok else 1

    if args.emit_cmd:
        print(format_array("internal_bsw_data", internal))
        print(format_array("external_bsw_data", external))
        return 0

    print(format_array("internal_bsw_data", internal))
    print(format_array("external_bsw_data", external))
    print(
        f"# n={len(internal)} h={DEPTH:.6f} root_ext={ROOT_EXTERNAL}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
