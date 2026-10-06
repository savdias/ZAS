import csv
import json

import pytest

import coordenadas
from coordenadas import carregar_coordenadas, enriquecer_registros, mapa_barragens


def salvar_csv(tmp_path, linhas):
    arquivo = tmp_path / "coordenadas.csv"
    with arquivo.open("w", encoding="utf-8-sig", newline="") as saida:
        escritor = csv.writer(saida, delimiter=";")
        escritor.writerow(["IDBarragem", "NMBarragem", "Latitude", "Longitude"])
        escritor.writerows(linhas)
    return arquivo


def test_arquivo_ausente_e_coordenadas_vazias_nao_criam_posicoes(tmp_path):
    assert carregar_coordenadas(tmp_path / "ausente.csv") == {}
    arquivo = salvar_csv(tmp_path, [[8391, "Barragem Rio Fiorita", "", ""]])
    assert carregar_coordenadas(arquivo) == {}


def test_csv_bom_ponto_virgula_e_decimais_locais(tmp_path):
    arquivo = salvar_csv(tmp_path, [
        ["008391.0", "Rio Fiorita", "-28,5", "-49.4"],
        [8412, "Lauro Muller", 0, 0],
    ])
    assert carregar_coordenadas(arquivo) == {
        "8391": {"Latitude": -28.5, "Longitude": -49.4},
        "8412": {"Latitude": 0.0, "Longitude": 0.0},
    }


@pytest.mark.parametrize("latitude,longitude", [
    ("", "-40"), ("-20", ""), ("NaN", "-40"),
    ("-20", "inf"), ("-91", "-40"), ("-20", "181"),
    ("texto", "-40"),
])
def test_par_incompleto_ou_invalido_e_ignorado(tmp_path, latitude, longitude):
    arquivo = salvar_csv(tmp_path, [[8391, "Barragem", latitude, longitude]])
    assert carregar_coordenadas(arquivo) == {}


def test_ids_repetidos_com_posicoes_conflitantes_nao_sao_associados(tmp_path):
    arquivo = salvar_csv(tmp_path, [
        [8391, "Barragem", -28, -49],
        [8391, "Barragem", -29, -49],
        [8391, "Barragem", -28, -49],
    ])
    assert carregar_coordenadas(arquivo) == {}


def test_enriquecimento_usa_id_e_preserva_registros_originais():
    registros = [
        {"IDBarragem": 9730, "NMBarragem": "Barragem 01", "UF": "SC"},
        {"IDBarragem": 9262.0, "NMBarragem": "Barragem 01", "UF": "MG"},
        {"IDBarragem": 9730.5, "NMBarragem": "Barragem 01", "UF": "MG"},
    ]
    coordenadas = {"9730": {"Latitude": -28, "Longitude": -49}}
    resultado = enriquecer_registros(registros, coordenadas)

    assert resultado[0] == {
        "IDBarragem": 9730, "NMBarragem": "Barragem 01", "UF": "SC",
        "Latitude": -28.0, "Longitude": -49.0,
    }
    assert resultado[1:] == registros[1:]
    assert all("Latitude" not in registro for registro in registros)
    assert all(novo is not original for novo, original in zip(resultado, registros))


def test_mapa_sem_coordenadas_exibe_aviso_sem_pontos():
    figura = mapa_barragens([{"IDBarragem": 8391, "NMBarragem": "Rio Fiorita"}])
    assert not any(trace.name == "Barragens" for trace in figura.data)
    assert any("Não há coordenadas válidas" in aviso.text for aviso in figura.layout.annotations)
    assert any("0 de 1 registros com coordenadas" == aviso.text for aviso in figura.layout.annotations)


def test_mapa_mostra_somente_pares_validos_sem_servicos_externos():
    figura = mapa_barragens([
        {"IDBarragem": 8391, "NMBarragem": "Rio Fiorita", "Latitude": -28.5, "Longitude": -49.4},
        {"IDBarragem": 8412, "Latitude": "nan", "Longitude": -49},
        {"IDBarragem": 9100, "Latitude": -28},
    ])
    trace = next(trace for trace in figura.data if trace.name == "Barragens")
    assert all(trace.type == "scatter" for trace in figura.data)
    assert list(trace.x) == [-49.4]
    assert list(trace.y) == [-28.5]
    assert trace.customdata[0][0] == "Rio Fiorita"
    assert figura.layout.title.text == "Localização das barragens"
    assert any("1 de 3 registros com coordenadas" == aviso.text for aviso in figura.layout.annotations)


