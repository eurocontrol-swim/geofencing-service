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
from datetime import datetime
from typing import List, Any, Union, Dict

from dateutil import parser

__author__ = "EUROCONTROL (SWIM)"

GeoJSONPolygonCoordinates = List[List[List[Union[float, int]]]]


class CompareMixin:
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.__dict__ == self.__dict__

    def __ne__(self, other: Any) -> bool:
        return not other == self


class Point(CompareMixin):

    def __init__(self, lat: float, lon: float) -> None:
        """

        :param lat:
        :param lon:
        """
        self.lat = lat
        self.lon = lon

    @classmethod
    def from_dict(cls, object_dict):
        return cls(
            lat=float(object_dict['lat']),
            lon=float(object_dict['lon']),
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "lat": self.lat,
            "lon": self.lon
        }


def geojson_polygon_coordinates_from_point_list(point_list: List[Point]) -> GeoJSONPolygonCoordinates:
    return [[[pf.lat, pf.lon] for pf in point_list]]


def point_list_from_geojson_polygon_coordinates(coordinates: GeoJSONPolygonCoordinates) -> List[Point]:
    return [Point(lat=lat, lon=lon) for lat, lon in coordinates[0]]
