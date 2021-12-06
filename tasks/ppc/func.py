import utils.positive_pixel_count as ppc
from flask import Flask, jsonify, request
from  flask_cors import CORS

import girder_client
import numpy as np

app = Flask(__name__)
CORS(app)


# set up parameters to use for PPC
params = ppc.Parameters(
    hue_value=0.05,
    hue_width=0.15,
    saturation_minimum=0.05,
    intensity_upper_limit=0.95,
    intensity_weak_threshold=0.65,
    intensity_strong_threshold=0.35,
    intensity_lower_limit=0.05,
)
roi_size = 500


def login(private=True):
    """login()
    Connects to chosen girder API.

    INPUTS
    ------
    api_url : str
        Url to the API to connect to (i.e. servername/api/v1).
    private : bool
        True to interactively authenticate (to access private items)
        or False if accessing public items.

    RETURNS
    -------
    gc : girder_client.GirderClient
        Girder client connected to a girder API.
    """
    gc = girder_client.GirderClient(apiUrl=request.args.get('apiUrl'))
    if private:
        gc.setToken(request.headers.get('girder-token'))
    return gc


def get_center_roi(gc, imid, roi_size=500):
    # get a square region from WSI in the center of WSI
    tileinfo = gc.get(f'item/{imid}/tiles')
    
    # get coords of rectangle centered around center
    xc, yc = tileinfo['sizeX'] / 2, tileinfo['sizeY'] / 2

    xmin, ymin = int(xc - roi_size / 2), int(yc - roi_size / 2)

    # set up the region dictionary
    region = dict(
        left=xmin, top=ymin, width=roi_size, height=roi_size
    )
    
    return region


@app.route("/test_ppc")
def get_marker():
    # get list of image ids
    gc = login()
    ids = request.args.get('ids')
    ids = ids.split(',')
    status = []
    for id in ids:

        try:
            item = gc.getItem(id)
            
            # get coords for image center ROI
            region = get_center_roi(gc, imid, roi_size=roi_size)
            
            # run ppc on image
            output = ppc.count_image(gc, imid, params, region, tile_dim=roi_size)
            
            status.append({'status': 'ok', 'id': id, 'results': output})
        except Exception as e:
            status.append({'status': 'error', 'id': id, 'error': str(e)})
            continue

    return jsonify(status)
