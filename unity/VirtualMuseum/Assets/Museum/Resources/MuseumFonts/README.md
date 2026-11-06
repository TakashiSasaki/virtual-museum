# Museum Japanese font

`NotoSansJP-Regular.otf` is the unmodified static Regular font from the official Noto CJK project. Its upstream Japanese subset contains Japanese and Latin glyphs; it is not a custom subset generated for this application.

- Source: <https://github.com/notofonts/noto-cjk/blob/main/Sans/SubsetOTF/JP/NotoSansJP-Regular.otf>
- Download: <https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/SubsetOTF/JP/NotoSansJP-Regular.otf>
- Retrieved: 2026-11-06
- Size: 4,533,028 bytes
- Copyright (font metadata): © 2014-2021 Adobe (http://www.adobe.com/).
- SHA-256: `dff723ba59d57d136764a04b9b2d03205544f7cd785a711442d6d2d085ac5073`
- License: SIL Open Font License 1.1, reproduced in [LICENSE.txt](LICENSE.txt).
- Upstream license: <https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE>

Keep **Include Font Data** enabled and the character set **Dynamic** in Unity's font importer. `MuseumExperience` loads this asset from Resources when its serialized font field is empty, so both browser and Editor use an included font. Room TextMeshes and the runtime interaction signs track the dynamic font atlas when it changes.
