"""Build the site images from the projects' docs/images folders.

Reads the README images of both projects (read only), writes resized WebP files,
app icons, Open Graph images, the favicon PNGs and the touch icon into assets/img/.
Run it again after the project images change:

    python scripts/prepare_images.py [--efm PATH] [--dc PATH]

Crops and stills are made from the WebP files already in assets/img/. To rebuild
only those, without the project folders:

    python scripts/prepare_images.py --derived

Requires Pillow. The default paths are the sibling project folders on the
maintainer's machine.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
PROJECTS = ROOT.parent
FONT_DIR = Path("C:/Windows/Fonts")

# Icon boxes inside the 2400x600 banners: (left, top, size).
EFM_ICON = (134, 128, 344)
DC_ICON = (113, 124, 352)

# Crop boxes inside the built 1600 px screenshots: (left, top, right, bottom).
EFM_FLOW = (339, 122, 1261, 704)  # the "Energy flow" card
DC_CARD_ONE = (26, 26, 523, 543)  # the push-ups card


def webp(src: Path, dst: Path, width: int | None = None, quality: int = 82) -> None:
    im = Image.open(src).convert("RGB")
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.Resampling.LANCZOS)
    im.save(dst, "WEBP", quality=quality, method=6)
    print(f"{dst.relative_to(ROOT)}  {im.size}  {dst.stat().st_size // 1024} KB")


def animated_webp(src: Path, dst: Path) -> None:
    im = Image.open(src)
    frames, durations = [], []
    for frame in ImageSequence.Iterator(im):
        frames.append(frame.convert("RGBA"))
        durations.append(frame.info.get("duration", 100))
    frames[0].save(
        dst,
        "WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        lossless=True,  # smaller than lossy for these flat UI recordings
        method=6,
    )
    print(f"{dst.relative_to(ROOT)}  {im.size}  {len(frames)} frames  {dst.stat().st_size // 1024} KB")


def crop_webp(src: Path, dst: Path, box: tuple[int, int, int, int]) -> None:
    im = Image.open(src).convert("RGB").crop(box)
    im.save(dst, "WEBP", quality=88, method=6)
    print(f"{dst.relative_to(ROOT)}  {im.size}  {dst.stat().st_size // 1024} KB")


def still_webp(src: Path, dst: Path) -> None:
    """The first frame of an animation, for visitors who prefer reduced motion."""
    im = Image.open(src).convert("RGB")
    im.save(dst, "WEBP", quality=88, method=6)
    print(f"{dst.relative_to(ROOT)}  {im.size}  {dst.stat().st_size // 1024} KB")


def derived() -> None:
    """Crops and stills, made from the files already in assets/img/."""
    for theme in ("light", "dark"):
        crop_webp(IMG / "efm" / f"diagram-{theme}.webp", IMG / "efm" / f"flow-{theme}.webp", EFM_FLOW)
        crop_webp(IMG / "dc" / f"hero-{theme}.webp", IMG / "dc" / f"card-one-{theme}.webp", DC_CARD_ONE)
    for name in ("periods", "drag", "tabs"):
        still_webp(IMG / "efm" / f"{name}.webp", IMG / "efm" / f"{name}-still.webp")
    for name in ("buttons", "input", "catch-up"):
        still_webp(IMG / "dc" / f"{name}.webp", IMG / "dc" / f"{name}-still.webp")


def rounded(im: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def icon(banner: Path, box: tuple[int, int, int], size: int = 256) -> Image.Image:
    left, top, side = box
    im = Image.open(banner).convert("RGB").crop((left, top, left + side, top + side))
    im = im.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
    return rounded(im, round(size * 2 * 0.22)).resize((size, size), Image.Resampling.LANCZOS)


def font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def og_project(banner: Path, dst: Path, bg: tuple[int, int, int]) -> None:
    """1200x630: the light banner centred on its own background colour."""
    canvas = Image.new("RGB", (1200, 630), bg)
    band = Image.open(banner).convert("RGB").resize((1200, 300), Image.Resampling.LANCZOS)
    canvas.paste(band, (0, 150))
    canvas.save(dst, "PNG", optimize=True)
    print(f"{dst.relative_to(ROOT)}  {dst.stat().st_size // 1024} KB")


def og_home(logo: Path, icons: list[Image.Image], dst: Path) -> None:
    """The logo, the name and the project icons."""
    canvas = Image.new("RGB", (1200, 630), (246, 248, 251))
    draw = ImageDraw.Draw(canvas)
    mark = Image.open(logo).convert("RGB").resize((560, 560), Image.Resampling.LANCZOS)
    mark = rounded(mark, 123).resize((280, 280), Image.Resampling.LANCZOS)
    canvas.paste(mark, (90, 175), mark)
    draw.text((430, 170), "Skylolerr", font=font(True, 104), fill=(13, 27, 42))
    draw.text((434, 315), "Home Assistant integrations,", font=font(False, 40), fill=(70, 84, 102))
    draw.text((434, 365), "installed with HACS", font=font(False, 40), fill=(70, 84, 102))
    for i, ic in enumerate(icons):
        tile = ic.resize((72, 72), Image.Resampling.LANCZOS)
        canvas.paste(tile, (434 + i * 88, 443), tile)
    canvas.save(dst, "PNG", optimize=True)
    print(f"{dst.relative_to(ROOT)}  {dst.stat().st_size // 1024} KB")


def site_icons(logo: Path) -> None:
    """Touch icon and favicon.ico from the 1024 px render of the logo.

    favicon.svg is the logo SVG with rounded corners; Pillow cannot render SVG, so
    the raster sizes come from the PNG export of the same design.
    """
    im = Image.open(logo).convert("RGB")
    touch = im.resize((180, 180), Image.Resampling.LANCZOS)  # iOS rounds it itself
    touch.save(ROOT / "apple-touch-icon.png", "PNG", optimize=True)
    rounded(im, round(im.width * 0.22)).resize((48, 48), Image.Resampling.LANCZOS).save(
        ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)]
    )
    print("apple-touch-icon.png, favicon.ico")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--efm", type=Path, default=PROJECTS / "HA Energy Hierarchy" / "docs" / "images")
    parser.add_argument("--dc", type=Path, default=PROJECTS / "Hacs integrationen" / "docs" / "images")
    parser.add_argument("--derived", action="store_true", help="only rebuild the crops and stills")
    args = parser.parse_args()
    if args.derived:
        derived()
        return
    efm, dc = args.efm, args.dc
    (IMG / "efm").mkdir(parents=True, exist_ok=True)
    (IMG / "dc").mkdir(parents=True, exist_ok=True)

    # Energy Flow Mapper
    for name in ("banner-light", "banner-dark"):
        webp(efm / f"{name}.png", IMG / "efm" / f"{name}.webp", 1200)
    for name in ("diagram-light", "diagram-dark", "card-light", "card-dark"):
        webp(efm / f"{name}.png", IMG / "efm" / f"{name}.webp", 1600)
        webp(efm / f"{name}.png", IMG / "efm" / f"{name}-800.webp", 800)
    for name in ("period", "save", "backups", "water-dark"):
        webp(efm / f"{name}.png", IMG / "efm" / f"{name}.webp", 1200)
    for name in ("phone-light", "phone-dark"):
        webp(efm / f"{name}.png", IMG / "efm" / f"{name}.webp", 412)
    for name in ("periods", "drag", "tabs"):
        animated_webp(efm / f"{name}.gif", IMG / "efm" / f"{name}.webp")

    # Daily Challenge
    for name in ("banner-light", "banner-dark"):
        webp(dc / f"{name}.png", IMG / "dc" / f"{name}.webp", 1200)
    for name in ("hero-light", "hero-dark"):
        webp(dc / f"{name}.png", IMG / "dc" / f"{name}.webp", 1600)
        webp(dc / f"{name}.png", IMG / "dc" / f"{name}-800.webp", 800)
    webp(dc / "card-finished.png", IMG / "dc" / "card-finished.webp", 376)
    for name in ("buttons", "input", "catch-up"):
        animated_webp(dc / f"{name}.gif", IMG / "dc" / f"{name}.webp")

    # App icons (the light banner for both themes of the Energy Flow Mapper tile;
    # Daily Challenge has a light and a dark tile)
    efm_icon = icon(efm / "banner-light.png", EFM_ICON)
    efm_icon.save(IMG / "efm" / "icon.png", optimize=True)
    dc_light = icon(dc / "banner-light.png", DC_ICON)
    dc_light.save(IMG / "dc" / "icon-light.png", optimize=True)
    icon(dc / "banner-dark.png", DC_ICON).save(IMG / "dc" / "icon-dark.png", optimize=True)

    # Open Graph images
    og_project(efm / "banner-light.png", IMG / "og-energy-flow-mapper.png", (238, 245, 250))
    og_project(dc / "banner-light.png", IMG / "og-daily-challenge.png", (253, 241, 233))
    logo = ROOT / "assets" / "logo" / "skylolerr-logo-1024.png"
    og_home(logo, [efm_icon, dc_light], IMG / "og-home.png")
    site_icons(logo)

    derived()


if __name__ == "__main__":
    main()
