"""Componentes visuais e módulos da plataforma; sem estado compartilhado de sessão."""

from dash import dcc, html, dash_table
import dados
from analises import metricas, chave_barragem, texto


MODULOS = {
    "panorama": ("Panorama geral", "Visão consolidada das bases do estudo", "▦"),
    "territorio": ("Explorador territorial", "Localização, seleção e detalhamento das barragens", "⌖"),
    "economia": ("Economia e trabalho", "Empreendimentos, trabalhadores e comunidades", "♧"),
    "fiscal": ("Fiscal e CFEM", "Receitas públicas e compensações financeiras", "▥"),
    "logistica": ("Logística", "Infraestrutura e conexões territoriais", "⇄"),
    "cenarios": ("Cenários", "Resultados de modelagens e premissas do estudo", "▤"),
    "comparacao": ("Comparação", "Comparação entre estruturas e escalas disponíveis", "⇆"),
    "evidencias": ("Dados e evidências", "Bases, qualidade, fontes e exportação", "≡"),
}


def titulo(titulo, descricao=None):
    return html.Div([html.H2(titulo), html.P(descricao) if descricao else None], className="section-heading")


def cartao(rotulo, valor, nota=None, icone="▦"):
    return html.Div([
        html.Div(icone, className="metric-icon", **{"aria-hidden": "true"}),
        html.Div([html.Div(rotulo, className="metric-label"), html.Div(valor, className="metric-value"), html.Div(nota, className="metric-note") if nota else None]),
    ], className="metric-card", **{"data-indicador": rotulo})


def indicadores_panorama(registros, colunas, base):
    m = metricas(registros, colunas, base)
    itens = [
        ("Barragens analisadas", "barragens", "Identificadas por ID", "▦"),
        ("ZAS avaliadas", "zas", "Requer identificação de cada ZAS", "⌘"),
        ("Municípios", "municipios", "Conforme coluna da base", "⌖"),
        ("Estados", "estados", "Conforme coluna da base", "◫"),
        ("Trabalhadores potencialmente afetados", "trabalhadores", "Quantidade de pessoas", "♧"),
        ("Produção associada", "producao", "Valor informado na base (R$)", "↗"),
        ("CFEM relacionada", "cfem", "Valor informado na base (R$)", "▥"),
        ("Receitas públicas", "receitas", "Valor informado na base (R$)", "▤"),
    ]
    return [cartao(label, m[chave], nota, icone) for label, chave, nota, icone in itens]


def tabela(id, colunas=None, dados_tabela=None):
    return dash_table.DataTable(
        id=id, columns=[{"name": c, "id": c} for c in (colunas or [])], data=dados_tabela or [],
        page_size=10, sort_action="native", style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "fontFamily": "inherit", "padding": "14px 12px", "fontSize": "13px", "minWidth": "100px", "maxWidth": "320px", "whiteSpace": "normal"},
        style_header={"backgroundColor": "#f0f5f7", "color": "#334d59", "fontWeight": "600", "border": "1px solid #e2e9ed"},
        style_data={"border": "1px solid #edf1f3"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#f8fafb"}],
    )


def indisponivel(titulo_texto, descricao, campos):
    return html.Div([
        html.Span("Base a incorporar", className="chip chip-pending"), html.H3(titulo_texto),
        html.P(descricao), html.Ul([html.Li(campo) for campo in campos]),
    ], className="empty-state")


