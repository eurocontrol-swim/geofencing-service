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
from unittest import mock
from unittest.mock import Mock

import pytest
from mongoengine import DoesNotExist

from geofencing_service import BASE_PATH
from geofencing_service.db.models import UASZonesSubscription
from geofencing_service.endpoints.schemas.db_schemas import UASZonesFilterSchema
from geofencing_service.events.uas_zones_subscription_handlers import \
    UASZonesSubscriptionCreateContext
from tests.conftest import DEFAULT_LOGIN_PASS
from tests.geofencing_service.utils import make_basic_auth_header, make_uas_zones_subscription

__author__ = "EUROCONTROL (SWIM)"

URL = f'{BASE_PATH}/subscriptions/'


def test_create_subscription_to_uas_zones_updates__invalid_user__returns_nok_401(test_client):

    response = test_client.post(URL, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


def test_create_subscription_to_uas_zones_updates__valid_input__returns_ok_and_creates_subscription__200(
        test_client, test_user
):
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

    context = UASZonesSubscriptionCreateContext(uas_zones_filter=UASZonesFilterSchema().load(data), user=test_user)
    context.uas_zones_subscription = make_uas_zones_subscription()

    with mock.patch('geofencing_service.events.events.create_uas_zones_subscription_event.handle',
                    return_value=context):
        response = test_client.post(URL, data=json.dumps(data), content_type='application/json',
                                    headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

        assert 201 == response.status_code
        response_data = json.loads(response.data)
        assert "OK" == response_data['genericReply']['RequestStatus']
        assert context.uas_zones_subscription.id == response_data['subscriptionID']
        assert context.uas_zones_subscription.sm_subscription.queue == response_data['publicationLocation']


def test_update_subscription_to_uas_zones_updates__invalid_user__returns_nok_401(test_client):
    uas_zones_subscription = make_uas_zones_subscription()
    uas_zones_subscription.save()

    response = test_client.put(URL + uas_zones_subscription.id,
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
def test_create_subscription_to_uas_zones_updates__invalid_horizontal_projection__returns_nok__400(
        test_client, test_user, horizontal_projection, expected_exception_description):

    data = {
        "airspaceVolume": {
            "lowerLimit": 0,
            "lowerVerticalReference": "AMSL",
            "horizontalProjection": horizontal_projection,
            "upperLimit": 0,
            "upperVerticalReference": "AMSL",
            "uomDimensions": "M"
        },
        "endDateTime": "2019-11-05T13:10:39.315Z",
        "regions": [
            0
        ],
        "startDateTime": "2019-11-05T13:10:39.315Z"
    }

    response = test_client.post(URL, data=json.dumps(data), content_type='application/json',
                                headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 400 == response.status_code

    generic_reply = json.loads(response.data)['genericReply']
    assert "NOK" == generic_reply['RequestStatus']
    assert expected_exception_description == generic_reply["RequestExceptionDescription"]


def test_update_subscription_to_uas_zones_updates__invalid_subscription_id__returns_nok_404(test_client, test_user):
    response = test_client.put(URL + 'invalid_subscription_id', data="{}", content_type='application/json',
                               headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 404 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Subscription with id invalid_subscription_id does not exist" == \
           response_data['genericReply']["RequestExceptionDescription"]


@pytest.mark.parametrize('invalid_data', [
    {"active": 1}, {"active": 1.0}, {"active": "invalid"}, {"active": ()}, {"active": []}, {"invalid_key": True}
])
def test_update_subscription_to_uas_zones_updates__invalid_data__returns_nok_400(
        test_client, test_user, invalid_data
):
    uas_zones_subscription = make_uas_zones_subscription(user=test_user)
    uas_zones_subscription.save()

    response = test_client.put(URL + uas_zones_subscription.id, data=json.dumps(invalid_data),
                               content_type='application/json',
                               headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 400 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']


@mock.patch('geofencing_service.events.uas_zones_subscription_handlers.sm_client')
def test_update_subscription_to_uas_zones_updates__is_updated__returns_ok_200(mock_sm_client, test_client, test_user):

    uas_zones_subscription = make_uas_zones_subscription(user=test_user)
    uas_zones_subscription.save()

    sm_subscription = Mock()
    sm_subscription.id = uas_zones_subscription.sm_subscription.id
    mock_sm_client.get_subscription_by_id = Mock(return_value=sm_subscription)
    mock_sm_client.put_subscription = Mock()

    data = {
        "active": not uas_zones_subscription.sm_subscription.active
    }

    response = test_client.put(URL + uas_zones_subscription.id, data=json.dumps(data), content_type='application/json',
                               headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code
    response_data = json.loads(response.data)
    assert "OK" == response_data['genericReply']['RequestStatus']

    updated_subscription = UASZonesSubscription.objects.get(id=uas_zones_subscription.id)

    assert updated_subscription.sm_subscription.active == (not uas_zones_subscription.sm_subscription.active)
    mock_sm_client.put_subscription.assert_called_once_with(sm_subscription.id, data)


def test_delete_subscription_to_uas_zones_updates__invalid_user__returns_nok_401(test_client):
    uas_zones_subscription = make_uas_zones_subscription()
    uas_zones_subscription.save()

    response = test_client.delete(URL + uas_zones_subscription.id,
                                  headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


def test_delete_subscription_to_uas_zones_updates__invalid_subscription_id__returns_nok_404(test_client, test_user):
    response = test_client.delete(URL + 'invalid_subscription_id',
                                  headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 404 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Subscription with id invalid_subscription_id does not exist" == \
           response_data['genericReply']["RequestExceptionDescription"]


@mock.patch('geofencing_service.events.uas_zones_subscription_handlers.sm_client')
def test_delete_subscription_to_uas_zones_updates__is_deleted__returns_ok_204(mock_sm_client, test_client, test_user):
    mock_sm_client.delete_subscription_by_id = Mock()

    uas_zones_subscription = make_uas_zones_subscription(user=test_user)
    uas_zones_subscription.save()

    response = test_client.delete(URL + uas_zones_subscription.id,
                                  headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 204 == response.status_code

    with pytest.raises(DoesNotExist):
        UASZonesSubscription.objects.get(id=uas_zones_subscription.id)

    mock_sm_client.delete_subscription_by_id.assert_called_once_with(uas_zones_subscription.sm_subscription.id)


def test_get_subscription_to_uas_zones_updates__invalid_user__returns_nok_401(test_client):
    uas_zones_subscription = make_uas_zones_subscription()
    uas_zones_subscription.save()

    response = test_client.get(URL + uas_zones_subscription.id,
                               headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


def test_get_subscription_to_uas_zones_updates__invalid_subscription_id__returns_nok_404(test_client, test_user):
    response = test_client.get(URL + 'invalid_subscription_id',
                               headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 404 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Subscription with id invalid_subscription_id does not exist" == \
           response_data['genericReply']["RequestExceptionDescription"]


def test_get_subscription_to_uas_zones_updates__returns_subscription_data_200(test_client, test_user):
    uas_zones_subscription = make_uas_zones_subscription(user=test_user)
    uas_zones_subscription.save()

    response = test_client.get(URL + uas_zones_subscription.id,
                               headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code
    response_data = json.loads(response.data)
    assert response_data['UASZoneSubscription']['subscriptionID'] == uas_zones_subscription.id
    assert response_data['UASZoneSubscription']['publicationLocation'] == uas_zones_subscription.sm_subscription.queue
    assert response_data['UASZoneSubscription']['active'] == uas_zones_subscription.sm_subscription.active
    assert 'UASZonesFilter' in response_data['UASZoneSubscription']


def test_get_subscriptions_to_uas_zones_updates__invalid_user__returns_nok_401(test_client):
    uas_zones_subscription = make_uas_zones_subscription()
    uas_zones_subscription.save()

    response = test_client.get(URL, headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


def test_get_subscriptions_to_uas_zones_updates__no_subscription_exists__returns_empty_list_200(test_client, test_user):
    response = test_client.get(URL, headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code
    response_data = json.loads(response.data)
    assert [] == response_data['UASZoneSubscriptions']


def test_get_subscriptions_to_uas_zones_updates__returns_subscriptions_data_200(test_client, test_user):
    uas_zones_subscription1 = make_uas_zones_subscription(user=test_user)
    uas_zones_subscription2 = make_uas_zones_subscription(user=test_user)
    uas_zones_subscription1.save()
    uas_zones_subscription2.save()

    response = test_client.get(URL, headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code
    response_data = json.loads(response.data)
    assert 2 == len(response_data['UASZoneSubscriptions'])
    assert response_data['UASZoneSubscriptions'][0]['subscriptionID'] == uas_zones_subscription1.id
    assert response_data['UASZoneSubscriptions'][0]['publicationLocation'] == uas_zones_subscription1.sm_subscription.queue
    assert response_data['UASZoneSubscriptions'][0]['active'] == uas_zones_subscription1.sm_subscription.active
    assert 'UASZonesFilter' in response_data['UASZoneSubscriptions'][0]
