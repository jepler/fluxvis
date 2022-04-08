import numpy as np
import click
from . import invpolar
from skimage.transform import downscale_local_mean
from skimage.io import imsave
from greaseweazle.image.scp import SCP

@click.command()
@click.option("--slices", default=4000, help="The angular resolution of the flux in 1/revolution (default: 4000)")
@click.option("--stacks", default=6, help="The pixel thickness of a track (default: 6)")
@click.option("--diameter", default=108., help="The diameter of the outermost track, in track-widths (5.25\" disk is approximately 108, 3.5\" disk is approximately 210 (default: 108)")
@click.option("--tracks", default=80, help="The total count of tracks (default: 80)")
@click.option("--stride", default=1, help="Stride between tracks (default: 1)")
@click.option("--start", default=0, help="Number of the first tracks (default: 0)")
@click.option("--side", default=0, help="Side of floppy (default: 0)")
@click.option("--resolution", default=960, help="Resolution of square output image (default: 960)")
@click.option("--linear/--polar", default=False, help="Use a linear instead of polar image")
@click.option("--oversample", default=2, help="Increase oversampling of polar transformation")
@click.argument("input", type=click.Path(exists=True))
@click.argument("output", type=click.Path())
def main(slices, stacks, diameter, tracks, input, output, stride, start, side, resolution, linear, oversample):
    """Visualize INPUT (an scp-format flux file) to OUTPUT (a png file)
    """
    flux = SCP.from_file(input)

    if linear:
        major = round(tracks*stacks)
    else:
        major = round(diameter*stacks/2)

    density = np.zeros((major , slices), dtype=np.float32)
    r = np.arange(slices)

    for cyl in range(0, tracks):
        t0 = major - (1+cyl) * stacks
        t1 = major - cyl * stacks - 1
        track = flux.get_track(cyl*stride+start, side)
        if track is None: continue
        track.cue_at_index()
        if not track.index_list:
            index = sum(track.list)
        else:
            index = track.index_list[0]
        index = track.index_list[0]
        indices = np.array(track.list, dtype=np.float32) * (slices/index)
        indices = np.floor(np.add.accumulate(indices))
        lo = np.searchsorted(indices, r, 'left'),
        hi = np.searchsorted(indices, r, 'right')
        density[t0:t1, :] = hi - lo

    if not linear:
        density = invpolar.warp_inverse_polar(density, output_shape=(resolution*oversample, resolution*oversample))
        density = downscale_local_mean(density, (oversample, oversample))
    maxdensity = np.max(density)
    
    imsave(output, (density * (255/maxdensity)).astype(np.uint8))

if __name__ == '__main__':
    main()