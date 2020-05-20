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

from geofencing_service import BASE_PATH
from geofencing_service.db.models import UASZone, UASZonesFilter
from geofencing_service.db.uas_zones import get_uas_zones_by_identifier
from geofencing_service.endpoints.schemas.db_schemas import UASZonesFilterSchema
from geofencing_service.events.uas_zone_handlers import UASZoneContext
from tests.conftest import DEFAULT_LOGIN_PASS
from tests.geofencing_service.utils import make_basic_auth_header, make_uas_zone, \
    BASILIQUE_POLYGON, INTERSECTING_BASILIQUE_POLYGON, NON_INTERSECTING_BASILIQUE_POLYGON, \
    make_uas_zones_filter_from_db_uas_zone

__author__ = "EUROCONTROL (SWIM)"

URL_UAS_ZONES_FILTER = f'{BASE_PATH}/uas_zones/filter/'
URL_UAS_ZONES = f'{BASE_PATH}/uas_zones/'


@pytest.fixture
def db_uas_zone_basilique(test_user):
    uas_zone = make_uas_zone(BASILIQUE_POLYGON)
    uas_zone.user = test_user
    uas_zone.save()

    return uas_zone


@pytest.fixture
def filter_with_intersecting_airspace_volume(db_uas_zone_basilique):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone_basilique)
    uas_zones_filter.airspace_volume.horizontal_projection = INTERSECTING_BASILIQUE_POLYGON

    return uas_zones_filter


@pytest.fixture
def filter_with_non_intersecting_airspace_volume(db_uas_zone_basilique):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone_basilique)
    uas_zones_filter.airspace_volume.horizontal_projection = NON_INTERSECTING_BASILIQUE_POLYGON

    return uas_zones_filter


