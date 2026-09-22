"""Replace education slogans on login cover with ticket-system copy."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path(r"d:\workspace\新建文件夹\super-campus\src\assets\Jhbackstage.png")
BAK = SRC.with_name("Jhbackstage.education.bak.png")

TITLE = "登记 · 处理 · 闭环跟进"
SUB = "让问题有人跟，让客户有回音"
TITLE_COLOR = (51, 51, 51, 255)
SUB_COLOR = (153, 153, 153, 255)
# Original glyph bands (inclusive), measured from education.bak
TITLE_BAND = (1030, 1095)
SUB_BAND = (1140, 1190)


def pick_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    candidates = (
        [
            Path(r"C:\Windows\Fonts\msyhbd.ttc"),
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\simhei.ttf"),
        ]
        if bold
        else [
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\msyhbd.ttc"),
            Path(r"C:\Windows\Fonts\simhei.ttf"),
        ]
    )
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise SystemExit("No Chinese font found")


def clear_band(im: Image.Image, y0: int, y1: int) -> None:
    pixels = im.load()
    w, _ = im.size
    for y in range(y0, y1 + 1):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a <= 10:
                continue
            # Only wipe near-gray slogan ink; leave illustration untouched
            if abs(r - g) < 25 and abs(g - b) < 25 and r < 200:
                pixels[x, y] = (0, 0, 0, 0)


def center_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    cy: int,
    fill: tuple[int, int, int, int],
    canvas_w: int,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (canvas_w - tw) // 2 - bbox[0]
    y = cy - th // 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fill)


def main() -> None:
    if not BAK.exists():
        BAK.write_bytes(SRC.read_bytes())

    im = Image.open(BAK).convert("RGBA")
    w, h = im.size

    clear_band(im, *TITLE_BAND)
    clear_band(im, *SUB_BAND)

    draw = ImageDraw.Draw(im)
    title_font = pick_font(bold=True, size=54)
    sub_font = pick_font(bold=False, size=41)

    center_text(draw, TITLE, title_font, (TITLE_BAND[0] + TITLE_BAND[1]) // 2, TITLE_COLOR, w)
    center_text(draw, SUB, sub_font, (SUB_BAND[0] + SUB_BAND[1]) // 2, SUB_COLOR, w)

    # Keep RGBA so transparent page background stays clean
    im.save(SRC, optimize=True)
    print("updated", SRC)
    print("title:", TITLE)
    print("sub:", SUB)
    print("backup", BAK)


if __name__ == "__main__":
    main()
