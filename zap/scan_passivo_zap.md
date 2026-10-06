# Scan passivo OWASP ZAP - API TP2

## Como o scan foi executado

| Item | Valor |
|---|---|
| Ferramenta | OWASP ZAP 2.17.0 (imagem Docker `ghcr.io/zaproxy/zaproxy:stable`) |
| Alvo | API FastAPI rodando localmente (`uvicorn main:app --app-dir fastapi --host 0.0.0.0 --port 8000`), acessada pelo container em `http://host.docker.internal:8000` |
| Tipo de scan | Somente passivo: nenhum job de active scan foi executado |
| Plano de automação | [zap_plan.yaml](zap_plan.yaml) |

O plano faz três coisas:
1. importa o `/openapi.json`, o que faz o ZAP requisitar todas as rotas documentadas;
2. requisita explicitamente a página `/docs` e as rotas protegidas, incluindo o acesso a uma prediction de outro usuário;
3. espera o scan passivo terminar e exporta os relatórios.

As requisições foram feitas com o token JWT da `janedoe`, passado pelas variáveis `ZAP_AUTH_HEADER_VALUE` e `ZAP_AUTH_HEADER_SITE`. Assim o ZAP analisou também as respostas reais das rotas protegidas (`200`, `201`, `403` e `422`), e não só respostas `401`.

O scan foi rodado duas vezes:

| Execução | Quando | Relatório |
|---|---|---|
| Scan 1 | Antes das correções | [zap_report_inicial.html](zap_report_inicial.html) ([json](zap_report_inicial.json)) |
| Scan 2 | Depois das correções (validação) | [zap_report.html](zap_report.html) ([json](zap_report.json)) |

Comando utilizado (Git Bash, a partir da raiz do projeto e com a API rodando):

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/token -d "username=janedoe&password=janedoe123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

docker run --rm \
  -e ZAP_AUTH_HEADER_VALUE="Bearer $TOKEN" \
  -e ZAP_AUTH_HEADER_SITE="host.docker.internal" \
  -v "$(pwd -W)/zap:/zap/wrk:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap.sh -cmd -autorun /zap/wrk/zap_plan.yaml
```

A importação do OpenAPI chama `POST /auth/register` e `POST /predictions/predict` com dados de exemplo e grava registros no banco. Por isso, depois de cada scan, o `fastapi/database.db` foi restaurado com `git restore fastapi/database.db`.

## Resumo dos findings

| Finding | Severidade | Scan 1 | Scan 2 |
|---|---|---|---|
| Content Security Policy (CSP) Header Not Set | **Medium** | 1 | 0 |
| Sub Resource Integrity Attribute Missing | **Medium** | 2 | 0 |
| Cross-Domain JavaScript Source File Inclusion | Low | 1 | 0 |
| Authentication Request Identified | Informational | 1 | 1 |
| Modern Web Application | Informational | 1 | 1 |

Nenhum finding **High** foi encontrado. Os dois findings **Medium** do scan 1 foram corrigidos e não aparecem mais no scan 2. **O scan final não tem nenhum finding Medium ou High.**

Todos os findings Medium estavam na página `/docs` (Swagger UI), que é a única resposta HTML da API. As rotas da API em si (JSON) não geraram nenhum alerta Medium ou High.

---

## Finding 1

**7.1. Finding:** Content Security Policy (CSP) Header Not Set (plugin 10038, CWE-693, WASC-15)

**7.2. Severidade:** Medium

**7.3. Confiança:** High

**7.4. URL afetada:** `GET http://host.docker.internal:8000/docs`

**7.5. O que foi detectado:** a resposta HTML do `/docs` não tinha o header `Content-Security-Policy`. Na verdade, nenhuma resposta da API tinha esse header. O middleware de segurança em `fastapi/main.py` só definia HSTS, `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection` e `Referrer-Policy`. O ZAP só aponta o problema no `/docs` porque essa regra é aplicada a respostas HTML.

**7.6. Por que é um problema:** sem CSP, o navegador executa qualquer script presente na página, venha de onde vier. Se alguém conseguir injetar conteúdo na página do Swagger (XSS), o script injetado roda com acesso ao token JWT que o usuário digitou no botão Authorize. O CSP também é um dos headers exigidos no TP2.

**7.7. Correção realizada:**
- Foi adicionado o header `Content-Security-Policy` no middleware `security_headers` (`fastapi/main.py`), com duas políticas:
  - **Rotas da API (JSON):** `default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'`. Como a API só devolve JSON, nada precisa ser carregado.
  - **`/docs`:** `default-src 'none'; script-src 'self' https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.33.1/; style-src https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.33.1/; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'`.
