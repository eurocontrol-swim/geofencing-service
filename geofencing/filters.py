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
from typing import List, Optional, Any

from geofencing.db import AIRSPACE_VOLUME_UPPER_LIMIT_IN_M, AIRSPACE_VOLUME_LOWER_LIMIT_IN_M

__author__ = "EUROCONTROL (SWIM)"


class CompareMixin:
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.__dict__ == self.__dict__

    def __ne__(self, other: Any) -> bool:
        return not other == self


class PolygonFilter(CompareMixin):

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
            lat=object_dict['lat'],
            lon=object_dict['lon'],
        )


class AirspaceVolumeFilter(CompareMixin):

    def __init__(self,
                 polygon: List[PolygonFilter],
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
        self.upper_vertical_reference = upper_vertical_reference
        self.lower_vertical_reference = lower_vertical_reference

    @classmethod
    def from_dict(cls, object_dict):
        return cls(
            polygon=[PolygonFilter.from_dict(coords) for coords in object_dict['polygon']],
            upper_limit_in_m=object_dict.get("upper_limit_in_m"),
            lower_limit_in_m=object_dict.get("lower_limit_in_m"),
            upper_vertical_reference=object_dict.get("upper_vertical_reference"),
            lower_vertical_reference=object_dict.get("lower_vertical_reference"),
        )


class UASZonesFilter(CompareMixin):

    def __init__(self,
                 airspace_volume: AirspaceVolumeFilter,
                 regions: List[int],
                 start_date_time: datetime,
                 end_date_time: datetime,
                 update_after_date_time: Optional[datetime] = None) -> None:
        """

        :param regions:
        :param start_date_time:
        :param end_date_time:
        :param update_after_date_time:
        """
        self.airspace_volume = airspace_volume
        self.regions = regions
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time
        self.update_after_date_time = update_after_date_time

    @classmethod
    def from_dict(cls, object_dict):
        return cls(
            airspace_volume=AirspaceVolumeFilter.from_dict(object_dict["airspace_volume"]),
            regions=object_dict['regions'],
            start_date_time=object_dict['start_date_time'],
            end_date_time=object_dict['end_date_time'],
            update_after_date_time=object_dict.get('update_after_date_time')
        )