@pytest.fixture
def uas_zone_input():
    return {
        "geometry": [{
            "uomDimensions": "M",
            "lowerLimit": 0,
            "lowerVerticalReference": "AMSL",
            "horizontalProjection": {
                "type": "Polygon",
                "coordinates": [[
                    [4.32812, 50.862525],
                    [4.329257, 50.865502],
                    [4.323686, 50.865468],
                    [4.32812, 50.862525]
                ]]
            },
            "upperLimit": 1000000,
            "upperVerticalReference": "AMSL"
        }],
        "applicability": {
            "schedule": [
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
        "zoneAuthority": {
            "contactName": "string",
            "email": "user@example.com",
            "name": "string",
            "phone": "string",
            "service": "string",
            "siteURL": "https://www.authority.com",
            "purpose": "AUTHORIZATION",
            "intervalBefore": "P3Y"
        },
        "country": "BEL",
        "regulationExemption": "YES",
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

    response = test_client.post(URL_UAS_ZONES_FILTER,
                                headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


@pytest.mark.parametrize('horizontal_projection, expected_exception_description', [
    (
        {
            'types': 'Polygon',
            'coordinates': [[[1, 2], [3, 4], [5, 6], [1, 2]]],
        },
        "{'airspaceVolume': {'horizontalProjection': [{'type': ['Missing data for required field.']}]}}"
    ),
    (
        {
            'type': 'Polygon',
            'coordinatesss': [[[1, 2], [3, 4], [5, 6], [1, 2]]],
        },
        "{'airspaceVolume': {'horizontalProjection': [{'coordinates': ['Missing data for required field.']}]}}"
    ),
    (
        {
            'type': 'Polygon',
            'coordinates': [[[1, 2], [3, 4], [5, 6]]],
        },
        "{'airspaceVolume': {'horizontalProjection': [{'coordinates': {0: ['Linestring is not closed.']}}]}}"
    ),
    (
        {
            'type': 'Polygon',
            'coordinates': [[[1, 2]]],
        },
        "{'airspaceVolume': {'horizontalProjection': [{'coordinates': {0: ['Linestring has less than 3 different vertices.']}}]}}"
    ),
    (
        {
            'type': 'Invalid',
            'coordinates': [[[1, 2], [3, 4], [5, 6]]],
        },
        "{'airspaceVolume': {'horizontalProjection': [{'type': ['Invalid geometry type. Expected one of [Circle, Polygon]']}]}}"
    ),
    (
        {
            'type': 'Polygon',
            'coordinates': 'invalid',
        },
        "{'airspaceVolume': {'horizontalProjection': [{'coordinates': ['Not a valid list.']}]}}"
    ),
    (
        {
            'type': 'Circle',
            'center': [],
        },
        "{'airspaceVolume': {'horizontalProjection': [{'radius': ['Missing data for required field.']}]}}"
    ),
    (
        {
            'type': 'Circle',
            'radius': 100,
        },
        "{'airspaceVolume': {'horizontalProjection': [{'center': ['Missing data for required field.']}]}}"
    ),
    (
        {
            'type': 'Circle',
            'radius': 100,
        },
        "{'airspaceVolume': {'horizontalProjection': [{'center': ['Missing data for required field.']}]}}"
    ),
    (
        {
            'type': 'Circle',
            'center': 'invalid',
            'radius': 100,
        },
        "{'airspaceVolume': {'horizontalProjection': [{'center': ['Not a valid list.']}]}}"
    ),
    (
        {
            'type': 'Circle',
            'center': [1, 2],
            'radius': 'invalid',
        },
        "{'airspaceVolume': {'horizontalProjection': [{'radius': ['Not a valid number.']}]}}"
    ),
    (
        {
            'type': 'Circle',
            'center': [1, 2],
            'radius': -1,
        },
        "{'airspaceVolume': {'horizontalProjection': [{'radius': ['Negative value not allowed.']}]}}"
    ),
])
def test_get_uas_zones__invalid_polygon_input__returns_nok__400(
        test_client, test_user, horizontal_projection, expected_exception_description):
    data = {
        "airspaceVolume": {
            "lowerLimit": 0,
            "lowerVerticalReference": "AMSL",
            "horizontalProjection": horizontal_projection,
            "upperLimit": 0,
            "upperVerticalReference": "AMSL"
        },
        "endDateTime": "2019-11-05T13:10:39.315Z",
        "regions": [
            0
        ],
        "startDateTime": "2019-11-05T13:10:39.315Z"
    }

    response = test_client.post(
        URL_UAS_ZONES_FILTER,
        data=json.dumps(data),
        content_type='application/json',
        headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS)
    )

    assert 400 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert expected_exception_description == \
           response_data['genericReply']["RequestExceptionDescription"]


def test_get_uas_zones__valid_input__returns_ok_and_empty_uas_zone_list__200(test_client,
                                                                             test_user):
    data = {
        "airspaceVolume": {
            "lowerLimit": 0,
            "lowerVerticalReference": "AMSL",
            "horizontalProjection": {
                "type": "Polygon",
                "coordinates": [[
                    [1.0, 2.0],
                    [3.0, 4.0],
                    [5.0, 6.0],
                    [1.0, 2.0]
                ]]
            },
            "upperLimit": 0,
            "upperVerticalReference": "AMSL"
        },
        "endDateTime": "2019-11-05T13:10:39.315Z",
        "regions": [
            0
        ],
        "startDateTime": "2019-11-05T13:10:39.315Z"
    }

    response = test_client.post(URL_UAS_ZONES_FILTER,
                                data=json.dumps(data),
                                content_type='application/json',
                                headers=make_basic_auth_header(test_user.username,
                                                               DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code
    response_data = json.loads(response.data)
    assert "OK" == response_data['genericReply']['RequestStatus']
    assert [] == response_data['UASZoneList']


def test_get_uas_zones__filter_by_airspace_volume__horizontal_projection(
    test_client,
    test_user,
    filter_with_intersecting_airspace_volume,
    filter_with_non_intersecting_airspace_volume
):
    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 1 == len(response_data['UASZoneList'])

    response_data, status_code = _post_uas_zones_filter(
        test_client, test_user, filter_with_non_intersecting_airspace_volume)

    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_airspace_volume__upper_lower_limit(
        test_client, test_user, filter_with_intersecting_airspace_volume
):
    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 1 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.airspace_volume.upper_limit -= 1
    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])

    filter_with_intersecting_airspace_volume.airspace_volume.upper_limit += 1
    filter_with_intersecting_airspace_volume.airspace_volume.lower_limit += 1
    response_data, status_code = _post_uas_zones_filter(test_client, test_user,
                                                        filter_with_intersecting_airspace_volume)
    assert 200 == status_code
    assert 0 == len(response_data['UASZoneList'])


def test_get_uas_zones__filter_by_regions(
        test_client, test_user, filter_with_intersecting_airspace_volume
):

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


def _post_uas_zones_filter(test_client, test_user, filter_data) -> Tuple[Dict[str, Any], int]:

    if isinstance(filter_data, UASZonesFilter):
        filter_data = UASZonesFilterSchema().dumps(filter_data)
    else:
        filter_data = json.dumps(filter_data)

    response = test_client.post(URL_UAS_ZONES_FILTER,
                                data=filter_data,
                                content_type='application/json',
                                headers=make_basic_auth_header(test_user.username,
                                                               DEFAULT_LOGIN_PASS))

    return json.loads(response.data), response.status_code


@pytest.mark.parametrize('filter_data, expected_uas_zones', [
    (
        {
            "airspaceVolume": {
                "uomDimensions": "M",
                "lowerLimit": 0,
                "lowerVerticalReference": "AMSL",
                "horizontalProjection": {
                    "type": "Circle",
                    "center": [4.32812, 50.862525],
                    "radius": 500,
                },
                "upperLimit": 1000000,
                "upperVerticalReference": "AMSL"
            },
            "endDateTime": "2021-11-05T13:10:39.315Z",
            "regions": [
                1
            ],
            "startDateTime": "2019-11-05T13:10:39.315Z"
        },
        [{
            'geometry': [{
                "uomDimensions": "M",
                'lowerLimit': 0,
                'lowerVerticalReference': "AMSL",
                'upperVerticalReference': "AMSL",
                'horizontalProjection': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [4.329385, 50.863648],
                        [4.328055, 50.865348],
                        [4.317369, 50.86847],
                        [4.314826, 50.867671],
                        [4.31592, 50.865873],
                        [4.326508, 50.862792],
                        [4.329385, 50.863648],
                    ]]
                },
                'upperLimit': 100000,
            }],
            'applicability': {
                'schedule': [{
                    'day': 'MON',
                    'endTime': '18:00:00+00:00',
                    'startTime': '12:00:00+00:00'
                }],
                'endDateTime': '2021-01-01T00:00:00+00:00',
                'permanent': 'YES',
                'startDateTime': '2020-01-01T00:00:00+00:00',
            },
            'zoneAuthority': {
                'contactName': 'Authority '
                'manager',
                'email': 'auth@autority.be',
                'name': '175d280099fb48eea5da490ac12f816a',
                'phone': '234234234',
                'service': 'Authority service',
                'siteURL': 'http://www.autority.be',
                'purpose': 'AUTHORIZATION',
                'intervalBefore': 'P3Y'
            },
            'country': 'BEL',
            'regulationExemption': 'YES',
            'extendedProperties': {},
            'identifier': "",
            'message': 'message',
            'name': "",
            'reason': ['AIR_TRAFFIC'],
            'otherReasonInfo': "other reason",
            'region': 1,
            'restriction': 'NO_RESTRICTION',
            'restrictionConditions': ['special conditions'],
            'type': 'COMMON',
            'uSpaceClass': 'EUROCONTROL',
        }]
    ),
    (
        {
            "airspaceVolume": {
                "uomDimensions": "M",
                "lowerLimit": 0,
                "lowerVerticalReference": "AMSL",
                "horizontalProjection": {
                    "type": "Polygon",
                    "coordinates": [[
                        [4.32812, 50.862525],
                        [4.329257, 50.865502],
                        [4.323686, 50.865468],
                        [4.32812, 50.862525]
                    ]]
                },
                "upperLimit": 1000000,
                "upperVerticalReference": "AMSL"
            },
            "endDateTime": "2021-11-05T13:10:39.315Z",
            "regions": [
                1
            ],
            "startDateTime": "2019-11-05T13:10:39.315Z"
        },
        [{
            'geometry': [{
                "uomDimensions": "M",
                'lowerLimit': 0,
                'lowerVerticalReference': "AMSL",
                'upperVerticalReference': "AMSL",
                'horizontalProjection': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [4.329385, 50.863648],
                        [4.328055, 50.865348],
                        [4.317369, 50.86847],
                        [4.314826, 50.867671],
                        [4.31592, 50.865873],
                        [4.326508, 50.862792],
                        [4.329385, 50.863648],
                    ]]
                },
                'upperLimit': 100000,
            }],
            'applicability': {
                'schedule': [{
                    'day': 'MON',
                    'endTime': '18:00:00+00:00',
                    'startTime': '12:00:00+00:00'
                }],
                'endDateTime': '2021-01-01T00:00:00+00:00',
                'permanent': 'YES',
                'startDateTime': '2020-01-01T00:00:00+00:00',
            },
            'zoneAuthority': {
                'contactName': 'Authority '
                'manager',
                'email': 'auth@autority.be',
                'name': '175d280099fb48eea5da490ac12f816a',
                'phone': '234234234',
                'service': 'Authority service',
                'siteURL': 'http://www.autority.be',
                'purpose': 'AUTHORIZATION',
                'intervalBefore': 'P3Y'
            },
            'country': 'BEL',
            'regulationExemption': 'YES',
            'extendedProperties': {},
            'identifier': "",
            'message': 'message',
            'name': "",
            'reason': ['AIR_TRAFFIC'],
            'otherReasonInfo': "other reason",
            'region': 1,
            'restriction': 'NO_RESTRICTION',
            'restrictionConditions': ['special conditions'],
            'type': 'COMMON',
            'uSpaceClass': 'EUROCONTROL',
        }]
    ),
    (
        {
            "airspaceVolume": {
                "lowerLimit": 0,
                "lowerVerticalReference": "AMSL",
                "horizontalProjection": {
                    "type": "Polygon",
                    "coordinates": [[
                        [4.325421, 50.870058],
                         [4.32689, 50.867615],
                         [4.321407, 50.867602],
                         [4.325421, 50.870058]
                    ]]
                },
                "upperLimit": 0,
                "upperVerticalReference": "AMSL"
            },
            "endDateTime": "2019-11-05T13:10:39.315Z",
            "regions": [
                0
            ],
            "startDateTime": "2019-11-05T13:10:39.315Z"
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
        expected_uas_zones[0]['zoneAuthority']['name'] = db_uas_zone_basilique.zone_authority.name
        expected_uas_zones[0]['zoneAuthority']['name'] = db_uas_zone_basilique.zone_authority.name

    response_data, status_code = _post_uas_zones_filter(test_client, test_user, filter_data)
    assert 200 == status_code
    assert len(expected_uas_zones) == len(response_data['UASZoneList'])
    assert expected_uas_zones == response_data['UASZoneList']


def test_create_uas_zone___invalid_user__returns_nok__401(test_client):

    response = test_client.post(URL_UAS_ZONES, headers=make_basic_auth_header('fake_username',
                                                                              'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


def test_create_uas_zone(test_client, test_user):
    uas_zone_input = """{
  "geometry": [{    
    "uomDimensions": "M",
    "lowerLimit": 0,
    "lowerVerticalReference": "AMSL",
    "horizontalProjection": {
        "type": "Polygon",
        "coordinates": [[
            [50.846889, 4.333428],
            [50.848857, 4.342644],
            [50.851817, 4.338588],
            [50.846889, 4.333428]
        ]]
    },
    "upperLimit": 100,
    "upperVerticalReference": "AMSL"
  }],
  "applicability": {
    "schedule": [
      {
        "day": "MON",
        "endTime": "18:00:00+00:00",
        "startTime": "09:00:00+00:00"
      }
    ],
    "endDateTime": "2020-02-14T10:16:33.532Z",
    "permanent": "YES",
    "startDateTime": "2020-01-14T10:16:33.532Z"
  },
  "zoneAuthority": {
      "contactName": "string",
      "email": "user@example.com",
      "name": "string",
      "phone": "string",
      "service": "string",
      "siteURL": "https://www.authority.com",
      "purpose": "AUTHORIZATION",
      "intervalBefore": "P3Y"
  },
  "country": "BEL",
  "regulationExemption": "YES",
  "extendedProperties": {},
  "identifier": "4rf04r0",
  "message": "string",
  "name": "string",
  "reason": [
    "AIR_TRAFFIC"
  ],
  "region": 1,
  "restriction": "PROHIBITED",
  "restrictionConditions": [
    "string"
  ],
  "type": "COMMON",
  "uSpaceClass": "EUROCONTROL"
}"""
    response = test_client.post(URL_UAS_ZONES,
                                data=uas_zone_input,
                                content_type='application/json',
                                headers=make_basic_auth_header(test_user.username,
                                                               DEFAULT_LOGIN_PASS))

    response_data = json.loads(response.data)
    assert response.status_code == 201


def test_create_uas_zone__valid_input__object_is_saved__returns_ok__201(
        test_client, test_user, uas_zone_input):

    uas_zone = make_uas_zone(BASILIQUE_POLYGON)

    # saving the expected uas_zone at this point contradicts a bit the nature of this test but here
    # we are actually testing the event outcome
    uas_zone.save()
    context = UASZoneContext(uas_zone=uas_zone, user=test_user)
    with mock.patch('geofencing_service.events.events.create_uas_zone_event.handle',
                    return_value=context) as mock_event:

        response = test_client.post(URL_UAS_ZONES,
                                    data=json.dumps(uas_zone_input),
                                    content_type='application/json',
                                    headers=make_basic_auth_header(test_user.username,
                                                                   DEFAULT_LOGIN_PASS))

        response_data = json.loads(response.data)

        assert 201 == response.status_code
        assert "OK" == response_data['genericReply']['RequestStatus']
        assert context.uas_zone in UASZone.objects.all()
        assert uas_zone_input['identifier'] == \
               mock_event.call_args[1]['context'].uas_zone.identifier


@pytest.mark.parametrize('horizontal_projection, expected_exception_description', [
    (
        {
            'types': 'Polygon',
            'coordinates': [[[1, 2], [3, 4], [5, 6], [1, 2]]],
        },
        "{'geometry': {0: {'horizontalProjection': [{'type': ['Missing data for required field.']}]}}}"
    ),
    (
        {
            'type': 'Polygon',
            'coordinatesss': [[[1, 2], [3, 4], [5, 6], [1, 2]]],
        },
        "{'geometry': {0: {'horizontalProjection': [{'coordinates': ['Missing data for required field.']}]}}}"
    ),
    (
        {
            'type': 'Polygon',
            'coordinates': [[[1, 2], [3, 4], [5, 6]]],
        },
        "{'geometry': {0: {'horizontalProjection': [{'coordinates': {0: ['Linestring is not closed.']}}]}}}"
    ),
    (
        {
            'type': 'Polygon',
            'coordinates': [[[1, 2]]],
        },
        "{'geometry': {0: {'horizontalProjection': [{'coordinates': {0: ['Linestring has less than 3 different vertices.']}}]}}}"
    ),
    (
        {
            'type': 'Invalid',
            'coordinates': [[[1, 2], [3, 4], [5, 6]]],
        },
        "{'geometry': {0: {'horizontalProjection': [{'type': ['Invalid geometry type. Expected one of [Circle, Polygon]']}]}}}"
    ),
    (
        {
            'type': 'Polygon',
            'coordinates': 'invalid',
        },
        "{'geometry': {0: {'horizontalProjection': [{'coordinates': ['Not a valid list.']}]}}}"
    ),
    (
        {
            'type': 'Circle',
            'center': [],
        },
        "{'geometry': {0: {'horizontalProjection': [{'radius': ['Missing data for required field.']}]}}}"
    ),
    (
        {
            'type': 'Circle',
            'radius': 100,
        },
        "{'geometry': {0: {'horizontalProjection': [{'center': ['Missing data for required field.']}]}}}"
    ),
    (
        {
            'type': 'Circle',
            'radius': 100,
        },
        "{'geometry': {0: {'horizontalProjection': [{'center': ['Missing data for required field.']}]}}}"
    ),
    (
        {
            'type': 'Circle',
            'center': 'invalid',
            'radius': 100,
        },
        "{'geometry': {0: {'horizontalProjection': [{'center': ['Not a valid list.']}]}}}"
    ),
    (
        {
            'type': 'Circle',
            'center': [1, 2],
            'radius': 'invalid',
        },
        "{'geometry': {0: {'horizontalProjection': [{'radius': ['Not a valid number.']}]}}}"
    ),
    (
        {
            'type': 'Circle',
            'center': [1, 2],
            'radius': -1,
        },
        "{'geometry': {0: {'horizontalProjection': [{'radius': ['Negative value not allowed.']}]}}}"
    ),
])
def test_create_uas_zone__invalid_airspace_volume__not_enough_points__returns_nok__400(
        test_client,
        test_user,
        uas_zone_input,
        horizontal_projection,
        expected_exception_description):

    uas_zone_input['geometry'][0]['horizontalProjection'] = horizontal_projection

    response = test_client.post(URL_UAS_ZONES,
                                data=json.dumps(uas_zone_input),
                                content_type='application/json',
                                headers=make_basic_auth_header(test_user.username,
                                                               DEFAULT_LOGIN_PASS))

    response_data = json.loads(response.data)

    assert 400 == response.status_code
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert expected_exception_description == \
           response_data['genericReply']['RequestExceptionDescription']


@pytest.mark.parametrize('invalid_identifier, expected_message', [
    ('short', "'short' is too short - 'identifier'"),
    ('looooooong', "'looooooong' is too long - 'identifier'")
])
def test_create_uas_zone__invalid_identifier_length__returns_nok__400(
        test_client, test_user, uas_zone_input, invalid_identifier, expected_message
):

    uas_zone_input['identifier'] = invalid_identifier

    response = test_client.post(URL_UAS_ZONES,
                                data=json.dumps(uas_zone_input),
                                content_type='application/json',
                                headers=make_basic_auth_header(test_user.username,
                                                               DEFAULT_LOGIN_PASS))

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
                                  headers=make_basic_auth_header(test_user.username,
                                                                 DEFAULT_LOGIN_PASS))

    assert 404 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "UASZone with identifier 'invalid_identifier' does not exist" == \
           response_data['genericReply']["RequestExceptionDescription"]


def test_delete_uas_zone___valid_identifier__uas_zone_is_deleted__returns_ok__204(
        test_client, test_user, db_uas_zone_basilique):

    response = test_client.delete(URL_UAS_ZONES + db_uas_zone_basilique.identifier,
                                  headers=make_basic_auth_header(test_user.username,
                                                                 DEFAULT_LOGIN_PASS))

    assert 204 == response.status_code

    assert get_uas_zones_by_identifier(db_uas_zone_basilique.identifier) is None
