import base64
from io import BytesIO, StringIO
import csv
from zipfile import ZipFile

from openpyxl import Workbook
import pytest

import app as painel


@pytest.fixture
def client():
    return painel.server.test_client()


@pytest.fixture
def planilha():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([
        "IDBarragem", "NMBarragem", "NMMineradora", "UF", "Município",
        "TrabalhadoresZAS", "ExisteComunidadeZAS",
    ])
    sheet.append([900001, "São Bento", "Empresa A", "MG", "Nova Lima", 10, "Sim"])
    sheet.append([900002, "Rio Claro", "Empresa B", "MG", "Mariana", 20, "Não"])
    sheet.append([900003, "Curuá", "Empresa A", "PA", "Belém", 30, "Sim"])
    arquivo = BytesIO()
    workbook.save(arquivo)
    return arquivo.getvalue()


def uri_upload(conteudo):
    encoded = base64.b64encode(conteudo).decode("ascii")
    return f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{encoded}"


def callback(client, componente, propriedade, inputs, states=None):
    """Exercita o endpoint real do Dash, incluindo registro e serialização."""
    states = states or {}
    for chave, configuracao in painel.app.callback_map.items():
        outputs = configuracao["output"]
        lista = outputs if isinstance(outputs, list) else [outputs]
        if any(item.component_id == componente and item.component_property == propriedade for item in lista):
            break
    else:
        raise AssertionError(f"Callback ausente: {componente}.{propriedade}")
    descricoes = [{"id": item.component_id, "property": item.component_property} for item in lista]
    resposta = client.post("/_dash-update-component", json={
        "output": chave,
        "outputs": descricoes if isinstance(outputs, list) else descricoes[0],
        "changedPropIds": [f"{key[0]}.{key[1]}" for key in inputs],
        "inputs": [{**item, "value": inputs[(item["id"], item["property"])]} for item in configuracao["inputs"]],
        "state": [{**item, "value": states[(item["id"], item["property"])]} for item in configuracao["state"]],
    })
    assert resposta.status_code == 200, resposta.get_data(as_text=True)
    return resposta.get_json()["response"]


def upload(client, planilha, filename="barragens.xlsx"):
    return callback(client, "dados-store", "data", {
        ("upload-planilha", "contents"): uri_upload(planilha),
    }, {("upload-planilha", "filename"): filename})


def atualizar(client, payload, estados=None, municipios=None, empreendedores=None, busca=None):
    return callback(client, "tabela-registros", "data", {
        ("dados-store", "data"): payload,
        ("filtro-estado", "value"): estados or [],
        ("filtro-municipio", "value"): municipios or [],
        ("filtro-empreendedor", "value"): empreendedores or [],
        ("busca", "value"): busca or "",
    })


def indicadores(resposta):
    resultado = {}
    def visitar(componente):
        if isinstance(componente, list):
            for filho in componente:
                yield from visitar(filho)
        elif isinstance(componente, dict):
            yield componente
            yield from visitar(componente.get("props", {}).get("children"))
    for bloco in ("indicadores-panorama", "indicadores-economia"):
        for card in resposta[bloco]["children"]:
            rotulo = card["props"]["data-indicador"]
            valor = next(item["props"]["children"] for item in visitar(card)
                         if item.get("props", {}).get("className") == "metric-value")
            resultado[rotulo] = valor
    return resultado


def test_servidor_layout_e_callbacks_registrados(client):
    assert client.get("/").status_code == 200
    assert client.get("/assets/style.css").status_code == 200
    layout = client.get("/_dash-layout")
    assert layout.status_code == 200
    assert "upload-planilha" in layout.get_data(as_text=True)
    dependencias = client.get("/_dash-dependencies")
    assert dependencias.status_code == 200
    outputs = " ".join(item["output"] for item in dependencias.get_json())
    assert all(target in outputs for target in (
        "indicadores-panorama.children", "mapa-barragens.figure",
        "detalhe-barragem.children", "resultado-comparacao.children",
        "download-csv.data", "platform-container.style",
    ))


def test_upload_xlsx_atualiza_tabela_grafico_e_indicadores(client, planilha):
    payload = upload(client, planilha)["dados-store"]["data"]
    assert payload["arquivo"] == "barragens.xlsx"
    resposta = atualizar(client, payload)
    assert resposta["contagem-registros"]["children"] == "3 de 3 registros"
    assert len(resposta["tabela-registros"]["data"]) == 3
    assert indicadores(resposta)["Barragens analisadas"] == "3"
    assert indicadores(resposta)["Trabalhadores · quantidade informada"] == "60"
    assert indicadores(resposta)["Barragens com comunidade na ZAS"] == "2"
    assert set(resposta["grafico-estados"]["figure"]["data"][0]["y"]) == {"MG", "PA"}


def test_filtros_em_intersecao_e_busca_sem_acentos(client, planilha):
    payload = upload(client, planilha)["dados-store"]["data"]
    resposta = atualizar(client, payload, estados=["MG"], empreendedores=["Empresa A"], busca="SAO")
    assert [row["NMBarragem"] for row in resposta["tabela-registros"]["data"]] == ["São Bento"]
    assert resposta["contagem-registros"]["children"] == "1 de 3 registros"
    assert indicadores(resposta)["Trabalhadores · quantidade informada"] == "10"
    vazia = atualizar(client, payload, estados=["PA"], municipios=["Nova Lima"])
    assert vazia["tabela-registros"]["data"] == []
    assert vazia["contagem-registros"]["children"] == "0 de 3 registros"
    assert indicadores(vazia)["Barragens analisadas"] == "0"


