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


@pytest.mark.parametrize('polygon, expected_exception_description', [
    ([{"LAT": "0", "LON": "0"}], "[{'LAT': '0', 'LON': '0'}] is too short - 'airspaceVolume.polygon'"),
    ([{"LAT": "1.0", "LON": "2.0"}, {"LAT": "3.0", "LON": "4.0"}, {"LAT": "5.0", "LON": "6.0"}],
     "{'airspaceVolume': {'polygon': ['Loop is not closed']}}"),
])
def test_create_subscription_to_uas_zones_updates__invalid_polygon_input__returns_nok__400(
        test_client, test_user, polygon, expected_exception_description):
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


def test_create_subscription_to_uas_zones_updates__valid_input__returns_ok_and_creates_subscription__200(test_client,
                                                                                                         test_user):
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

    uas_zones_subscription = make_uas_zones_subscription()

    with mock.patch('geofencing_service.events.events.create_uas_zones_subscription_event',
                    return_value=uas_zones_subscription):
        response = test_client.post(URL, data=json.dumps(data), content_type='application/json',
                                    headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

        assert 201 == response.status_code
        response_data = json.loads(response.data)
        assert "OK" == response_data['genericReply']['RequestStatus']
        assert uas_zones_subscription.id == response_data['subscriptionID']
        assert uas_zones_subscription.sm_subscription.queue == response_data['publicationLocation']


def test_update_subscription_to_uas_zones_updates__invalid_user__returns_nok_401(test_client):
    uas_zones_subscription = make_uas_zones_subscription()
    uas_zones_subscription.save()

    response = test_client.put(URL + uas_zones_subscription.id,
                               headers=make_basic_auth_header('fake_username', 'fake_password'))

    assert 401 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']
    assert "Invalid credentials" == response_data['genericReply']["RequestExceptionDescription"]


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
def test_update_subscription_to_uas_zones_updates__invalid_data__returns_nok_400(test_client, test_user, invalid_data):
    uas_zones_subscription = make_uas_zones_subscription()
    uas_zones_subscription.save()

    response = test_client.put(URL + uas_zones_subscription.id, data=json.dumps(invalid_data),
                               content_type='application/json',
                               headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 400 == response.status_code
    response_data = json.loads(response.data)
    assert "NOK" == response_data['genericReply']['RequestStatus']


@mock.patch('geofencing_service.events.uas_zones_subscription_handlers.sm_client')
def test_update_subscription_to_uas_zones_updates__is_updated__returns_ok_200(mock_sm_client, test_client, test_user):

    uas_zones_subscription = make_uas_zones_subscription()
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
    mock_sm_client.get_subscription_by_id.assert_called_once_with(uas_zones_subscription.sm_subscription.id)
    mock_sm_client.put_subscription.assert_called_once_with(sm_subscription.id, sm_subscription)


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

    uas_zones_subscription = make_uas_zones_subscription()
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
    uas_zones_subscription = make_uas_zones_subscription()
    uas_zones_subscription.save()

    response = test_client.get(URL + uas_zones_subscription.id,
                               headers=make_basic_auth_header(test_user.username, DEFAULT_LOGIN_PASS))

    assert 200 == response.status_code
    response_data = json.loads(response.data)
    assert response_data['subscriptionID'] == uas_zones_subscription.id
    assert response_data['publicationLocation'] == uas_zones_subscription.sm_subscription.queue
    assert response_data['active'] == uas_zones_subscription.sm_subscription.active
