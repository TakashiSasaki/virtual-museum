"""Create the museum font subset. Requires fonttools (see docs/web-optimization.md).

The original font stays outside Unity Assets; the existing runtime GUID/path stays
unchanged. All current source/catalog/scene characters plus Latin and kana remain.
"""
from pathlib import Path
import hashlib
import io
import json
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "unity/VirtualMuseum"
ASSETS = PROJECT / "Assets/Museum"
SOURCE = ROOT / "source-assets/fonts/NotoSansJP-Regular.otf"
OUTPUT = ASSETS / "Resources/MuseumFonts/NotoSansJP-Regular.otf"
MANIFEST = ASSETS / "Editor/FontSubset.json"
ORIGINAL_SHA = "dff723ba59d57d136764a04b9b2d03205544f7cd785a711442d6d2d085ac5073"


def requested_characters():
    chars = set(range(32, 127)) | set(range(0x3000, 0x3100)) | set(range(0xFF00, 0xFFF0))
    for path in sorted(ASSETS.rglob("*")):
        if path.suffix not in {".cs", ".asset", ".unity"} or "GeneratedWeb" in path.parts:
            continue
        text = path.read_text(encoding="utf-8-sig")
        text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda match: chr(int(match[1], 16)), text)
        chars.update(map(ord, text))
    return {c for c in chars if unicodedata.category(chr(c)) not in {"Cc", "Cf", "Cs", "Cn"}}


def main():
    if not SOURCE.exists():
        original = OUTPUT.read_bytes()
        if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
            raise RuntimeError("Original font missing; refusing to treat a modified/subset font as source")
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        SOURCE.write_bytes(original)
        (SOURCE.parent / "LICENSE.txt").write_bytes((OUTPUT.parent / "LICENSE.txt").read_bytes())
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != ORIGINAL_SHA:
        raise RuntimeError("Original font fingerprint differs; review the source before regenerating")
    # Optional project-local tooling; no machine-specific path is recorded here.
    sys.path.insert(0, str(PROJECT / "Library/MuseumPython"))
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont(SOURCE, recalcTimestamp=False)
    original_cmap = set(font.getBestCmap())
    requested = requested_characters()
    supported = requested & original_cmap
    options = subset.Options()
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]
    options.recalc_timestamp = False
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=supported)
    subsetter.subset(font)
    # Derivative font has its own family name; copyright/license records remain.
    for record in font["name"].names:
        if record.nameID in {1, 3, 4, 6, 16, 17}:
            value = "Regular" if record.nameID == 17 else "MuseumJPSubset-Regular" if record.nameID in {3, 6} else "Museum JP Subset"
            record.string = value.encode(record.getEncoding())
    if "CFF " in font:
        cff = font["CFF "].cff
        cff.fontNames = ["MuseumJPSubset-Regular"]
        cff.topDictIndex[0].FullName = "Museum JP Subset Regular"
        cff.topDictIndex[0].FamilyName = "Museum JP Subset"
    buffer = io.BytesIO()
    font.save(buffer)
    data = buffer.getvalue()
    verified = TTFont(io.BytesIO(data))
    assert supported <= set(verified.getBestCmap()), "Subset lost requested glyphs"
    if not OUTPUT.exists() or OUTPUT.read_bytes() != data:
        OUTPUT.write_bytes(data)
    manifest = {"version": 1, "sourceSha256": ORIGINAL_SHA, "subsetSha256": hashlib.sha256(data).hexdigest(),
                "originalBytes": SOURCE.stat().st_size, "subsetBytes": len(data),
                "codepoints": sorted(supported), "unsupported": sorted(requested - original_cmap)}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"glyphCodepoints": len(supported), "originalBytes": SOURCE.stat().st_size, "subsetBytes": len(data)}))


if __name__ == "__main__":
    main()
