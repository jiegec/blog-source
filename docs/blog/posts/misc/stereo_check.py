#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "numpy>=1.24",
#     "matplotlib>=3.7",
# ]
# ///
"""
stereo_check.py —— 视频/音频左右声道波形 + 音量检测

用法（依赖由 uv 自动安装，无需手动建虚拟环境）：
    ./stereo_check.py 录像.mp4
    ./stereo_check.py 录像.mp4 --sr 16000 --output wave.png
    ./stereo_check.py 录像.mp4 --no-plot --json

功能：
    1. 用 ffmpeg 解码视频里的第一条音轨（>2 声道自动下混为立体声）；
    2. 绘制左/右声道全片波形（包络）和 L/R 散点图（相关性）；
    3. 打印峰值、RMS 音量电平（dBFS）、波峰因数、直流偏移。

依赖外部命令：ffmpeg / ffprobe
"""

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

EPS = 1e-12
CHUNK = 1 << 22  # 分块处理，避免长视频一次性占用大量内存


# --------------------------------------------------------------------------- #
# 基础工具
# --------------------------------------------------------------------------- #
def die(msg: str, code: int = 1):
    print(f"\n[错误] {msg}", file=sys.stderr)
    sys.exit(code)


def db(x: float) -> float:
    """线性幅度 -> dBFS"""
    return 20.0 * math.log10(max(float(x), EPS))


def fmt_db(x: float) -> str:
    return "  -inf " if x <= -200 else f"{x:7.2f}"


def need_tools():
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        die(
            "找不到 " + " / ".join(missing) + "，请先安装 ffmpeg。\n"
            "  macOS : brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
            "  Win   : winget install Gyan.FFmpeg"
        )


