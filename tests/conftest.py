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
from unittest.mock import Mock

import pytest
from mongoengine import connect, connection
from pkg_resources import resource_filename

from swim_backend.config import load_app_config

from geofencing_service.app import create_flask_app
from geofencing_service.db.models import User
from geofencing_service.db.users import create_user
from tests.geofencing_service.utils import make_user, get_unique_id

DEFAULT_LOGIN_PASS = 'password'


@pytest.yield_fixture(scope='session')
def app():
    config_file = resource_filename(__name__, 'test_config.yml')
    _app = create_flask_app(config_file)
    if _app.testing:
        _app.pub_app = Mock()
        _app.swim_publisher = Mock()
    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope='session')
def test_client(app):
    return app.test_client()


@pytest.fixture(scope='function', autouse=True)
def setup_mongodb():
    config = load_app_config(filename=resource_filename('tests', 'test_config.yml'))
    connect(db=config['MONGO']['db'])

    db = connection.get_db()
    db.client.drop_database(db.name)


@pytest.fixture(scope='function')
def test_user():
    user = make_user(get_unique_id(), DEFAULT_LOGIN_PASS)
    create_user(user)


@pytest.fixture(scope='function')
def test_user() -> User:
    user = make_user(password=DEFAULT_LOGIN_PASS)

    return create_user(user)
