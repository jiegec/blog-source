#!/usr/bin/env python3
"""Calibrate an MS2130S capture stick (e.g. UGREEN 95348) and emit a .cube LUT.

Workflow
--------
1. On the machine you want to capture (Mac / MateBook / ...), open
   `ms2130s-calibration.html` fullscreen on the display that feeds the
   capture card.  Set that display's colour profile to sRGB first, otherwise
   the correction bakes the profile into the LUT (and re-fit whenever you
   change the profile).
2. On the capture host, close anything that holds the capture device (OBS,
   QuickTime, ...) and run this script.  It grabs a frame (with ffmpeg, or
   reads an existing PNG), samples every patch, fits a captured -> intended
   correction, and writes a .cube that OBS can apply with the
   "Apply LUT" filter.

It also writes three images so you can eyeball the result:

    <out>.expected.png   what the calibration page looks like (target)
    <out>.captured.png   what the card actually captured (no LUT)
    <out>.corrected.png  with the LUT applied (what OBS would output)

If the captured frame does not look like the calibration page the script
refuses to emit a LUT (use --force to override).

Examples
--------
    python3 calibrate.py --list-devices
    python3 calibrate.py --out macbookair-fix.cube
    python3 calibrate.py --image cap.png --out macbookair-fix.cube
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image


# --------------------------------------------------------------------------- #
# test pattern
# --------------------------------------------------------------------------- #
def build_patches(n, mode):
    levels = [round(i * 255 / (n - 1)) for i in range(n)]
    patches = []
    if mode == "cube":
        for b in levels:
            for g in levels:
                for r in levels:
                    patches.append((r, g, b))
    elif mode == "gray":
        for v in levels:
            patches.append((v, v, v))
    elif mode == "ramp":
        for v in levels:
            patches.append((v, 0, 0))
        for v in levels:
            patches.append((0, v, 0))
        for v in levels:
            patches.append((0, 0, v))
    else:
        raise SystemExit(f"unknown mode {mode!r}")
    return patches


# --------------------------------------------------------------------------- #
# capture
# --------------------------------------------------------------------------- #
def list_avfoundation_devices():
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-f",
            "avfoundation",
            "-list_devices",
            "true",
            "-i",
            "",
        ],
        capture_output=True,
        text=True,
    )
    devices, in_video = [], False
    for line in proc.stderr.splitlines():
        if "AVFoundation video devices" in line:
            in_video = True
            continue
        if "AVFoundation audio devices" in line:
            in_video = False
            continue
        if in_video:
            m = re.search(r"\[(\d+)\]\s+(.*)$", line)
            if m:
                devices.append((int(m.group(1)), m.group(2).strip()))
    return devices


def resolve_input(spec):
    if spec:
        return spec
    for idx, name in list_avfoundation_devices():
        if "UGREEN" in name.upper() or "95348" in name:
            print(f"auto-detected input: [{idx}] {name}")
            return name
    raise SystemExit(
        "could not auto-detect the capture device; "
        "pass --ffmpeg-input '<name>' (see --list-devices)"
    )


def grab_ffmpeg(device, size, rate, frames, matrix="bt709"):
    """Grab `frames` frames and average the good ones.

    The card emits dark frames for a moment after the stream is opened, so
    instead of blindly taking the last few frames we keep the bright,
    stabilised ones.  An explicit framerate also matters: the AVFoundation
    default (29.97) is not offered by many capture sticks.

    The YUV->RGB conversion must use the matrix the card reports (BT.709);
    ffmpeg otherwise defaults to BT.601 and shifts saturated colours
    (e.g. green 0,255,0 comes out as 19,255,6) which looks like cross-talk.
    """
    scale = (
        f"scale=in_range=limited:in_color_matrix={matrix}:"
        f"out_range=pc:out_color_matrix={matrix}"
    )
    tmp = tempfile.mkdtemp(prefix="calibrate-")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "avfoundation"]
    if rate:
        cmd += ["-framerate", str(rate)]
    known_size = bool(size) and str(size).lower() != "auto"
    if known_size:
        cmd += ["-video_size", str(size)]
    cmd += ["-pixel_format", "nv12"]

    if known_size:
        w, h = (int(x) for x in str(size).lower().split("x"))
        raw = os.path.join(tmp, "f.raw")
        cmd += [
            "-i",
            device,
            "-frames:v",
            str(frames),
            "-vf",
            scale,
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            raw,
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            raise SystemExit(
                "ffmpeg failed to grab; is OBS (or another app) "
                "holding the capture device?  Close it and retry."
            )
        data = np.fromfile(raw, dtype=np.uint8)
        per = w * h * 3
        n = len(data) // per
        if n == 0:
            raise SystemExit("ffmpeg produced no frames")
        arrs = data[: n * per].reshape(n, h, w, 3).astype(np.float64)
    else:
        pattern = os.path.join(tmp, "f%04d.png")
        cmd += ["-i", device, "-frames:v", str(frames), "-vf", scale, pattern]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            raise SystemExit(
                "ffmpeg failed to grab; is OBS (or another app) "
                "holding the capture device?  Close it and retry."
            )
        files = sorted(glob.glob(os.path.join(tmp, "f*.png")))
        if not files:
            raise SystemExit("ffmpeg produced no frames")
        arrs = [
            np.asarray(Image.open(f).convert("RGB"), dtype=np.float64) for f in files
        ]

    arrs = list(arrs) if not isinstance(arrs, np.ndarray) else list(arrs)
    bright = np.array([a.mean() for a in arrs])
    good = [a for a, b in zip(arrs, bright) if b >= 0.8 * bright.max()]
    if not good:
        good = arrs
    elif len(good) < len(arrs):
        print(f"dropped {len(arrs) - len(good)}/{len(arrs)} dark startup frames")
    shutil.rmtree(tmp, ignore_errors=True)
    return np.mean(good[-10:], axis=0)


# --------------------------------------------------------------------------- #
# sampling + validation
# --------------------------------------------------------------------------- #
def sample_patches(img, patches, cols, rows):
    h, w = img.shape[:2]
    cap, spread = [], []
    for idx, _ in enumerate(patches):
        row, col = divmod(idx, cols)
        cx = int((col + 0.5) * w / cols)
        cy = int((row + 0.5) * h / rows)
        hw = max(2, min(w // cols, h // rows) // 4)
        win = img[max(0, cy - hw) : cy + hw, max(0, cx - hw) : cx + hw].reshape(-1, 3)
        cap.append(np.median(win, axis=0))
        spread.append(win.std(axis=0))
    return np.asarray(cap, dtype=np.float64), np.asarray(spread, dtype=np.float64)


def validate(cap, spread, intended):
    """Return (blocking issues, non-blocking warnings)."""
    issues, warnings = [], []
    mean_spread = float(spread.mean())
    if mean_spread > 12:
        issues.append(
            f"sampled patches are not flat (mean in-patch std {mean_spread:.1f}); "
            f"is the calibration page really fullscreen on the captured display?"
        )

    # cross-talk.  For a correct sRGB source, patches whose R/G/B is 0 should
    # capture the same value for that channel no matter what the others are.
    # Big variation means the source converted the colours, which almost always
    # means the display colour profile is not sRGB.
    xt = []
    for c, name in enumerate("RGB"):
        m = intended[:, c] == 0
        if m.sum() >= 2:
            rng = float(cap[m, c].max() - cap[m, c].min())
            if rng > 30:
                xt.append(f"{name} varies by {rng:.0f} across patches where {name}=0")
    if xt:
        warnings.append(
            "colour cross-talk: "
            + "; ".join(xt)
            + "  -> the source converted the colours.  On the machine "
            "showing the page, check the *built-in* display colour "
            "profile (mirroring uses that one) and HDR; a per-channel "
            "LUT cannot undo a gamut conversion"
        )

    for c, name in enumerate("RGB"):
        if intended[:, c].std() > 1 and cap[:, c].std() > 1e-6:
            r = np.corrcoef(cap[:, c], intended[:, c])[0, 1]
            if r < 0.90:
                issues.append(
                    f"{name} channel does not track the pattern " f"(corr {r:.3f})"
                )

    dark = int(np.argmin(intended.sum(axis=1)))
    bright = int(np.argmax(intended.sum(axis=1)))
    if cap[dark].max() > 90:
        issues.append(
            f"darkest patch captured as {cap[dark].round().astype(int).tolist()}"
            f" (should be dark)"
        )
    if cap[bright].min() < 160:
        issues.append(
            f"brightest patch captured as {cap[bright].round().astype(int).tolist()}"
            f" (should be bright)"
        )

    for c, name in enumerate("RGB"):
        if cap[:, c].max() - cap[:, c].min() < 100:
            issues.append(
                f"{name} channel range is only "
                f"{cap[:, c].max() - cap[:, c].min():.0f}"
            )
    return issues, warnings


# --------------------------------------------------------------------------- #
# fitting
# --------------------------------------------------------------------------- #
def fit_perchannel(cap, intended, nbins=33):
    """One monotone curve per channel: captured value -> intended value.

    The captured values cluster on the test pattern's levels, so we place one
    knot per *intended* level (at the median captured value for that level).
    Binning by captured value instead would leave gaps between the clusters
    and interpolate wrongly across them (e.g. 64 -> 51,71,59 for a near-identity
    capture).
    """
    funcs, info = [], []
    for c in range(3):
        x, y = cap[:, c], intended[:, c]
        knots = [(0.0, 0.0)]
        for level in sorted(set(y.tolist())):
            m = y == level
            knots.append((float(np.median(x[m])), float(level)))
        knots.append((255.0, 255.0))
        knots.sort()

        cx, cy = [knots[0][0]], [knots[0][1]]
        for kx, ky in knots[1:]:
            if kx <= cx[-1] + 1e-9:
                cy[-1] = max(cy[-1], ky)
            else:
                cx.append(kx)
                cy.append(ky)
        cx = np.asarray(cx)
        cy = np.maximum.accumulate(np.asarray(cy))  # enforce monotone

        def make(cx=cx, cy=cy):
            return lambda v: np.interp(v, cx, cy)

        funcs.append(make())
        resid = np.abs(funcs[c](x) - y)
        info.append((resid.mean(), resid.max()))
    return funcs, info


def fit_matrix(cap, intended):
    """intended = captured @ coef, a 3x3 matrix (no offset, so black->black).

    A full matrix can undo the channel cross-talk that a per-channel curve
    cannot, and it keeps greys exact because M @ (v,v,v) ~ (v,v,v).
    """
    coef, _, _, _ = np.linalg.lstsq(cap, intended, rcond=None)
    return coef


def correct_matrix(coef, rgb):
    return np.clip(np.asarray(rgb, dtype=np.float64) @ coef, 0, 255)


def _poly_features(rgb, deg):
    r, g, b = rgb[:, 0] / 255, rgb[:, 1] / 255, rgb[:, 2] / 255
    cols = [np.ones_like(r)]
    for d in range(1, deg + 1):
        for i in range(d + 1):
            for j in range(d - i + 1):
                k = d - i - j
                cols.append(r**i * g**j * b**k)
    return np.stack(cols, axis=1)


def fit_poly(cap, intended, deg=3):
    """A smooth 3D polynomial: captures both the per-channel tone curve and
    the channel cross-talk that the other two models each miss."""
    coef, _, _, _ = np.linalg.lstsq(_poly_features(cap, deg), intended, rcond=None)
    return coef, deg


def correct_poly(params, rgb):
    coef, deg = params
    return np.clip(
        _poly_features(np.asarray(rgb, dtype=np.float64), deg) @ coef, 0, 255
    )


def build_lut(correct, n):
    """Sample the correction model on the LUT grid: lut[bi, gi, ri]."""
    r = np.linspace(0, 255, n).reshape(1, 1, n)
    g = np.linspace(0, 255, n).reshape(1, n, 1)
    b = np.linspace(0, 255, n).reshape(n, 1, 1)
    pts = np.stack(np.broadcast_arrays(r, g, b), axis=-1).reshape(-1, 3)
    return correct(pts).reshape(n, n, n, 3)


def correct_lut(lut, rgb):
    """Trilinear interpolation on a lut[bi, gi, ri] array, exactly what a
    3D-LUT renderer (e.g. OBS's Apply LUT) does."""
    n = lut.shape[0]
    v = np.clip(np.asarray(rgb, dtype=np.float64), 0, 255) / 255 * (n - 1)
    i0 = np.clip(np.floor(v).astype(int), 0, n - 2)
    f = v - i0
    out = np.zeros((len(v), 3))
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                w = (
                    (f[:, 0] if dx else 1 - f[:, 0])
                    * (f[:, 1] if dy else 1 - f[:, 1])
                    * (f[:, 2] if dz else 1 - f[:, 2])
                )
                out += w[:, None] * lut[i0[:, 2] + dz, i0[:, 1] + dy, i0[:, 0] + dx]
    return np.clip(out, 0, 255)


# --------------------------------------------------------------------------- #
# images
# --------------------------------------------------------------------------- #
def render_expected(shape, patches, cols, rows):
    h, w = shape[:2]
    out = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, (r, g, b) in enumerate(patches):
        row, col = divmod(idx, cols)
        y0, y1 = int(row * h / rows), int((row + 1) * h / rows)
        x0, x1 = int(col * w / cols), int((col + 1) * w / cols)
        out[y0:y1, x0:x1] = (r, g, b)
    return out


def apply_funcs(img, funcs):
    out = np.empty_like(img)
    for c in range(3):
        out[..., c] = funcs[c](img[..., c])
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_diag(funcs, rgb):
    """Apply the per-channel curves to an (N, 3) array of RGB values."""
    return np.stack([funcs[c](rgb[:, c]) for c in range(3)], axis=1)


# --------------------------------------------------------------------------- #
# colour-difference metrics
# --------------------------------------------------------------------------- #
def _srgb_to_linear(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _rgb_to_lab(rgb):
    lin = _srgb_to_linear(rgb)
    m = np.array(
        [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]
    )
    xyz = lin @ m.T
    wp = np.array([0.95047, 1.0, 1.08883])
    r = xyz / wp
    f = np.where(r > (6.0 / 29) ** 3, np.cbrt(r), r / (3 * (6.0 / 29) ** 2) + 4.0 / 29)
    return np.stack(
        [
            116 * f[..., 1] - 16,
            500 * (f[..., 0] - f[..., 1]),
            200 * (f[..., 1] - f[..., 2]),
        ],
        axis=-1,
    )


def rgb_distance(a, b):
    """Euclidean distance in 8-bit RGB."""
    return np.linalg.norm(np.asarray(a, float) - np.asarray(b, float), axis=-1)


def delta_e76(a, b):
    """CIE76 colour difference (not perceptually perfect, but good enough)."""
    return np.linalg.norm(_rgb_to_lab(a) - _rgb_to_lab(b), axis=-1)


def _fmt(v):
    return f"mean {v.mean():5.1f}  p95 {np.percentile(v, 95):5.1f}  max {v.max():5.1f}"


def report(cap, intended, correct):
    """Print a before/after quality summary and return the per-patch table."""
    corrected = correct(cap)
    gray = (intended[:, 0] == intended[:, 1]) & (intended[:, 1] == intended[:, 2])

    d_rgb_b, d_rgb_a = rgb_distance(cap, intended), rgb_distance(corrected, intended)
    d_de_b, d_de_a = delta_e76(cap, intended), delta_e76(corrected, intended)

    print("\nquality (RGB distance / \u0394E76), lower is better:")
    print(f"  all     before: {_fmt(d_rgb_b)}   |  \u0394E {_fmt(d_de_b)}")
    print(f"  all     after : {_fmt(d_rgb_a)}   |  \u0394E {_fmt(d_de_a)}")
    for name, m in (("gray", gray), ("colour", ~gray)):
        if m.any():
            print(
                f"  {name:6s}  before: {_fmt(d_rgb_b[m])}   |  \u0394E {_fmt(d_de_b[m])}"
            )
            print(
                f"  {name:6s}  after : {_fmt(d_rgb_a[m])}   |  \u0394E {_fmt(d_de_a[m])}"
            )

    worst = int(np.argmax(d_de_a))
    tgt = corrected[worst].round().astype(int).tolist()
    print(
        f"  worst after: intended {intended[worst].astype(int).tolist()} "
        f"captured {cap[worst].round().astype(int).tolist()} -> {tgt} "
        f"(\u0394E {d_de_a[worst]:.1f})"
    )

    table = np.column_stack(
        [
            np.arange(len(intended)),
            intended,
            cap.round(),
            corrected.round(),
            d_rgb_b,
            d_rgb_a,
            d_de_b,
            d_de_a,
        ]
    )
    return table


def write_report(path, table):
    header = (
        "index,intended_r,intended_g,intended_b,captured_r,captured_g,"
        "captured_b,corrected_r,corrected_g,corrected_b,"
        "rgb_dist_before,rgb_dist_after,dE_before,dE_after"
    )
    with open(path, "w") as fh:
        fh.write(header + "\n")
        for row in table:
            fh.write(",".join(f"{v:.3f}" for v in row) + "\n")


def save_images(out_path, img, correct, patches, cols, rows, size=1200):
    base = os.path.splitext(out_path)[0]
    h, w = img.shape[:2]
    scale = min(1.0, size / max(h, w))
    tw, th = max(1, int(w * scale)), max(1, int(h * scale))

    def small(a):
        return np.asarray(
            Image.fromarray(a.astype(np.uint8)).resize((tw, th), Image.NEAREST)
        )

    expected = small(render_expected(img.shape, patches, cols, rows))
    captured = small(np.clip(img, 0, 255).astype(np.uint8))

    paths = {
        "expected": f"{base}.expected.png",
        "captured": f"{base}.captured.png",
    }
    Image.fromarray(expected).save(paths["expected"])
    Image.fromarray(captured).save(paths["captured"])

    # side by side: expected | captured [| with LUT]
    sep = np.full((th, 8, 3), 255, np.uint8)
    panels = [expected, sep, captured]
    if correct is not None:
        fixed = np.clip(correct(img.reshape(-1, 3)), 0, 255).reshape(img.shape)
        corrected = small(fixed)
        paths["corrected"] = f"{base}.corrected.png"
        Image.fromarray(corrected).save(paths["corrected"])
        panels += [sep, corrected]
    combo_path = f"{base}.compare.png"
    Image.fromarray(np.concatenate(panels, axis=1)).save(combo_path)
    return paths, combo_path


# --------------------------------------------------------------------------- #
# .cube writer
# --------------------------------------------------------------------------- #
def write_cube(path, lut, title, comment):
    n = lut.shape[0]
    lines = [
        f'TITLE "{title}"',
        f"# {comment}",
        f"LUT_3D_SIZE {n}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
        "",
    ]
    for bi in range(n):
        for gi in range(n):
            for ri in range(n):
                out = lut[bi, gi, ri] / 255
                lines.append(f"{out[0]:.6f} {out[1]:.6f} {out[2]:.6f}")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    src = ap.add_argument_group("source")
    src.add_argument("--image", help="use an existing capture PNG instead of grabbing")
    src.add_argument(
        "--ffmpeg-input",
        default=None,
        help="AVFoundation device name (or index); "
        "default: auto-detect 'UGREEN 95348'",
    )
    src.add_argument(
        "--ffmpeg-size",
        default=None,
        help="force a resolution; default: try 3840x2160@30, 1920x1080@60, ...",
    )
    src.add_argument(
        "--ffmpeg-framerate",
        default=None,
        help="force a framerate (29.97 is usually rejected)",
    )
    src.add_argument(
        "--ffmpeg-frames",
        type=int,
        default=120,
        help="frames to grab (default 120; the first ones can be dark)",
    )
    src.add_argument(
        "--retries",
        type=int,
        default=3,
        help="re-grab if the capture is still dark (default 3)",
    )
    src.add_argument(
        "--colorspace",
        default="bt709",
        help="YUV matrix reported by the card (default bt709)",
    )
    src.add_argument(
        "--list-devices",
        action="store_true",
        help="print the AVFoundation devices and exit",
    )

    pat = ap.add_argument_group("pattern (must match the page)")
    pat.add_argument("--n", type=int, default=6)
    pat.add_argument("--cols", type=int, default=18)
    pat.add_argument("--rows", type=int, default=12)
    pat.add_argument("--mode", default="cube", choices=["cube", "gray", "ramp"])

    fit = ap.add_argument_group("fit / output")
    fit.add_argument("--bins", type=int, default=33)
    fit.add_argument(
        "--model",
        default="auto",
        choices=["auto", "perchannel", "matrix", "poly"],
        help="auto = whichever model fits best",
    )
    fit.add_argument(
        "--poly-deg",
        type=int,
        default=3,
        help="degree of the 3D polynomial model (default 3)",
    )
    fit.add_argument("--size3d", type=int, default=33, help="LUT_3D_SIZE")
    fit.add_argument("--out", default="capture-fix.cube")
    fit.add_argument(
        "--no-images", action="store_true", help="do not write the comparison PNGs"
    )
    fit.add_argument(
        "--no-report", action="store_true", help="do not write the per-patch CSV report"
    )
    fit.add_argument(
        "--force", action="store_true", help="write the LUT even if validation fails"
    )
    ap.add_argument("--title", default="MS2130S capture fix")
    args = ap.parse_args()

    if args.list_devices:
        for idx, name in list_avfoundation_devices():
            print(f"[{idx}] {name}")
        return

    patches = build_patches(args.n, args.mode)
    if len(patches) != args.cols * args.rows:
        raise SystemExit(
            f"pattern has {len(patches)} patches but grid is "
            f"{args.cols}x{args.rows}={args.cols * args.rows}"
        )

    if args.image:
        img = np.asarray(Image.open(args.image).convert("RGB"), dtype=np.float64)
        origin = args.image
    else:
        device = resolve_input(args.ffmpeg_input)
        if args.ffmpeg_size or args.ffmpeg_framerate:
            modes = [(args.ffmpeg_size or "auto", args.ffmpeg_framerate or "60")]
        else:
            # some modes come out black on this firmware, so try them in turn
            modes = [
                ("3840x2160", "30"),
                ("1920x1080", "60"),
                ("2560x1440", "60"),
                ("1280x720", "60"),
            ]
        img = None
        size = rate = None
        for size, rate in modes:
            for attempt in range(1, max(1, args.retries) + 1):
                img = grab_ffmpeg(
                    device, size, rate, args.ffmpeg_frames, args.colorspace
                )
                if img.mean() >= 20:
                    break
                print(
                    f"{size}@{rate} came out dark (mean {img.mean():.0f}), "
                    f"retry {attempt}/{args.retries} ..."
                )
            if img.mean() >= 20:
                break
            print(f"mode {size}@{rate} stays dark, trying another mode ...")
        origin = f"ffmpeg input {device!r} {size}@{rate}"
    print(f"capture: {origin}  ({img.shape[1]}x{img.shape[0]})")

    cap, spread = sample_patches(img, patches, args.cols, args.rows)
    intended = np.asarray(patches, dtype=np.float64)

    issues, warnings = validate(cap, spread, intended)
    for w in warnings:
        print(f"note: {w}")
    if issues:
        print("WARNING: the capture does not look like the calibration page:")
        for it in issues:
            print(f"  - {it}")
        print("  ... is the page fullscreen on the display that feeds the card?")
        if not args.no_images:
            _, combo = save_images(args.out, img, None, patches, args.cols, args.rows)
            print(f"wrote {combo} (expected | captured) for comparison")
        if not args.force:
            raise SystemExit("refusing to write a LUT (pass --force to override)")

    funcs, _ = fit_perchannel(cap, intended, args.bins)
    coef_m = fit_matrix(cap, intended)
    coef_p, pdeg = fit_poly(cap, intended, args.poly_deg)
    models = {
        "perchannel": (lambda rgb: apply_diag(funcs, rgb), "per-channel curves"),
        "matrix": (lambda rgb: correct_matrix(coef_m, rgb), "3x3 matrix"),
        "poly": (
            lambda rgb: correct_poly((coef_p, pdeg), rgb),
            f"3D polynomial deg {pdeg}",
        ),
    }
    resid = {k: np.abs(f(cap) - intended) for k, (f, _) in models.items()}
    model = args.model
    if model == "auto":
        model = min(models, key=lambda k: resid[k].mean())
    correct_model, desc = models[model]
    print(
        "  model residuals (RGB mean): "
        + "  ".join(f"{k}={resid[k].mean():.2f}" for k in models)
    )
    print(f"  using: {desc}")

    # everything below uses the sampled LUT, so the preview and the report
    # match exactly what OBS's Apply LUT filter will produce
    lut = build_lut(correct_model, args.size3d)
    correct = lambda rgb: correct_lut(lut, rgb)
    r = np.abs(correct(cap) - intended)
    print(f"  LUT ({args.size3d}^3) residual (RGB mean): {r.mean():.2f}")
    for c, name in enumerate("RGB"):
        print(
            f"  {name}: fit residual mean={r[:, c].mean():.2f} "
            f"max={r[:, c].max():.2f}"
        )

    # sanity: the LUT must map captured black/white to black/white
    dark = np.argmin(intended.sum(axis=1))
    bright = np.argmax(intended.sum(axis=1))
    blk = tuple(round(v) for v in correct(cap[dark : dark + 1])[0])
    wht = tuple(round(v) for v in correct(cap[bright : bright + 1])[0])
    print(f"  check: captured black -> {blk}, captured white -> {wht}")

    table = report(cap, intended, correct)
    if not args.no_report:
        rp = os.path.splitext(args.out)[0] + ".report.csv"
        write_report(rp, table)
        print(f"wrote {rp}")

    write_cube(args.out, lut, args.title, f"{desc}: captured -> intended")
    print(f"wrote {args.out}  (LUT_3D_SIZE {args.size3d}, model {model})")

    if not args.no_images:
        paths, combo = save_images(
            args.out, img, correct, patches, args.cols, args.rows
        )
        print(f"wrote {combo}")
        print(f"      {paths['expected']} / {paths['captured']} / {paths['corrected']}")


if __name__ == "__main__":
    main()
