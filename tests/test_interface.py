"""Checks for truthful indicators and progressive exploration in the new interface."""
import json

from dash.development.base_component import Component
import pytest

import analises
import app as painel
import dados
import interface
from test_app import callback


def componentes(value):
    """Traverse a component tree without relying on incidental DOM nesting."""
    if isinstance(value, Component):
        yield value
        yield from componentes(getattr(value, "children", None))
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from componentes(child)


def texto_arvore(value):
    if isinstance(value, Component):
        return texto_arvore(getattr(value, "children", None))
    if isinstance(value, (list, tuple)):
        return " ".join(texto_arvore(child) for child in value if child is not None)
    return "" if value is None else str(value)


def valores_cards(cards):
    result = {}
    for card in cards:
        label = card.to_plotly_json()["props"].get("data-indicador")
        value = next(
            item for item in componentes(card)
            if getattr(item, "className", None) == "metric-value"
        )
        result[label] = texto_arvore(value)
    return result


def test_panorama_nao_apresenta_dados_ausentes_como_zero_ou_pessoas():
    payload = painel.payload_inicial()
    colunas = dados.identificar_colunas(payload["cabecalhos"])
    metricas = analises.metricas(payload["registros"], colunas)
    assert metricas["barragens"] == "41"  # 40 nomes distintos, 41 IDs.
    assert metricas["empreendedores"] == "20"
    assert metricas["localizadas"] == "34"
    assert metricas["presenca_trabalhadores"] == "41"
    assert metricas["comunidade"] == "13"
    assert all(metricas[field] == "—" for field in (
        "trabalhadores", "municipios", "estados", "zas", "producao",
        "cfem", "receitas", "exportacoes", "atividades",
    ))
    cards = valores_cards(interface.indicadores_panorama(
        payload["registros"], colunas, payload["registros"],
    ))
    assert cards["Barragens analisadas"] == "41"
    assert cards["Trabalhadores potencialmente afetados"] == "—"
    assert cards["ZAS avaliadas"] == "—"


def test_nova_base_pode_informar_pessoas_e_valores_sem_inventar_estimativa():
    registros = [
        {"IDBarragem": 1, "NMBarragem": "B1", "UF": "MG", "Município": "M1",
         "TrabalhadoresZAS": 12, "ValorCFEM": 0, "IDZAS": "Z1",
         "ValorProducao": "1.234,50", "ValorReceitasPublicas": "30,25"},
        {"IDBarragem": 2, "NMBarragem": "B2", "UF": "MG", "Município": "M1",
         "TrabalhadoresZAS": 8, "ValorCFEM": 10, "IDZAS": "Z1",
         "ValorProducao": "2.000", "ValorReceitasPublicas": "10,25"},
    ]
    colunas = dados.identificar_colunas(list(registros[0]))
    resultado = analises.metricas(registros, colunas)
    assert resultado["trabalhadores"] == "20"
    assert resultado["presenca_trabalhadores"] == "—"
    assert resultado["cfem"] == "10"
    assert resultado["producao"] == "3.234,5"
    assert resultado["receitas"] == "40,5"
    assert resultado["zas"] == "1"
    assert resultado["municipios"] == "1"
    assert analises.metricas(registros[:1], colunas, registros)["cfem"] == "0"


def test_comparacao_preserva_barragens_homonimas_e_municipios_de_ufs_distintas():
    registros = [
        {"IDBarragem": 1, "NMBarragem": "Barragem 01", "NMMineradora": "A", "UF": "MG", "Município": "Santa Rita"},
        {"IDBarragem": 2, "NMBarragem": "Barragem 01", "NMMineradora": "B", "UF": "SP", "Município": "Santa Rita"},
    ]
    colunas = dados.identificar_colunas(list(registros[0]))
    barragens = analises.opcoes_comparacao(registros, colunas, "barragens")
    assert {option["value"] for option in barragens} == {"1", "2"}
    assert all("ID" in option["label"] for option in barragens)
    assert analises.selecionar_grupo(registros, colunas, "barragens", "2") == registros[1:]
    municipios = analises.opcoes_comparacao(registros, colunas, "municipios")
    assert {tuple(json.loads(option["value"])) for option in municipios} == {
        ("MG", "Santa Rita"), ("SP", "Santa Rita"),
    }
    assert analises.selecionar_grupo(registros, colunas, "municipios", json.dumps(["MG", "Santa Rita"])) == registros[:1]


