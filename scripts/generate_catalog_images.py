from __future__ import annotations

import hashlib
import json
from pathlib import Path
from textwrap import wrap
from xml.sax.saxutils import escape

from django.utils.text import slugify


CATEGORY_TREE = {
    "Personal Care & Hygiene": [
        "Shampoo",
        "Conditioner",
        "Hair Oil",
        "Hair Serum",
        "Hair Cream",
        "Hair Styling Gel",
        "Hair Wax",
        "Hair Color",
        "Henna",
        "Shampoo Hair Color",
        "Bath Soap",
        "Body Wash",
        "Hand Wash",
        "Hand Sanitizer",
        "Adult Diapers",
        "Body Oil",
    ],
    "Oral Care": ["Toothpaste", "Toothbrush", "Mouthwash"],
    "Skin Care / Creams & Lotion": [
        "Antiseptic Cream",
        "Fairness Cream",
        "Moisturizer",
        "Sunscreen",
        "Face Serum",
        "Men's Cream",
        "Men's Face Wash",
        "Face Wash",
        "Anti Aging Cream",
        "BB Cream",
        "CC Cream",
        "Foundation",
        "Compact",
        "Glycerin",
        "Cold Cream",
        "Face Pack",
        "Face Scrub",
        "Antiseptic Liquids",
    ],
    "Vaseline & Lip Care": ["Petroleum Jelly", "Lip Balm"],
    "Perfume & Fragrance": ["Perfume", "Deodorant", "Pocket Deo", "Roll On"],
    "Razor & Grooming": ["Blades", "Razor", "Shaving Cream", "Shaving Lotion", "Shaving Brush"],
    "Household Essentials": [
        "Toilet Cleaner",
        "Glass Cleaner",
        "Lizol/Floor Cleaner",
        "Bathroom Cleaner",
        "Phenyl",
        "Bleaching Powder",
        "Toilet Brush",
        "Utensil Scrub",
        "Cloth Washing Brush",
        "Floor Brush",
        "Dishwasher Bar",
        "Dishwasher Gel",
        "Clothes Detergent",
        "Naphthalene Balls",
        "Incense Sticks",
        "Safety Pins",
        "Lighters",
        "Shoe Brush",
        "Shoe Polish",
    ],
    "Utilities": [
        "Batteries",
        "Torch Light",
        "Glue / Gum",
        "Tapes",
        "Scissors",
        "Nail Cutter",
        "Needles & Thread",
        "Nail Remover",
        "Cotton",
        "Combs",
        "Handkerchief",
        "Rope",
        "Lock & Keys",
        "Mirrors",
        "Ear Buds",
        "Candles",
        "Bandages",
        "Cloth Clips",
        "Toilet Papers",
        "Bulbs",
        "Drawing Pins",
    ],
    "Games": ["Playing Cards", "Housie Books", "Tennis Balls", "Balloons"],
    "Baby care": [
        "Baby Soap",
        "Baby Cream",
        "Baby Powder",
        "Baby Oil",
        "Baby Shampoo",
        "Baby Lotion",
        "Baby Hair Oil",
        "Baby Body Wash",
        "Baby Diapers",
        "Baby Wipes",
        "Anti Rash Cream",
        "Baby Bottles",
        "Soother",
        "Teether",
        "Gripe Water",
        "Baby Gift Sets",
    ],
    "Stationery": [
        "Plain notebook",
        "Ruled notebook",
        "Gell Pen",
        "Ball pen",
        "Pencil",
        "Rubber",
        "Sharpner",
        "Lid pencils",
        "Lid",
        "Marker pen",
        "Highlighter",
        "Scale",
        "Correction pen",
        "Scissors",
        "Cellotapes",
        "Staplers and pin",
        "Pocket dairies and notebooks",
        "Color pencils",
        "Sceth pen",
        "Wax crayons",
        "Plastic crayons",
        "Water color",
        "Geometry box",
        "Book cover",
        "Chalk",
        "Slid",
        "Exam board",
        "Glue stics and gum",
    ],
    "Female Hygiene": ["Sanitary Pads", "Panty Liners", "Veet", "Hair Remover", "Razor"],
}


