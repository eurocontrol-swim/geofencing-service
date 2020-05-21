"""
Copyright 2020 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions
   and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
   and the following disclaimer in the documentation and/or other materials provided with the
   distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse
   or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open
Source Initiative: http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""

__author__ = "EUROCONTROL (SWIM)"

from typing import List

from shapely.geometry import Polygon as ShapelyPolygon

from geofencing_service.db.models import AirspaceVolume


def shapely_polygon_from_geo_polygon(polygon: dict) -> ShapelyPolygon:
    """

    :param polygon:
    :return:
    """
    return ShapelyPolygon(shell=polygon['coordinates'][0], holes=polygon['coordinates'][1:])


def _geo_polygons_intersect(poly1: dict, poly2: dict) -> bool:
    """

    :param poly1:
    :param poly2:
    :return:
    """

    s_poly1 = shapely_polygon_from_geo_polygon(poly1)
    s_poly2 = shapely_polygon_from_geo_polygon(poly2)

    return s_poly1.intersects(s_poly2)


def uas_zone_geometry_intersects_polygon(geometry: List[AirspaceVolume], polygon: dict) -> bool:
    """

    :param geometry:
    :param polygon:
    :return:
    """
    return any(
        [
            _geo_polygons_intersect(poly1=geo.horizontal_projection, poly2=polygon)
            for geo in geometry
        ]
    )
