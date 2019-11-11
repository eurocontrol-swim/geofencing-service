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
from geofencing.endpoints.schemas.filters import UASZonesFilterSchema
from geofencing.filters import UASZonesFilter
from tests.conftest import DEFAULT_LOGIN_PASS
from tests.geofencing.utils import make_basic_auth_header, make_uas_zone, BASILIQUE_POLYGON, \
    INTERSECTING_BASILIQUE_POLYGON, NON_INTERSECTING_BASILIQUE_POLYGON, make_uas_zones_filter_from_db_uas_zone, \
    NOW_STRING
from geofencing.common import point_list_from_geojson_polygon_coordinates

__author__ = "EUROCONTROL (SWIM)"

URL = f'{BASE_PATH}/uas_zones/'


@pytest.fixture
def db_uas_zone_basilique():
    uas_zone = make_uas_zone(BASILIQUE_POLYGON)
    uas_zone.save()

    return uas_zone


@pytest.fixture
def filter_with_intersecting_airspace_volume(db_uas_zone_basilique):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone_basilique)
    uas_zones_filter.airspace_volume.polygon = point_list_from_geojson_polygon_coordinates(INTERSECTING_BASILIQUE_POLYGON)

    return uas_zones_filter


@pytest.fixture
def filter_with_non_intersecting_airspace_volume(db_uas_zone_basilique):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone_basilique)
    uas_zones_filter.airspace_volume.polygon = point_list_from_geojson_polygon_coordinates(NON_INTERSECTING_BASILIQUE_POLYGON)

    return uas_zones_filter


