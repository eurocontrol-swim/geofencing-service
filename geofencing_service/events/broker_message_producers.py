"""
Copyright 2020 EUROCONTROL
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

__author__ = "EUROCONTROL (SWIM)"

import enum
import logging

import proton
from flask import current_app
from swim_proton.messaging_handlers import MessageProducerError

from geofencing_service.db.models import UASZone
from geofencing_service.endpoints.schemas.db_schemas import UASZoneSchema
from geofencing_service.events.uas_zone_handlers import UASZoneContext

_logger = logging.getLogger(__name__)


class UASZonesUpdatesMessageType(enum.Enum):
    UAS_ZONE_CREATION = 'UAS_ZONE_CREATION'
    UAS_ZONE_DELETION = 'UAS_ZONE_DELETION'


class UASZonesUpdatesMessageProducerContext:
    def __init__(self, message_type: UASZonesUpdatesMessageType, uas_zone: UASZone):
        self.message_type = message_type
        self.uas_zone: UASZone = uas_zone


def uas_zones_updates_message_producer(context: UASZonesUpdatesMessageProducerContext) -> proton.Message:
    """
    The message producer (UASZones retrieval) that will be called every time the topic is triggered for publishing.

    :param context: Mandatory parameter required by `swim-pubsub`. Here it contains the UASZone filtering criteria of
                    the subscription
    :return:
    """
    if context.message_type == UASZonesUpdatesMessageType.UAS_ZONE_CREATION:
        message_body = {
            'uas_zone': UASZoneSchema().dump(context.uas_zone)
        }
    elif context.message_type == UASZonesUpdatesMessageType.UAS_ZONE_DELETION:
        message_body = {
            'uas_zone_identifier': context.uas_zone.identifier
        }
    else:
        raise MessageProducerError('Invalid message_type')

    message_body['message_type'] = context.message_type.value

    return proton.Message(body=message_body, content_type="application/json")


def publish_uas_zone_creation(event_context: UASZoneContext):
    _publish_uas_zone_update(event_context, UASZonesUpdatesMessageType.UAS_ZONE_CREATION)


def publish_uas_zone_deletion(event_context: UASZoneContext):
    _publish_uas_zone_update(event_context, UASZonesUpdatesMessageType.UAS_ZONE_DELETION)


def _publish_uas_zone_update(event_context: UASZoneContext, message_type: UASZonesUpdatesMessageType):
    message_producer_context = UASZonesUpdatesMessageProducerContext(
        message_type=message_type,
        uas_zone=event_context.uas_zone
    )
    for subscription in event_context.uas_zones_subscriptions:
        current_app.swim_publisher.publish_topic(topic_name=subscription.sm_subscription.topic_name,
                                                 context=message_producer_context)
