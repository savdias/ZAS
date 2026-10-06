"""Painel ZAS: leitura de XLSX, filtros, indicadores e exportação."""

import base64
import binascii
import csv
import io
import os
from collections import Counter
from pathlib import Path
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

from dash import Dash, Input, Output, State, dash_table, dcc, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from openpyxl.utils.exceptions import InvalidFileException
from dash import ctx

import dados
from coordenadas import enriquecer_registros, mapa_barragens
from analises import metricas, opcoes_comparacao, selecionar_grupo, resumo_empreendedores, chave_barragem, trabalhadores_categoricos
from interface import MODULOS, criar_paginas, indicadores_panorama, cartao, detalhe_estrutura
from landing import pagina_inicial, marca

AZUL_ESCURO = "#071E2B"
AZUL = "#0B3954"
VERDE = "#11462C"
FUNDO = "#F4F7F9"
PASTA_PROJETO = Path(__file__).resolve().parent
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def imagem_para_base64(caminho):
    """Retorna uma imagem local como data URI, ou None se não existir."""
    import mimetypes

    caminho = Path(caminho)
    if not caminho.is_file():
        return None
    tipo = mimetypes.guess_type(caminho.name)[0] or "application/octet-stream"
    conteudo = base64.b64encode(caminho.read_bytes()).decode("ascii")
    return f"data:{tipo};base64,{conteudo}"


def payload_inicial():
    return {
        "cabecalhos": list(dados.CABECALHOS),
        "registros": enriquecer_registros(dados.REGISTROS),
        "arquivo": dados.localizar_planilha().name if dados.REGISTROS else "",
    }


