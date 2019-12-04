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
from typing import TypeVar

from geofencing_server.db.models import UASZonesSubscription, UASZone
from geofencing_server.events import uas_zone_handlers
from geofencing_server.events import uas_zones_subscription_handlers
from geofencing_server.filters import UASZonesFilter

__author__ = "EUROCONTROL (SWIM)"

Context = TypeVar('Context')


class Event(list):
    """
    Simplistic implementation of event handling.

    A list of callables handlers. They all accept a `context` keyword parameter which is supposed to be shared
    and updated among them.
    The handlers will be called in ascending order by index.
    """
    _type = 'Generic'

    def __call__(self, context: Context):
        for handler in self:
            handler(context)

        return context

    def __repr__(self):
        return f"{self._type} Event({list.__repr__(self)})"


""" The sequence of handlers to be applied in order upon creating a new subscription"""
CREATE_UAS_ZONES_SUBSCRIPTION_HANDLERS = [
    uas_zones_subscription_handlers.get_topic_name,
    uas_zones_subscription_handlers.publish_topic,
    uas_zones_subscription_handlers.get_or_create_sm_topic,
    uas_zones_subscription_handlers.create_sm_subscription,
    uas_zones_subscription_handlers.uas_zones_subscription_db_save
]

""" The sequence of handlers to be applied in order upon creating a new UASZone"""
CREATE_UAS_ZONE_EVENT = [
    uas_zone_handlers.uas_zone_db_save,
    uas_zone_handlers.get_relevant_topic_names,
    uas_zone_handlers.publish_relevant_topics
]


""" The sequence of handlers to be applied in order upon deleting a new UASZone"""
DELETE_UAS_ZONE_EVENT = [
    uas_zone_handlers.get_relevant_topic_names,
    uas_zone_handlers.uas_zones_db_delete,
    uas_zone_handlers.publish_relevant_topics
]


def create_uas_zones_subscription_event(uas_zones_filter: UASZonesFilter) -> UASZonesSubscription:
    """
    Handles the event of creating a new subscription by creating the relevant context and applying the respective
    handlers in order

    :param uas_zones_filter:
    :return:
    """
    context = uas_zones_subscription_handlers.UASZonesSubscriptionContext(uas_zones_filter=uas_zones_filter)

    event = Event(CREATE_UAS_ZONES_SUBSCRIPTION_HANDLERS)

    event(context=context)

    return context.uas_zones_subscription


def create_uas_zone_event(uas_zone: UASZone) -> UASZone:
    """
    Handles the event of creating a new UASZone by creating the relevant context and applying the respective
    handlers in order

    :param uas_zone:
    :return:
    """
    context = uas_zone_handlers.UASZoneContext(uas_zone=uas_zone)

    event = Event(CREATE_UAS_ZONE_EVENT)

    event(context=context)

    return context.uas_zone


def delete_uas_zone_event(uas_zone: UASZone) -> None:
    """
    Handles the event of deleting a UASZone by creating the relevant context and applying the respective
    handlers in order

    :param uas_zone:
    """
    context = uas_zone_handlers.UASZoneContext(uas_zone=uas_zone)

    event = Event(DELETE_UAS_ZONE_EVENT)

    event(context=context)
