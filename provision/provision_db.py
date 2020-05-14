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
import logging.config
from datetime import datetime, timezone
from typing import Optional

from mongoengine import connect
from pkg_resources import resource_filename
from swim_backend.config import load_app_config

from geofencing_service.db.models import UASZone, CodeZoneType, CodeRestrictionType, CodeYesNoType, \
    CodeUSpaceClassType, \
    AirspaceVolume, Authority, DailyPeriod, CodeWeekDay, TimePeriod, User, \
    CodeAuthorityRole, CodeZoneReasonType, UomDistance, CodeVerticalReferenceType

__author__ = "EUROCONTROL (SWIM)"

from geofencing_service.db.uas_zones import create_uas_zone

from geofencing_service.db.users import create_user

_logger = logging.getLogger(__name__)

NOW = datetime.now(timezone.utc)

POLYGONS = {
    "basilique_polygon": dict(
        type='Polygon',
        coordinates=[[
            [4.329385, 50.863648],
            [4.328055, 50.865348],
            [4.317369, 50.868470],
            [4.314826, 50.867671],
            [4.315920, 50.865873],
            [4.326508, 50.862792],
            [4.329385, 50.863648]
        ]]
    ),
    "parc_royal": dict(
        type='Polygon',
        coordinates=[[
            [4.362334, 50.846844],
            [4.360553, 50.843125],
            [4.364823, 50.842244],
            [4.366797, 50.845977],
            [4.362334, 50.846844]
        ]]
    ),
    "parc_du_cinquantenaire": dict(
        type='Polygon',
        coordinates=[[
            [4.387284, 50.844065],
            [4.395417, 50.842222],
            [4.397841, 50.839485],
            [4.392970, 50.838055],
            [4.384977, 50.839681],
            [4.387284, 50.844065]
        ]]
    ),
    "bois_de_la_cambre": dict(
        type='Polygon',
        coordinates=[[
            [4.367825, 50.814009],
            [4.376479, 50.815210],
            [4.400072, 50.795249],
            [4.381311, 50.788147],
            [4.376037, 50.805531],
            [4.372529, 50.805314],
            [4.367825, 50.814009]
        ]]
    )
}


def get_unique_id():
    return uuid.uuid4().hex


def make_authority() -> Authority:
    result = Authority()
    result.name = get_unique_id()
    result.contact_name = "Authority manager"
    result.service = "Authority service"
    result.email = "auth@autority.be"
    result.phone = "123123123"
    result.purpose = CodeAuthorityRole.AUTHORIZATION.value
    result.interval_before = "P3Y"

    return result


def make_daily_period():
    return DailyPeriod(
        day=CodeWeekDay.MON.value,
        start_time=datetime(2000, 1, 1, 12, 00, tzinfo=timezone.utc),
        end_time=datetime(2000, 1, 1, 18, 00, tzinfo=timezone.utc),
    )


def make_time_period():
    return TimePeriod(
        permanent=CodeYesNoType.YES.value,
        start_date_time=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        end_date_time=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        schedule=[make_daily_period()]
    )


def make_airspace_volume(horizontal_projection: dict,
                         uom_dimensions: str = UomDistance.METERS.value,
                         upper_limit: Optional[int] = None,
                         lower_limit: Optional[int] = None) -> AirspaceVolume:
    return AirspaceVolume(
        horizontal_projection=horizontal_projection,
        uom_dimensions=uom_dimensions,
        lower_vertical_reference=CodeVerticalReferenceType.AMSL.value,
        upper_vertical_reference=CodeVerticalReferenceType.AMSL.value,
        upper_limit=upper_limit or 100000,
        lower_limit=lower_limit or 0
    )


def make_uas_zone(name, polygon, user):
    result = UASZone()
    result.identifier = get_unique_id()[:7]
    result.country = "BEL"
    result.name = name
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
    result.applicability = make_time_period()
    result.geometry = [make_airspace_volume(horizontal_projection=polygon)]
    result.user = user

    return result


def _get_users(users):
    return [
        User(username=user_data['user'], password=user_data['pass'])
        for user_data in users
    ]


if __name__ == '__main__':

    config_file = resource_filename(__name__, 'config.yml')

    config = load_app_config(config_file)

    logging.config.dictConfig(config['LOGGING'])

    connect(**config['MONGO'])

    # save Geofencing Users
    users = _get_users(config['DB_USERS'])
    for user in users:
        create_user(user)
        _logger.info(f"Saved user {user.username} in DB")

    # save UASZones
    for name, polygon in POLYGONS.items():
        uas_zone = make_uas_zone(name, polygon, users[0])
        try:
            create_uas_zone(uas_zone)
            _logger.info(f"Saved UASZone {name} in DB")
        except Exception as e:
            _logger.error(f"Error while saving object {uas_zone} in DB: {str(e)}")
