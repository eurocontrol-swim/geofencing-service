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
import pytest
from mongoengine import DoesNotExist

from geofencing_service.db.models import UASZonesSubscription
from geofencing_service.db.subscriptions import get_uas_zones_subscriptions, \
    get_uas_zones_subscription_by_id, create_uas_zones_subscription, update_uas_zones_subscription,\
    delete_uas_zones_subscription
from tests.geofencing_service.utils import make_uas_zones_subscription

__author__ = "EUROCONTROL (SWIM)"


def test_get_uas_zones_subscriptions(test_user):
    subscription = make_uas_zones_subscription(user=test_user)
    subscription.save()

    db_subscriptions = get_uas_zones_subscriptions()
    assert 1 == len(db_subscriptions)
    assert subscription in db_subscriptions


def test_get_uas_zones_subscriptionby_id(test_user):
    subscription1 = make_uas_zones_subscription(user=test_user)
    subscription2 = make_uas_zones_subscription(user=test_user)
    subscription1.save()

    assert get_uas_zones_subscription_by_id(subscription2.id) is None
    assert subscription1 == get_uas_zones_subscription_by_id(subscription1.id)


def test_create_uas_zones_subscription():
    subscription = make_uas_zones_subscription()

    create_uas_zones_subscription(subscription)

    assert subscription == UASZonesSubscription.objects.get(id=subscription.id)


def test_update_uas_zones_subscription():
    subscription = make_uas_zones_subscription()
    subscription.save()

    subscription.topic_name = 'new_name'

    update_uas_zones_subscription(subscription)

    db_subscription = UASZonesSubscription.objects.get(id=subscription.id)

    assert subscription.sm_subscription.topic_name == db_subscription.sm_subscription.topic_name


def test_delete_uas_zones_subscription():
    subscription = make_uas_zones_subscription()
    subscription.save()

    delete_uas_zones_subscription(subscription)

    with pytest.raises(DoesNotExist):
        UASZonesSubscription.objects.get(id=subscription.id)
