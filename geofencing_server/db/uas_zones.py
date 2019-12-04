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
from functools import reduce
from typing import List, Optional

from mongoengine import Q, DoesNotExist

from geofencing_server.db.models import UASZone
from geofencing_server.filters import UASZonesFilter

__author__ = "EUROCONTROL (SWIM)"


def get_uas_zones_by_identifier(uas_zone_identifier: str) -> Optional[UASZone]:
    """
    Retrieves a UASZone by its identifier
    :param uas_zone_identifier:
    :return:
    """
    try:
        result = UASZone.objects.get(identifier=uas_zone_identifier)
    except DoesNotExist:
        result = None

    return result


def get_uas_zones(uas_zones_filter: UASZonesFilter) -> List[UASZone]:
    """
    Retrieves UASZones based on the provided filters criteria.

    :param uas_zones_filter:
    :return:
    """

    queries_list = [
        Q(airspace_volume__polygon__geo_intersects=uas_zones_filter.airspace_volume.polygon_coordinates),
        Q(airspace_volume__upper_limit_in_m__lte=uas_zones_filter.airspace_volume.upper_limit_in_m),
        Q(airspace_volume__lower_limit_in_m__gte=uas_zones_filter.airspace_volume.lower_limit_in_m),
        Q(region__in=uas_zones_filter.regions),
        Q(applicable_time_period__start_date_time__gte=uas_zones_filter.start_date_time),
        Q(applicable_time_period__end_date_time__lte=uas_zones_filter.end_date_time)
    ]

    if uas_zones_filter.updated_after_date_time:
        queries_list.append(Q(data_source__update_date_time__gte=uas_zones_filter.updated_after_date_time))

    query: Q = reduce(lambda q1, q2: q1 & q2, queries_list, Q())

    return UASZone.objects(query).all()


def create_uas_zone(uas_zone: UASZone):
    """
    Saves the uas_zone in DB
    :param uas_zone:
    """
    uas_zone.save()


def delete_uas_zone(uas_zone: UASZone):
    """
    Deletes the uas_zone from DB
    :param uas_zone:
    """
    uas_zone.delete()
