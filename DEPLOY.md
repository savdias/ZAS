# Colocar a plataforma ZAS na internet

A configuração `render.yaml` permite hospedar a plataforma no Render.
O serviço executa `app:server` com Gunicorn e fornece um endereço HTTPS.
Depois de hospedado, o site funciona sem depender do computador local ligado.

## Criar o serviço no Render

1. Entre em https://render.com e crie uma conta ou faça login.
2. No painel, escolha **New → Web Service**.
3. Conecte o GitHub e selecione o repositório **savdias/ZAS**.
4. No campo **Branch**, selecione **zas-interface-delivery**.
5. Escolha o ambiente **Python** e configure os comandos abaixo.

**Build Command:**

```bash
pip install -r requirements-deploy.txt
```

**Start Command:**

```bash
gunicorn app:server
```

6. Em **Environment Variables**, adicione `PYTHON_VERSION` com valor `3.12.14`.
7. Selecione o plano desejado e clique em **Create Web Service**.
8. Aguarde a instalação e o status **Live**. Abra o endereço HTTPS mostrado
   pelo Render e compartilhe esse endereço com as outras pessoas.

Caso use **New → Blueprint**, informe o mesmo repositório e a mesma branch.
O Render lê `render.yaml` e preenche os comandos e a versão do Python.
Confira o plano e as condições apresentadas antes de criar o serviço.

## Como o site hospedado funciona

- O serviço carrega as planilhas e os arquivos locais incluídos no GitHub.
  A configuração usa Gunicorn, em vez do servidor de desenvolvimento do Flask.
  `gunicorn.conf.py` define a porta informada pela hospedagem e os parâmetros
  do servidor; esse arquivo é carregado automaticamente na pasta do projeto.
- Cada pessoa utiliza seus próprios filtros e a própria sessão de upload.
  Um upload não substitui o arquivo do estudo para os demais visitantes.
- Para atualizar a base principal permanentemente, altere os arquivos na
  branch `zas-interface-delivery` e publique novamente o serviço. Com a opção
  de deploy automático habilitada no Render, os commits dessa branch iniciam
  uma nova publicação.
- Esta versão abre por link e não exige login. Se o acesso precisar ficar
  restrito aos públicos autorizados do estudo, será necessário implementar
  autenticação e perfis de acesso.
- Consulte as condições atuais do plano no Render. Planos gratuitos podem
  suspender serviços sem uso, fazendo o primeiro acesso levar mais tempo;
  escolha um plano com execução contínua se essa disponibilidade for necessária.

## Conferir a publicação

Abra o endereço do serviço e verifique a entrada institucional, o panorama,
as 41 barragens da base e os 34 pontos no explorador territorial. Teste também
um filtro, a comparação e a exportação CSV. O caminho `/plataforma/territorio`
pode ser aberto diretamente no mesmo endereço.

Se a publicação falhar, consulte os logs de build e execução no Render.
Verifique primeiro a branch selecionada, os dois comandos e a variável
`PYTHON_VERSION`. O comando local `python app.py` continua disponível para
utilizar a plataforma no computador.