- A página padrão do FastAPI tem um `<script>` inline para iniciar o Swagger, o que obrigaria a usar `'unsafe-inline'` (o próprio ZAP também aponta isso como Medium). Por isso o `/docs` passou a ser servido por `fastapi/routes/docs.py`, e o script de inicialização foi movido para um arquivo próprio (`/docs/swagger-init.js`).
- O `/redoc`, que não era usado, foi desativado.

**7.8. Validação:**
- No scan 2 o finding não aparece mais, e também não apareceu nenhum alerta sobre a própria política, como `unsafe-inline` ou diretivas faltando.
- Com `curl -I` foi confirmado que todas as respostas trazem o header.
- O `/docs` foi aberto no navegador: o Swagger carregou, o login pelo botão Authorize funcionou e o console não mostrou nenhuma violação de CSP.
- Os testes automatizados (`pytest`) continuaram passando.

**7.9. Risco aceito, se não corrigido:** não se aplica, o finding foi corrigido.

---

## Finding 2

**7.1. Finding:** Sub Resource Integrity Attribute Missing (plugin 90003, CWE-345, WASC-15)

**7.2. Severidade:** Medium

**7.3. Confiança:** High

**7.4. URL afetada:** `GET http://host.docker.internal:8000/docs`, com 2 instâncias:
- `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">`
- `<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js">`

**7.5. O que foi detectado:** o Swagger UI carregava o JavaScript e o CSS de um CDN externo (jsDelivr) sem o atributo `integrity`. Além disso, a versão usada era `@5`, que aponta sempre para a versão 5.x mais recente, então o arquivo entregue podia mudar a qualquer momento.

**7.6. Por que é um problema:** sem SRI, o navegador não tem como saber se o arquivo recebido é o esperado. Se o CDN ou o pacote no npm forem comprometidos, um JavaScript malicioso seria executado dentro da página de documentação da API, com acesso ao token JWT do usuário.

**7.7. Correção realizada:**
- Em `fastapi/routes/docs.py`, a versão do Swagger UI foi fixada em `5.33.1`.
- Foi adicionado o atributo `integrity` com o hash SHA-384 de cada arquivo, junto com `crossorigin="anonymous"`.
- Os hashes foram calculados a partir dos arquivos baixados do próprio CDN, com `openssl dgst -sha384 -binary <arquivo> | openssl base64 -A`.
- O CSP do `/docs` só permite scripts e estilos desse caminho do CDN, na versão fixa.

**7.8. Validação:**
- No scan 2 o finding não aparece mais.
- O alerta Low "Cross-Domain JavaScript Source File Inclusion" também sumiu, porque o ZAP considera mitigado um script externo com SRI.
- No navegador, o Swagger carregou normalmente, o que mostra que os hashes conferem: se não conferissem, o navegador bloquearia os arquivos.

**7.9. Risco aceito, se não corrigido:** não se aplica, o finding foi corrigido.

Fica um risco residual: o `/docs` continua dependendo da disponibilidade do jsDelivr. Se o CDN estiver fora do ar, a documentação não carrega, mas a API continua funcionando normalmente. Para ambiente de desenvolvimento e para o trabalho isso é aceitável. Em produção, a alternativa seria servir os arquivos do Swagger UI pela própria aplicação ou desativar o `/docs`.

---

## Findings Low e Informational

Não exigem documentação detalhada, mas ficam registrados:

- **Cross-Domain JavaScript Source File Inclusion (Low):** apareceu só no scan 1 e foi resolvido junto com o Finding 2.
- **Authentication Request Identified (Informational):** o ZAP apenas identificou que o `POST /auth/token` é a requisição de login (campos `username` e `password`). Não é uma vulnerabilidade. Esse endpoint já tem rate limiting de 10 requisições por minuto.
- **Modern Web Application (Informational):** indica que o `/docs` é uma aplicação JavaScript (Swagger UI). Também não é uma vulnerabilidade.

## Limitações

- O scan foi feito em HTTP local, sem TLS. O header HSTS é enviado, mas só tem efeito quando a API é servida por HTTPS.
- Por ser passivo, o scan não testa ataques como injeção ou BOLA, apenas analisa as requisições e respostas. Esses controles são cobertos pelos testes automatizados em `tests/` e serão alvo do pentest previsto para os próximos TPs.
