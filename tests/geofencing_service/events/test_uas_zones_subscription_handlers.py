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
from unittest import mock
from unittest.mock import Mock

from subscription_manager_client.models import Topic

from geofencing_service.events.uas_zones_subscription_handlers import UASZonesSubscriptionCreateContext, publish_topic, \
    get_or_create_sm_topic
from tests.geofencing_service.utils import make_uas_zones_filter_from_db_uas_zone, BASILIQUE_POLYGON, make_uas_zone

__author__ = "EUROCONTROL (SWIM)"


def test_publish_topic(test_client):
    app = test_client.application

    mock_add_topic = Mock()
    mock_publish_topic = Mock()
    app.swim_publisher.add_topic = mock_add_topic
    app.swim_publisher.publish_topic = mock_publish_topic

    uas_zone = make_uas_zone(BASILIQUE_POLYGON)
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(uas_zone)
    context = UASZonesSubscriptionCreateContext(uas_zones_filter=uas_zones_filter)
    context.topic_name = 'topic_name1'

    publish_topic(context)
    mock_add_topic_arg = mock_add_topic.call_args[1]
    assert context.topic_name == mock_add_topic_arg['topic_name']

    mock_publish_topic.assert_called_once_with(topic_name=context.topic_name, context=context.uas_zones_filter)


@mock.patch('geofencing_service.events.uas_zones_subscription_handlers.sm_client')
def test_get_or_create_sm_topic__topic_is_found_and_returned(mock_sm_client, test_client):
    topic_name = 'topic'
    topic = Topic(name=topic_name)

    mock_sm_client.get_topics = Mock(return_value=[topic])

    context = UASZonesSubscriptionCreateContext(Mock())
    context.topic_name = topic_name

    get_or_create_sm_topic(context)

    assert topic == context.sm_topic


@mock.patch('geofencing_service.events.uas_zones_subscription_handlers.sm_client')
def test_get_or_create_sm_topic__topic_is_not_found_and_is_created(mock_sm_client, test_client):
    not_existent_topic_name = 'topic'
    mock_sm_client.get_topics = Mock(return_value=[])
    mock_sm_client.post_topic = Mock()

    context = UASZonesSubscriptionCreateContext(Mock())
    context.topic_name = not_existent_topic_name

    get_or_create_sm_topic(context)

    topic_to_create = mock_sm_client.post_topic.call_args[0][0]
    assert not_existent_topic_name == topic_to_create.name
