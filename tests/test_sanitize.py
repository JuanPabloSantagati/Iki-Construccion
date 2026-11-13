from apps.projects.sanitize import clean_html


def test_quita_scripts_y_manejadores_de_eventos():
    html = '<p onclick="x()">Hola<script>alert(1)</script></p>'
    result = clean_html(html)
    assert "<script" not in result
    assert "alert" not in result
    assert "onclick" not in result
    assert "Hola" in result


def test_quita_enlaces_javascript():
    assert "javascript" not in clean_html('<a href="javascript:alert(1)">x</a>')


def test_conserva_formato_permitido_y_enlaces_seguros():
    result = clean_html('<p><strong>Casa</strong> <a href="https://iki.example">sitio</a></p>')
    assert "<strong>Casa</strong>" in result
    assert 'href="https://iki.example"' in result
    assert 'rel="noopener noreferrer"' in result


def test_quita_etiquetas_no_permitidas():
    result = clean_html('<iframe src="https://x.example"></iframe><img src="a.png"><p>ok</p>')
    assert "<iframe" not in result
    assert "<img" not in result
    assert "<p>ok</p>" in result