def carregar_dados(contents, filename):
    """Valida um upload e mantém a base anterior quando o arquivo é inválido."""
    if not contents:
        raise PreventUpdate
    if not filename or Path(filename).suffix.lower() != ".xlsx":
        return no_update, dbc.Alert("Envie uma planilha no formato .xlsx.", color="warning")
    try:
        _, encoded = contents.split(",", 1)
        if len(encoded) > ((MAX_UPLOAD_BYTES + 2) // 3) * 4:
            raise ValueError("A planilha deve ter até 10 MB.")
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_UPLOAD_BYTES:
            raise ValueError("A planilha deve ter até 10 MB.")
        cabecalhos, registros = dados.carregar_planilha(io.BytesIO(raw))
        if not registros:
            raise ValueError("A planilha não contém registros de barragens.")
        colunas = dados.identificar_colunas(cabecalhos)
        if {"latitude", "longitude"}.issubset({dados.normalizar(c) for c in cabecalhos}) and not any(colunas.get(c) for c in ("empreendedores", "estados", "municipios", "trabalhadores", "comunidade")):
            raise ValueError("Esta é uma planilha complementar de coordenadas. Envie a planilha principal de barragens para atualizar a base do estudo.")
    except (ValueError, binascii.Error, BadZipFile, InvalidFileException, KeyError, OSError, ParseError) as erro:
        return no_update, dbc.Alert(f"Não foi possível ler a planilha: {erro}", color="danger")
    registros = enriquecer_registros(registros)
    payload = {"cabecalhos": cabecalhos, "registros": registros, "arquivo": Path(filename).name}
    return payload, dbc.Alert(f"{Path(filename).name}: {len(registros)} registros carregados.", color="success")


def texto_valor(valor):
    return "" if valor is None else str(valor).strip()


def opcoes_coluna(registros, coluna):
    valores = {texto_valor(r.get(coluna)) for r in registros} if coluna else set()
    return [{"label": valor, "value": valor} for valor in sorted(valores - {""}, key=dados.normalizar)]


def filtrar_dados(payload, estados=None, municipios=None, empreendedores=None, busca=None):
    payload = payload or {}
    registros = payload.get("registros", [])
    colunas = dados.identificar_colunas(payload.get("cabecalhos", []))
    filtros = [("estados", estados), ("municipios", municipios), ("empreendedores", empreendedores)]
    termo = dados.normalizar(busca)
    resultado = []
    for registro in registros:
        if any(valores and texto_valor(registro.get(colunas.get(chave))) not in valores for chave, valores in filtros):
            continue
        if termo and not any(termo in dados.normalizar(valor) for valor in registro.values()):
            continue
        resultado.append(registro)
    return resultado


def cards_indicadores(registros, colunas, base=None):
    base = registros if base is None else base
    indicadores = dados.calcular_indicadores(registros, colunas)
    itens = [
        ("Barragens", indicadores["barragens"]),
        ("Empreendedores", indicadores["empreendedores"]),
        ("Municípios", indicadores["municipios"]),
        ("Estados", indicadores["estados"]),
    ]
    coluna_trabalhadores = colunas.get("trabalhadores")
    categorica = any(dados.normalizar(r.get(coluna_trabalhadores)) in {"sim", "nao", "s", "n", "yes", "no", "true", "false"} for r in base)
    trabalhadores = dados.contar_respostas_sim(registros, coluna_trabalhadores) if categorica else None
    if categorica:
        valor = 0 if not registros else trabalhadores
        itens.append(("Barragens com trabalhadores na ZAS", dados.formatar_numero(valor)))
    else:
        itens.append(("Trabalhadores (quantidade informada)", indicadores["trabalhadores"]))
    comunidades = dados.contar_respostas_sim(registros, colunas.get("comunidade"))
    if not registros and dados.contar_respostas_sim(base, colunas.get("comunidade")) is not None:
        comunidades = 0
    itens.append(("Barragens com comunidade na ZAS", dados.formatar_numero(comunidades)))
    return [
        html.Div([html.Div(valor, className="indicador-valor"), html.Div(rotulo, className="indicador-rotulo")], className="indicador")
        for rotulo, valor in itens
    ]


def grafico_distribuicao(registros, colunas):
    chave = "estados" if colunas.get("estados") else "empreendedores"
    coluna = colunas.get(chave)
    rotulo = "estado" if chave == "estados" else "empreendedor"
    grupos = {}
    for registro in registros:
        grupo = texto_valor(registro.get(coluna)) if coluna else ""
        grupo = grupo or "Não informado"
        grupos.setdefault(grupo, []).append(registro)
    contagens = Counter({grupo: int(dados.calcular_indicadores(linhas, colunas)["barragens"].replace(".", "")) for grupo, linhas in grupos.items()}) if colunas.get("id") or colunas.get("barragens") else Counter()
    principais = list(reversed(contagens.most_common(10)))
    fig = go.Figure(go.Bar(
        x=[quantidade for _, quantidade in principais],
        y=[nome for nome, _ in principais], orientation="h", marker_color=VERDE,
        hovertemplate="%{y}<br>%{x} barragens<extra></extra>",
    ))
    fig.update_layout(
        title={"text": f"Barragens por {rotulo}", "font": {"size": 16}},
        template="plotly_white", height=390, margin=dict(l=10, r=20, t=60, b=30),
        xaxis_title="Barragens", yaxis_title=None,
    )
    if not registros:
        fig.add_annotation(text="Nenhum registro para os filtros selecionados", x=.5, y=.5, xref="paper", yref="paper", showarrow=False)
    return fig


def atualizar_painel(payload, estados, municipios, empreendedores, busca):
    payload = payload or {}
    colunas = dados.identificar_colunas(payload.get("cabecalhos", []))
    registros = filtrar_dados(payload, estados, municipios, empreendedores, busca)
    cabecalhos = list(payload.get("cabecalhos", []))
    for coluna in ("Latitude", "Longitude"):
        if any(coluna in registro for registro in registros) and coluna not in cabecalhos:
            cabecalhos.append(coluna)
    return (
        cards_indicadores(registros, colunas, payload.get("registros", [])), grafico_distribuicao(registros, colunas),
        registros, [{"name": c, "id": c} for c in cabecalhos],
        f"{len(registros)} de {len(payload.get('registros', []))} registros",
        mapa_barragens(registros),
    )


def baixar_csv(n_clicks, payload, estados, municipios, empreendedores, busca):
    if not n_clicks:
        raise PreventUpdate
    payload = payload or {}
    registros = filtrar_dados(payload, estados, municipios, empreendedores, busca)
    cabecalhos = list(payload.get("cabecalhos", []))
    if not cabecalhos:
        raise PreventUpdate
    cabecalhos = list(dict.fromkeys(cabecalhos + [c for r in payload.get("registros", []) for c in r]))
    buffer = io.StringIO()
    buffer.write("\ufeff")
    # Evita que textos sejam interpretados como fórmulas ao abrir o CSV no Excel.
    def celula_csv(valor):
        if isinstance(valor, str) and valor.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + valor
        return valor

    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([celula_csv(coluna) for coluna in cabecalhos])
    for registro in registros:
        writer.writerow([celula_csv(registro.get(coluna)) for coluna in cabecalhos])
    return dcc.send_string(buffer.getvalue(), "barragens_filtradas.csv", type="text/csv;charset=utf-8")



app = Dash(__name__, assets_folder=str(PASTA_PROJETO / "assets"))
app.title = "ZAS · Inteligência territorial"
server = app.server
server.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def criar_layout():
    inicial = payload_inicial()
    aviso = f"{len(inicial['registros'])} registros na base · filtros aplicados a todos os módulos." if inicial["registros"] else getattr(dados, "ERRO_DADOS", None) or "Envie a planilha principal de barragens para começar."
    nav = [dcc.Link([html.Span(icone, className="nav-icon", **{"aria-hidden": "true"}), html.Span(nome)], href=f"/plataforma/{chave}", id=f"nav-{chave}", className="nav-link") for chave, (nome, _, icone) in MODULOS.items()]
    return html.Div([
        dcc.Location(id="url", refresh=False), dcc.Store(id="dados-store", data=inicial),
        dcc.Download(id="download-csv"),
        html.Div(pagina_inicial(), id="landing-container"),
        html.Div([
            html.Aside([
                marca(href="/", className="sidebar-brand"),
                html.P("ANÁLISES DO ESTUDO", className="sidebar-caption"),
                html.Nav(nav, className="sidebar-nav", **{"aria-label": "Módulos da plataforma"}),
                html.Div([html.Span("BASES DO ESTUDO", className="eyebrow"), html.P("Exploração com rastreabilidade de evidências."), dcc.Link("Voltar à entrada ↗", href="/", className="sidebar-home")], className="sidebar-bottom"),
            ], className="sidebar"),
            html.Div([
                html.Header([
                    html.Div([html.H2(id="pagina-titulo", className="topbar-title"), html.P(id="pagina-descricao")]),
                    html.Div([html.Span("●", className="status-dot"), html.Span("Ambiente de consulta")], className="topbar-meta"),
                ], className="topbar"),
                html.Div([
                    html.Div([
                        html.Div([html.Span("RECORTE DA ANÁLISE", className="eyebrow"), html.P("Os filtros acompanham a navegação entre os módulos.")]),
                        html.Div([
                            html.Button("Limpar filtros", id="limpar-filtros", n_clicks=0, className="button button-light"),
                            dcc.Upload(id="upload-planilha", children=html.Button("Atualizar base XLSX", className="button button-secondary"), accept=".xlsx", multiple=False),
                        ], className="toolbar-actions"),
                    ], className="toolbar"),
                    html.Div([
                        html.Div([html.Label("Estado", htmlFor="filtro-estado"), dcc.Dropdown(id="filtro-estado", multi=True, placeholder="Todos os estados")], className="filter-field"),
                        html.Div([html.Label("Município", htmlFor="filtro-municipio"), dcc.Dropdown(id="filtro-municipio", multi=True, placeholder="Todos os municípios")], className="filter-field"),
                        html.Div([html.Label("Empreendedor", htmlFor="filtro-empreendedor"), dcc.Dropdown(id="filtro-empreendedor", multi=True, placeholder="Todos os empreendedores")], className="filter-field"),
                        html.Div([html.Label("Buscar na base", htmlFor="busca"), dcc.Input(id="busca", type="search", placeholder="Nome, ID ou outro campo", debounce=True)], className="filter-field"),
                    ], className="filter-grid"),
                    html.Div(dbc.Alert(aviso, color="info"), id="mensagem-dados", className="data-status"),
                    html.Div(id="aviso-colunas"),
                ], className="filter-container"),
                html.Main([
                    *criar_paginas(),
                    html.Section([html.H1("Página não encontrada"), dcc.Link("Voltar ao panorama", href="/plataforma/panorama", className="button button-primary")], id="pagina-inexistente", className="page-content"),
                ], className="platform-main"),
                html.Footer("ZAS · Inteligência territorial | Indicadores descritivos das bases disponibilizadas. Campos ausentes aparecem como —.", className="platform-footer"),
            ], className="app-body"),
        ], id="platform-container", className="app-shell", style={"display": "none"}),
    ])


app.layout = criar_layout


@app.callback(
    Output("landing-container", "style"), Output("platform-container", "style"),
    Output("pagina-titulo", "children"), Output("pagina-descricao", "children"),
    *[Output(f"pagina-{chave}", "style") for chave in MODULOS],
    Output("pagina-inexistente", "style"),
    *[Output(f"nav-{chave}", "className") for chave in MODULOS],
    Input("url", "pathname"),
)
def navegar(pathname):
    pathname = (pathname or "/").rstrip("/") or "/"
    entrada = pathname == "/"
    chave = "panorama" if pathname == "/plataforma" else pathname.removeprefix("/plataforma/")
    valida = not entrada and pathname.startswith("/plataforma") and chave in MODULOS
    nome, descricao, _ = MODULOS[chave] if valida else ("Página não encontrada", "", "")
    return (
        {} if entrada else {"display": "none"}, {"display": "none"} if entrada else {}, nome, descricao,
        *[{} if valida and pagina == chave else {"display": "none"} for pagina in MODULOS],
        {"display": "none"} if valida or entrada else {},
        *["nav-link active" if valida and pagina == chave else "nav-link" for pagina in MODULOS],
    )


app.callback(Output("dados-store", "data"), Output("mensagem-dados", "children"), Input("upload-planilha", "contents"), State("upload-planilha", "filename"), prevent_initial_call=True)(carregar_dados)


@app.callback(
    Output("filtro-estado", "options"), Output("filtro-municipio", "options"), Output("filtro-empreendedor", "options"),
    Output("filtro-estado", "value"), Output("filtro-municipio", "value"), Output("filtro-empreendedor", "value"),
    Output("filtro-estado", "disabled"), Output("filtro-municipio", "disabled"), Output("filtro-empreendedor", "disabled"),
    Output("aviso-colunas", "children"), Output("busca", "value"),
    Input("dados-store", "data"), Input("limpar-filtros", "n_clicks"),
)
def atualizar_filtros(payload, limpar=0):
    payload = payload or {}
    colunas = dados.identificar_colunas(payload.get("cabecalhos", []))
    registros = payload.get("registros", [])
    chaves = ("estados", "municipios", "empreendedores")
    ausentes = [rotulo for chave, rotulo in [("estados", "estado"), ("municipios", "município")] if not colunas.get(chave)]
    aviso = html.P("A base carregada não informa " + " e ".join(ausentes) + ". Os filtros territoriais correspondentes ficam indisponíveis.", className="info-note") if ausentes else None
    return (*[opcoes_coluna(registros, colunas.get(chave)) for chave in chaves], [], [], [], *[not bool(colunas.get(chave)) for chave in chaves], aviso, "")


def fontes_resumo(payload, registros, colunas):
    com_fonte = sum(bool(texto_valor(r.get("Fonte"))) for r in registros)
    return [
        html.Section([
            html.H3("Bases disponibilizadas"),
            html.Dl([html.Dt("Base principal"), html.Dd(payload.get("arquivo") or "Nenhuma base carregada"), html.Dt("Localização"), html.Dd("CSV de coordenadas associado pelo ID da barragem"), html.Dt("Fontes e observações"), html.Dd(f"{com_fonte} de {len(registros)} registros com fonte da coordenada informada")]),
            html.P("A planilha complementar registra o status, a fonte e a observação de cada localização. O detalhe da estrutura permite abrir a fonte indicada.", className="info-note"),
        ], className="panel"),
        html.Section([
            html.H3("Como os indicadores são calculados"),
            html.Ul([html.Li("Barragens: IDs distintos; nomes e contexto territorial são usados quando não há ID."), html.Li("Municípios: nomes distintos por Estado, quando essas colunas existem."), html.Li("Trabalhadores e comunidade: respostas da planilha. Sim/Não expressa presença, sem quantificar pessoas."), html.Li("Coordenadas: pares válidos associados pelo ID; pontos ausentes não são estimados."), html.Li("Valores monetários: somas dos campos explicitamente informados na base. Sem campo, o indicador fica —.")]),
        ], className="panel"),
    ]


@app.callback(
    Output("indicadores-panorama", "children"), Output("grafico-estados", "figure"),
    Output("tabela-registros", "data"), Output("tabela-registros", "columns"), Output("contagem-registros", "children"),
    Output("indicadores-economia", "children"), Output("tabela-empreendedores", "data"),
    Output("resumo-panorama", "children"), Output("nota-trabalhadores", "children"),
    Output("indicadores-fiscal", "children"), Output("indicadores-logistica", "children"), Output("fontes-resumo", "children"),
    Input("dados-store", "data"), Input("filtro-estado", "value"), Input("filtro-municipio", "value"), Input("filtro-empreendedor", "value"), Input("busca", "value"),
)
def atualizar_dashboard(payload, estados, municipios, empreendedores, busca):
    payload = payload or {}
    base = payload.get("registros", [])
    colunas = dados.identificar_colunas(payload.get("cabecalhos", []))
    registros = filtrar_dados(payload, estados, municipios, empreendedores, busca)
    m = metricas(registros, colunas, base)
    headers = list(dict.fromkeys(payload.get("cabecalhos", []) + [c for r in base for c in r]))
    economia = [cartao("Empreendedores", m["empreendedores"], icone="▦"), cartao("Barragens com trabalhadores na ZAS", m["presenca_trabalhadores"], "Resposta Sim na base", "♧"), cartao("Barragens com comunidade na ZAS", m["comunidade"], "Resposta Sim na base", "⌖"), cartao("Trabalhadores · quantidade informada", m["trabalhadores"], "Quantidade de pessoas", "♧"), cartao("Atividades econômicas", m["atividades"], "Identificação na base", "↗"), cartao("Exportações", m["exportacoes"], "Valor e unidade conforme base", "⇄")]
    resumo = html.Div([cartao("Empreendedores", m["empreendedores"], icone="▦"), cartao("Barragens localizadas", m["localizadas"], "Pares de coordenadas válidos", "⌖"), cartao("Com trabalhadores na ZAS", m["presenca_trabalhadores"], "Barragens com resposta Sim", "♧"), cartao("Com comunidade na ZAS", m["comunidade"], "Barragens com resposta Sim", "⌘")], className="summary-grid")
    nota = "A coluna TrabalhadoresZAS da base registra Sim/Não. A contagem se refere a barragens com presença de trabalhadores; a quantidade de pessoas potencialmente afetadas não foi disponibilizada." if trabalhadores_categoricos(base, colunas) else "Quantidades são somadas somente quando a coluna da base fornece valores numéricos. O período e a abrangência devem ser interpretados conforme a fonte."
    fiscal = [cartao("CFEM relacionada", m["cfem"], "Valor informado na base (R$)", "▥"), cartao("Receitas públicas", m["receitas"], "Valor informado na base (R$)", "▤"), cartao("Municípios de referência", m["municipios"], "Conforme base principal", "⌖")]
    logistica = [cartao("Barragens localizadas", m["localizadas"], "Localização disponível", "⌖"), cartao("Rodovias relacionadas", "—", "Camada não disponibilizada", "⇄"), cartao("Ferrovias relacionadas", "—", "Camada não disponibilizada", "⇄"), cartao("Instalações industriais", "—", "Camada não disponibilizada", "▦")]
    return (indicadores_panorama(registros, colunas, base), grafico_distribuicao(registros, colunas), registros, [{"name": c, "id": c} for c in headers], f"{len(registros)} de {len(base)} registros", economia, resumo_empreendedores(registros, colunas, base), resumo, nota, fiscal, logistica, fontes_resumo(payload, registros, colunas))


@app.callback(
    Output("mapa-barragens", "figure"), Output("barragem-selecionada", "options"), Output("comparar-escala", "options"), Output("comparar-escala", "value"),
    Input("dados-store", "data"), Input("filtro-estado", "value"), Input("filtro-municipio", "value"), Input("filtro-empreendedor", "value"), Input("busca", "value"), Input("camadas-mapa", "value"),
    State("comparar-escala", "value"),
)
def atualizar_territorio(payload, estados, municipios, empreendedores, busca, camadas, escala="barragens"):
    payload = payload or {}
    registros = filtrar_dados(payload, estados, municipios, empreendedores, busca)
    colunas = dados.identificar_colunas(payload.get("cabecalhos", []))
    camadas = camadas or []
    escalas = [{"label": nome, "value": chave, "disabled": not bool(colunas.get(chave) or chave == "barragens" and colunas.get("id"))} for chave, nome in [("barragens", "Barragem"), ("empreendedores", "Empreendedor"), ("estados", "Estado"), ("municipios", "Município")]]
    escala = escala if any(item["value"] == escala and not item["disabled"] for item in escalas) else "barragens"
    return mapa_barragens(registros, exibir_barragens="barragens" in camadas, exibir_contorno="contorno" in camadas), opcoes_comparacao(registros, colunas, "barragens"), escalas, escala


@app.callback(
    Output("barragem-selecionada", "value"), Input("mapa-barragens", "clickData"), Input("dados-store", "data"),
    Input("filtro-estado", "value"), Input("filtro-municipio", "value"), Input("filtro-empreendedor", "value"), Input("busca", "value"),
    prevent_initial_call=True,
)
def selecionar_barragem(click_data, payload, estados=None, municipios=None, empreendedores=None, busca=None):
    if ctx.triggered_id != "mapa-barragens":
        return None
    pontos = (click_data or {}).get("points", [])
    if not pontos:
        return no_update
    custom = pontos[0].get("customdata") or []
    if len(custom) < 3:
        return no_update
    chave = str(custom[2])
    colunas = dados.identificar_colunas((payload or {}).get("cabecalhos", []))
    return chave if any(chave_barragem(r, colunas) == chave for r in (payload or {}).get("registros", [])) else no_update


@app.callback(
    Output("detalhe-barragem", "children"), Input("barragem-selecionada", "value"), Input("dados-store", "data"),
    Input("filtro-estado", "value"), Input("filtro-municipio", "value"), Input("filtro-empreendedor", "value"), Input("busca", "value"),
)
def mostrar_detalhe(chave, payload, estados=None, municipios=None, empreendedores=None, busca=None):
    if not chave:
        return html.Div([html.H3("Escolha uma estrutura"), html.P("Clique em um ponto no mapa ou use a seleção acima para consultar os dados e as fontes.")], className="empty-state")
    payload = payload or {}
    colunas = dados.identificar_colunas(payload.get("cabecalhos", []))
    registros = filtrar_dados(payload, estados, municipios, empreendedores, busca)
    registro = next((r for r in registros if chave_barragem(r, colunas) == chave), None)
    return detalhe_estrutura(registro, colunas) if registro else html.P("Esta estrutura não está no recorte atual. Selecione outra barragem.", className="info-note")


@app.callback(
    Output("comparar-itens", "options"), Output("comparar-itens", "value"),
    Input("comparar-escala", "value"), Input("dados-store", "data"), Input("filtro-estado", "value"), Input("filtro-municipio", "value"), Input("filtro-empreendedor", "value"), Input("busca", "value"),
    Input("comparar-itens", "value"),
)
def atualizar_opcoes_comparacao(escala, payload, estados, municipios, empreendedores, busca, selecionados):
    payload = payload or {}
    colunas = dados.identificar_colunas(payload.get("cabecalhos", []))
    registros = filtrar_dados(payload, estados, municipios, empreendedores, busca)
    opcoes = opcoes_comparacao(registros, colunas, escala)
    validos = {item["value"] for item in opcoes}
    selecionados = [item for item in (selecionados or []) if item in validos][:4]
    return opcoes, selecionados


@app.callback(
    Output("resultado-comparacao", "children"), Input("comparar-itens", "value"), Input("comparar-escala", "value"), Input("dados-store", "data"),
    Input("filtro-estado", "value"), Input("filtro-municipio", "value"), Input("filtro-empreendedor", "value"), Input("busca", "value"),
)
def comparar_grupos(itens, escala, payload, estados, municipios, empreendedores, busca):
    if not itens:
        return html.Div([html.H3("Monte sua comparação"), html.P("Escolha a escala e selecione até quatro estruturas ou grupos. As métricas serão apresentadas lado a lado.")], className="empty-state")
    payload = payload or {}
    colunas = dados.identificar_colunas(payload.get("cabecalhos", []))
    registros = filtrar_dados(payload, estados, municipios, empreendedores, busca)
    labels = {o["value"]: o["label"] for o in opcoes_comparacao(registros, colunas, escala)}
    cards = []
    for item in itens[:4]:
        linhas = selecionar_grupo(registros, colunas, escala, item)
        if item not in labels:
            continue
        m = metricas(linhas, colunas, payload.get("registros", []))
        campos = [("Barragens", "barragens"), ("Empreendedores", "empreendedores"), ("Municípios", "municipios"), ("Estados", "estados"), ("Barragens localizadas", "localizadas"), ("Com trabalhadores na ZAS", "presenca_trabalhadores"), ("Com comunidade na ZAS", "comunidade"), ("Trabalhadores · quantidade", "trabalhadores"), ("CFEM (R$)", "cfem")]
        cards.append(html.Section([html.Span("GRUPO SELECIONADO", className="eyebrow"), html.H3(labels[item]), html.Dl([html.Div([html.Dt(label), html.Dd(m[chave])], className="comparison-row") for label, chave in campos])], className="comparison-card"))
    return cards


app.callback(
    Output("download-csv", "data"), Input("baixar-csv", "n_clicks"),
    State("dados-store", "data"), State("filtro-estado", "value"), State("filtro-municipio", "value"), State("filtro-empreendedor", "value"), State("busca", "value"), prevent_initial_call=True,
)(baixar_csv)


if __name__ == "__main__":
    app.run(host=os.environ.get("ZAS_HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8050")), debug=False)
