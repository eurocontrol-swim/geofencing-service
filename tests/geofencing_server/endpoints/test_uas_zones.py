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
from typing import Dict, Any, Tuple
from unittest import mock

import pytest

from geofencing_server import BASE_PATH
from geofencing_server.db.uas_zones import get_uas_zones_by_identifier, create_uas_zone as db_create_uas_zone
from geofencing_server.endpoints.schemas.filters_schemas import UASZonesFilterSchema
from geofencing_server.filters import UASZonesFilter
from tests.conftest import DEFAULT_LOGIN_PASS
from tests.geofencing_server.utils import make_basic_auth_header, make_uas_zone, BASILIQUE_POLYGON, \
    INTERSECTING_BASILIQUE_POLYGON, NON_INTERSECTING_BASILIQUE_POLYGON, make_uas_zones_filter_from_db_uas_zone, \
    NOW_STRING
from geofencing_server.common import point_list_from_geojson_polygon_coordinates

__author__ = "EUROCONTROL (SWIM)"

URL_UAS_ZONES_FILTER = f'{BASE_PATH}/uas_zones/filter/'
URL_UAS_ZONES = f'{BASE_PATH}/uas_zones/'


@pytest.fixture
def db_uas_zone_basilique():
    uas_zone = make_uas_zone(BASILIQUE_POLYGON)
    uas_zone.authorization_authority.save()
    uas_zone.notification_authority.save()
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


@pytest.fixture
def uas_zone_input():
    return {
        "airspaceVolume": {
            "lowerLimit": 0,
            "lowerVerticalReference": "AGL",
            "polygon": [
                {
                    "LAT": "50.862525",
                    "LON": "4.328120"
                },
                {
                    "LAT": "50.865502",
                    "LON": "4.329257"
                },
                {
                    "LAT": "50.865468",
                    "LON": "4.323686"
                },
                {
                    "LAT": "50.862525",
                    "LON": "4.328120"
                }
            ],
            "upperLimit": 0,
            "upperVerticalReference": "AGL"
        },
        "applicableTimePeriod": {
            "dailySchedule": [
                {
                    "day": "MON",
                    "endTime": "18:00:00+00:00",
                    "startTime": "09:00:00+00:00"
                }
            ],
            "endDateTime": "2019-11-29T10:30:16.548Z",
            "permanent": "YES",
            "startDateTime": "2019-11-29T10:30:16.548Z"
        },
        "authority": {
            "requiresAuthorisationFrom": {
                "authority": {
                    "contactName": "string",
                    "email": "user@example.com",
                    "name": "string",
                    "phone": "string",
                    "service": "string",
                    "siteURL": "https://www.authority.com"
                }
            },
            "requiresNotificationTo": {
                "authority": {
                    "contactName": "string",
                    "email": "user@example.com",
                    "name": "string",
                    "phone": "string",
                    "service": "string",
                    "siteURL": "https://www.authority.com"
                },
                "intervalBefore": "string"
            }
        },
        "country": "BEL",
        "dataCaptureProhibition": "YES",
        "dataSource": {
            "author": "string",
            "creationDateTime": "2019-11-29T10:30:16.549Z",
            "updateDateTime": "2019-11-29T10:30:16.549Z"
        },
        "extendedProperties": {},
        "identifier": "4rf04r1",
        "message": "string",
        "name": "string",
        "reason": [
            "AIR_TRAFFIC"
        ],
        "region": 0,
        "restriction": "PROHIBITED",
        "restrictionConditions": [
            "string"
        ],
        "type": "COMMON",
        "uSpaceClass": "EUROCONTROL"
    }