def test_get_uas_zones__invalid_user__returns_nok(test_client):

    response = test_client.post(URL, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


@pytest.mark.parametrize('polygon, expected_exception_description', [
    ([{"LAT": "0", "LON": "0"}], "[{'LAT': '0', 'LON': '0'}] is too short"),
    ([{"LAT": "1.0", "LON": "2.0"}, {"LAT": "3.0", "LON": "4.0"}, {"LAT": "5.0", "LON": "6.0"}],
     "{'airspaceVolume': {'polygon': ['Loop is not closed']}}"),
])
def test_get_uas_zones__invalid_polygon_input__returns_nok(test_client, test_user, polygon,
                                                           expected_exception_description):
    data = {
        "airspaceVolume": {
            "lowerLimit": 0,
            "lowerVerticalReference": "WGS84",
            "polygon": polygon,
            "upperLimit": 0,
            "upperVerticalReference": "WGS84"
        },
        "endDateTime": "2019-11-05T13:10:39.315Z",
        "regions": [
            0
        ],
        "requestID": "string",
        "startDateTime": "2019-11-05T13:10:39.315Z",
        "updatedAfterDateTime": "2019-11-05T13:10:39.315Z"
    }

    response = test_client.post(URL, data=json.dumps(data), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 400 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert expected_exception_description == response_data['genericReply']["RequestExceptionDescription"]


def test_get_uas_zones__valid_input__returns_ok_and_empty_uas_zone_list(test_client, test_user):
    data = {
        "airspaceVolume": {
            "lowerLimit": 0,
            "lowerVerticalReference": "WGS84",
            "polygon": [
                {
                    "LAT": "1.0",
                    "LON": "2.0"
                },
                {
                    "LAT": "3.0",
                    "LON": "4.0"
                },
                {
                    "LAT": "5.0",
                    "LON": "6.0"
                },
                {
                    "LAT": "1.0",
                    "LON": "2.0"
                }
            ],
            "upperLimit": 0,
            "upperVerticalReference": "WGS84"
        },
        "endDateTime": "2019-11-05T13:10:39.315Z",
        "regions": [
            0
        ],
        "requestID": "string",
        "startDateTime": "2019-11-05T13:10:39.315Z",
        "updatedAfterDateTime": "2019-11-05T13:10:39.315Z"
    }

    response = test_client.post(URL, data=json.dumps(data), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code
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

    if isinstance(filter_data, UASZonesFilter):
        filter_data = UASZonesFilterSchema().dumps(filter_data)
    else:
        filter_data = json.dumps(filter_data)

    response = test_client.post(URL, data=filter_data, content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))
    return json.loads(response.data)


@pytest.mark.parametrize('filter_data, expected_uas_zones', [
    (
        {
            'requestID': '1',
            'airspaceVolume': {
                'polygon': [{'LON': '4.32812', 'LAT': '50.862525'},
                            {'LON': '4.329257', 'LAT': '50.865502'},
                            {'LON': '4.323686', 'LAT': '50.865468'},
                            {'LON': '4.32812', 'LAT': '50.862525'}],
                'lowerVerticalReference': 'WGS84',
                'lowerLimit': 0,
                'upperLimit': 100000,
            },
            'regions': [1],
            'endDateTime': '2021-01-01T00:00:00+00:00',
            'updatedAfterDateTime': NOW_STRING,
            'startDateTime': '2020-01-01T00:00:00+00:00',
        },
        [{
            'airspaceVolume': {
                'lowerLimit': 0,
                'lowerVerticalReference': "WGS84",
                'polygon': [
                    {'LAT': '50.863648', 'LON': '4.329385'},
                    {'LAT': '50.865348', 'LON': '4.328055'},
                    {'LAT': '50.86847', 'LON': '4.317369'},
                    {'LAT': '50.867671', 'LON': '4.314826'},
                    {'LAT': '50.865873', 'LON': '4.31592'},
                    {'LAT': '50.862792', 'LON': '4.326508'},
                    {'LAT': '50.863648', 'LON': '4.329385'},
                ],
                'upperLimit': 100000,
            },
            'applicableTimePeriod': {
                'dailySchedule': [{
                    'day': 'MON',
                     'endTime': '18:00:00+00:00',
                     'startTime': '12:00:00+00:00'
                }],
                'endDateTime': '2021-01-01T00:00:00+00:00',
                'permanent': 'YES',
                'startDateTime': '2020-01-01T00:00:00+00:00',
            },
            'authority': None,
            'country': 'BEL',
            'dataCaptureProhibition': 'YES',
            'dataSource': {
                'author': 'Author',
                'creationDateTime': NOW_STRING,
                'updateDateTime': NOW_STRING
            },
            'extendedProperties': {},
            'identifier': "",
            'message': 'message',
            'name': "",
            'reason': [],
            'region': 1,
            'restriction': 'NO_RESTRICTION',
            'type': 'COMMON',
            'uSpaceClass': 'EUROCONTROL',
        }]
    ),
    (
        {
            'requestID': '1',
            'airspaceVolume': {
                'polygon': [{'LON': '4.325421', 'LAT': '50.870058'},
                            {'LON': '4.32689', 'LAT': '50.867615'},
                            {'LON': '4.321407', 'LAT': '50.867602'},
                            {'LON': '4.325421', 'LAT': '50.870058'}],
                'lowerVerticalReference': 'WGS84',
                'lowerLimit': 0,
                'upperLimit': 100000,
            },
            'regions': [1],
            'endDateTime': '2021-01-01T00:00:00+00:00',
            'updatedAfterDateTime': NOW_STRING,
            'startDateTime': '2020-01-01T00:00:00+00:00',
        },
        []
    )
])
def test_get_uas_zones__filter_by_airspace_volume__polygon__response_is_serialized(
        test_client, test_user, db_uas_zone_basilique, filter_data, expected_uas_zones):

    # make them compatible
    if expected_uas_zones:
        expected_uas_zones[0]['identifier'] = db_uas_zone_basilique.identifier
        expected_uas_zones[0]['name'] = db_uas_zone_basilique.name

    response_data = _post_uas_zones_filter(test_client, test_user, filter_data)
    assert len(expected_uas_zones) == len(response_data['UASZoneList'])
    assert expected_uas_zones == response_data['UASZoneList']
