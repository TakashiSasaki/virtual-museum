"""Generate repeatable, seamless color/height textures for the V1 museum.

Run with a Python containing NumPy, for example Blender's bundled Python:
    python generate_material_textures.py --output <texture-directory>
The PNG alpha channel stores a subtle height field used for surface relief.
Existing files are never overwritten unless --overwrite is explicitly given.
"""
import argparse
from pathlib import Path
import struct
import zlib

import numpy as np

SIZE = 512
RNG = np.random.default_rng(20261105)
Y, X = np.mgrid[0:SIZE, 0:SIZE] / SIZE


def noise(scale_x, scale_y=None):
    """Periodic, smoothly filtered noise; scale is feature frequency per tile."""
    scale_y = scale_x if scale_y is None else scale_y
    ky = np.fft.fftfreq(SIZE)[:, None] * SIZE
    kx = np.fft.rfftfreq(SIZE)[None, :] * SIZE
    spectrum = np.fft.rfft2(RNG.standard_normal((SIZE, SIZE)))
    spectrum *= np.exp(-((kx / scale_x) ** 2 + (ky / scale_y) ** 2) * .5)
    field = np.fft.irfft2(spectrum, s=(SIZE, SIZE)).real
    return field / max(field.std(), 1e-6)


def rgba(base, shade, height, tint=(1, 1, 1)):
    c = np.asarray(base, dtype=np.float64)[None, None, :]
    tone = np.asarray(tint, dtype=np.float64)[None, None, :]
    rgb = np.clip(c + shade[:, :, None] * tone, 0, 1)
    alpha = np.clip(.5 + height, 0, 1)[:, :, None]
    return (np.concatenate((rgb, alpha), axis=2) * 255 + .5).astype(np.uint8)


def png_bytes(image):
    """Encode a color RGBA PNG using only the Python standard library."""
    h, w, _ = image.shape
    def chunk(kind, payload):
        body = kind + payload
        return struct.pack('>I', len(payload)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)
    scan = b''.join(b'\0' + image[row].tobytes() for row in range(h))
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(scan, 9)) + chunk(b'IEND', b''))


def textures():
    # Fine matte wall coating: subtle plaster clouding and roller stipple.
    coarse, fine = noise(7), noise(110)
    wall_height = .02 * coarse + .035 * fine
    wall = rgba((.82, .82, .79), .004 * coarse + .003 * fine, wall_height)

    # Horizontal wood fibres with broad variation, fine pores and warm brown varnish.
    flow = .010 * np.sin(2*np.pi*X*2) + .006 * noise(3, 3)
    phase = 2*np.pi*(Y*32 + flow)
    fibres = (np.sin(phase) + .42*np.sin(phase*2 + .3) +
              .22*np.sin(phase*3 - .4)) / 1.64
    waves = noise(3, 18)
    pores = np.maximum(noise(5, 75) - 1.0, 0)
    wood_height = .16 * fibres + .045 * waves - .14 * pores
    wood = rgba((.36, .205, .115), .050*fibres + .022*waves - .022*pores,
                wood_height, (1.0, .77, .55))

    # Quiet off-white laminate with fine speckles and soft directional finish.
    mottled, speckle = noise(9), noise(140)
    laminate_height = .025 * mottled + .065 * speckle
    laminate = rgba((.85, .85, .82), .005*mottled + .006*speckle, laminate_height)

    # Powder-coated steel, very fine pebbled enamel on the storage units.
    metal_fine = noise(105)
    metal = rgba((.72, .75, .72), .006*metal_fine, .07*metal_fine)

    # Tight woven, subdued carpet, not a high-contrast checkerboard.
    yarn_x = np.cos(2*np.pi*(X*110 + .012*noise(2)))
    yarn_y = np.cos(2*np.pi*(Y*110 + .012*noise(2)))
    weave = .45*yarn_x + .55*yarn_y
    carpet_noise = noise(75)
    carpet = rgba((.44, .43, .39), .025*weave + .012*carpet_noise,
                  .18*weave + .09*carpet_noise, (1, .98, .9))

    # Commercial homogeneous vinyl: a continuous pale warm-grey sheet rather
    # than wooden planks or stone slabs. At 1 repeat/metre these mineral flecks
    # are millimetres across. Most contrast belongs in the finish, not color.
    floor_cloud, floor_grain = noise(5), noise(150)
    dark_fleck = np.maximum(noise(210)-1.35, 0)
    light_fleck = np.maximum(noise(190)-1.55, 0)
    wear_mask = np.maximum(noise(6)-.6, 0)
    fine_scuff = noise(90, 5) * wear_mask
    vinyl = rgba((.735, .738, .705),
                 .0035*floor_cloud + .003*floor_grain - .014*dark_fleck +
                 .009*light_fleck - .0015*fine_scuff,
                 .018*floor_grain - .025*dark_fleck + .018*light_fleck + .009*fine_scuff)

    # Soft grained rubber work mat.
    rubber_fine = noise(95)
    rubber = rgba((.055, .28, .23), .007*rubber_fine, .08*rubber_fine,
                  (.5, .9, .8))
    return {'WallPaint.png': wall, 'Walnut.png': wood, 'Laminate.png': laminate,
            'PowderCoat.png': metal, 'CarpetWeave.png': carpet,
            'VinylFloor.png': vinyl, 'RubberMat.png': rubber}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--only', nargs='+', help='Write only these texture names, e.g. VinylFloor (with or without .png)')
    args = parser.parse_args()
    maps = textures()
    if args.only:
        requested = {name if name.endswith('.png') else name + '.png' for name in args.only}
        unknown = requested - maps.keys()
        if unknown:
            raise SystemExit('Unknown texture names: ' + ', '.join(sorted(unknown)))
        maps = {name: pixels for name, pixels in maps.items() if name in requested}
    collisions = [str(args.output / name) for name in maps if (args.output / name).exists()]
    if collisions and not args.overwrite:
        raise SystemExit('Refusing to overwrite: ' + ', '.join(collisions))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, pixels in maps.items():
        (args.output / name).write_bytes(png_bytes(pixels))
        print(name)


if __name__ == '__main__':
    main()
