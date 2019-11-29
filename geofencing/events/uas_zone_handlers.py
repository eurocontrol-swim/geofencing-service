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

from flask import current_app
from swim_pubsub.core.errors import PubSubClientError

from geofencing.db.models import UASZone, UASZonesSubscription
from geofencing.db.uas_zones import create_uas_zone as db_create_uas_zone, get_uas_zones as db_get_uas_zones
from geofencing.db.subscriptions import get_uas_zones_subscriptions as db_get_uas_zones_subscriptions

__author__ = "EUROCONTROL (SWIM)"

_logger = logging.getLogger(__name__)


class UASZoneContext:
    def __init__(self, uas_zone: UASZone) -> None:
        self.uas_zone = uas_zone
        self.topic_names = []


def uas_zone_db_save(context: UASZoneContext) -> None:
    db_create_uas_zone(context.uas_zone)


def _uas_zone_matches_subscription(uas_zone: UASZone, subscription: UASZonesSubscription):
    uas_zones = db_get_uas_zones(uas_zones_filter=subscription.uas_zones_filter)

    return uas_zone in uas_zones


def get_topic_names(context: UASZoneContext) -> None:
    uas_zones_subscriptions = db_get_uas_zones_subscriptions()

    context.topic_names = [subscription.topic_name for subscription in uas_zones_subscriptions
                           if _uas_zone_matches_subscription(context.uas_zone, subscription)]


def publish_topics(context: UASZoneContext) -> None:
    for topics_name in context.topic_names:
        try:
            current_app.publisher.publish_topic(topics_name)
        except PubSubClientError as e:
            _logger.error(str(e))


def uas_zones_db_delete(context: UASZoneContext):
    context.uas_zone.delete()
