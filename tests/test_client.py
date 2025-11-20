from sam_invoice.client import Client


def test_client_creation():
    client = Client(nom="Dupont", adresse="1 rue du Vin", email="dupont@email.com")
    assert client.nom == "Dupont"
    assert client.adresse == "1 rue du Vin"
    assert client.email == "dupont@email.com"
