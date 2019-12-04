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
from pathlib import Path
from typing import Tuple

import connexion
from flask import Flask
from mongoengine import connect
from pkg_resources import resource_filename
from swagger_ui_bundle import swagger_ui_3_path
from swim_backend.config import load_app_config, configure_logging
from swim_backend.flask import configure_flask
from swim_pubsub.core.clients import PubSubClient
from swim_pubsub.core.errors import PubSubClientError
from swim_pubsub.publisher import PubApp

from geofencing.endpoints.reply import handle_flask_request_error

__author__ = "EUROCONTROL (SWIM)"

_logger = logging.getLogger(__name__)


def create_flask_app(config_file: str) -> Flask:
    """
    Creates and configures the Flask app.

    :param config_file:
    :return:
    """
    options = {'swagger_path': swagger_ui_3_path}
    connexion_app = connexion.App(__name__, options=options)

    connexion_app.add_api(Path('openapi.yml'), strict_validation=True)

    app = connexion_app.app

    app.after_request(handle_flask_request_error)

    app_config = load_app_config(filename=config_file)

    app.config.update(app_config)

    configure_flask(app)

    configure_logging(app)

    connect(db=app.config['MONGO']['db'])

    # the PubApp as well as the broker publisher of the Geofencing Service will be added as flask app properties for
    # easier usage across the project
    with app.app_context():
        app.pub_app, app.publisher = configure_pub_app(config_file)

    return app


def configure_pub_app(config_file: str) -> Tuple[PubApp, PubSubClient]:
    """
    Creates and configures the PubApp and it resisteres the Geofencing Service broker publisher.

    :param config_file:
    :return:
    """
    pub_app = PubApp.create_from_config(config_file)

    try:
        publisher = pub_app.register_publisher(username=pub_app.config['GEOFENCING_SM_USER'],
                                               password=pub_app.config['GEOFENCING_SM_PASS'])
        _logger.info(f"Publisher '{pub_app.config['GEOFENCING_SM_USER']}' registered in PubApp")
    except PubSubClientError as e:
        _logger.error(f"Publisher failed to be registered in PubApp: {str(e)}")
        publisher = None

    return pub_app, publisher


def run_appication(host="0.0.0.0", port=8000, debug=True):
    flask_app = create_flask_app(config_file=resource_filename(__name__, 'config.yml'))

    # the PubApp is started in threaded mode in order to be able to use its publisher across the project
    flask_app.pub_app.run(threaded=True)

    flask_app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_appication()
