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
import logging
from unittest.mock import Mock, call

from geofencing_service.db.uas_zones import create_uas_zone as db_create_uas_zone
from geofencing_service.events.uas_zone_handlers import _uas_zone_matches_subscription_uas_zones_filter, \
    UASZoneContext, publish_relevant_topics, get_relevant_uas_zones_subscriptions
from tests.geofencing_service.utils import make_uas_zone, BASILIQUE_POLYGON, make_uas_zones_filter_from_db_uas_zone, \
    make_uas_zones_subscription, INTERSECTING_BASILIQUE_POLYGON, NON_INTERSECTING_BASILIQUE_POLYGON

__author__ = "EUROCONTROL (SWIM)"


def test_uas_zone_matches_subscription():
    uas_zone_basilique = make_uas_zone(BASILIQUE_POLYGON)
    db_create_uas_zone(uas_zone_basilique)
    uas_zone_intersecting_basilique = make_uas_zone(INTERSECTING_BASILIQUE_POLYGON)
    uas_zone_non_intersecting_basilique = make_uas_zone(NON_INTERSECTING_BASILIQUE_POLYGON)

    intersecting_uas_zone_filter = make_uas_zones_filter_from_db_uas_zone(uas_zone_intersecting_basilique)

    intersecting_uas_zones_subscription = make_uas_zones_subscription()
    intersecting_uas_zones_subscription.uas_zones_filter = intersecting_uas_zone_filter.to_dict()
    intersecting_uas_zones_subscription.save()

    assert _uas_zone_matches_subscription_uas_zones_filter(uas_zone_basilique, intersecting_uas_zones_subscription) is True

    non_intersecting_uas_zone_filter = make_uas_zones_filter_from_db_uas_zone(uas_zone_non_intersecting_basilique)

    non_intersecting_uas_zones_subscription = make_uas_zones_subscription()
    non_intersecting_uas_zones_subscription.uas_zones_filter = non_intersecting_uas_zone_filter.to_dict()
    non_intersecting_uas_zones_subscription.save()

    assert _uas_zone_matches_subscription_uas_zones_filter(uas_zone_basilique, non_intersecting_uas_zones_subscription) is False


def test_get_relevant_uas_zones_subscriptions(test_user):
    uas_zone_basilique = make_uas_zone(BASILIQUE_POLYGON)
    db_create_uas_zone(uas_zone_basilique)

    uas_zone_intersecting_basilique = make_uas_zone(INTERSECTING_BASILIQUE_POLYGON)
    intersecting_uas_zone_filter = make_uas_zones_filter_from_db_uas_zone(uas_zone_intersecting_basilique)

    intersecting_uas_zones_subscription = make_uas_zones_subscription()
    intersecting_uas_zones_subscription.uas_zones_filter = intersecting_uas_zone_filter.to_dict()
    intersecting_uas_zones_subscription.save()

    uas_zone_non_intersecting_basilique = make_uas_zone(NON_INTERSECTING_BASILIQUE_POLYGON)
    non_intersecting_uas_zone_filter = make_uas_zones_filter_from_db_uas_zone(uas_zone_non_intersecting_basilique)

    non_intersecting_uas_zones_subscription = make_uas_zones_subscription()
    non_intersecting_uas_zones_subscription.uas_zones_filter = non_intersecting_uas_zone_filter.to_dict()
    non_intersecting_uas_zones_subscription.save()

    context = UASZoneContext(uas_zone=uas_zone_basilique, user=test_user)
    get_relevant_uas_zones_subscriptions(context=context)

    assert intersecting_uas_zones_subscription in context.uas_zones_subscriptions
    assert non_intersecting_uas_zones_subscription not in context.uas_zones_subscriptions


def test_publish_relevent_topics__all_topics_are_published(test_client, test_user):
    app = test_client.application

    mock_publish_topic = Mock()
    app.swim_publisher.publish_topic = mock_publish_topic

    context = UASZoneContext(uas_zone=make_uas_zone(BASILIQUE_POLYGON), user=test_user)
    context.topic_names = ['topic_name1', 'topic_name2', 'topic_name3']

    publish_relevant_topics(context)

    expected_mock_calls = [call(topic_name=sub.sm_subscription.topic_name) for sub in context.uas_zones_subscriptions]

    assert expected_mock_calls == mock_publish_topic.mock_calls

