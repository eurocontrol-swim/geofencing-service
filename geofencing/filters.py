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
from typing import List, Optional, Dict, Any

from geofencing.common import CompareMixin, Point, geojson_polygon_coordinates_from_point_list, \
    GeoJSONPolygonCoordinates
from geofencing.db import AIRSPACE_VOLUME_UPPER_LIMIT_IN_M, AIRSPACE_VOLUME_LOWER_LIMIT_IN_M
from geofencing.endpoints.utils import make_datetime_aware

__author__ = "EUROCONTROL (SWIM)"


class AirspaceVolumeFilter(CompareMixin):

    def __init__(self,
                 polygon: List[Point],
                 upper_limit_in_m: Optional[int] = AIRSPACE_VOLUME_UPPER_LIMIT_IN_M,
                 lower_limit_in_m: Optional[int] = AIRSPACE_VOLUME_LOWER_LIMIT_IN_M,
                 upper_vertical_reference: Optional[str] = None,
                 lower_vertical_reference: Optional[str] = None) -> None:
        """

        :param polygon:
        :param upper_limit_in_m:
        :param lower_limit_in_m:
        :param upper_vertical_reference:
        :param lower_vertical_reference:
        """
        self.polygon = polygon
        self.upper_limit_in_m = upper_limit_in_m
        self.lower_limit_in_m = lower_limit_in_m
        self.upper_vertical_reference = upper_vertical_reference or ""
        self.lower_vertical_reference = lower_vertical_reference or ""

    @property
    def polygon_coordinates(self) -> GeoJSONPolygonCoordinates:
        return geojson_polygon_coordinates_from_point_list(self.polygon)

    @classmethod
    def from_dict(cls, object_dict):
        return cls(
            polygon=[Point.from_dict(coords) for coords in object_dict['polygon']],
            upper_limit_in_m=object_dict.get("upper_limit_in_m"),
            lower_limit_in_m=object_dict.get("lower_limit_in_m"),
            upper_vertical_reference=object_dict.get("upper_vertical_reference"),
            lower_vertical_reference=object_dict.get("lower_vertical_reference"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "polygon": [point.to_dict() for point in self.polygon],
            "upper_limit_in_m": self.upper_limit_in_m,
            "lower_limit_in_m": self.lower_limit_in_m,
            "upper_vertical_reference": self.upper_vertical_reference,
            "lower_vertical_reference": self.lower_vertical_reference
        }


class UASZonesFilter(CompareMixin):

    def __init__(self,
                 airspace_volume: AirspaceVolumeFilter,
                 regions: List[int],
                 request_id: str,
                 start_date_time: datetime,
                 end_date_time: datetime,
                 updated_after_date_time: Optional[datetime] = None) -> None:
        """

        :param airspace_volume:
        :param request_id:
        :param regions:
        :param start_date_time:
        :param end_date_time:
        :param updated_after_date_time:
        """
        self.airspace_volume = airspace_volume
        self.regions = regions
        self.request_id = request_id
        self.start_date_time = make_datetime_aware(start_date_time)
        self.end_date_time = make_datetime_aware(end_date_time)
        self.updated_after_date_time = make_datetime_aware(updated_after_date_time) \
            if updated_after_date_time is not None else None

    @classmethod
    def from_dict(cls, object_dict):
        return cls(
            airspace_volume=AirspaceVolumeFilter.from_dict(object_dict["airspace_volume"]),
            regions=object_dict['regions'],
            start_date_time=object_dict['start_date_time'],
            end_date_time=object_dict['end_date_time'],
            updated_after_date_time=object_dict.get('updated_after_date_time'),
            request_id=object_dict.get('request_id')
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "airspace_volume": self.airspace_volume.to_dict(),
            "regions": self.regions,
            "start_date_time": self.start_date_time,
            "end_date_time": self.end_date_time,
            "updated_after_date_time": self.updated_after_date_time,
            "request_id": self.request_id
        }
