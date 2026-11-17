import pytest
from django.core.cache import cache
from django.test import RequestFactory, override_settings

from apps.core.clientip import get_client_ip
from tests.test_contact import URL, data

rf = RequestFactory()


def req(**meta):
    return rf.get("/", **meta)


def test_sin_proxy_usa_remote_addr_e_ignora_x_forwarded_for():
    request = req(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="1.2.3.4")
    assert get_client_ip(request) == "10.0.0.1"


@override_settings(TRUSTED_PROXY_COUNT=1)
def test_con_un_proxy_toma_la_ultima_ip_y_no_la_que_escribe_el_cliente():
    request = req(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="6.6.6.6, 203.0.113.7")
    assert get_client_ip(request) == "203.0.113.7"


@override_settings(TRUSTED_PROXY_COUNT=2)
def test_con_dos_proxies_toma_la_penultima():
    request = req(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.7, 172.16.0.5")
    assert get_client_ip(request) == "203.0.113.7"


@override_settings(TRUSTED_PROXY_COUNT=1)
def test_sin_header_cae_en_remote_addr():
    assert get_client_ip(req(REMOTE_ADDR="10.0.0.1")) == "10.0.0.1"


@pytest.mark.django_db
@override_settings(TRUSTED_PROXY_COUNT=1, CONTACT_RATE_LIMIT=1)
def test_limite_de_contacto_distingue_visitantes_detras_del_proxy(client):
    cache.clear()
    a = {"REMOTE_ADDR": "10.0.0.1", "HTTP_X_FORWARDED_FOR": "203.0.113.7"}
    b = {"REMOTE_ADDR": "10.0.0.1", "HTTP_X_FORWARDED_FOR": "203.0.113.8"}
    assert client.post(URL, data(), **a).status_code == 302
    assert client.post(URL, data(), **b).status_code == 302
    assert client.post(URL, data(), **a).status_code == 429
