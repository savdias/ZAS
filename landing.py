"""Página de entrada e apresentação do estudo territorial das ZAS."""

from dash import dcc, html


def marca(href="/", className=""):
    """Marca textual acessível, compartilhada entre a entrada e a plataforma."""
    return dcc.Link(
        [html.Strong("ZAS"), html.Span("Inteligência territorial")],
        href=href,
        className=f"brand {className}".strip(),
        title="ZAS — página inicial",
    )


def _objetivo(numero, titulo, descricao):
    return html.Article(
        [html.Span(numero, className="purpose-number"), html.H3(titulo), html.P(descricao)],
        className="purpose-card",
    )


def _etapa(numero, titulo, descricao):
    return html.Li(
        [html.Span(numero, className="flow-number"), html.H3(titulo), html.P(descricao)],
        className="flow-step",
    )


def pagina_inicial():
    """Apresenta o estudo e conduz à exploração das bases disponíveis."""
    return html.Div(
        [
            html.A("Ir para o conteúdo", href="#conteudo-inicial", className="skip-link"),
            html.Section(
                [
                    html.Header(
                        [
                            marca(),
                            html.Nav(
                                [
                                    html.A("Sobre o estudo", href="#sobre-estudo"),
                                    html.A("O que é ZAS", href="#o-que-e-zas"),
                                    dcc.Link(
                                        "Acessar plataforma",
                                        href="/plataforma/panorama",
                                        className="button button-outline",
                                    ),
                                ],
                                className="landing-nav",
                                **{"aria-label": "Navegação inicial"},
                            ),
                        ],
                        className="landing-header",
                    ),
                    html.Div(
                        [
                            html.P("Estudo territorial · econômico · social", className="eyebrow"),
                            html.H1(
                                [
                                    "Impactos socioeconômicos e territoriais nas ",
                                    html.Span("Zonas de Autossalvamento"),
                                ]
                            ),
                            html.P(
                                "Uma plataforma integrada para compreender a relação entre barragens de mineração, "
                                "território, trabalho, atividade econômica, infraestrutura e receitas públicas.",
                                className="landing-lead",
                            ),
                            html.Div(
                                [
                                    dcc.Link(
                                        ["Acessar plataforma", html.Span("→", **{"aria-hidden": "true"})],
                                        href="/plataforma/panorama",
                                        className="button button-primary",
                                    ),
                                    html.A("Conheça o estudo", href="#sobre-estudo", className="button button-outline"),
                                ],
                                className="landing-actions",
                            ),
                        ],
                        className="landing-hero-content",
                        id="conteudo-inicial",
                    ),
                    html.Div(
                        [html.Span("Do panorama ao território"), html.Span("Visão geral", className="hero-step"), html.Span("Filtro", className="hero-step"), html.Span("Comparação", className="hero-step"), html.Span("Detalhamento", className="hero-step")],
                        className="hero-journey",
                        **{"aria-label": "Fluxo de exploração: visão geral, filtro, comparação e detalhamento"},
                    ),
                ],
                className="landing-hero",
            ),
            html.Main(
                [
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.P("Sobre o estudo", className="eyebrow"),
                                    html.H2("Evidências para compreender o território"),
                                ],
                                className="landing-section-title",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "A interface reúne os resultados do estudo das Zonas de Autossalvamento para apoiar "
                                        "a consulta e a análise técnica pelo IBRAM e pelos públicos definidos pelo Instituto."
                                    ),
                                    html.P(
                                        "A exploração começa com indicadores consolidados e permite avançar para filtros, "
                                        "comparações e informações de cada estrutura, preservando a identificação das fontes "
                                        "e dos dados disponíveis."
                                    ),
                                ],
                                className="landing-section-copy",
                            ),
                        ],
                        id="sobre-estudo",
                        className="landing-section study-intro",
                    ),
                    html.Section(
                        [
                            _objetivo("01", "Consultar e explorar", "Investigue as barragens e seus territórios em diferentes escalas, do panorama nacional à estrutura selecionada."),
                            _objetivo("02", "Comparar e aprofundar", "Compare empreendimentos, municípios e Estados com os mesmos critérios, sem manipular manualmente as bases."),
                            _objetivo("03", "Rastrear e atualizar", "Consulte a origem das informações e acompanhe a disponibilidade dos indicadores incorporados ao estudo."),
                        ],
                        className="purpose-grid",
                        **{"aria-label": "Objetivos da interface"},
                    ),
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.P("Explore a plataforma", className="eyebrow"),
                                    html.H2("Uma visão integrada, em diferentes escalas"),
                                    html.P("Os módulos acompanham as frentes analíticas do estudo."),
                                ],
                                className="landing-section-title",
                            ),
                            html.Div(
                                [
                                    dcc.Link(
                                        [
                                            html.Div([html.Span("01", className="module-number"), html.Span("Consultar →", className="module-cta")], className="module-card-top"),
                                            html.H3("Panorama geral das ZAS"),
                                            html.P("Indicadores consolidados, distribuição territorial e comparação das barragens na base do estudo."),
                                            html.Span("Visão geral · filtros · comparações", className="module-tags"),
                                        ],
                                        href="/plataforma/panorama",
                                        className="landing-module module-card",
                                    ),
                                    dcc.Link(
                                        [
                                            html.Div([html.Span("02", className="module-number"), html.Span("Explorar →", className="module-cta")], className="module-card-top"),
                                            html.H3("Explorador territorial das ZAS"),
                                            html.P("Mapa interativo das estruturas com coordenadas, seleção de barragens e consulta aos indicadores disponíveis."),
                                            html.Span("Mapa · seleção · detalhamento", className="module-tags"),
                                        ],
                                        href="/plataforma/territorio",
                                        className="landing-module module-card",
                                    ),
                                ],
                                className="landing-modules",
                            ),
                            html.Div(
                                [html.Span("Frentes analíticas", className="analytical-label"), html.Span("Economia e trabalho"), html.Span("Fiscal e CFEM"), html.Span("Logística"), html.Span("Cenários")],
                                className="analytical-fronts",
                            ),
                            html.P("Indicadores adicionais e camadas territoriais serão incorporados conforme a disponibilidade e a validação das respectivas bases.", className="landing-note"),
                        ],
                        className="landing-section platform-intro",
                    ),
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.P("Entenda o conceito", className="eyebrow"),
                                    html.H2(["O que é uma ", html.Span("ZAS?", className="text-teal")]),
                                    html.P(
                                        "A Zona de Autossalvamento é a porção do vale a jusante da barragem na qual "
                                        "o tempo de chegada de uma eventual onda de inundação não permite a intervenção "
                                        "das autoridades competentes em situação de emergência."
                                    ),
                                    html.P(
                                        "Neste estudo, o território é também analisado a partir de suas relações com o trabalho, "
                                        "a produção, a infraestrutura e as receitas públicas."
                                    ),
                                ],
                                className="zas-definition",
                            ),
                            html.Div(
                                [
                                    html.Span("Leitura territorial", className="eyebrow"),
                                    html.H3("Estrutura, território e suas conexões"),
                                    html.Div([html.Span("Barragem"), html.Span("→", **{"aria-hidden": "true"}), html.Span("ZAS"), html.Span("→", **{"aria-hidden": "true"}), html.Span("Território")], className="territory-chain"),
                                    html.P("As coordenadas identificam a localização das barragens. A delimitação de cada ZAS depende de uma camada territorial específica e validada."),
                                ],
                                className="zas-concept-card",
                            ),
                        ],
                        id="o-que-e-zas",
                        className="landing-section zas-section",
                    ),
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.P("Arquitetura do estudo", className="eyebrow"),
                                    html.H2("Da informação à consulta técnica"),
                                    html.P("Fluxo de referência para integrar as frentes do estudo e tornar as evidências rastreáveis."),
                                ],
                                className="landing-section-title",
                            ),
                            html.Ol(
                                [
                                    _etapa("01", "Fontes de dados", "ANM, IBRAM, empresas, IBGE, MTE, MDIC, STN e bases territoriais."),
                                    _etapa("02", "Ingestão e tratamento", "Padronização, integração, validação e controle de qualidade."),
                                    _etapa("03", "Base consolidada", "Território, trabalhadores, economia, fiscal, logística e cenários."),
                                    _etapa("04", "Camada analítica", "GIS, estatística, modelagem econômica e análises de decisão."),
                                    _etapa("05", "IA assistiva", "Busca e consulta assistidas, com implementação e validação futuras."),
                                    _etapa("06", "Validação humana", "Revisão das evidências pelos especialistas técnicos."),
                                    _etapa("07", "Interface interativa", "Mapas, gráficos, tabelas, comparações e filtros."),
                                    _etapa("08", "Públicos do estudo", "IBRAM, especialistas e demais interlocutores definidos pelo Instituto."),
                                ],
                                className="study-flow",
                            ),
                        ],
                        className="landing-section architecture-section",
                    ),
                    html.Section(
                        [html.Div([html.P("Comece pelo panorama", className="eyebrow"), html.H2("Explore as evidências disponíveis.")]), dcc.Link(["Acessar plataforma", html.Span("→", **{"aria-hidden": "true"})], href="/plataforma/panorama", className="button button-primary")],
                        className="landing-closing",
                    ),
                ],
                className="landing-main",
            ),
            html.Footer(
                [marca(), html.P("Estudo sobre impactos socioeconômicos e territoriais nas Zonas de Autossalvamento."), html.A("Voltar ao início ↑", href="#conteudo-inicial")],
                className="landing-footer",
            ),
        ],
        className="landing-page",
    )
