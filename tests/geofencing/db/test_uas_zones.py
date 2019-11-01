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

from geofencing.common import polygon_filter_from_mongo_polygon
from geofencing.db import MongoPolygonType
from geofencing.db.uas_zones import get_uas_zones
from geofencing.filters import UASZonesFilter
from tests.geofencing.utils import make_uas_zone, make_airspace_volume, make_uas_zones_filter_from_db_uas_zone

__author__ = "EUROCONTROL (SWIM)"

BASILIQUE_POLYGON: MongoPolygonType = [
    [[50.863648, 4.329385],
     [50.865348, 4.328055],
     [50.868470, 4.317369],
     [50.867671, 4.314826],
     [50.865873, 4.315920],
     [50.862792, 4.326508],
     [50.863648, 4.329385]]]

INTERSECTING_BASILIQUE_POLYGON: MongoPolygonType = [
    [[50.862525, 4.328120],
     [50.865502, 4.329257],
     [50.865468, 4.323686],
     [50.862525, 4.328120]]]

NON_INTERSECTING_BASILIQUE_POLYGON: MongoPolygonType = [
    [[50.870058, 4.325421],
     [50.867615, 4.326890],
     [50.867602, 4.321407],
     [50.870058, 4.325421]]]


@pytest.fixture
def db_uas_zone():
    uas_zone = make_uas_zone(BASILIQUE_POLYGON)
    uas_zone.save()

    return uas_zone


@pytest.fixture
def intersecting_airspace_volume():
    return make_airspace_volume(polygon=INTERSECTING_BASILIQUE_POLYGON)


@pytest.fixture
def non_intersecting_airspace_volume():
    return make_airspace_volume(polygon=NON_INTERSECTING_BASILIQUE_POLYGON)


def test_uas_zones__filter_by_airspace_volume__polygon(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = polygon_filter_from_mongo_polygon(INTERSECTING_BASILIQUE_POLYGON)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 1
    assert result[0].id == db_uas_zone.id

    uas_zones_filter.airspace_volume.polygon = polygon_filter_from_mongo_polygon(NON_INTERSECTING_BASILIQUE_POLYGON)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 0


def test_uas_zones__filter_by_airspace_volume__upper_lower_limit(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = polygon_filter_from_mongo_polygon(INTERSECTING_BASILIQUE_POLYGON)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 1

    uas_zones_filter.airspace_volume.upper_limit_in_m -= 1

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 0

    uas_zones_filter.airspace_volume.upper_limit_in_m += 1
    uas_zones_filter.airspace_volume.lower_limit_in_m += 1

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 0


def test_uas_zones__filter_by_regions(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = polygon_filter_from_mongo_polygon(INTERSECTING_BASILIQUE_POLYGON)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 1

    uas_zones_filter.regions = [100000]

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 0


def test_uas_zones__filter_by_applicable_time_period(db_uas_zone, intersecting_airspace_volume):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = polygon_filter_from_mongo_polygon(INTERSECTING_BASILIQUE_POLYGON)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 1

    uas_zones_filter.start_date_time += timedelta(days=1)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 0

    uas_zones_filter.start_date_time -= timedelta(days=1)
    uas_zones_filter.end_date_time -= timedelta(days=1)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 0


def test_uas_zones__filter_by_updated_date_time(db_uas_zone, intersecting_airspace_volume):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = polygon_filter_from_mongo_polygon(INTERSECTING_BASILIQUE_POLYGON)

    uas_zones_filter.update_after_date_time -= timedelta(days=1)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 1

    uas_zones_filter.update_after_date_time += timedelta(days=2)

    result = get_uas_zones(uas_zones_filter)
    assert len(result) == 0
