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

from geofencing_service.events.uas_zones_subscription_handlers import UASZonesSubscriptionCreateContext, \
    get_or_create_sm_topic

__author__ = "EUROCONTROL (SWIM)"


@mock.patch('geofencing_service.events.uas_zones_subscription_handlers.sm_client')
def test_get_or_create_sm_topic__topic_is_found_and_returned(mock_sm_client, test_client, test_user):
    topic_name = 'topic'
    topic = Topic(name=topic_name)

    mock_sm_client.get_topics = Mock(return_value=[topic])

    context = UASZonesSubscriptionCreateContext(Mock(), user=test_user)
    context.topic_name = topic_name

    get_or_create_sm_topic(context)

    assert topic == context.sm_topic


@mock.patch('geofencing_service.events.uas_zones_subscription_handlers.sm_client')
def test_get_or_create_sm_topic__topic_is_not_found_and_is_created(mock_sm_client, test_client, test_user):
    not_existent_topic_name = 'topic'
    mock_sm_client.get_topics = Mock(return_value=[])
    mock_sm_client.post_topic = Mock()

    context = UASZonesSubscriptionCreateContext(Mock(), user=test_user)
    context.topic_name = not_existent_topic_name

    get_or_create_sm_topic(context)

    topic_to_create = mock_sm_client.post_topic.call_args[0][0]
    assert not_existent_topic_name == topic_to_create.name
