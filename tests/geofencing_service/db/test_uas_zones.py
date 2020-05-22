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
from datetime import timedelta

import pytest

from geofencing_service.db.models import UASZone, UomDistance
from geofencing_service.db.uas_zones import get_uas_zones, create_uas_zone, delete_uas_zone
from tests.geofencing_service.utils import make_uas_zone, make_uas_zones_filter_from_db_uas_zone, \
    BASILIQUE_POLYGON, INTERSECTING_BASILIQUE_POLYGON, NON_INTERSECTING_BASILIQUE_POLYGON

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def db_uas_zone():
    uas_zone = make_uas_zone(BASILIQUE_POLYGON)
    uas_zone.save()

    return uas_zone


@pytest.fixture
def intersecting_filter(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.horizontal_projection = INTERSECTING_BASILIQUE_POLYGON

    return uas_zones_filter


@pytest.fixture
def non_intersecting_filter(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.horizontal_projection = NON_INTERSECTING_BASILIQUE_POLYGON

    return uas_zones_filter


def test_get_uas_zones__filter_by_airspace_volume__polygon(
        intersecting_filter, non_intersecting_filter):

    result = get_uas_zones(intersecting_filter)
    assert len(result) == 1

    result = get_uas_zones(non_intersecting_filter)
    assert len(result) == 0


@pytest.mark.parametrize(
    'zone_uom, zone_upper, zone_lower, filter_uom, filter_upper, filter_lower, n_result', [
    (UomDistance.METERS.value, 100, 100, UomDistance.METERS.value, 100, 100, 1),
    (UomDistance.METERS.value, 99, 100, UomDistance.METERS.value, 100, 100, 1),
    (UomDistance.METERS.value, 101, 100, UomDistance.METERS.value, 100, 100, 0),
    (UomDistance.METERS.value, 100, 101, UomDistance.METERS.value, 100, 100, 1),
    (UomDistance.METERS.value, 100, 99, UomDistance.METERS.value, 100, 100, 0),
    (UomDistance.FEET.value, 100, 100, UomDistance.METERS.value, 100, 100, 0),
    (UomDistance.FEET.value, 350, 100, UomDistance.METERS.value, 100, 100, 0),
    (UomDistance.FEET.value, 350, 350, UomDistance.METERS.value, 100, 100, 0),
    (UomDistance.FEET.value, 100, 350, UomDistance.METERS.value, 100, 100, 1),
    (UomDistance.FEET.value, 100, 300, UomDistance.METERS.value, 100, 100, 0),
    (UomDistance.FEET.value, 300, 350, UomDistance.METERS.value, 100, 100, 1),
    (UomDistance.METERS.value, 100, 100, UomDistance.FEET.value, 100, 100, 0),
    (UomDistance.METERS.value, 100, 100, UomDistance.FEET.value, 350, 100, 1),
    (UomDistance.METERS.value, 100, 100, UomDistance.FEET.value, 350, 350, 0),
    (UomDistance.METERS.value, 100, 100, UomDistance.FEET.value, 350, 300, 1),
    (UomDistance.METERS.value, 100, 100, UomDistance.FEET.value, 300, 350, 0),
    (UomDistance.METERS.value, 100, 100, UomDistance.FEET.value, 300, 300, 0),
])
def test_get_uas_zones__filter_by_airspace_volume__upper_lower_limit(
        db_uas_zone,
        intersecting_filter,
        zone_uom,
        zone_upper,
        zone_lower,
        filter_uom,
        filter_upper,
        filter_lower,
        n_result
):

    db_uas_zone.geometry[0].uom_dimensions = zone_uom
    db_uas_zone.geometry[0].upper_limit = zone_upper
    db_uas_zone.geometry[0].lower_limit = zone_lower
    db_uas_zone.save()

    intersecting_filter.airspace_volume.uom_dimensions = filter_uom
    intersecting_filter.airspace_volume.upper_limit = filter_upper
    intersecting_filter.airspace_volume.lower_limit = filter_lower

    result = get_uas_zones(intersecting_filter)
    assert len(result) == n_result


def test_get_uas_zones__filter_by_regions(intersecting_filter):

    result = get_uas_zones(intersecting_filter)
    assert len(result) == 1

    intersecting_filter.regions = [100000]

    result = get_uas_zones(intersecting_filter)
    assert len(result) == 0


def test_get_uas_zones__filter_by_applicable_time_period(intersecting_filter):

    result = get_uas_zones(intersecting_filter)
    assert len(result) == 1

    intersecting_filter.start_date_time += timedelta(days=1)

    result = get_uas_zones(intersecting_filter)
    assert len(result) == 0

    intersecting_filter.start_date_time -= timedelta(days=1)
    intersecting_filter.end_date_time -= timedelta(days=1)

    result = get_uas_zones(intersecting_filter)
    assert len(result) == 0


def test_create_uas_zone():
    uas_zone = make_uas_zone(horizontal_projection=BASILIQUE_POLYGON)

    create_uas_zone(uas_zone)

    assert uas_zone in UASZone.objects.all()


def test_delete_uas_zone(db_uas_zone):
    delete_uas_zone(db_uas_zone)

    assert db_uas_zone not in UASZone.objects.all()
