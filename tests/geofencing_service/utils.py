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
import random
import uuid
from base64 import b64encode
from datetime import datetime, timezone
from typing import Optional, Dict

from geofencing_service.db.models import AirspaceVolume, TimePeriod, CodeYesNoType, UASZone, \
    UASZonesFilter, CodeRestrictionType, CodeUSpaceClassType, CodeZoneType, DailyPeriod, \
    CodeWeekDay, User, CodeVerticalReferenceType, Authority, UASZonesSubscription, \
    GeofencingSMSubscription, CodeAuthorityRole, CodeZoneReasonType, UomDistance

__author__ = "EUROCONTROL (SWIM)"


def get_unique_id():
    return uuid.uuid4().hex


NOW = datetime.now(timezone.utc)
NOW_STRING = NOW.isoformat()

BASILIQUE_POLYGON = {
    'type': 'Polygon',
    'coordinates': [[
        [4.329385, 50.863648],
        [4.328055, 50.865348],
        [4.317369, 50.868470],
        [4.314826, 50.867671],
        [4.315920, 50.865873],
        [4.326508, 50.862792],
        [4.329385, 50.863648]
    ]]
}


INTERSECTING_BASILIQUE_POLYGON = {
    'type': 'Polygon',
    'coordinates': [[
        [4.328120, 50.862525],
        [4.329257, 50.865502],
        [4.323686, 50.865468],
        [4.328120, 50.862525]
    ]]
}


NON_INTERSECTING_BASILIQUE_POLYGON = {
    'type': 'Polygon',
    'coordinates': [[
        [4.325421, 50.870058],
        [4.326890, 50.867615],
        [4.321407, 50.867602],
        [4.325421, 50.870058]
    ]]
}


def make_airspace_volume(horizontal_projection: dict,
                         uom_dimensions: str = UomDistance.METERS.value,
                         upper_limit: Optional[int] = None,
                         lower_limit: Optional[int] = None) -> AirspaceVolume:
    return AirspaceVolume(
        horizontal_projection=horizontal_projection,
        uom_dimensions=uom_dimensions,
        lower_vertical_reference=CodeVerticalReferenceType.AMSL.value,
        upper_vertical_reference=CodeVerticalReferenceType.AMSL.value,
        upper_limit=upper_limit,
        lower_limit=lower_limit or 0
    )


def make_authority() -> Authority:
    return Authority(
        name=get_unique_id(),
        contact_name="Authority manager",
        service="Authority service",
        email="auth@autority.be",
        site_url="http://www.autority.be",
        phone="234234234",
        purpose=CodeAuthorityRole.AUTHORIZATION.value,
        interval_before="P3Y"
    )


def make_daily_period():
    return DailyPeriod(
        day=CodeWeekDay.MON.value,
        start_time=datetime(2000, 1, 1, 12, 00, tzinfo=timezone.utc),
        end_time=datetime(2000, 1, 1, 18, 00, tzinfo=timezone.utc),
    )


def make_applicable_period():
    result = TimePeriod(
        permanent=CodeYesNoType.YES.value,
        start_date_time=datetime(2020, 1, 1, 0, 0, 0).replace(tzinfo=timezone.utc),
        end_date_time=datetime(2021, 1, 1, 0, 0, 0).replace(tzinfo=timezone.utc),
        schedule=[make_daily_period()]
    )

    return result


def make_user(username=None, password='password'):
    user = User()
    user.username = username or get_unique_id()
    user.password = password

    return user


def make_uas_zone(horizontal_projection: Optional[dict] = None,
                  user: Optional[User] = None) -> UASZone:
    result = UASZone()
    result.identifier = get_unique_id()[:7]
    result.country = "BEL"
    result.name = get_unique_id()
    result.type = CodeZoneType.COMMON.value
    result.restriction = CodeRestrictionType.NO_RESTRICTION.value
    result.restriction_conditions = ["special conditions"]
    result.region = 1
    result.reason = [CodeZoneReasonType.AIR_TRAFFIC.value]
    result.other_reason_info = "other reason"
    result.regulation_exemption = CodeYesNoType.YES.value
    result.u_space_class = CodeUSpaceClassType.EUROCONTROL.value
    result.message = "message"
    result.zone_authority = make_authority()
    result.applicability = make_applicable_period()
    result.geometry = [make_airspace_volume(
        horizontal_projection=horizontal_projection or BASILIQUE_POLYGON)]
    result.user = user or make_user()

    return result


def make_uas_zones_filter_from_db_uas_zone(
        uas_zone: UASZone, uom_dimensions: str = UomDistance.METERS.value) -> UASZonesFilter:

    uas_zones_filter = UASZonesFilter(
        airspace_volume=AirspaceVolume(
            horizontal_projection=uas_zone.geometry[0].horizontal_projection,
            uom_dimensions=uom_dimensions,
            upper_limit=uas_zone.geometry[0].upper_limit,
            lower_limit=uas_zone.geometry[0].lower_limit,
            upper_vertical_reference=uas_zone.geometry[0].upper_vertical_reference,
            lower_vertical_reference=uas_zone.geometry[0].lower_vertical_reference
        ),
        regions=[uas_zone.region],
        start_date_time=uas_zone.applicability.start_date_time,
        end_date_time=uas_zone.applicability.end_date_time
    )

    return uas_zones_filter


def make_basic_auth_header(username, password) -> Dict[str, str]:
    basic_auth_str = b64encode(bytes(f'{username}:{password}', 'utf-8'))

    result = {'Authorization': f"Basic {basic_auth_str.decode('utf-8')}"}

    return result


def make_geofencing_sm_subscription() -> GeofencingSMSubscription:
    return GeofencingSMSubscription(
        id=random.randint(0, 1000),
        queue=get_unique_id(),
        topic_name=get_unique_id(),
        active=True
    )


def make_uas_zones_subscription(polygon: dict = BASILIQUE_POLYGON, user: Optional[User] = None) \
        -> UASZonesSubscription:

    uas_zone_filter = make_uas_zones_filter_from_db_uas_zone(make_uas_zone(polygon))

    subscription = UASZonesSubscription()
    subscription.id = get_unique_id()
    subscription.sm_subscription = make_geofencing_sm_subscription()
    subscription.uas_zones_filter = uas_zone_filter
    subscription.user = user or make_user()

    return subscription
