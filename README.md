# ZAS · Inteligência territorial

Interface em Python e Dash para consultar as bases do estudo sobre impactos
socioeconômicos e territoriais nas Zonas de Autossalvamento (ZAS).
A navegação segue **visão geral → filtro → comparação → detalhamento**.

## Executar no Windows

Extraia **toda a pasta** do ZIP. Abra essa pasta no VS Code e execute no terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abra `http://127.0.0.1:8050` no navegador. A primeira página é a entrada
institucional; o botão **Acessar plataforma** abre o panorama geral.
Mantenha o terminal aberto enquanto utiliza o site. `Ctrl+C` encerra o servidor.

Se `python` não for reconhecido, use `py -m venv .venv` no primeiro comando.
Para executar pelo botão do VS Code, escolha **Python: Select Interpreter** e
selecione `.venv\Scripts\python.exe`. O erro `No module named 'dash'` indica
que as dependências não foram instaladas no Python selecionado; os comandos
acima instalam e executam usando o mesmo ambiente. Não é necessário ativar
a `.venv` no PowerShell.

## Executar no Linux ou na nuvem

Versão validada: Python 3.12. Na pasta do projeto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Na nuvem, o ambiente preparado usa `/workspace/.venvs/zas/bin/python` e o
projeto fica em `/workspace/ZAS`. A porta padrão é 8050. As variáveis `PORT`
e `ZAS_HOST` permitem ajustar a porta e o endereço de escuta.

## Páginas e funções

| Página | Funções nesta versão |
| --- | --- |
| Entrada institucional | Apresentação do estudo, objetivos, conceito de ZAS, módulos e fluxo de evolução dos dados. |
| Panorama geral | Indicadores consolidados e distribuição das barragens por território ou empreendedor, conforme a base. |
| Explorador territorial | Mapa interativo, camadas de barragens e contorno do Brasil, seleção por ponto ou nome e detalhe com fonte/status/observação. |
| Economia e trabalho | Empreendedores, presença de trabalhadores e comunidades, tabela agregada e quantidades/valores quando informados. |
| Fiscal e CFEM | Indicadores fiscais quando houver campos explícitos e requisitos para incorporar as bases do estudo. |
| Logística | Localizações disponíveis e indicação das camadas de infraestrutura a incorporar. |
| Cenários | Estrutura para resultados de modelagens, com indicação das bases e premissas necessárias. |
| Comparação | Até quatro barragens ou grupos lado a lado. Empreendedor, Estado e município dependem das colunas da base. |
| Dados e evidências | Fontes, critérios de cálculo, tabela dos registros filtrados e exportação CSV. |

Os filtros e a busca acompanham a navegação entre módulos. O botão
**Limpar filtros** restaura o recorte completo. O mapa permite aproximação,
seleção de pontos e consulta individual. Estruturas sem coordenadas continuam
disponíveis na seleção por nome e na tabela.

## Dados fornecidos e limites da informação

A base principal contém **41 barragens e 20 empreendedores**. Os IDs são usados
para distinguir estruturas, pois existem nomes repetidos. A coluna
`TrabalhadoresZAS` é uma resposta **Sim/Não**: há **41 barragens com presença de
trabalhadores na ZAS**, mas a quantidade de pessoas não foi informada.
Há **13 barragens com comunidade na ZAS**. Existem **34 localizações válidas**;
**7 estruturas continuam sem coordenadas**.

A planilha enviada não informa UF, município, identificação individual das ZAS,
produção, CFEM, receitas públicas ou exportações. Esses indicadores mostram
**—**, e os filtros sem coluna correspondente ficam desabilitados. Não se
estima um valor a partir da localização nem se apresenta informação ausente
como zero.

O mapa utiliza pontos de barragens e um contorno local do Brasil. Ele **não
representa os limites das ZAS**. Polígonos de ZAS, lavra, beneficiamento,
infraestrutura e núcleos populacionais dependem de bases geográficas adicionais.
A fonte do contorno está em `dados/FONTES.md`.

Os módulos destinados a modelagens e a arquitetura de IA são apresentados
como etapas a incorporar; não há resultados econômicos simulados, busca
semântica ou assistente de IA nesta versão. A consulta é local, sem autenticação
ou definição de perfis de acesso. A configuração dos públicos autorizados
integra uma etapa futura de disponibilização da plataforma.

## Atualizar as bases

- **Base principal:** `dados/Lista Barragens AIR ANM 2026.xlsx` é carregada
  automaticamente. O botão **Atualizar base XLSX** aceita outra planilha de até
  10 MB. O upload vale para a sessão aberta e não substitui o arquivo local.
  Um arquivo inválido preserva a base e os filtros anteriores. A planilha
  complementar de coordenadas não deve ser enviada como base principal.
- **Coordenadas:** `dados/coordenadas_barragens.csv`, associado por
  `IDBarragem`. Para atualização permanente, substitua o CSV mantendo os campos
  `IDBarragem;NMBarragem;Latitude;Longitude` e reinicie o aplicativo. Pares
  ausentes, inválidos ou conflitantes para o mesmo ID são ignorados.
- **Rastreabilidade:**
  `dados/referencias/coordenadas_barragens_preenchidas.xlsx` contém `Status`,
  `Fonte` e `Observação`, também associados por ID. O painel apresenta as
  declarações dessa planilha; não certifica as fontes por conta própria.
- **Colunas territoriais e trabalhadores:** nomes como `UF`, `Estado`,
  `Município`, `NMBarragem`, `NMMineradora` e `TrabalhadoresZAS` são reconhecidos
  automaticamente. Quantidades de trabalhadores são somadas somente quando
  a coluna fornece valores numéricos; respostas Sim/Não indicam presença.
- **Indicadores adicionais:** campos como `IDZAS`, `ValorProducao`,
  `CFEM (R$)`, `Receitas públicas (R$)`, `ValorExportacoes` e `CNAE` alimentam
  os indicadores correspondentes quando presentes. As somas são descritivas
  dos valores informados. Período, unidade e atribuição territorial precisam
  ser compatíveis e validados pelo estudo.

A exportação em **Dados e evidências** inclui todos os registros do recorte,
independentemente da página visível na tabela, com coordenadas e metadados de
fonte. O CSV usa UTF-8 com BOM e separador `;`.

## Arquivos da aplicação

Mantenha juntos `app.py`, `dados.py`, `coordenadas.py`, `analises.py`,
`interface.py`, `landing.py`, `requirements.txt` e as pastas `assets` e `dados`.
A capa utiliza uma ilustração original em `assets/hero.svg`; os estilos ficam
em `assets/style.css`. Dados, gráficos, fontes tipográficas do sistema e
contorno geográfico funcionam sem serviços externos, tiles ou chave de API.
Links de fontes abrem os sites indicados somente ao serem acionados.

## Publicar na internet

A pasta inclui `render.yaml` e `requirements-deploy.txt` para hospedar o site
no Render usando Gunicorn. Veja o passo a passo em [DEPLOY.md](DEPLOY.md).
A branch de publicação é `zas-interface-delivery`; o site poderá ser acessado
por um endereço HTTPS fornecido pela hospedagem.

## Validar

```bash
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
```

No Windows, substitua `.venv/bin/python` por
`.\.venv\Scripts\python.exe`. Os testes verificam leitura de XLSX, indicadores,
coordenadas e metadados, rotas, callbacks HTTP do Dash, upload, filtros,
seleção, comparação e exportação. Dados de teste ficam em arquivos temporários;
os anexos enviados são preservados.
