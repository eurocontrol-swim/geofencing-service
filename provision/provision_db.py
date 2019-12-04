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
import os
import uuid
import logging
import logging.config
from datetime import datetime, timezone
from typing import Dict

from mongoengine import connect
from pkg_resources import resource_filename
from swim_backend.config import load_app_config

from geofencing_server.common import GeoJSONPolygonCoordinates
from geofencing_server.db.models import UASZone, CodeZoneType, CodeRestrictionType, CodeYesNoType, CodeUSpaceClassType,\
    AirspaceVolume, AuthorityEntity, DailySchedule, CodeWeekDay, ApplicableTimePeriod, DataSource, User
from geofencing_server.db.users import create_user

__author__ = "EUROCONTROL (SWIM)"

_logger = logging.getLogger(__name__)

NOW = datetime.now(timezone.utc)

POLYGONS: Dict[str, GeoJSONPolygonCoordinates] = {
    "basilique_polygon":  [
        [[50.863648, 4.329385],
         [50.865348, 4.328055],
         [50.868470, 4.317369],
         [50.867671, 4.314826],
         [50.865873, 4.315920],
         [50.862792, 4.326508],
         [50.863648, 4.329385]]
    ],
    "parc_royal": [
        [[50.846844, 4.362334],
         [50.843125, 4.360553],
         [50.842244, 4.364823],
         [50.845977, 4.366797],
         [50.846844, 4.362334]]
    ],
    "parc_du_cinquantenaire": [
        [[50.844065, 4.387284],
         [50.842222, 4.395417],
         [50.839485, 4.397841],
         [50.838055, 4.392970],
         [50.839681, 4.384977],
         [50.844065, 4.387284]]
    ],
    "bois_de_la_cambre": [
        [[50.814009, 4.367825],
         [50.815210, 4.376479],
         [50.795249, 4.400072],
         [50.788147, 4.381311],
         [50.805531, 4.376037],
         [50.805314, 4.372529],
         [50.814009, 4.367825]]
    ]
}


def get_unique_id():
    return uuid.uuid4().hex


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


def make_uas_zone(name, polygon):
    result = UASZone()
    result.identifier = get_unique_id()[:7]
    result.name = name
    result.type = CodeZoneType.COMMON.value
    result.region = 1
    result.restriction = CodeRestrictionType.NO_RESTRICTION.value
    result.data_capture_prohibition = CodeYesNoType.YES.value
    result.u_space_class = CodeUSpaceClassType.EUROCONTROL.value
    result.message = "message"
    result.country = "BEL"
    result.airspace_volume = AirspaceVolume(polygon=polygon)
    result.authorization_requirement = make_authority()
    result.applicable_time_period = make_applicable_period()
    result.data_source = DataSource(
        creation_date_time=NOW,
    )

    return result


def make_user():
    user = User()
    user.username = os.environ['GEOFENCING_SERVER_USER']
    user.password = os.environ['GEOFENCING_SERVER_PASS']

    return user


def _save_object(obj):
    try:
        obj.save()
    except Exception as e:
        _logger.error(f"Error while saving object {obj} in DB: {str(e)}")


if __name__ == '__main__':

    config_file = resource_filename(__name__, 'config.yml')

    config = load_app_config(config_file)

    logging.config.dictConfig(config['LOGGING'])

    connect(db=config['MONGO']['db'])

    # save UASZones
    for name, polygon in POLYGONS.items():
        uas_zone = make_uas_zone(name, polygon)
        _save_object(uas_zone)
        _logger.info(f"Saved UASZone {name} in DB")

    # save Geofencing User
    geofencing_user = make_user()
    create_user(geofencing_user)
    _logger.info(f"Saved user {geofencing_user} in DB")

