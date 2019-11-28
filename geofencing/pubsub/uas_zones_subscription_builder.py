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
from abc import ABC, abstractmethod
from functools import partial
from typing import Optional, List, Type

from flask import current_app
from subscription_manager_client.models import Subscription as SMSubscription, Topic as SMTopic
from swim_pubsub.core.topics import Topic

from geofencing.db.models import UASZonesSubscription
from geofencing.db.uas_zones import get_uas_zones as db_get_uas_zones
from geofencing.db.subscriptions import create_uas_zones_subscription as db_create_uas_zones_subscription
from geofencing.endpoints.schemas.filters import UASZonesFilterSchema
from geofencing.filters import UASZonesFilter
from geofencing.pubsub import sm_client

__author__ = "EUROCONTROL (SWIM)"


class UASZonesSubscriptionContext:
    def __init__(self, uas_zones_filter: UASZonesFilter):
        self.uas_zones_filter: UASZonesFilter = uas_zones_filter
        self.topic_name: Optional[str] = None
        self.sm_topic: Optional[SMTopic] = None
        self.sm_subscription: Optional[SMSubscription] = None
        self.uas_zones_subscription: Optional[UASZonesSubscription] = None


class Builder(ABC):

    @classmethod
    @abstractmethod
    def build(cls, context: UASZonesSubscriptionContext):
        pass


class TopicNameBuilder(Builder):

    @classmethod
    def build(cls, context: UASZonesSubscriptionContext):
        uas_zones_filter_dict = UASZonesFilterSchema().dump(context.uas_zones_filter)
        context.topic_name = hashlib.sha1(json.dumps(uas_zones_filter_dict).encode()).hexdigest()


class TopicPublisherBuilder(Builder):

    @classmethod
    def build(cls, context: UASZonesSubscriptionContext):
        topic = Topic(topic_name=context.topic_name,
                      data_handler=partial(db_get_uas_zones, uas_zones_filter=context.uas_zones_filter))

        current_app.publisher.register_topic(topic)

        current_app.publisher.publish_topic(context.topic_name)


class SMSubscriptionBuilder(Builder):

    @classmethod
    def build(cls, context: UASZonesSubscriptionContext):
        sm_subscription = SMSubscription(topic_id=context.sm_topic.id)

        context.sm_subscription = sm_client.post_subscription(sm_subscription)


class UASZonesSubscriptionBuilder(Builder):

    @classmethod
    def build(cls, context: UASZonesSubscriptionContext):
        subscription = UASZonesSubscription()
        subscription.id = uuid.uuid4().hex,
        subscription.topic_name = context.topic_name,
        subscription.publication_location = context.sm_subscription.queue,
        subscription.uas_zones_filter = context.uas_zones_filter
        subscription.active = True

        db_create_uas_zones_subscription(subscription)

        context.uas_zones_subscription = subscription


_UAS_ZONES_SUBSCRIPTIONS_BUILDERS: List[Type[Builder]] = [
    TopicNameBuilder,
    TopicPublisherBuilder,
    SMSubscriptionBuilder,
    UASZonesSubscriptionBuilder
]


def _build_uas_zones_subscribtion(context: UASZonesSubscriptionContext, builders: List[Type[Builder]]):
    for builder in builders:
        builder.build(context)


def build_uas_zones_subscribtion(context: UASZonesSubscriptionContext) -> None:
    return _build_uas_zones_subscribtion(context=context, builders=_UAS_ZONES_SUBSCRIPTIONS_BUILDERS)
