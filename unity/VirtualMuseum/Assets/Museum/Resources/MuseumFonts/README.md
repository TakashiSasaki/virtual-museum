# Museum Japanese font

`NotoSansJP-Regular.otf` now contains **Museum JP Subset**, a glyph subset derived from the official Noto CJK static Regular font. The filename and Unity GUID are preserved for existing references; the internal family name is renamed. The original is retained at repository `source-assets/fonts/NotoSansJP-Regular.otf`, outside Unity Assets, with its license. The source metadata below describes that original, not the derivative.

- Source: <https://github.com/notofonts/noto-cjk/blob/main/Sans/SubsetOTF/JP/NotoSansJP-Regular.otf>
- Download: <https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/SubsetOTF/JP/NotoSansJP-Regular.otf>
- Retrieved: 2026-11-06
- Size: 4,533,028 bytes
- Copyright (font metadata): © 2014-2021 Adobe (http://www.adobe.com/).
- SHA-256: `dff723ba59d57d136764a04b9b2d03205544f7cd785a711442d6d2d085ac5073`
- License: SIL Open Font License 1.1, reproduced in [LICENSE.txt](LICENSE.txt).
- Upstream license: <https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE>

Keep **Include Font Data** enabled and the character set **Dynamic** in Unity's font importer. `MuseumExperience` loads this asset from Resources when its serialized font field is empty, so both browser and Editor use an included font. Room TextMeshes and the runtime interaction signs track the dynamic font atlas when it changes.

Regenerate with `python work/prepare_web_font.py` from the repository root after adding Japanese text. The script scans current C# source, catalogs, and scenes, retaining Latin, kana and their used characters; it preserves license metadata and verifies the resulting cmap. `MuseumFontSubset` checks the font fingerprint and source coverage before any player build and stops if regeneration is required. See `docs/web-optimization.md` for tooling setup. This is appropriate for curated exhibition text, not arbitrary user-entered Japanese.