def test_modulos_possuem_ids_unicos_e_mapa_so_oferece_camadas_existentes():
    paginas = interface.criar_paginas()
    ids = [component.id for component in componentes(paginas) if getattr(component, "id", None)]
    assert len(ids) == len(set(ids))
    assert {f"pagina-{module}" for module in interface.MODULOS} <= set(ids)
    camadas = next(component for component in componentes(paginas) if getattr(component, "id", None) == "camadas-mapa")
    assert {option["value"] for option in camadas.options} == {"barragens", "contorno"}
    territorio = next(page for page in paginas if page.id == "pagina-territorio")
    assert "ainda não foram disponibilizadas" in texto_arvore(territorio)


def test_cenarios_e_ia_explicam_o_que_ainda_depende_do_estudo():
    paginas = {page.id: page for page in interface.criar_paginas()}
    assert "ainda não foram fornecidas" in texto_arvore(paginas["pagina-cenarios"])
    assert "validação" in texto_arvore(paginas["pagina-cenarios"])
    evidencias = texto_arvore(paginas["pagina-evidencias"])
    assert "Busca semântica e consulta assistida previstas" in evidencias
    assert "controle de acesso" in evidencias
    assert "ambiente de consulta local" in evidencias


def test_detalhe_mostra_barragem_sem_coordenadas_e_sua_rastreabilidade():
    payload = painel.payload_inicial()
    colunas = dados.identificar_colunas(payload["cabecalhos"])
    sem_coordenadas = next(r for r in payload["registros"] if r.get("Latitude") is None)
    conteudo = interface.detalhe_estrutura(sem_coordenadas, colunas)
    texto = texto_arvore(conteudo)
    assert str(sem_coordenadas["IDBarragem"]) in texto
    assert sem_coordenadas["NMBarragem"] in texto
    assert "Não representam uma quantidade de pessoas" in texto
    assert "Rastreabilidade da localização" in texto
    if sem_coordenadas.get("Observação"):
        assert sem_coordenadas["Observação"] in texto
    campos = {
        texto_arvore(component.children[0]): texto_arvore(component.children[1])
        for component in componentes(conteudo)
        if getattr(component, "className", None) == "detail-item"
    }
    assert campos["Latitude"] == "—"
    assert campos["Longitude"] == "—"


@pytest.fixture
def client():
    return painel.server.test_client()


def entradas_filtro(payload, busca=""):
    return {
        ("dados-store", "data"): payload,
        ("filtro-estado", "value"): [],
        ("filtro-municipio", "value"): [],
        ("filtro-empreendedor", "value"): [],
        ("busca", "value"): busca,
    }


@pytest.mark.parametrize("module", list(interface.MODULOS))
def test_navegacao_http_exibe_apenas_modulo_escolhido_sem_redefinir_filtros(client, module):
    assert client.get(f"/plataforma/{module}").status_code == 200
    resposta = callback(client, "platform-container", "style", {
        ("url", "pathname"): f"/plataforma/{module}",
    })
    assert resposta["landing-container"]["style"] == {"display": "none"}
    assert resposta["platform-container"]["style"] == {}
    assert resposta[f"pagina-{module}"]["style"] == {}
    assert resposta[f"nav-{module}"]["className"] == "nav-link active"
    assert all(resposta[f"pagina-{other}"]["style"] == {"display": "none"}
               for other in interface.MODULOS if other != module)
    assert not any(key.startswith("filtro-") or key == "busca" for key in resposta)


def test_navegacao_http_entrada_e_rota_inexistente(client):
    entrada = callback(client, "platform-container", "style", {
        ("url", "pathname"): "/",
    })
    assert entrada["landing-container"]["style"] == {}
    assert entrada["platform-container"]["style"] == {"display": "none"}
    inexistente = callback(client, "platform-container", "style", {
        ("url", "pathname"): "/plataforma/inexistente",
    })
    assert inexistente["pagina-inexistente"]["style"] == {}
    assert inexistente["pagina-titulo"]["children"] == "Página não encontrada"


