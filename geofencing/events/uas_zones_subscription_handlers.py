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
import hashlib
import json
import uuid
from typing import Optional, Any, List

from flask import current_app
from subscription_manager_client.models import Subscription as SMSubscription, Topic as SMTopic
from subscription_manager_client.subscription_manager import SubscriptionManagerClient
from swim_backend.local import AppContextProxy
from swim_pubsub.core.topics import Topic

from geofencing.db.models import UASZonesSubscription
from geofencing.db.uas_zones import get_uas_zones as db_get_uas_zones
from geofencing.db.subscriptions import create_uas_zones_subscription as db_create_uas_zones_subscription
from geofencing.endpoints.schemas.filters_schemas import UASZonesFilterSchema
from geofencing.filters import UASZonesFilter

__author__ = "EUROCONTROL (SWIM)"


def _get_sm_client_from_config() -> SubscriptionManagerClient:
    return SubscriptionManagerClient.create(
        host=current_app.config['SUBSCRIPTION-MANAGER']['host'],
        https=current_app.config['SUBSCRIPTION-MANAGER']['https'],
        timeout=current_app.config['SUBSCRIPTION-MANAGER']['timeout'],
        verify=current_app.config['SUBSCRIPTION-MANAGER']['verify'],
        username=current_app.config['GEO_SM_USER'],
        password=current_app.config['GEO_SM_PASS']
    )


sm_client = AppContextProxy(_get_sm_client_from_config)


class UASZonesSubscriptionContext:
    def __init__(self, uas_zones_filter: UASZonesFilter) -> None:
        self.uas_zones_filter: UASZonesFilter = uas_zones_filter
        self.topic_name: Optional[str] = None
        self.sm_topic: Optional[SMTopic] = None
        self.sm_subscription: Optional[SMSubscription] = None
        self.uas_zones_subscription: Optional[UASZonesSubscription] = None


def get_topic_name(context: UASZonesSubscriptionContext) -> None:
    uas_zones_filter_dict = UASZonesFilterSchema().dump(context.uas_zones_filter)
    context.topic_name = hashlib.sha1(json.dumps(uas_zones_filter_dict).encode()).hexdigest()


def data_handler(context: Optional[Any] = None):
    return db_get_uas_zones(uas_zones_filter=context)


def publish_topic(context: UASZonesSubscriptionContext) -> None:
    topic = Topic(topic_name=context.topic_name, data_handler=data_handler)

    current_app.publisher.register_topic(topic)

    current_app.publisher.publish_topic(context.topic_name, context=context.uas_zones_filter)


def get_or_create_sm_topic(context: UASZonesSubscriptionContext) -> None:
    sm_topics: List[SMTopic] = sm_client.get_topics()

    try:
        context.sm_topic = [topic for topic in sm_topics if topic.name == context.topic_name][0]
    except IndexError:
        context.sm_topic = sm_client.post_topic(SMTopic(name=context.topic_name))


def create_sm_subscription(context: UASZonesSubscriptionContext) -> None:
    sm_subscription = SMSubscription(topic_id=context.sm_topic.id)

    context.sm_subscription = sm_client.post_subscription(sm_subscription)


def uas_zones_subscription_db_save(context: UASZonesSubscriptionContext) -> None:
    subscription = UASZonesSubscription()
    subscription.id = uuid.uuid4().hex,
    subscription.topic_name = context.topic_name,
    subscription.publication_location = context.sm_subscription.queue,
    subscription.uas_zones_filter = context.uas_zones_filter.to_dict()
    subscription.active = True

    db_create_uas_zones_subscription(subscription)

    context.uas_zones_subscription = subscription