def test_get_uas_zones__invalid_user__returns_nok__401(test_client):

    response = test_client.post(URL_UAS_ZONES_FILTER, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


@pytest.mark.parametrize('polygon, expected_exception_description', [
    ([{"LAT": "0", "LON": "0"}], "[{'LAT': '0', 'LON': '0'}] is too short"),
    ([{"LAT": "1.0", "LON": "2.0"}, {"LAT": "3.0", "LON": "4.0"}, {"LAT": "5.0", "LON": "6.0"}],
     "{'airspaceVolume': {'polygon': ['Loop is not closed']}}"),
])
def test_get_uas_zones__invalid_polygon_input__returns_nok__400(test_client, test_user, polygon,
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

    response = test_client.post(URL_UAS_ZONES_FILTER, data=json.dumps(data), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 400 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert expected_exception_description == response_data['genericReply']["RequestExceptionDescription"]


def test_get_uas_zones__valid_input__returns_ok_and_empty_uas_zone_list__200(test_client, test_user):
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

    response = test_client.post(URL_UAS_ZONES_FILTER, data=json.dumps(data), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code
    response_data = json.loads(response.data)
    assert "OK" == response_data['genericReply']['RequestStatus']
    assert [] == response_data['UASZoneList']


def test_get_uas_zones__filter_by_airspace_volume__polygon(test_client, test_user,
                                                           filter_with_intersecting_airspace_volume,
                                                           filter_with_non_intersecting_airspace_volume):
    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 1 == len(response_data['UASZoneList'])

    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_non_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_airspace_volume__upper_lower_limit(test_client, test_user,
                                                                     filter_with_intersecting_airspace_volume):
    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.airspace_volume.upper_limit_in_m -= 1
    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.airspace_volume.upper_limit_in_m += 1
    filter_with_intersecting_airspace_volume.airspace_volume.lower_limit_in_m += 1
    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_regions(test_client, test_user, filter_with_intersecting_airspace_volume):

    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.regions = [100000]

    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_applicable_time_period(test_client, test_user,
                                                         filter_with_intersecting_airspace_volume):

    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.start_date_time += timedelta(days=1)

    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.start_date_time -= timedelta(days=1)
    filter_with_intersecting_airspace_volume.end_date_time -= timedelta(days=1)

    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_updated_date_time(test_client, test_user, filter_with_intersecting_airspace_volume):
    filter_with_intersecting_airspace_volume.updated_after_date_time -= timedelta(days=1)

    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.updated_after_date_time += timedelta(days=2)

    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])


def _post_uas_zones_filter(test_client, test_user, filter_data) -> Tuple[Dict[str, Any], int]:

    if isinstance(filter_data, UASZonesFilter):
        filter_data = UASZonesFilterSchema().dumps(filter_data)
    else:
        filter_data = json.dumps(filter_data)

    response = test_client.post(URL_UAS_ZONES_FILTER, data=filter_data, content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    return json.loads(response.data), response.status_code


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
                'upperVerticalReference': "WGS84",
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
            'authority': {'requiresAuthorisationFrom': {'authority': {'contactName': 'AuthorityEntity '
                                                                           'manager',
                                                            'email': 'auth@autority.be',
                                                            'name': '175d280099fb48eea5da490ac12f816a',
                                                            'phone': '234234234',
                                                            'service': 'AuthorityEntity '
                                                                       'service',
                                                            'siteURL': 'http://www.autority.be'}},
                'requiresNotificationTo': {'authority': {'contactName': 'AuthorityEntity '
                                                                        'manager',
                                                         'email': 'auth@autority.be',
                                                         'name': 'eb3a0c42283440ab8ae1386d092d6853',
                                                         'phone': '234234234',
                                                         'service': 'AuthorityEntity '
                                                                    'service',
                                                         'siteURL': 'http://www.autority.be'},
                                           'intervalBefore': 'interval'}},
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
            'restrictionConditions': [],
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

    # make them compatible due to random values' generation
    if expected_uas_zones:
        expected_uas_zones[0]['identifier'] = db_uas_zone_basilique.identifier
        expected_uas_zones[0]['name'] = db_uas_zone_basilique.name
        expected_uas_zones[0]['authority']['requiresAuthorisationFrom']['authority']['name'] = \
            db_uas_zone_basilique.authorization_authority.name
        expected_uas_zones[0]['authority']['requiresNotificationTo']['authority']['name'] = \
            db_uas_zone_basilique.notification_authority.name

    response_data, status_code = _post_uas_zones_filter(test_client, test_user, filter_data)
    assert 200 == status_code
    assert len(expected_uas_zones) == len(response_data['UASZoneList'])
    assert expected_uas_zones == response_data['UASZoneList']


def test_create_uas_zone___invalid_user__returns_nok__401(test_client):

    response = test_client.post(URL_UAS_ZONES, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


@pytest.mark.parametrize('expected_uas_zone_output', [
     {'airspaceVolume': {'lowerLimit': 0,
                         'lowerVerticalReference': 'AGL',
                         'polygon': [{'LAT': '50.862525', 'LON': '4.32812'},
                                     {'LAT': '50.865502', 'LON': '4.329257'},
                                     {'LAT': '50.865468', 'LON': '4.323686'},
                                     {'LAT': '50.862525', 'LON': '4.32812'}],
                         'upperLimit': 0,
                         'upperVerticalReference': 'AGL'},
      'applicableTimePeriod': {'dailySchedule': [{'day': 'MON',
                                                  'endTime': '18:00:00+00:00',
                                                  'startTime': '09:00:00+00:00'}],
                               'endDateTime': '2019-11-29T10:30:16.548000+00:00',
                               'permanent': 'YES',
                               'startDateTime': '2019-11-29T10:30:16.548000+00:00'},
      'authority': {'requiresAuthorisationFrom': {'authority': {'contactName': 'string',
                                                                'email': 'user@example.com',
                                                                'name': 'string',
                                                                'phone': 'string',
                                                                'service': 'string',
                                                                'siteURL': 'https://www.authority.com'}},
                    'requiresNotificationTo': {'authority': {'contactName': 'string',
                                                             'email': 'user@example.com',
                                                             'name': 'string',
                                                             'phone': 'string',
                                                             'service': 'string',
                                                             'siteURL': 'https://www.authority.com'},
                                               'intervalBefore': 'string'}},
      'country': 'BEL',
      'dataCaptureProhibition': 'YES',
      'dataSource': {'author': 'string',
                     'creationDateTime': '2019-11-29T10:30:16.549000+00:00',
                     'updateDateTime': '2019-11-29T10:30:16.549000+00:00'},
      'extendedProperties': {},
      'identifier': '4rf04r1',
      'message': 'string',
      'name': 'string',
      'reason': ['AIR_TRAFFIC'],
      'region': 0,
      'restriction': 'PROHIBITED',
      'restrictionConditions': ['string'],
      'type': 'COMMON',
      'uSpaceClass': 'EUROCONTROL'}
])
def test_create_uas_zone__valid_input__object_is_saved__returns_ok__201(test_client, test_user, uas_zone_input,
                                                                        expected_uas_zone_output):

    uas_zone = make_uas_zone(BASILIQUE_POLYGON)

    # saving the expected uas_zone at this point contradicts a bit the nature of this test but here we are actually
    # testing the event outcome
    db_create_uas_zone(uas_zone)

    with mock.patch('geofencing_server.events.events.create_uas_zone_event', return_value=uas_zone):
        response = test_client.post(URL_UAS_ZONES, data=json.dumps(uas_zone_input), content_type='application/json',
                                    headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

        response_data = json.loads(response.data)

        assert 201 == response.status_code
        assert "OK" == response_data['genericReply']['RequestStatus']
        assert expected_uas_zone_output == response_data['UASZone']


def test_create_uas_zone__invalid_airspace_volume__not_enough_points__returns_nok__400(test_client, test_user,
                                                                                       uas_zone_input):

    uas_zone_input['airspaceVolume']['polygon'] = [{'LAT': '50.862525', 'LON': '4.32812'}]

    response = test_client.post(URL_UAS_ZONES, data=json.dumps(uas_zone_input), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    response_data = json.loads(response.data)

    assert 400 == response.status_code
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "[{'LAT': '50.862525', 'LON': '4.32812'}] is too short" == \
           response_data['genericReply']['RequestExceptionDescription']


def test_create_uas_zone__invalid_airspace_volume__not_closing_loop__returns_nok__400(test_client, test_user,
                                                                                      uas_zone_input):

    uas_zone_input['airspaceVolume']['polygon'] = uas_zone_input['airspaceVolume']['polygon'][:-1]

    response = test_client.post(URL_UAS_ZONES, data=json.dumps(uas_zone_input), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    response_data = json.loads(response.data)

    assert 400 == response.status_code
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "{'airspaceVolume': {'polygon': ['Loop is not closed']}}" == \
           response_data['genericReply']['RequestExceptionDescription']


@pytest.mark.parametrize('invalid_identifier, expected_message', [
    ('short', "'short' is too short"), ('looooooong', "'looooooong' is too long")
])
def test_create_uas_zone__invalid_identifier_length__returns_nok__400(test_client, test_user, uas_zone_input,
                                                                      invalid_identifier, expected_message):

    uas_zone_input['identifier'] = invalid_identifier

    response = test_client.post(URL_UAS_ZONES, data=json.dumps(uas_zone_input), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    response_data = json.loads(response.data)

    assert 400 == response.status_code
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert expected_message == response_data['genericReply']['RequestExceptionDescription']


def test_delete_uas_zone___invalid_user__returns_nok__401(test_client):

    response = test_client.delete(URL_UAS_ZONES + 'identifier',
                                  headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


def test_delete_uas_zone___invalid_identifier__returns_nok__404(test_client, test_user):

    response = test_client.delete(URL_UAS_ZONES + 'invalid_identifier',
                                  headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 404 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "UASZone with identifier 'invalid_identifier' does not exist" == \
           response_data['genericReply']["RequestExceptionDescription"]


def test_delete_uas_zone___valid_identifier__uas_zone_is_deleted__returns_ok__204(test_client, test_user,
                                                                                  db_uas_zone_basilique):

    response = test_client.delete(URL_UAS_ZONES + db_uas_zone_basilique.identifier,
                                  headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 204 == response.status_code

    assert get_uas_zones_by_identifier(db_uas_zone_basilique.identifier) is None
