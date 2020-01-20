"""
Copyright 2019 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
   disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open Source Initiative:
http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""
from typing import List, Any, Union, Dict

__author__ = "EUROCONTROL (SWIM)"

GeoJSONPolygonCoordinates = List[List[List[Union[float, int]]]]


class CompareMixin:
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.__dict__ == self.__dict__

    def __ne__(self, other: Any) -> bool:
        return not other == self


class Point(CompareMixin):

    def __init__(self, lon: float, lat: float) -> None:
        """

        :param lat:
        :param lon:
        """
        self.lon = lon
        self.lat = lat

    @classmethod
    def from_dict(cls, object_dict):
        return cls(
            lon=float(object_dict['lon']),
            lat=float(object_dict['lat'])
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "lon": self.lon,
            "lat": self.lat
        }


def geojson_polygon_coordinates_from_point_list(point_list: List[Point]) -> GeoJSONPolygonCoordinates:
    """
        Converts a list of Point to a list of GeoJSON polygon coordinates.

        Example:
        this list of points:
        [
             Point(lon=50.863648, lat=4.329385),
             Point(lon=50.865348, lat=4.328055),
             Point(lon=50.86847, lat=4.317369),
             Point(lon=50.863648, lat=4.329385)
        ]
        will be converted to:
        [
            [[50.863648, 4.329385],
             [50.865348, 4.328055],
             [50.86847, 4.317369],
             [50.863648, 4.329385]]
        ]
    :param point_list:
    :return:
    """
    return [[[pf.lon, pf.lat] for pf in point_list]]


def point_list_from_geojson_polygon_coordinates(coordinates: GeoJSONPolygonCoordinates) -> List[Point]:
    """
        Converts a list of GeoJSON polygon coordinates to a list of Point.

        Example:
        this list of coordinates:
        [
            [[50.863648, 4.329385],
             [50.865348, 4.328055],
             [50.86847, 4.317369],
             [50.863648, 4.329385]]
        ]
        will be converted to:
        [
             Point(lon=50.863648, lat=4.329385),
             Point(lon=50.865348, lat=4.328055),
             Point(lon=50.86847, lat=4.317369),
             Point(lon=50.863648, lat=4.329385)
        ]
    :param coordinates:
    :return:
    """
    return [Point(lon=lon, lat=lat) for lon, lat in coordinates[0]]
