#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "app/assets"

DEFAULT_TOUR_FRAMES = [
    Path("/tmp/rr-tour-01-overview.png"),
    Path("/tmp/rr-tour-02-map.png"),
    Path("/tmp/rr-tour-03-zip.png"),
    Path("/tmp/rr-tour-04-model.png"),
    Path("/tmp/rr-tour-05-explorer.png"),
]
DEFAULT_ZIP_FRAMES = [
    Path("/tmp/rr-zip-01-11230.png"),
    Path("/tmp/rr-zip-02-10001.png"),
    Path("/tmp/rr-zip-03-11221.png"),
    Path("/tmp/rr-zip-04-11358.png"),
]


def load_frame(path: Path, width: int = 960) -> Image.Image:
    image = Image.open(path).convert("RGB")
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def transition_frames(
    images: list[Image.Image],
    *,
    hold_ms: int = 1_500,
    transition_ms: int = 90,
) -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    durations: list[int] = []
    for index, image in enumerate(images):
        frames.append(image)
        durations.append(hold_ms)
        next_image = images[(index + 1) % len(images)]
        for alpha in (0.25, 0.5, 0.75):
            frames.append(Image.blend(image, next_image, alpha))
            durations.append(transition_ms)
    return frames, durations


def save_gif(source_paths: list[Path], output_path: Path) -> None:
    missing = [path for path in source_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing demo frames: {missing}")

    frames, durations = transition_frames([load_frame(path) for path in source_paths])
    palette_frames = [
        frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for frame in frames
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    palette_frames[0].save(
        output_path,
        save_all=True,
        append_images=palette_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Saved {output_path} ({output_path.stat().st_size / 1_000_000:.1f} MB)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build RatRadar browser demo GIFs")
    parser.add_argument(
        "--tour-output",
        type=Path,
        default=ASSET_DIR / "ratradar-product-tour.gif",
    )
    parser.add_argument(
        "--zip-output",
        type=Path,
        default=ASSET_DIR / "ratradar-zip-demo.gif",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    save_gif(DEFAULT_TOUR_FRAMES, args.tour_output)
    save_gif(DEFAULT_ZIP_FRAMES, args.zip_output)


if __name__ == "__main__":
    main()
