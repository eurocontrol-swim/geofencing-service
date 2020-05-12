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
# from datetime import datetime
# from typing import List, Optional, Dict, Any
#
# from geofencing_service.common import CompareMixin, Polygon
# from geofencing_service.db import AIRSPACE_VOLUME_UPPER_LIMIT, AIRSPACE_VOLUME_LOWER_LIMIT
# from geofencing_service.endpoints.utils import make_datetime_aware
#
# __author__ = "EUROCONTROL (SWIM)"
#
#
# class AirspaceVolumeFilter(CompareMixin):
#
#     def __init__(self,
#                  horizontal_projection: Polygon,
#                  uom_dimensions: str,
#                  upper_limit: Optional[int] = AIRSPACE_VOLUME_UPPER_LIMIT,
#                  lower_limit: Optional[int] = AIRSPACE_VOLUME_LOWER_LIMIT,
#                  upper_vertical_reference: Optional[str] = None,
#                  lower_vertical_reference: Optional[str] = None) -> None:
#         """
#         :param horizontal_projection:
#         :param uom_dimensions:
#         :param upper_limit:
#         :param lower_limit:
#         :param upper_vertical_reference:
#         :param lower_vertical_reference:
#         """
#         self.horizontal_projection = horizontal_projection
#         self.uom_dimensions = uom_dimensions
#         self.upper_limit = upper_limit
#         self.lower_limit = lower_limit
#         self.upper_vertical_reference = upper_vertical_reference or ""
#         self.lower_vertical_reference = lower_vertical_reference or ""
#
#     @classmethod
#     def from_dict(cls, object_dict):
#         return cls(
#             horizontal_projection=Polygon.from_dic(object_dict['horizontal_projection']),
#             uom_dimensions=object_dict.get('uom_dimensions'),
#             upper_limit=object_dict.get("upper_limit"),
#             lower_limit=object_dict.get("lower_limit"),
#             upper_vertical_reference=object_dict.get("upper_vertical_reference"),
#             lower_vertical_reference=object_dict.get("lower_vertical_reference")
#         )
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             "horizontal_projection": self.horizontal_projection,
#             "uom_dimensions": self.uom_dimensions,
#             "upper_limit": self.upper_limit,
#             "lower_limit": self.lower_limit,
#             "upper_vertical_reference": self.upper_vertical_reference,
#             "lower_vertical_reference": self.lower_vertical_reference
#         }
#
#
# class UASZonesFilter(CompareMixin):
#
#     def __init__(self,
#                  airspace_volume: AirspaceVolumeFilter,
#                  regions: List[int],
#                  start_date_time: datetime,
#                  end_date_time: datetime) -> None:
#         """
#
#         :param airspace_volume:
#         :param regions:
#         :param start_date_time:
#         :param end_date_time:
#         """
#         self.airspace_volume = airspace_volume
#         self.regions = regions
#         self.start_date_time = make_datetime_aware(start_date_time)
#         self.end_date_time = make_datetime_aware(end_date_time)
#
#     @classmethod
#     def from_dict(cls, object_dict):
#         return cls(
#             airspace_volume=AirspaceVolumeFilter.from_dict(object_dict["airspace_volume"]),
#             regions=object_dict['regions'],
#             start_date_time=object_dict['start_date_time'],
#             end_date_time=object_dict['end_date_time']
#         )
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             "airspace_volume": self.airspace_volume.to_dict(),
#             "regions": self.regions,
#             "start_date_time": self.start_date_time,
#             "end_date_time": self.end_date_time
#         }
