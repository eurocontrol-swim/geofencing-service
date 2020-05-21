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
import json
import logging.config
from typing import Dict, Any

from marshmallow import ValidationError
from mongoengine import connect, NotUniqueError
from pkg_resources import resource_filename
from swim_backend.config import load_app_config

from geofencing_service.db.models import User

__author__ = "EUROCONTROL (SWIM)"

from geofencing_service.db.uas_zones import create_uas_zone

from geofencing_service.db.users import create_user
from geofencing_service.endpoints.schemas.db_schemas import UASZoneSchema

_logger = logging.getLogger(__name__)


def _get_users(users):
    return [
        User(username=user_data['user'], password=user_data['pass'])
        for user_data in users
    ]


def configure(config_file: str) -> Dict[str, Any]:
    config = load_app_config(config_file)
    logging.config.dictConfig(config['LOGGING'])
    connect(**config['MONGO'])

    return config


def get_uas_zones(uas_zones_file: str) -> Dict[str, Any]:
    with open(uas_zones_file, 'r') as f:
        return json.loads(f.read())['uas_zones']


if __name__ == '__main__':

    config_file = resource_filename(__name__, 'config.yml')
    uas_zones_file = resource_filename(__name__, 'uas_zones.json')

    config = configure(config_file)
    uas_zones = get_uas_zones(uas_zones_file)

    # save Geofencing Users
    users = _get_users(config['DB_USERS'])
    for user in users:
        try:
            create_user(user)
            _logger.info(f"Saved user {user.username} in DB")
        except NotUniqueError:
            _logger.error(f"User {user.username} already exists.")

    for uas_zone_data in uas_zones:
        try:
            uas_zone = UASZoneSchema().load(uas_zone_data)
        except ValidationError as e:
            _logger.error(f"Invalid UASZone: {str(e)}")
            continue

        try:
            uas_zone.user = users[0]
            create_uas_zone(uas_zone)
            _logger.info(f"Saved UASZone {uas_zone.name} in DB")
        except Exception as e:
            _logger.error(f"Error while saving UASZone {uas_zone.name} in DB: {str(e)}")
            continue