def test_mapa_http_camada_selecao_por_id_e_detalhamento(client):
    payload = painel.payload_inicial()
    resposta = callback(client, "mapa-barragens", "figure", {
        **entradas_filtro(payload),
        ("camadas-mapa", "value"): ["barragens", "contorno"],
    }, {("comparar-escala", "value"): "estados"})
    mapa = resposta["mapa-barragens"]["figure"]
    pontos = next(trace for trace in mapa["data"] if trace["name"] == "Barragens")
    assert len(pontos["x"]) == 34
    assert len(resposta["barragem-selecionada"]["options"]) == 41
    escalas = {item["value"]: item for item in resposta["comparar-escala"]["options"]}
    assert escalas["municipios"]["disabled"] is True
    assert escalas["estados"]["disabled"] is True
    assert escalas["barragens"]["disabled"] is False
    assert resposta["comparar-escala"]["value"] == "barragens"
    click = pontos["customdata"][0]
    selecionada = callback(client, "barragem-selecionada", "value", {
        ("mapa-barragens", "clickData"): {"points": [{"customdata": click}]},
        **entradas_filtro(payload),
    })["barragem-selecionada"]["value"]
    assert selecionada == str(click[2])
    detalhe = callback(client, "detalhe-barragem", "children", {
        ("barragem-selecionada", "value"): selecionada,
        **entradas_filtro(payload),
    })
    assert selecionada in json.dumps(detalhe, ensure_ascii=False)
    assert "Rastreabilidade da localização" in json.dumps(detalhe, ensure_ascii=False)
    sem_pontos = callback(client, "mapa-barragens", "figure", {
        **entradas_filtro(payload), ("camadas-mapa", "value"): ["contorno"],
    }, {("comparar-escala", "value"): "barragens"})
    assert not any(trace["name"] == "Barragens" for trace in sem_pontos["mapa-barragens"]["figure"]["data"])


def test_comparacao_http_limita_quatro_grupos_e_respeita_recorte(client):
    payload = painel.payload_inicial()
    ids = [str(registro["IDBarragem"]) for registro in payload["registros"][:5]]
    resposta = callback(client, "resultado-comparacao", "children", {
        **entradas_filtro(payload),
        ("comparar-itens", "value"): ids,
        ("comparar-escala", "value"): "barragens",
    })
    cards = resposta["resultado-comparacao"]["children"]
    assert len(cards) == 4
    assert ids[4] not in json.dumps(cards)
    assert "Trabalhadores · quantidade" in json.dumps(cards, ensure_ascii=False)
    assert "CFEM (R$)" in json.dumps(cards, ensure_ascii=False)
    options = callback(client, "comparar-itens", "options", {
        **entradas_filtro(payload, busca=ids[0]),
        ("comparar-escala", "value"): "barragens",
        ("comparar-itens", "value"): ids,
    })
    assert [item["value"] for item in options["comparar-itens"]["options"]] == ids[:1]
    assert options["comparar-itens"]["value"] == ids[:1]
    limite = callback(client, "comparar-itens", "options", {
        **entradas_filtro(payload), ("comparar-escala", "value"): "barragens",
        ("comparar-itens", "value"): ids,
    })
    assert limite["comparar-itens"]["value"] == ids[:4]


def test_limpar_filtros_http_redefine_recorte_e_busca(client):
    resposta = callback(client, "filtro-estado", "options", {
        ("dados-store", "data"): painel.payload_inicial(),
        ("limpar-filtros", "n_clicks"): 1,
    })
    assert resposta["filtro-estado"]["value"] == []
    assert resposta["filtro-municipio"]["value"] == []
    assert resposta["filtro-empreendedor"]["value"] == []
    assert resposta["busca"]["value"] == ""


def test_detalhamento_http_nao_exibe_estrutura_fora_do_recorte(client):
    payload = painel.payload_inicial()
    registro = payload["registros"][0]
    resposta = callback(client, "detalhe-barragem", "children", {
        **entradas_filtro(payload, busca="BARRAGEM_INEXISTENTE_XYZ"),
        ("barragem-selecionada", "value"): str(registro["IDBarragem"]),
    })
    conteudo = json.dumps(resposta["detalhe-barragem"]["children"], ensure_ascii=False)
    assert registro["NMBarragem"] not in conteudo
    assert "detail-card" not in conteudo
