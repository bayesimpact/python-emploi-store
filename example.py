"""An example server to use emploi_store library.

This runs a HTTP server locally with a simple page that helps retrieve the job
names for a given ROME ID.

To run it, you will need to set your environment variable:
    EMPLOI_STORE_CLIENT_ID and EMPLOI_STORE_CLIENT_SECRET.
See documentation about accessing the REST API at
https://www.emploi-store-dev.fr/portail-developpeur/donneesdoctechnique

There are few environment variables that allow you to specify how to run the
server:
 - DEBUG: set it to 1 to turn on debug mode.
 - PORT: set it to the port you want the server to listen on.
 - BIND_HOST: set it to 0.0.0.0 to listen on all interfaces.
"""
import os
import re

import emploi_store
import flask

app = flask.Flask(__name__)  # pylint: disable=invalid-name

# Access to the ROME appellations resource on Emploi Store Dev.
_ROME_APPELLATIONS = (
    emploi_store.Client()
    .get_package('rome')
    .get_resource(name_re=re.compile(r'.*appellations.*')))


@app.route("/")
def main():
    """Homepage."""
    page = (
        '<form action=".">'
        '<input name="rome" placeholder="ROME code, e.g. F1402"/>'
        '</form>')
    rome = flask.request.args.get('rome', '')
    if rome:
        page += '<ul>'
        filters = {'ROME_PROFESSION_CARD_CODE': rome}
        for appellation in _ROME_APPELLATIONS.records(filters=filters):
            page += '<li>%s</li>' % appellation['ROME_PROFESSION_NAME']
        page += '</ul>'
    return page


if __name__ == '__main__':
    app.run(
        debug=bool(os.getenv('DEBUG')),
        host=os.getenv('BIND_HOST', 'localhost'),
        port=int(os.getenv('PORT', '80')))
