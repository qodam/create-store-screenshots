# storeshot

Generate App Store and Google Play marketing screenshots: a headline, a subheadline and a device mockup on a coloured or image background, at the exact sizes the stores require.

| Script             | Output size    | Target                                                                 |
| ------------------ | -------------- | ---------------------------------------------------------------------- |
| `shots_mobile.py`  | 1284 × 2778 px | iPhone 6.5" / Android phone                                            |
| `shots_tablet.py`  | 2064 × 2752 px | iPad 13" / Android tablet                                              |
| `struct-folder.py` | —              | Sorts raw captures named `{number}_{device}_{lang}.{ext}` into folders |

Output is always an **RGB PNG with no alpha channel**, because both stores reject transparent images.

Rendering is deterministic: no browser, no HTML, no network access.

---

## Requirements

- Python 3 (tested with Python 3.13)
- [Pillow](https://pypi.org/project/Pillow/)
- Optional, for Arabic and Hebrew text when Pillow is built without Raqm: `arabic-reshaper` and `python-bidi`
- Fonts: for each text style, the script uses the font you set in the config. If none is set or the file is missing, it falls back to a system font (Poppins, Inter, Segoe UI, Arial or DejaVu Sans). If no system font is found, the script stops with an error.

```bash
pip install Pillow
# Arabic / Hebrew, if needed:
pip install arabic-reshaper python-bidi
```

## Quick start

1. Copy the template and edit it:

   ```bash
   cp config.example.json config.json
   ```

2. Put your captures where the config points, for example:

   ```
   assets/
   ├── mobile/fr/01-work.png
   ├── mobile/fr/02-end.png
   ├── tablet/fr/01-work.png
   └── ...
   ```

3. Run both renderers from the folder that contains `config.json`:

   ```bash
   python shots_mobile.py config.json
   python shots_tablet.py config.json
   ```

4. Find the results in `out/`:

   ```
   out/
   ├── mobile/fr/01.png    (1284 × 2778)
   ├── mobile/fr/02.png
   ├── tablet/fr/01.png    (2064 × 2752)
   └── ...
   ```

### Command-line options

Both `shots_*.py` scripts accept:

| Option         | Description                                                                |
| -------------- | -------------------------------------------------------------------------- |
| `config`       | Path to the JSON config (required)                                         |
| `--lang`, `-l` | Render only this language. Repeat the option for several languages.        |
| `--out`, `-o`  | Output folder, relative to the config file. Overrides `out` in the config. |

```bash
python shots_mobile.py config.json --lang fr --out preview
```

> **All paths are relative to the config file**, not to the folder you run the command from. This applies to `img`, `background_image`, font paths, frame paths and the output folder.

---

## Configuration

Start from [`config.example.json`](config.example.json). The keys below are the ones the scripts actually read.

### Top-level keys

| Key                                        | Description                                                                                                                                        |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `screens`                                  | Object: language code → list of screens. **Required.**                                                                                             |
| `out`                                      | Output folder (default `out`)                                                                                                                      |
| `font_bold`, `font_medium`, `font_regular` | Default fonts for all languages, e.g. `"fonts/Inter-Bold.ttf"`                                                                                     |
| `fonts`                                    | Per-language fonts, e.g. `"ru": {"bold": "...", "regular": "..."}`. Use this for scripts your default font does not cover (Cyrillic, CJK, Arabic). |
| `bg`                                       | Background colours, e.g. `["#F4F4F6", "#E3E4E8"]` (gradient)                                                                                       |
| `background_image`                         | Background image. It is cut into one slice per screen, so the set flows as one picture. Overrides `bg`.                                            |
| `color`                                    | Text colour used for both headline and subheadline                                                                                                 |
| `layout`                                   | Settings applied to every screen and language                                                                                                      |
| `mobile` / `tablet`                        | Settings applied to one format only. `mobile` is read by `shots_mobile.py`, `tablet` by `shots_tablet.py`.                                         |

### Screens

```json
"screens": {
  "fr": [
    {
      "img": "assets/mobile/fr/01-work.png",
      "img_tablet": "assets/tablet/fr/01-work.png",
      "headline": "S’entraîner",
      "sub": "Sans pub, sans compte"
    }
  ]
}
```

| Key                         | Description                                                                      |
| --------------------------- | -------------------------------------------------------------------------------- |
| `img`                       | Screenshot path, used for every format unless overridden                         |
| `img_mobile` / `img_tablet` | Screenshot for one format only                                                   |
| `headline`                  | Main text. Use `\n` to force a line break.                                       |
| `sub`                       | Subheadline                                                                      |
| `bg`                        | Background colours for this screen only. Ignored when `background_image` is set. |
| `layout`                    | Layout overrides for this screen only                                            |
| `mobile` / `tablet`         | Layout overrides for this screen and this format only                            |

**Skipping a screen on one format.** Set `"img_tablet": null` to leave this screen out of the tablet set. `shots_tablet.py` prints `IGNORE … pas de version tablet` and moves on. `shots_mobile.py` treats a `null` `img_mobile` the same way as a missing key: it falls back to `img`.

**Numbering.** Output files are numbered `01`, `02`… in config order. Skipped screens leave no gap.

### Layout keys

Settings are merged in this order, later ones winning:

```
built-in defaults  <  "layout"  <  "mobile" / "tablet"  <  screen "layout"  <  screen "mobile" / "tablet"
```

**`title` and `subtitle`**

| Key           | Description                                                                                                    |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| `x`           | `"center"`, `"left"`, `"right"` or a pixel value                                                               |
| `y`           | Pixel position of the **top of the capitals**, or `"auto"` to sit under the block above (spacing set by `gap`) |
| `gap`         | Spacing used when `y` is `"auto"`                                                                              |
| `size`        | Font size in px                                                                                                |
| `font`        | `"bold"`, `"medium"`, `"regular"`, or a direct path to a `.ttf` / `.otf`                                       |
| `color`       | `"#RRGGBB"`                                                                                                    |
| `align`       | `"center"`, `"left"` or `"right"` (for multi-line text)                                                        |
| `max_width`   | Maximum line width in px. `null` = image width minus margins.                                                  |
| `shrink`      | `true`: reduce the font size if the text overflows                                                             |
| `wrap`        | `true`: wrap onto several lines instead of shrinking                                                           |
| `tracking`    | Letter spacing in px (can be negative)                                                                         |
| `line_height` | Line spacing multiplier                                                                                        |
| `uppercase`   | `true`: convert to capitals                                                                                    |
| `shadow`      | `null` or `{"color": "#00000055", "blur": 12, "offset": [0, 4]}`                                               |

**`mockup`** (device frame and screenshot)

| Key           | Description                                                                                                                                                                                  |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `x`           | `"center"` or a pixel value                                                                                                                                                                  |
| `y`           | `"bottom"` (anchored to the bottom edge), `"auto"` (under the text, using `gap`) or a pixel value                                                                                            |
| `w`           | Width of the frame in px                                                                                                                                                                     |
| `h`           | Height in px, or `"auto"` to size the frame from the screenshot's own ratio so it is not cropped                                                                                             |
| `fit`         | `"stretch"`: the whole screenshot fills the screen, slightly distorted if the ratio differs. `"cover"`: fills, keeps ratio, may crop. `"contain"`: whole screenshot, keeps ratio, with bars. |
| `radius`      | Corner radius. Number of px, or a keyword (see below), or `"N%"` of the frame width.                                                                                                         |
| `border`      | Frame border width in px                                                                                                                                                                     |
| `color`       | Frame colour. `border_color` is accepted as an alias.                                                                                                                                        |
| `buttons`     | `true`: draw side buttons (volume, mute, power)                                                                                                                                              |
| `shadow`      | `null` or `{"color": "#00000055", "blur": 40, "offset": [0, 25]}`                                                                                                                            |
| `crop_bottom` | `true`: the frame may extend below the bottom edge. By default the frame is shrunk to fit the space under the text.                                                                          |
| `frame`       | Path to a transparent device-frame PNG. The screen area must be transparent.                                                                                                                 |

**Radius keywords**

| Value                         | `shots_mobile.py`           | `shots_tablet.py`        |
| ----------------------------- | --------------------------- | ------------------------ |
| `"iphone"`, `"ios"`, `"auto"` | 14 % of frame width         | same                     |
| `"android"`                   | 9 %                         | same                     |
| `"ipad"`, `"tablet"`          | — **not supported (error)** | 4.5 %                    |
| `"ipad-old"`                  | —                           | 2 % (square-edged iPads) |
| `"square"`                    | —                           | 0                        |
| `"N%"` or a number            | yes                         | yes                      |

> ⚠️ `"ipad"` in `shots_mobile.py` stops the script with `ValueError: could not convert string to float: 'ipad'`. Use a number or `"N%"` there, or keep `"ipad"` in the `tablet` section only.

**`background`** (set through `bg` or `background_image` at the top level)

| Key         | Description                                                |
| ----------- | ---------------------------------------------------------- |
| `colors`    | Gradient colours. A single colour gives a flat background. |
| `direction` | `"vertical"` or `"horizontal"`                             |
| `image`     | Image path, sliced per screen (see `background_image`)     |

### Fonts

Font lookup for each language, in order:

1. `fonts.<lang>.bold` / `.regular`
2. `font_bold` / `font_regular` at the top level
3. A system font (Poppins, Inter, Segoe UI, Arial, DejaVu Sans…)

If a font file is missing, the script prints `! [lang] police … introuvable` and uses the system fallback. Check the output visually when you add a new script: a fallback font may not cover all glyphs.

### Arabic and Hebrew

Pillow built with Raqm handles connected letters and right-to-left order itself. Without Raqm, the scripts use `arabic-reshaper` and `python-bidi` if they are installed. If neither is available, letters stay disconnected and a warning is printed.

---

## Sorting raw captures: `struct-folder.py`

This helper copies raw captures named `{number}_{device}_{lang}.{ext}` into a per-language, per-format folder:

```
1_iphone_fr.png   →  fr/mobile/1.png
2_ipad_fr.png     →  fr/tablet/2.png
1_android_en.jpg  →  en/mobile/1.jpg
```

| Device in the file name | Folder                        |
| ----------------------- | ----------------------------- |
| `iphone`, `android`     | `mobile`                      |
| `ipad`, `tablet`        | `tablet`                      |
| anything else           | used as the folder name as-is |

```bash
python struct-folder.py
```

It asks for a source folder (default: current folder) and a destination (default: same as source). It **copies** files and never moves or deletes them. Files that do not match the pattern are ignored.

The renderers do not read this layout automatically. Point the `img` / `img_tablet` paths in `config.json` at the copied files.

---

## Uploading to the stores

The output folders are `out/mobile/<lang>/` and `out/tablet/<lang>/`. The store tools expect different names:

| Store                                 | Expected folders                  | Expected locale folder     |
| ------------------------------------- | --------------------------------- | -------------------------- |
| App Store (`update-store-metadata`)   | `iphone/`, `ipad/`                | store locale, e.g. `fr-FR` |
| Google Play (`update-store-metadata`) | `phone/`, `tablet7/`, `tablet10/` | store locale, e.g. `fr-FR` |

Rename or copy the folders before uploading. `fr` → `fr-FR`, `mobile` → `iphone` (Apple) or `phone` (Google), `tablet` → `ipad` (Apple) or `tablet10` (Google).

---

## Project layout

```
.
├── shots_mobile.py        # renderer, 1284 × 2778
├── shots_tablet.py        # renderer, 2064 × 2752
├── struct-folder.py       # sorts raw captures
├── config.example.json    # template: copy to config.json
├── .gitignore
└── README.md
```

The two renderers share the same structure. Their defaults differ: `LAYOUT` at the top of each file holds the built-in values.

## Troubleshooting

| Message                             | Meaning and fix                                                                                                |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `IGNORE <path> : introuvable`       | The `img` path is wrong. The message lists the images that do exist in that folder.                            |
| `IGNORE … pas de version tablet`    | Expected when `img_tablet` is `null`.                                                                          |
| `police … introuvable`              | A font path in the config does not exist. The script uses a system font instead.                               |
| `Aucune police trouvee`             | No font on the system and none set in the config. Set `font_bold` and `font_regular`.                          |
| `mockup reduit (… -> … px de haut)` | The frame was too tall for the space under the text. Shrink `w`, move the text up, or set `crop_bottom: true`. |
| `aucun ecran transparent detecte`   | A `frame` PNG was given but its screen area is not transparent.                                                |
| `radius "…" inconnu`                | Unknown keyword for the tablet renderer. See the radius table.                                                 |
| `ValueError … 'ipad'`               | `radius: "ipad"` used in the mobile renderer. See the radius table.                                            |
| `lettres … detachees`               | Arabic/Hebrew without Raqm. Install `arabic-reshaper` and `python-bidi`.                                       |