# --------------------------------------------------------------------------- #
# 探测 & 解码
# --------------------------------------------------------------------------- #
def probe(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels,channel_layout",
        "-show_entries", "format=duration,format_name",
        "-of", "json", str(path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"ffprobe 读取失败：{r.stderr.strip()[:400]}")
    data = json.loads(r.stdout or "{}")
    streams = data.get("streams") or []
    if not streams:
        die("该文件中没有找到音频流。")
    st, fmt = streams[0], data.get("format") or {}
    try:
        dur = float(fmt.get("duration") or 0)
    except (TypeError, ValueError):
        dur = 0.0
    return {
        "codec": st.get("codec_name") or "?",
        "sample_rate": int(st.get("sample_rate") or 0) or None,
        "channels": int(st.get("channels") or 0) or None,
        "layout": st.get("channel_layout") or "",
        "duration": dur or None,
        "format": (fmt.get("format_name") or "?").split(",")[0],
    }


def decode(path: Path, src_channels: int, sr=None, start=0.0, max_seconds=None):
    """解码为 float32 的 (n_samples, n_channels)，n_channels ∈ {1, 2}。"""
    out_ch = 1 if src_channels == 1 else 2
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += [
        "-i", str(path),
        "-map", "0:a:0", "-vn",
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ac", str(out_ch),
    ]
    if sr:
        cmd += ["-ar", str(sr)]
    if max_seconds:
        cmd += ["-t", str(max_seconds)]
    cmd += ["-"]

    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        die("ffmpeg 解码失败：" + r.stderr.decode("utf-8", "replace").strip()[:400])
    x = np.frombuffer(r.stdout, dtype="<f4")
    if x.size == 0:
        die("解码得到的采样点数为 0。")
    x = x[: (x.size // out_ch) * out_ch].reshape(-1, out_ch)
    return x


# --------------------------------------------------------------------------- #
# 音量统计
# --------------------------------------------------------------------------- #
def collect(x: np.ndarray) -> dict:
    """分块统计每个声道的均值、峰值、RMS（双声道时含左右协方差）。"""
    n, ch = x.shape
    s = np.zeros(ch)
    ss = np.zeros(ch)
    pk = np.zeros(ch)
    lr = 0.0
    for i in range(0, n, CHUNK):
        b = x[i:i + CHUNK].astype(np.float64)
        s += b.sum(axis=0)
        ss += np.einsum("ij,ij->j", b, b)
        pk = np.maximum(pk, np.abs(b).max(axis=0))
        if ch == 2:
            lr += float(np.dot(b[:, 0], b[:, 1]))
    mean = s / n
    return {
        "n": n, "ch": ch,
        "mean": mean,
        "peak": pk,
        "rms": np.sqrt(np.maximum(ss / n, 0.0)),
        "cov": (lr / n - mean[0] * mean[1]) if ch == 2 else 0.0,
    }


def corr_of(st: dict) -> float:
    """零延迟相关系数 corr(L,R)：+1 完全相同，0 不相关，-1 完全反相。"""
    if st["ch"] != 2:
        return float("nan")
    v0 = max(st["rms"][0] ** 2 - st["mean"][0] ** 2, 0.0)
    v1 = max(st["rms"][1] ** 2 - st["mean"][1] ** 2, 0.0)
    d = math.sqrt(v0 * v1)
    return float(st["cov"] / d) if d > EPS else float("nan")


# --------------------------------------------------------------------------- #
# 绘图
# --------------------------------------------------------------------------- #
def setup_cjk_font() -> bool:
    """找一个可用的中文字体；找不到则返回 False（调用方把中文降级为 ASCII）。"""
    import matplotlib
    from matplotlib import font_manager

    candidates = [
        "PingFang SC", "Heiti SC", "Hiragino Sans GB", "Songti SC", "STHeiti",
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Noto Sans SC",
        "Source Han Sans SC", "WenQuanYi Zen Hei", "WenQuanYi Micro Hei",
        "Arial Unicode MS",
    ]
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in have:
            matplotlib.rcParams["font.family"] = "sans-serif"
            matplotlib.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            matplotlib.rcParams["axes.unicode_minus"] = False
            return True
    return False


def envelope(x: np.ndarray, sr: float, bins: int = 2000):
    """把长波形压缩成 bins 个 (最小值, 最大值) 包络点。"""
    n = x.size
    if n <= bins:
        return np.arange(n) / sr, x, x
    block = n // bins
    y = x[: block * bins].reshape(bins, block)
    t = (np.arange(bins) * block + block / 2) / sr
    return t, y.min(axis=1), y.max(axis=1)


def plot_env(ax, x, sr, color, label, alpha=0.35, bins=2000):
    t, lo, hi = envelope(x, sr, bins)
    ax.fill_between(t, lo, hi, color=color, alpha=alpha, linewidth=0)
    ax.plot(t, hi, color=color, lw=0.5, alpha=0.9)
    ax.plot(t, lo, color=color, lw=0.5, alpha=0.9, label=label)
    ax.set_xlim(0, max(t[-1], 1e-6))


def make_plot(x, sr, st, corr, title, out_png, show, bins=2000):
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not setup_cjk_font():          # 无中文字体时避免标题出现豆腐块
        title = title.encode("ascii", "replace").decode()

    n, ch = x.shape
    names = [("Left", "C0"), ("Right", "C3")]

    if ch == 1:
        fig = plt.figure(figsize=(13, 3.6))
        axes = [fig.add_subplot(111)]
    else:
        # 上两个面板：左/右声道全片波形；下面板居中：L/R 散点图（相关性）
        fig = plt.figure(figsize=(13, 9.5))
        gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 1.35], hspace=0.55)
        axes = [fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :]),
                fig.add_subplot(gs[2, 1])]

    for i in range(ch):
        ax = axes[i]
        name, color = names[i]
        plot_env(ax, x[:, i], sr, color, name, bins=bins)
        label = "L" if i == 0 else "R"
        ax.set_title(f"{name} channel ({label})   "
                     f"peak {fmt_db(db(st['peak'][i])).strip()} dBFS   "
                     f"RMS {fmt_db(db(st['rms'][i])).strip()} dBFS")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("amplitude")

    # L/R 散点图：点落在 y=x 上为同相，落在 y=-x 上为反相
    if ch == 2:
        ax = axes[2]
        m = min(n, 20000)
        idx = np.linspace(0, n - 1, m).astype(np.int64)
        L, R = x[idx, 0], x[idx, 1]
        ax.scatter(L, R, s=1.5, alpha=0.25, color="C7", edgecolors="none")
        lim = float(max(np.abs(L).max(), np.abs(R).max())) or 1.0
        ax.plot([-lim, lim], [-lim, lim], "g--", lw=1, label="in phase (y=x)")
        ax.plot([-lim, lim], [lim, -lim], "r--", lw=1, label="anti phase (y=-x)")
        ax.set_xlim(-lim, lim), ax.set_ylim(-lim, lim)
        corr_txt = "n/a" if math.isnan(corr) else f"{corr:+.3f}"
        ax.set_title(f"L vs R scatter   correlation = {corr_txt}")
        ax.set_xlabel("Left"), ax.set_ylabel("Right")
        ax.legend(loc="upper right", fontsize=8)

    fig.suptitle(title, fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    if ch == 2:                       # tight_layout 之后设置，保证散点图是正方形
        axes[2].set_aspect("equal", adjustable="box")
    fig.savefig(out_png, dpi=130)
    print(f"波形图已保存：{out_png}")
    if show:
        plt.show()
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="视频/音频左右声道波形与音量检测（uv 单文件脚本）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("input", help="视频或音频文件")
    ap.add_argument("-o", "--output", help="波形图输出路径（默认 <输入>_waveform.png）")
    ap.add_argument("--sr", type=int, default=None,
                    help="解码重采样率；默认保持源采样率，长视频会自动降采样控内存")
    ap.add_argument("--max-mem-mb", type=float, default=400.0,
                    help="自动选 --sr 时的采样数据内存上限（MB）")
    ap.add_argument("--start", type=float, default=0.0, help="从第几秒开始分析")
    ap.add_argument("--max-seconds", type=float, default=None, help="只分析前 N 秒")
    ap.add_argument("--bins", type=int, default=2000, help="全片包络的显示点数")
    ap.add_argument("--show", action="store_true", help="弹窗显示（默认只保存 PNG）")
    ap.add_argument("--no-plot", action="store_true", help="不绘图，只打印数据")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    need_tools()
    path = Path(args.input)
    if not path.exists():
        die(f"文件不存在：{path}")

    info = probe(path)
    src_ch = info["channels"] or 2

    # 选分析采样率：估算 PCM 内存，超限则自动降采样
    base_sr = info["sample_rate"] or 48000
    dur = info["duration"]
    if args.max_seconds:
        dur = min(dur, args.max_seconds) if dur else args.max_seconds
    sr = args.sr
    if sr is None:
        sr = base_sr
        if dur:
            budget = args.max_mem_mb * 1e6 / (2 * 4)      # 可容纳的采样点数
            if dur * base_sr > budget:
                sr = max(8000, int(budget / dur / 100) * 100)
                if not args.json:
                    print(f"[提示] 音频较长，自动降采样到 {sr} Hz 以控制内存"
                          f"（可用 --sr 指定，或用 --max-seconds 只分析片段）。")
    if src_ch == 1 and not args.json:
        print("[提示] 源文件为单声道。")
    if src_ch > 2 and not args.json:
        print(f"[提示] 源文件有 {src_ch} 个声道，已按 ffmpeg 默认规则下混为立体声分析。")

    x = decode(path, src_ch, sr=sr, start=args.start, max_seconds=args.max_seconds)
    n, ch = x.shape
    dur = n / sr

    est = n * ch * 4
    if est > 1_500_000_000:
        print(f"[提示] 已解码约 {est/1e9:.1f} GB 采样数据，建议加 --sr 16000 或 --max-seconds。")

    st = collect(x)
    corr = corr_of(st)

    result = {
        "file": str(path),
        "format": info["format"], "codec": info["codec"],
        "source_channels": src_ch, "analysis_channels": ch,
        "sample_rate": sr, "samples": int(n), "duration": round(dur, 3),
        "correlation": None if math.isnan(corr) else round(corr, 5),
        "channels": {
            name: {
                "peak_dbfs": round(db(st["peak"][i]), 3),
                "rms_dbfs": round(db(st["rms"][i]), 3),
                "crest_db": round(db(st["peak"][i]) - db(st["rms"][i]), 3),
                "dc_offset": float(st["mean"][i]),
            }
            for i, name in enumerate(["L", "R"][:ch])
        },
    }

    if not args.no_plot:
        out = Path(args.output) if args.output else path.with_name(path.stem + "_waveform.png")
        make_plot(x, sr, st, corr, path.name, out, args.show, args.bins)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ---------------- 文本报告 ---------------- #
    print()
    print("=" * 62)
    print(f"文件    : {path.name}")
    print(f"容器/流 : {info['format']} / {info['codec']}   "
          f"源声道数 {src_ch}  分析声道数 {ch}")
    print(f"采样率  : {sr} Hz   时长: {dur:.2f} s   采样点: {n:,}")
    print("-" * 62)
    print(f"{'通道':<10}{'峰值 dBFS':>12}{'RMS dBFS':>12}{'波峰因数':>12}{'直流偏移':>12}")
    for i, name in enumerate(["左 L", "右 R"][:ch]):
        print(f"{name:<10}{fmt_db(db(st['peak'][i])):>12}"
              f"{fmt_db(db(st['rms'][i])):>12}"
              f"{db(st['peak'][i]) - db(st['rms'][i]):>10.1f}dB"
              f"{st['mean'][i]:>+12.5f}")
    print("=" * 62)


if __name__ == "__main__":
    main()
