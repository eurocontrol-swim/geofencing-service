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

import geofencing_service.events.broker_message_producers
from geofencing_service.events import uas_zone_handlers
from geofencing_service.events import uas_zones_subscription_handlers
from geofencing_service.events.uas_zones_subscription_handlers import update_sm_subscription, \
    uas_zones_subscription_db_update, delete_sm_subscription, uas_zones_subscription_db_delete

__author__ = "EUROCONTROL (SWIM)"

Context = TypeVar('Context')


class Event(list):
    """
    Simplistic implementation of event handling.

    A list of callables handlers. They all accept a `context` keyword parameter which is supposed to
    be shared and updated among them.
    The handlers will be called in ascending order by index.
    """
    _type = 'Generic'

    def handle(self, context: Context):
        for handler in self:
            handler(context)

        return context

    def __repr__(self):
        return f"{self._type} Event({list.__repr__(self)})"


create_uas_zones_subscription_event = Event([
    uas_zones_subscription_handlers.get_topic_name,
    uas_zones_subscription_handlers.add_broker_topic,
    uas_zones_subscription_handlers.get_or_create_sm_topic,
    uas_zones_subscription_handlers.create_sm_subscription,
    uas_zones_subscription_handlers.uas_zones_subscription_db_save
])


update_uas_zones_subscription_event = Event([
    update_sm_subscription,
    uas_zones_subscription_db_update,
])


delete_uas_zones_subscription_event = Event([
    delete_sm_subscription,
    uas_zones_subscription_db_delete
])


create_uas_zone_event = Event([
    uas_zone_handlers.uas_zone_db_save,
    uas_zone_handlers.get_relevant_uas_zones_subscriptions,
    geofencing_service.events.broker_message_producers.publish_uas_zone_creation
])


delete_uas_zone_event = Event([
    uas_zone_handlers.get_relevant_uas_zones_subscriptions,
    uas_zone_handlers.uas_zones_db_delete,
    geofencing_service.events.broker_message_producers.publish_uas_zone_deletion
])
