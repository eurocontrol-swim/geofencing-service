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
from pathlib import Path

import connexion
from swagger_ui_bundle import swagger_ui_3_path
from pkg_resources import resource_filename

from swim_backend.flask import configure_flask
from swim_backend.config import configure_logging, load_app_config
from swim_backend.db import db

__author__ = "EUROCONTROL (SWIM)"


# TODO: fix typing hints


def create_app(config_file):
    options = {'swagger_path': swagger_ui_3_path}
    connexion_app = connexion.App(__name__, options=options)

    connexion_app.add_api(Path('openapi.yml'), strict_validation=True)

    app = connexion_app.app

    app_config = load_app_config(filename=config_file)

    app.config.update(app_config)

    configure_flask(app)

    configure_logging(app)

    _configure_db(db, app)

    return app


def _configure_db(db, app):

    with app.app_context():
        db.init_app(app)
        db.create_all()


if __name__ == '__main__':
    config_file = resource_filename(__name__, 'config.yml')
    app = create_app(config_file)

    app.run(host="0.0.0.0", port=8080, debug=False)
