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
from typing import Optional, List

from mongoengine import DoesNotExist, Q

from geofencing_service.db.models import UASZonesSubscription, User

__author__ = "EUROCONTROL (SWIM)"


def get_uas_zones_subscriptions(user: Optional[User] = None) -> List[UASZonesSubscription]:
    """
    Retrieve all the subscriptions from DB
    :param user: object
    :return:
    """
    query = Q(user=user) if user is not None else Q()

    return UASZonesSubscription.objects(query).all()


def get_uas_zones_subscription_by_id(subscription_id: str, user: Optional[User] = None) -> Optional[UASZonesSubscription]:
    """
    Retrieves a subscription based on its id
    :param subscription_id:
    :param user:
    :return:
    """
    query = Q(id=subscription_id)

    if user is not None:
        query &= Q(user=user)

    try:
        result = UASZonesSubscription.objects.get(query)
    except DoesNotExist:
        result = None

    return result


def create_uas_zones_subscription(subscription: UASZonesSubscription):
    """
    Saves a subscription in DB
    :param subscription:
    """
    subscription.save()


def update_uas_zones_subscription(subscription: UASZonesSubscription):
    """
    Updates a subscription in DB
    :param subscription:
    """
    subscription.save()


def delete_uas_zones_subscription(subscription: UASZonesSubscription):
    """
    Deletes a subscription in DB
    :param subscription:
    """
    subscription.delete()
