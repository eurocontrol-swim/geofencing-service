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
import pytest
from mongoengine import NotUniqueError
from werkzeug.security import check_password_hash

from geofencing_service.db.models import User
from geofencing_service.db.users import get_user_by_username, create_user
from tests.geofencing_service.utils import make_user

__author__ = "EUROCONTROL (SWIM)"


def test_get_user_by_username__username_exists__user_is_returned():
    user = make_user('username', 'password')
    user.save()

    user_from_db = get_user_by_username(username=user.username)
    assert user_from_db is not None
    assert user.username == user_from_db.username


def test_get_user_by_username__invalid_username__none_is_returned():
    user_from_db = get_user_by_username(username="invalid")

    assert user_from_db is None


def test_create_user__user_is_saved_in_db():
    user = User(username="username", password="password")

    create_user(user)

    user_from_db = User.objects.get(username='username')

    assert user_from_db is not None
    assert user.username == user_from_db.username
    assert check_password_hash(user_from_db.password, 'password')


def test_create_user__username_should_be_unique():
    user1 = User(username="username", password="password")
    user2 = User(username="username", password="password")

    user1.save()
    with pytest.raises(NotUniqueError):
        user2.save()