def criar_paginas():
    return [
        html.Section([
            html.Div([html.Span("PANORAMA DO ESTUDO", className="eyebrow"), html.H1("Inteligência territorial das ZAS"), html.P("Visão geral para explorar barragens, territórios, trabalho, economia e receitas públicas."), dcc.Link("Explorar o território →", href="/plataforma/territorio", className="button button-primary")], className="page-hero"),
            html.Div([
                titulo("Indicadores consolidados", "Valores calculados a partir da seleção atual. — indica informação não disponibilizada."),
                html.Div(id="indicadores-panorama", className="metric-grid"),
                html.Div([
                    html.Section([titulo("Distribuição das barragens", "Até 10 maiores grupos da base carregada."), dcc.Graph(id="grafico-estados", responsive=True, config={"displayModeBar": False})], className="panel"),
                    html.Section([titulo("Economia e trabalho", "O que a planilha permite observar."), html.Div(id="resumo-panorama"), dcc.Link("Consultar economia e trabalho →", href="/plataforma/economia", className="text-link")], className="panel"),
                ], className="panels-grid"),
                html.Section([titulo("Do panorama ao detalhe", "Uma exploração progressiva das evidências."), html.Div([
                    html.Div([html.Span("01", className="step-number"), html.H3("Visão geral"), html.P("Observe a dimensão e a disponibilidade das bases.")], className="module-card"),
                    html.Div([html.Span("02", className="step-number"), html.H3("Filtro"), html.P("Recorte por território, empreendedor ou estrutura.")], className="module-card"),
                    html.Div([html.Span("03", className="step-number"), html.H3("Comparação"), html.P("Compare até quatro grupos com as mesmas métricas."), dcc.Link("Comparar →", href="/plataforma/comparacao", className="text-link")], className="module-card"),
                    html.Div([html.Span("04", className="step-number"), html.H3("Detalhamento"), html.P("Consulte registros, fontes e observações."), dcc.Link("Ver evidências →", href="/plataforma/evidencias", className="text-link")], className="module-card"),
                ], className="module-grid")], className="panel"),
            ], className="page-content"),
        ], id="pagina-panorama"),
        html.Section([
            titulo("Explorador territorial das ZAS", "Selecione uma barragem pelo mapa ou pelo nome para consultar suas evidências."),
            html.Div([
                html.Aside([
                    html.H3("Camadas territoriais"),
                    dcc.Checklist(id="camadas-mapa", options=[{"label": "Barragens", "value": "barragens"}, {"label": "Contorno do Brasil", "value": "contorno"}], value=["barragens", "contorno"], className="layer-list"),
                    html.H4("Camadas a incorporar"),
                    html.Ul([html.Li(item) for item in ["Delimitação das ZAS", "Áreas de lavra e beneficiamento", "Rejeitos e estéril", "Instalações industriais", "Rodovias e ferrovias", "Municípios e núcleos populacionais", "Atividades econômicas"]], className="pending-layers"),
                    html.P("As bases fornecidas contêm pontos de barragens. Delimitações de ZAS e demais camadas ainda não foram disponibilizadas.", className="info-note"),
                ], className="panel layer-panel"),
                html.Section([dcc.Graph(id="mapa-barragens", responsive=True, style={"height": "520px", "width": "100%"}, config={"displaylogo": False, "scrollZoom": True}), html.P("Contorno geográfico de referência. Use a barra do mapa para aproximar ou selecionar pontos; clique em uma barragem para detalhar.", className="info-note")], className="panel map-panel"),
            ], className="territory-grid"),
            html.Section([
                titulo("Detalhamento da estrutura", "Inclui as barragens que ainda estão sem coordenadas."),
                dcc.Dropdown(id="barragem-selecionada", placeholder="Selecione uma barragem", clearable=True),
                html.Div(id="detalhe-barragem"),
            ], className="panel"),
        ], id="pagina-territorio", className="page-content"),
        html.Section([
            titulo("Economia e trabalho", "Relações entre empreendimentos, presença de trabalhadores e comunidades na ZAS."),
            html.Div(id="indicadores-economia", className="metric-grid"),
            html.Div(id="nota-trabalhadores", className="info-note"),
            html.Section([titulo("Empreendedores da seleção", "Agregação descritiva por empreendedor, sem estimar pessoas ou impactos monetários."), tabela("tabela-empreendedores", ["Empreendedor", "Barragens", "Com trabalhadores na ZAS", "Com comunidade na ZAS", "Localizadas"])], className="panel table-wrap"),
            indisponivel("Resultados econômicos do estudo", "Valores de produção, exportações e atividades econômicas poderão ser apresentados quando as respectivas bases forem incorporadas e validadas.", ["Quantidade de trabalhadores e período de referência", "Atividades econômicas e identificação dos estabelecimentos", "Produção e exportações com unidades e recortes territoriais"]),
        ], id="pagina-economia", className="page-content"),
        html.Section([
            titulo("Fiscal e CFEM", "Receitas públicas e compensações financeiras relacionadas ao estudo."),
            html.Div(id="indicadores-fiscal", className="metric-grid"),
            indisponivel("Base fiscal do estudo", "A base de barragens fornecida não informa valores fiscais. A relação entre arrecadação e ZAS exige critérios territoriais e validação específica.", ["Arrecadação da CFEM e período", "Receitas tributárias e municípios de referência", "Critérios de atribuição, fonte e metodologia"]),
        ], id="pagina-fiscal", className="page-content"),
        html.Section([
            titulo("Logística e infraestrutura", "Conexões territoriais entre empreendimentos e infraestrutura."),
            html.Div(id="indicadores-logistica", className="metric-grid"),
            indisponivel("Camadas de infraestrutura", "Os pontos de barragens estão disponíveis para exploração. As interseções territoriais dependerão das camadas de infraestrutura e dos limites das ZAS.", ["Vias rodoviárias e ferrovias", "Instalações industriais e unidades de beneficiamento", "Áreas de disposição de rejeitos e estéril", "Infraestrutura logística e delimitações das ZAS"]),
            dcc.Link("Consultar a localização das barragens →", href="/plataforma/territorio", className="button button-secondary"),
        ], id="pagina-logistica", className="page-content"),
        html.Section([
            titulo("Cenários e modelagens", "Comparação de resultados, premissas e horizontes do estudo."),
            indisponivel("Resultados de cenários", "Modelagens econômicas, análises de custo-benefício e avaliações multicritério ainda não foram fornecidas. Os resultados serão vinculados a premissas, período, unidades e validação técnica.", ["Cenário de referência e alternativas", "Hipóteses, parâmetros e intervalo temporal", "Resultados dos modelos e incertezas", "Responsável e registro da validação humana"]),
            html.Section([html.H3("Comparações disponíveis agora"), html.P("Compare barragens e empreendedores com os indicadores descritivos já carregados."), dcc.Link("Abrir comparação →", href="/plataforma/comparacao", className="button button-primary")], className="panel"),
        ], id="pagina-cenarios", className="page-content"),
        html.Section([
            titulo("Comparação", "Selecione até quatro estruturas ou grupos dentro do recorte atual."),
            html.Section([
                html.Div([html.Label("Escala de comparação"), dcc.Dropdown(id="comparar-escala", value="barragens", clearable=False)], className="filter-field"),
                html.Div([html.Label("Estruturas ou grupos"), dcc.Dropdown(id="comparar-itens", multi=True, placeholder="Selecione os grupos a comparar")], className="filter-field"),
            ], className="panel comparison-controls"),
            html.Div(id="resultado-comparacao", className="comparison-grid"),
            html.P("Comparações descritivas da mesma base e do mesmo recorte. Informação ausente aparece como —; períodos e unidades de bases futuras precisam ser compatíveis.", className="info-note"),
        ], id="pagina-comparacao", className="page-content"),
        html.Section([
            titulo("Dados e evidências", "Consulte a base, identifique lacunas e acompanhe a origem dos registros."),
            html.Div(id="fontes-resumo", className="panels-grid"),
            html.Section([
                html.Div([html.H3("Base consolidada da seleção"), html.Span(id="contagem-registros"), html.Button("Exportar seleção CSV", id="baixar-csv", className="button button-primary", n_clicks=0)], className="table-heading"),
                tabela("tabela-registros"),
            ], className="panel table-wrap"),
            html.Section([titulo("Arquitetura de evolução do estudo", "Fluxo de referência para incorporar novas informações."), html.Div([
                html.Div([html.H4("01 · Fontes"), html.P("ANM, IBRAM, empresas, IBGE, MTE, MDIC, STN e bases territoriais, conforme disponibilização.")], className="module-card"),
                html.Div([html.H4("02 · Tratamento"), html.P("Padronização de cabeçalhos, integração por ID e validação de coordenadas nesta versão.")], className="module-card"),
                html.Div([html.H4("03 · Análise"), html.P("Indicadores e comparações descritivas disponíveis; modelagens dependem dos resultados do estudo.")], className="module-card"),
                html.Div([html.H4("04 · IA e validação humana"), html.P("Busca semântica e consulta assistida previstas. Modelos e validações técnicas a incorporar.")], className="module-card"),
            ], className="module-grid"), html.P("A configuração dos públicos autorizados e do controle de acesso será necessária para disponibilizar bases confidenciais. Esta versão é um ambiente de consulta local.", className="info-note")], className="panel"),
        ], id="pagina-evidencias", className="page-content"),
    ]


