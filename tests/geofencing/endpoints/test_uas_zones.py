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
from datetime import timedelta

import pytest

from geofencing import BASE_PATH
from geofencing.common import polygon_filter_from_mongo_polygon
from geofencing.endpoints.schemas.request import UASZonesRequestSchema
from tests.conftest import DEFAULT_LOGIN_PASS
from tests.geofencing.utils import make_basic_auth_header, make_uas_zone, make_airspace_volume, BASILIQUE_POLYGON, \
    INTERSECTING_BASILIQUE_POLYGON, NON_INTERSECTING_BASILIQUE_POLYGON, make_uas_zones_filter_from_db_uas_zone

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def db_uas_zone():
    uas_zone = make_uas_zone(BASILIQUE_POLYGON)
    uas_zone.save()

    return uas_zone


@pytest.fixture
def filter_with_intersecting_airspace_volume(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = polygon_filter_from_mongo_polygon(INTERSECTING_BASILIQUE_POLYGON)

    return uas_zones_filter


@pytest.fixture
def filter_with_non_intersecting_airspace_volume(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = polygon_filter_from_mongo_polygon(NON_INTERSECTING_BASILIQUE_POLYGON)

    return uas_zones_filter


def test_get_uas_zones__invalid_user__returns_nok(test_client):
    url = f'{BASE_PATH}/uas_zones/filter/'

    response = test_client.post(url, headers=make_basic_auth_header('fake_username', 'fake_password'))

    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


@pytest.mark.parametrize('polygon, expected_exception_description', [
    ([{"LAT": 0, "LON": 0}], "[{'LAT': 0, 'LON': 0}] is too short"),
    ([{"LAT": 1.0, "LON": 2.0}, {"LAT": 3.0, "LON": 4.0}, {"LAT": 5.0, "LON": 6.0}],
     "The server has encountered an error during the requestLoop is not closed: [ [ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ] ]"),
])
def test_get_uas_zones__invalid_polygon_input__returns_nok(test_client, test_user, polygon,
                                                           expected_exception_description):
    url = f'{BASE_PATH}/uas_zones/filter/'
    data = {
        "airspaceVolume": {
            "lowerLimit": 0,
            "lowerVerticalReference": "string",
            "polygon": polygon,
            "upperLimit": 0,
            "upperVerticalReference": "string"
        },
        "endDateTime": "2019-11-05T13:10:39.315Z",
        "regions": [
            0
        ],
        "requestID": "string",
        "startDateTime": "2019-11-05T13:10:39.315Z",
        "updatedAfterDateTime": "2019-11-05T13:10:39.315Z"
    }

    response = test_client.post(url, data=json.dumps(data), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert expected_exception_description == response_data['genericReply']["RequestExceptionDescription"]


def test_get_uas_zones__valid_input__returns_ok_and_empty_uas_zone_list(test_client, test_user):
    url = f'{BASE_PATH}/uas_zones/filter/'
    data = {
        "airspaceVolume": {
            "lowerLimit": 0,
            "lowerVerticalReference": "string",
            "polygon": [
                {
                    "LAT": 1.0,
                    "LON": 2.0
                },
                {
                    "LAT": 3.0,
                    "LON": 4.0
                },
                {
                    "LAT": 5.0,
                    "LON": 6.0
                },
                {
                    "LAT": 1.0,
                    "LON": 2.0
                }
            ],
            "upperLimit": 0,
            "upperVerticalReference": "string"
        },
        "endDateTime": "2019-11-05T13:10:39.315Z",
        "regions": [
            0
        ],
        "requestID": "string",
        "startDateTime": "2019-11-05T13:10:39.315Z",
        "updatedAfterDateTime": "2019-11-05T13:10:39.315Z"
    }

    response = test_client.post(url, data=json.dumps(data), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    response_data = json.loads(response.data)
    assert "OK" == response_data['genericReply']['RequestStatus']
    assert [] == response_data['UASZoneList']


def test_get_uas_zones__filter_by_airspace_volume__polygon(test_client, test_user,
                                                           filter_with_intersecting_airspace_volume,
                                                           filter_with_non_intersecting_airspace_volume):
    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 1 == len(response_data['UASZoneList'])

    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_non_intersecting_airspace_volume)
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_airspace_volume__upper_lower_limit(test_client, test_user,
                                                                     filter_with_intersecting_airspace_volume):
    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.airspace_volume.upper_limit_in_m -= 1
    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 0 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.airspace_volume.upper_limit_in_m += 1
    filter_with_intersecting_airspace_volume.airspace_volume.lower_limit_in_m += 1
    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_regions(test_client, test_user, filter_with_intersecting_airspace_volume):

    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.regions = [100000]

    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_applicable_time_period(test_client, test_user,
                                                         filter_with_intersecting_airspace_volume):

    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.start_date_time += timedelta(days=1)

    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 0 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.start_date_time -= timedelta(days=1)
    filter_with_intersecting_airspace_volume.end_date_time -= timedelta(days=1)

    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_updated_date_time(test_client, test_user, filter_with_intersecting_airspace_volume):
    filter_with_intersecting_airspace_volume.updated_after_date_time -= timedelta(days=1)

    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.updated_after_date_time += timedelta(days=2)

    response_data = _post_uas_zones_filter(test_client, test_user, filter_with_intersecting_airspace_volume)
    assert 0 == len(response_data['UASZoneList'])


def _post_uas_zones_filter(test_client, test_user, filter_data):
    url = f'{BASE_PATH}/uas_zones/filter/'

    data = UASZonesRequestSchema().dumps(filter_data)
    response = test_client.post(url, data=data, content_type='application/json',
                                headers=make_basic_auth_header(test_user.username,
                                                               DEFAULT_LOGIN_PASS))
    return json.loads(response.data)
