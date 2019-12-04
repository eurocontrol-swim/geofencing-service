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

from geofencing_server.db.models import UASZone, AuthorityEntity
from geofencing_server.db.uas_zones import get_uas_zones, create_uas_zone, delete_uas_zone
from tests.geofencing_server.utils import make_uas_zone, make_uas_zones_filter_from_db_uas_zone, \
    BASILIQUE_POLYGON, INTERSECTING_BASILIQUE_POLYGON, NON_INTERSECTING_BASILIQUE_POLYGON
from geofencing_server.common import point_list_from_geojson_polygon_coordinates

__author__ = "EUROCONTROL (SWIM)"


@pytest.fixture
def db_uas_zone():
    uas_zone = make_uas_zone(BASILIQUE_POLYGON)
    uas_zone.authorization_authority.save()
    uas_zone.notification_authority.save()
    uas_zone.save()

    return uas_zone


@pytest.fixture
def filter_with_intersecting_airspace_volume(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = point_list_from_geojson_polygon_coordinates(
        INTERSECTING_BASILIQUE_POLYGON)

    return uas_zones_filter


@pytest.fixture
def filter_with_non_intersecting_airspace_volume(db_uas_zone):
    uas_zones_filter = make_uas_zones_filter_from_db_uas_zone(db_uas_zone)
    uas_zones_filter.airspace_volume.polygon = point_list_from_geojson_polygon_coordinates(
        NON_INTERSECTING_BASILIQUE_POLYGON)

    return uas_zones_filter


def test_get_uas_zones__filter_by_airspace_volume__polygon(filter_with_intersecting_airspace_volume,
                                                           filter_with_non_intersecting_airspace_volume):

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 1

    result = get_uas_zones(filter_with_non_intersecting_airspace_volume)
    assert len(result) == 0


def test_get_uas_zones__filter_by_airspace_volume__upper_lower_limit(filter_with_intersecting_airspace_volume):

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 1

    filter_with_intersecting_airspace_volume.airspace_volume.upper_limit_in_m -= 1

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 0

    filter_with_intersecting_airspace_volume.airspace_volume.upper_limit_in_m += 1
    filter_with_intersecting_airspace_volume.airspace_volume.lower_limit_in_m += 1

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 0


def test_get_uas_zones__filter_by_regions(filter_with_intersecting_airspace_volume):

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 1

    filter_with_intersecting_airspace_volume.regions = [100000]

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 0


def test_get_uas_zones__filter_by_applicable_time_period(filter_with_intersecting_airspace_volume):

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 1

    filter_with_intersecting_airspace_volume.start_date_time += timedelta(days=1)

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 0

    filter_with_intersecting_airspace_volume.start_date_time -= timedelta(days=1)
    filter_with_intersecting_airspace_volume.end_date_time -= timedelta(days=1)

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 0


def test_get_uas_zones__filter_by_updated_date_time(filter_with_intersecting_airspace_volume):
    filter_with_intersecting_airspace_volume.updated_after_date_time -= timedelta(days=1)

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 1

    filter_with_intersecting_airspace_volume.updated_after_date_time += timedelta(days=2)

    result = get_uas_zones(filter_with_intersecting_airspace_volume)
    assert len(result) == 0


def test_create_uas_zone():
    uas_zone = make_uas_zone(polygon=BASILIQUE_POLYGON)

    create_uas_zone(uas_zone)

    assert uas_zone in UASZone.objects.all()
    assert uas_zone.notification_authority in AuthorityEntity.objects.all()
    assert uas_zone.authorization_authority in AuthorityEntity.objects.all()


def test_delete_uas_zone(db_uas_zone):
    delete_uas_zone(db_uas_zone)

    assert db_uas_zone not in UASZone.objects.all()