def test_planilha_real_expoe_colunas_ausentes_sem_inventar_numeros(client):
    payload = painel.payload_inicial()
    assert len(payload["registros"]) == 41
    resposta = atualizar(client, payload)
    valores = indicadores(resposta)
    assert valores["Barragens analisadas"] == "41"
    assert valores["Empreendedores"] == "20"
    assert valores["Municípios"] == "—"
    assert valores["Estados"] == "—"
    assert valores["Barragens com trabalhadores na ZAS"] == "41"
    assert valores["Barragens com comunidade na ZAS"] == "13"
    filtros = callback(client, "filtro-estado", "options", {
        ("dados-store", "data"): payload,
        ("limpar-filtros", "n_clicks"): 0,
    })
    assert filtros["filtro-estado"]["disabled"] is True
    assert filtros["filtro-municipio"]["disabled"] is True
    assert filtros["filtro-empreendedor"]["disabled"] is False


def test_filtro_vazio_preserva_natureza_categorica_de_trabalhadores(client):
    resposta = atualizar(client, painel.payload_inicial(), busca="barragem que não existe")
    valores = indicadores(resposta)
    assert valores["Barragens com trabalhadores na ZAS"] == "0"
    assert valores["Trabalhadores · quantidade informada"] == "—"


def test_quantidade_numerica_um_nao_e_resposta_categorica_sim(client):
    payload = {
        "cabecalhos": ["IDBarragem", "NMBarragem", "TrabalhadoresZAS"],
        "registros": [{"IDBarragem": 900005, "NMBarragem": "Barragem teste", "TrabalhadoresZAS": 1}],
    }
    valores = indicadores(atualizar(client, payload))
    assert valores["Trabalhadores · quantidade informada"] == "1"
    assert valores["Barragens com trabalhadores na ZAS"] == "—"


@pytest.mark.parametrize("conteudo,filename", [
    (b"nao e um Excel", "arquivo.xlsx"),
    (b"texto CSV", "arquivo.csv"),
])
def test_upload_invalido_mantem_base_anterior(client, conteudo, filename):
    resposta = upload(client, conteudo, filename)
    assert "dados-store" not in resposta
    assert resposta["mensagem-dados"]["children"]["props"]["color"] in {"warning", "danger"}


def test_xlsx_com_xml_corrompido_apresenta_erro_sem_substituir_base(client, planilha):
    arquivo = BytesIO()
    with ZipFile(BytesIO(planilha)) as original, ZipFile(arquivo, "w") as corrompido:
        for item in original.infolist():
            conteudo = b"<worksheet><sheetData>" if item.filename == "xl/worksheets/sheet1.xml" else original.read(item.filename)
            corrompido.writestr(item, conteudo)
    resposta = upload(client, arquivo.getvalue())
    assert "dados-store" not in resposta
    assert resposta["mensagem-dados"]["children"]["props"]["color"] == "danger"


def test_csv_exporta_apenas_filtro_preserva_acentos_e_neutraliza_formulas(client, planilha):
    payload = upload(client, planilha)["dados-store"]["data"]
    payload["registros"][1]["NMBarragem"] = "  =SOMA(A1:A2)"
    payload["cabecalhos"].append("=Cabecalho")
    payload["registros"][0]["=Cabecalho"] = "Texto seguro"
    resposta = callback(client, "download-csv", "data", {("baixar-csv", "n_clicks"): 1}, {
        ("dados-store", "data"): payload,
        ("filtro-estado", "value"): ["MG"],
        ("filtro-municipio", "value"): [],
        ("filtro-empreendedor", "value"): [],
        ("busca", "value"): "",
    })
    download = resposta["download-csv"]["data"]
    assert download["filename"] == "barragens_filtradas.csv"
    assert download["content"].startswith("\ufeff")
    registros = list(csv.DictReader(StringIO(download["content"].lstrip("\ufeff")), delimiter=";"))
    assert len(registros) == 2
    assert registros[0]["NMBarragem"] == "São Bento"
    assert registros[1]["NMBarragem"] == "'  =SOMA(A1:A2)"
    assert registros[0]["'=Cabecalho"] == "Texto seguro"


def test_base_vazia_produz_layout_sem_erro(client):
    resposta = atualizar(client, {"cabecalhos": [], "registros": [], "arquivo": ""})
    assert resposta["tabela-registros"]["data"] == []
    assert resposta["contagem-registros"]["children"] == "0 de 0 registros"


def test_upload_referencia_coordenadas_nao_substitui_base_do_estudo(client):
    arquivo = painel.PASTA_PROJETO / "dados" / "referencias" / "coordenadas_barragens_preenchidas.xlsx"
    resposta = upload(client, arquivo.read_bytes(), arquivo.name)
    assert "dados-store" not in resposta
    mensagem = str(resposta["mensagem-dados"]["children"])
    assert "planilha complementar de coordenadas" in mensagem
    assert "planilha principal" in mensagem