def test_contorno_local_aparece_antes_dos_pontos(tmp_path, monkeypatch):
    monkeypatch.setattr(coordenadas, "PASTA_DADOS", tmp_path)
    feature = {"type": "Feature", "geometry": {
        "type": "Polygon", "coordinates": [[[-60, -20], [-50, -20], [-55, -10], [-60, -20]]],
    }}
    (tmp_path / "brasil.geojson").write_text(json.dumps(feature), encoding="utf-8")
    figura = mapa_barragens([{"Latitude": -18, "Longitude": -55}])
    assert [trace.name for trace in figura.data] == ["Brasil", "Barragens"]
    assert figura.data[0].fill == "toself"
    assert list(figura.data[0].x) == [-60, -50, -55, -60]


def test_ausencia_do_contorno_nao_bloqueia_pontos(tmp_path, monkeypatch):
    monkeypatch.setattr(coordenadas, "PASTA_DADOS", tmp_path)
    figura = mapa_barragens([{"Latitude": -18, "Longitude": -55}])
    assert [trace.name for trace in figura.data] == ["Barragens"]


def test_id_de_clickdata_e_normalizado_e_rotulos_sao_escapados():
    figura = mapa_barragens([{
        "IDBarragem": "008391.0", "NMBarragem": "Barragem <teste>",
        "NMMineradora": "Empresa & parceiros", "Latitude": -28, "Longitude": -49,
    }])
    pontos = next(trace for trace in figura.data if trace.name == "Barragens")
    assert pontos.customdata[0] == ["Barragem &lt;teste&gt;", "Empresa &amp; parceiros", "8391"]
    assert figura.layout.clickmode == "event+select"
    assert figura.layout.dragmode == "zoom"


@pytest.mark.parametrize("coluna", [" ID Barragem ", "Código da Barragem", "Codigo Barragem"])
def test_variantes_da_coluna_id_associam_coordenadas_e_detalhes(coluna):
    original = {coluna: "008391.0", "NMBarragem": "Barragem de teste"}
    resultado = enriquecer_registros([original], {"8391": {"Latitude": -28, "Longitude": -49}})
    assert resultado[0]["Latitude"] == -28
    figura = mapa_barragens(resultado)
    trace = next(trace for trace in figura.data if trace.name == "Barragens")
    assert trace.customdata[0][2] == "8391"
    assert "Latitude" not in original


@pytest.mark.parametrize("barragens,contorno,nomes", [
    (True, True, ["Brasil", "Barragens"]),
    (True, False, ["Barragens"]),
    (False, True, ["Brasil"]),
    (False, False, []),
])
def test_controle_de_camadas_preserva_cobertura(tmp_path, monkeypatch, barragens, contorno, nomes):
    monkeypatch.setattr(coordenadas, "PASTA_DADOS", tmp_path)
    feature = {"type": "Feature", "geometry": {
        "type": "Polygon", "coordinates": [[[-60, -20], [-50, -20], [-55, -10], [-60, -20]]],
    }}
    (tmp_path / "brasil.geojson").write_text(json.dumps(feature), encoding="utf-8")
    figura = mapa_barragens(
        [{"IDBarragem": 8391, "Latitude": -18, "Longitude": -55}, {"IDBarragem": 8412}],
        exibir_barragens=barragens, exibir_contorno=contorno,
    )
    assert [trace.name for trace in figura.data] == nomes
    assert any(aviso.text == "1 de 2 registros com coordenadas" for aviso in figura.layout.annotations)
    if not barragens:
        assert any(aviso.text == "Camada de barragens desativada." for aviso in figura.layout.annotations)
        assert not any("Não há coordenadas válidas" in aviso.text for aviso in figura.layout.annotations)
