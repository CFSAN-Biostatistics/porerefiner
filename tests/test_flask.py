"Smoke tests for the Flask web app: import, app object, and route registration."

from unittest.mock import patch

from pytest import fixture


@fixture
def client():
    from porerefiner.app import app
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_app_imports():
    from porerefiner.app import app
    assert app.name


def test_routes_registered():
    from porerefiner.app import app
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert '/api/runs' in rules
    assert '/api/runs/<int:run_id>' in rules
    assert '/attach' in rules


def test_attach_route_accepts_post():
    "Regression: attach route had a malformed methods=['POST,'] typo."
    from porerefiner.app import app
    methods = set()
    for r in app.url_map.iter_rules():
        if r.rule == '/api/runs/<int:run_id>/attach':
            methods |= r.methods
    assert 'POST' in methods


def test_template_route(client):
    "The static CSV template route needs no backend server."
    resp = client.get('/template')
    assert resp.status_code == 200
    assert b'porerefiner_ver' in resp.data
