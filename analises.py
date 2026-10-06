"""Indicadores descritivos e comparações calculados das bases disponibilizadas."""

import json
from collections import defaultdict

import dados
from coordenadas import normalizar_id, _par_coordenadas


def texto(valor):
    return "" if valor is None else str(valor).strip()


def chave_barragem(registro, colunas):
    identificador = normalizar_id(registro.get(colunas.get("id")))
    if identificador is not None:
        return identificador
    return json.dumps([texto(registro.get(colunas.get(c))) for c in ("estados", "municipios", "barragens")], ensure_ascii=False)


def trabalhadores_categoricos(base, colunas):
    coluna = colunas.get("trabalhadores")
    return any(dados.normalizar(r.get(coluna)) in {"sim", "nao", "s", "n", "yes", "no", "true", "false"} for r in base)


def metricas(registros, colunas, base=None):
    base = registros if base is None else base
    totais = dados.calcular_indicadores(registros, colunas)
    localizadas = {chave_barragem(r, colunas) for r in registros if _par_coordenadas(r) is not None}
    categoria = trabalhadores_categoricos(base, colunas)
    trabalhadores = dados.contar_respostas_sim(registros, colunas.get("trabalhadores")) if categoria else None
    comunidade = dados.contar_respostas_sim(registros, colunas.get("comunidade"))
    if not registros:
        if categoria:
            trabalhadores = 0
        if dados.contar_respostas_sim(base, colunas.get("comunidade")) is not None:
            comunidade = 0
    quantidade = "—" if categoria else totais["trabalhadores"]
    resultado = {
        "barragens": totais["barragens"], "empreendedores": totais["empreendedores"],
        "municipios": totais["municipios"], "estados": totais["estados"],
        "localizadas": dados.formatar_numero(len(localizadas)),
        "presenca_trabalhadores": dados.formatar_numero(trabalhadores),
        "comunidade": dados.formatar_numero(comunidade), "trabalhadores": quantidade,
    }
    extras = {
        "zas": ["IDZAS", "ID ZAS", "Nome ZAS", "Nome da ZAS"],
        "producao": ["Valor da produção (R$)", "ValorProducao", "Produção associada (R$)"],
        "cfem": ["CFEM (R$)", "ValorCFEM", "CFEMRelacionada", "CFEM"],
        "receitas": ["Receitas públicas (R$)", "ReceitasPublicas", "ValorReceitasPublicas"],
        "exportacoes": ["ValorExportacoes", "Valor das exportações", "Exportações (valor)"],
        "atividades": ["CNAE", "Atividade econômica", "AtividadeEconomica"],
    }
    cabecalhos = list(dict.fromkeys(c for r in base for c in r))
    for chave, aliases in extras.items():
        coluna = dados.localizar_coluna(cabecalhos, aliases)
        if not coluna:
            resultado[chave] = "—"
        elif chave in {"zas", "atividades"}:
            resultado[chave] = dados.formatar_numero(len({dados.normalizar(r.get(coluna)) for r in registros if texto(r.get(coluna))}))
        else:
            resultado[chave] = dados.formatar_numero(dados.somar_coluna(coluna, registros))
    return resultado


def opcoes_comparacao(registros, colunas, escala):
    opcoes = {}
    for registro in registros:
        if escala == "barragens":
            valor = chave_barragem(registro, colunas)
            nome = texto(registro.get(colunas.get("barragens"))) or "Barragem"
            label = f"{nome} · ID {texto(registro.get(colunas.get('id'))) or 'não informado'}"
        elif escala == "municipios":
            nome = texto(registro.get(colunas.get("municipios")))
            uf = texto(registro.get(colunas.get("estados")))
            if not nome:
                continue
            valor, label = json.dumps([uf, nome], ensure_ascii=False), f"{nome} / {uf}" if uf else nome
        else:
            valor = texto(registro.get(colunas.get(escala)))
            label = valor
        if valor:
            opcoes[valor] = label
    return [{"label": label, "value": valor} for valor, label in sorted(opcoes.items(), key=lambda item: dados.normalizar(item[1]))]


def selecionar_grupo(registros, colunas, escala, valor):
    if escala == "barragens":
        return [r for r in registros if chave_barragem(r, colunas) == valor]
    if escala == "municipios":
        try:
            uf, municipio = json.loads(valor)
        except (ValueError, TypeError):
            return []
        return [r for r in registros if texto(r.get(colunas.get("municipios"))) == municipio and texto(r.get(colunas.get("estados"))) == uf]
    return [r for r in registros if texto(r.get(colunas.get(escala))) == valor]


def resumo_empreendedores(registros, colunas, base):
    grupos = defaultdict(list)
    for registro in registros:
        grupos[texto(registro.get(colunas.get("empreendedores"))) or "Não informado"].append(registro)
    resultado = []
    for nome, linhas in grupos.items():
        valores = metricas(linhas, colunas, base)
        resultado.append({"Empreendedor": nome, "Barragens": valores["barragens"], "Com trabalhadores na ZAS": valores["presenca_trabalhadores"], "Com comunidade na ZAS": valores["comunidade"], "Localizadas": valores["localizadas"]})
    return sorted(resultado, key=lambda row: dados.normalizar(row["Empreendedor"]))
