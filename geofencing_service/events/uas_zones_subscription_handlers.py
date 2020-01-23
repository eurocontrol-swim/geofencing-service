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
import logging
import uuid
from typing import Optional, List

from flask import current_app
from subscription_manager_client.models import Subscription as SMSubscription, Topic as SMTopic
from subscription_manager_client.subscription_manager import SubscriptionManagerClient
from swim_backend.local import AppContextProxy

from geofencing_service.events.broker_message_producers import uas_zones_updates_message_producer
from geofencing_service.db.models import UASZonesSubscription, GeofencingSMSubscription, User
from geofencing_service.db.subscriptions import create_uas_zones_subscription as db_create_uas_zones_subscription,\
    update_uas_zones_subscription as db_update_uas_zones_subscription, \
    delete_uas_zones_subscription as db_delete_uas_zones_subscription
from geofencing_service.endpoints.schemas.filters_schemas import UASZonesFilterSchema
from geofencing_service.filters import UASZonesFilter

__author__ = "EUROCONTROL (SWIM)"

_logger = logging.getLogger(__name__)


def _get_sm_client_from_config() -> SubscriptionManagerClient:
    return SubscriptionManagerClient.create(
        host=current_app.config['SUBSCRIPTION-MANAGER-API']['host'],
        https=current_app.config['SUBSCRIPTION-MANAGER-API']['https'],
        timeout=current_app.config['SUBSCRIPTION-MANAGER-API']['timeout'],
        verify=current_app.config['SUBSCRIPTION-MANAGER-API']['verify'],
        username=current_app.config['SUBSCRIPTION-MANAGER-API']['username'],
        password=current_app.config['SUBSCRIPTION-MANAGER-API']['password']
    )


sm_client = AppContextProxy(_get_sm_client_from_config)


class UASZonesSubscriptionCreateContext:
    def __init__(self, uas_zones_filter: UASZonesFilter, user: User) -> None:
        """
        :param uas_zones_filter: The filtering criteria of the subscription
        :param user: The current user
        """

        self.uas_zones_filter: UASZonesFilter = uas_zones_filter
        self.user: User = user

        """Holds the new topic name where the new subscription will be subscribed to"""
        self.topic_name: Optional[str] = None

        """Holds the topic of the Subscription Manager"""
        self.sm_topic: Optional[SMTopic] = None

        """Holds the subscription of the Subscription Manager"""
        self.sm_subscription: Optional[SMSubscription] = None

        """Holds the UASZone subscription that is eventually created"""
        self.uas_zones_subscription: Optional[UASZonesSubscription] = None


class UASZonesSubscriptionUpdateContext:
    def __init__(self, uas_zones_subscription: UASZonesSubscription, user: User) -> None:
        """
        :param uas_zones_subscription:
        :param user: the current user
        """
        self.uas_zones_subscription = uas_zones_subscription
        self.user = user


def get_topic_name(context: UASZonesSubscriptionCreateContext) -> None:
    """
    Hashes the json of the subscription filter criteria in order to create a unique topic name

    :param context:
    """
    uas_zones_filter_dict = UASZonesFilterSchema().dump(context.uas_zones_filter)
    context.topic_name = hashlib.sha1(json.dumps(uas_zones_filter_dict).encode()).hexdigest()


def add_broker_topic(context: UASZonesSubscriptionCreateContext):
    current_app.swim_publisher.add_topic(topic_name=context.topic_name,
                                         message_producer=uas_zones_updates_message_producer)


def get_or_create_sm_topic(context: UASZonesSubscriptionCreateContext) -> None:
    """
    Checks if the topic_name already exists in Subscription Manager and it creates it if not

    :param context:
    """
    sm_topics: List[SMTopic] = sm_client.get_topics()

    try:
        context.sm_topic = [topic for topic in sm_topics if topic.name == context.topic_name][0]
    except IndexError:
        context.sm_topic = sm_client.post_topic(SMTopic(name=context.topic_name))


def create_sm_subscription(context: UASZonesSubscriptionCreateContext) -> None:
    """
    Creates a new subscription in Subscription Manager

    :param context:
    """
    sm_subscription = SMSubscription(topic_id=context.sm_topic.id, active=False)

    context.sm_subscription = sm_client.post_subscription(sm_subscription)


def uas_zones_subscription_db_save(context: UASZonesSubscriptionCreateContext) -> None:
    """
    Creates and saves the UASZoneSubscription

    :param context:
    """
    subscription = UASZonesSubscription()
    subscription.id = uuid.uuid4().hex
    subscription.sm_subscription = GeofencingSMSubscription(
        id=context.sm_subscription.id,
        queue=context.sm_subscription.queue,
        topic_name=context.topic_name,
        active=context.sm_subscription.active
    )
    subscription.uas_zones_filter = context.uas_zones_filter.to_dict()
    subscription.user = context.user

    db_create_uas_zones_subscription(subscription)

    context.uas_zones_subscription = subscription


def update_sm_subscription(context: UASZonesSubscriptionUpdateContext) -> None:
    sm_client.put_subscription(context.uas_zones_subscription.sm_subscription.id,
                               {'active': context.uas_zones_subscription.sm_subscription.active})


def uas_zones_subscription_db_update(context: UASZonesSubscriptionUpdateContext) -> None:
    db_update_uas_zones_subscription(context.uas_zones_subscription)


def delete_sm_subscription(context: UASZonesSubscriptionUpdateContext) -> None:
    sm_client.delete_subscription_by_id(context.uas_zones_subscription.sm_subscription.id)


def uas_zones_subscription_db_delete(context: UASZonesSubscriptionUpdateContext) -> None:
    db_delete_uas_zones_subscription(context.uas_zones_subscription)