CATEGORY_ICONS = {
    "Personal Care & Hygiene": "🧴",
    "Oral Care": "🪥",
    "Skin Care / Creams & Lotion": "🧖",
    "Vaseline & Lip Care": "💋",
    "Perfume & Fragrance": "🌸",
    "Razor & Grooming": "🪒",
    "Household Essentials": "🧹",
    "Utilities": "🔋",
    "Games": "🎲",
    "Baby care": "🍼",
    "Stationery": "✏️",
    "Female Hygiene": "🩷",
}


def color_pair(seed: str) -> tuple[str, str]:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    c1 = f"#{digest[:6]}"
    c2 = f"#{digest[6:12]}"
    return c1, c2


def line_blocks(text: str, width: int = 20, max_lines: int = 3) -> list[str]:
    lines = wrap(text, width=width)
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [" ".join(lines[max_lines - 1 :])]
    return lines


def svg_card(category: str, name: str, item_type: str) -> str:
    grad_a, grad_b = color_pair(f"{category}-{name}-{item_type}")
    icon = CATEGORY_ICONS.get(category, "📦")
    title_lines = line_blocks(name, width=21 if item_type == "subcategory" else 18)
    cat_lines = line_blocks(category, width=27, max_lines=2)

    title_svg = "\n".join(
        f'<text x="72" y="{690 + idx * 64}" fill="#0c1f3e" font-size="56" font-family="Inter,Segoe UI,Arial,sans-serif" font-weight="700">{escape(line)}</text>'
        for idx, line in enumerate(title_lines)
    )
    category_svg = "\n".join(
        f'<text x="72" y="{300 + idx * 42}" fill="rgba(255,255,255,0.92)" font-size="36" font-family="Inter,Segoe UI,Arial,sans-serif" font-weight="600">{escape(line)}</text>'
        for idx, line in enumerate(cat_lines)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{grad_a}" />
      <stop offset="100%" stop-color="{grad_b}" />
    </linearGradient>
  </defs>
  <rect width="1200" height="1200" fill="url(#bg)" />
  <rect x="48" y="48" width="1104" height="1104" rx="56" fill="rgba(255,255,255,0.14)" />
  <rect x="72" y="540" width="1056" height="548" rx="44" fill="#f8fbff" />
  <text x="72" y="170" fill="white" font-size="120" font-family="Segoe UI Emoji,Apple Color Emoji,Noto Color Emoji,sans-serif">{icon}</text>
  <text x="210" y="155" fill="white" font-size="58" font-family="Inter,Segoe UI,Arial,sans-serif" font-weight="800">AaramKart</text>
  <text x="72" y="248" fill="rgba(255,255,255,0.94)" font-size="34" font-family="Inter,Segoe UI,Arial,sans-serif" font-weight="600">{escape(item_type.title())}</text>
  {category_svg}
  {title_svg}
  <text x="72" y="1122" fill="#4b6287" font-size="28" font-family="Inter,Segoe UI,Arial,sans-serif">Generated catalog image</text>
</svg>
"""


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    output_root = project_root / "static" / "img" / "generated"
    category_dir = output_root / "categories"
    subcategory_dir = output_root / "subcategories"
    category_dir.mkdir(parents=True, exist_ok=True)
    subcategory_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict[str, str | dict[str, str]]] = {}
    generated = 0

    for category, subcats in CATEGORY_TREE.items():
        c_slug = slugify(category)
        category_file = f"{c_slug}.svg"
        (category_dir / category_file).write_text(
            svg_card(category, category, "category"), encoding="utf-8"
        )
        generated += 1

        subcat_entries: dict[str, str] = {}
        for sub_name in subcats:
            s_slug = slugify(sub_name)
            filename = f"{c_slug}--{s_slug}.svg"
            (subcategory_dir / filename).write_text(
                svg_card(category, sub_name, "subcategory"), encoding="utf-8"
            )
            subcat_entries[sub_name] = f"img/generated/subcategories/{filename}"
            generated += 1

        manifest[category] = {
            "category_image": f"img/generated/categories/{category_file}",
            "subcategories": subcat_entries,
        }

    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Generated {generated} images.")
    print(f"Manifest: {output_root / 'manifest.json'}")


if __name__ == "__main__":
    main()
