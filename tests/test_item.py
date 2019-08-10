import factory
from pytest_factoryboy import register

from autoshop.models import Item


@register
class ItemFactory(factory.Factory):

    itemname = factory.Sequence(lambda n: 'item%d' % n)
    email = factory.Sequence(lambda n: 'item%d@mail.com' % n)
    password = "mypwd"

    class Meta:
        model = Item


def test_get_item(client, db, item, admin_headers):
    # test 404
    rep = client.get("/api/v1/items/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(item)
    db.session.commit()

    # test get_item
    rep = client.get('/api/v1/items/%d' % item.id, headers=admin_headers)
    assert rep.status_code == 200

    data = rep.get_json()['item']
    assert data['itemname'] == item.itemname
    assert data['email'] == item.email
    assert data['active'] == item.active


def test_put_item(client, db, item, admin_headers):
    # test 404
    rep = client.put("/api/v1/items/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(item)
    db.session.commit()

    data = {'itemname': 'updated'}

    # test update item
    rep = client.put(
        '/api/v1/items/%d' % item.id,
        json=data,
        headers=admin_headers
    )
    assert rep.status_code == 200

    data = rep.get_json()['item']
    assert data['itemname'] == 'updated'
    assert data['email'] == item.email
    assert data['active'] == item.active


def test_delete_item(client, db, item, admin_headers):
    # test 404
    rep = client.delete("/api/v1/items/100000", headers=admin_headers)
    assert rep.status_code == 404

    db.session.add(item)
    db.session.commit()

    # test get_item
    item_id = item.id
    rep = client.delete(
        '/api/v1/items/%d' % item_id,
        headers=admin_headers
    )
    assert rep.status_code == 200
    assert db.session.query(Item).filter_by(id=item_id).first() is None


def test_create_item(client, db, admin_headers):
    # test bad data
    data = {
        'itemname': 'created'
    }
    rep = client.post(
        '/api/v1/items',
        json=data,
        headers=admin_headers
    )
    assert rep.status_code == 422

    data['password'] = 'admin'
    data['email'] = 'create@mail.com'

    rep = client.post(
        '/api/v1/items',
        json=data,
        headers=admin_headers
    )
    assert rep.status_code == 201

    data = rep.get_json()
    item = db.session.query(Item).filter_by(id=data['item']['id']).first()

    assert item.itemname == 'created'
    assert item.email == 'create@mail.com'


def test_get_all_item(client, db, item_factory, admin_headers):
    items = item_factory.create_batch(30)

    db.session.add_all(items)
    db.session.commit()

    rep = client.get('/api/v1/items', headers=admin_headers)
    assert rep.status_code == 200

    results = rep.get_json()
    for item in items:
        assert any(u['id'] == item.id for u in results['results'])
