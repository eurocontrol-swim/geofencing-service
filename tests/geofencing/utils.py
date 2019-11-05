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
import uuid
from datetime import datetime, timezone

from geofencing.common import polygon_filter_from_mongo_polygon
from geofencing.db import MongoPolygonType
from geofencing.db.models import AirspaceVolume, AuthorityEntity, ApplicableTimePeriod, CodeYesNoType, UASZone, \
    CodeRestrictionType, CodeUSpaceClassType, CodeZoneType, DataSource, DailySchedule, CodeWeekDay, User
from geofencing.filters import UASZonesFilter, AirspaceVolumeFilter

__author__ = "EUROCONTROL (SWIM)"


def get_unique_id():
    return uuid.uuid4().hex


def make_airspace_volume(polygon: MongoPolygonType, upper_limit_in_m=None, lower_limit_in_m=None) -> AirspaceVolume:
    return AirspaceVolume(
        polygon=polygon,
        upper_limit_in_m=upper_limit_in_m,
        lower_limit_in_m=lower_limit_in_m or 0
    )


def make_authority() -> AuthorityEntity:
    result = AuthorityEntity()
    result.authority_id = get_unique_id()
    result.name = "AuthorityEntity"
    result.contact_name = "AuthorityEntity manager"
    result.service = "AuthorityEntity service"
    result.email = "auth@autority.be"

    return result


def make_daily_schedule():
    return DailySchedule(
        day=CodeWeekDay.MON.value,
        start_time=datetime(2000, 1, 1, 12, 00, tzinfo=timezone.utc),
        end_time=datetime(2000, 1, 1, 18, 00, tzinfo=timezone.utc),
    )


def make_applicable_period():
    return ApplicableTimePeriod(
        permanent=CodeYesNoType.YES.value,
        start_date_time=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        end_date_time=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        daily_schedule=[make_daily_schedule()]
    )


def make_user():
    user = User()
    user.username = get_unique_id()
    user.password = ""

    return user


def make_uas_zone(polygon: MongoPolygonType) -> UASZone:
    result = UASZone()
    result.identifier = get_unique_id()[:7]
    result.name = get_unique_id()
    result.type = CodeZoneType.COMMON.value
    result.region = 1
    result.restriction = CodeRestrictionType.NO_RESTRICTION.value
    result.data_capture_prohibition = CodeYesNoType.YES.value
    result.u_space_class = CodeUSpaceClassType.EUROCONTROL.value
    result.message = "message"
    result.country = "BEL"
    result.airspace_volume = make_airspace_volume(polygon)
    result.authorization_requirement = make_authority()
    result.applicable_time_period = make_applicable_period()
    result.data_source = DataSource(
        creation_date_time=datetime.now(timezone.utc),
    )
    result.user = make_user()

    return result


def make_uas_zones_filter_from_db_uas_zone(uas_zone: UASZone):
    uas_zones_filter = UASZonesFilter(
        airspace_volume=AirspaceVolumeFilter(
            polygon=polygon_filter_from_mongo_polygon(uas_zone.airspace_volume.polygon),
            upper_limit_in_m=uas_zone.airspace_volume.upper_limit_in_m,
            lower_limit_in_m=uas_zone.airspace_volume.lower_limit_in_m,
            upper_vertical_reference=uas_zone.airspace_volume.upper_vertical_reference,
            lower_vertical_reference=uas_zone.airspace_volume.lower_vertical_reference
        ),
        regions=[uas_zone.region],
        start_date_time=uas_zone.applicable_time_period.start_date_time,
        end_date_time=uas_zone.applicable_time_period.end_date_time,
        update_after_date_time=uas_zone.data_source.update_date_time,
    )

    return uas_zones_filter