def detalhe_estrutura(registro, colunas):
    nome = texto(registro.get(colunas.get("barragens"))) or "Barragem"
    fonte = texto(registro.get("Fonte"))
    fonte_componente = html.A("Consultar fonte da coordenada ↗", href=fonte, target="_blank", rel="noopener noreferrer", className="text-link") if fonte.startswith(("https://", "http://")) else html.Span(fonte or "Fonte da coordenada não disponibilizada")
    campos = [("ID da barragem", registro.get(colunas.get("id"))), ("Empreendedor", registro.get(colunas.get("empreendedores"))), ("Município", registro.get(colunas.get("municipios"))), ("Estado", registro.get(colunas.get("estados"))), ("Trabalhadores na ZAS · resposta da base", registro.get(colunas.get("trabalhadores"))), ("Comunidade na ZAS · resposta da base", registro.get(colunas.get("comunidade"))), ("Latitude", registro.get("Latitude")), ("Longitude", registro.get("Longitude"))]
    return html.Div([
        html.Div([html.H3(nome), html.Span(texto(registro.get("Status")) or "Status da coordenada não informado", className="chip chip-success" if registro.get("Latitude") is not None else "chip chip-pending")], className="table-heading"),
        html.Div([html.Div([html.Span(label, className="metric-label"), html.Strong(texto(valor) or "—")], className="detail-item") for label, valor in campos], className="detail-grid"),
        html.Div([html.H4("Rastreabilidade da localização"), fonte_componente, html.P(texto(registro.get("Observação")) or "Sem observação adicional na fonte.")], className="source-list"),
        html.P("Os valores Sim/Não indicam presença. Não representam uma quantidade de pessoas. O status e a observação são os declarados na planilha de coordenadas.", className="info-note"),
    ], className="detail-card")
