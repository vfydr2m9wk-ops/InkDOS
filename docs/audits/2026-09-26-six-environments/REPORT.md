# Auditoria geral dos seis ambientes do InkDOS

- **Data:** 2026-09-26
- **Baseline auditada:** `main` @ `7ba5029` (InkDOS 2.6.2 beta, `VERSION.json`)
- **Natureza:** somente diagnóstico. Nenhum arquivo de produto, versão, release, tag, updater, service worker ou arquitetura foi alterado.
- **Legenda:** **PASS** comprovadamente correto · **WARNING** aceitável mas inconsistente/potencialmente problemático · **FAIL** problema concreto reproduzido · **NOT VERIFIED** a infraestrutura não permitiu verificar.

---

## 0. Resposta curta

> *Os seis ambientes formam hoje um produto coerente, isolado, funcional, visualmente consistente e com desempenho aceitável?*

**Parcialmente.**

- **Isolamento: sim.** Nenhum app referencia runtime de outro app. O que é compartilhado fica dentro do contrato. Os seis funcionam abertos diretamente, via Home e offline.
- **Funcionalidade central: sim, com três defeitos concretos:**
  - **Spreadsheets** gera XLSX com índice de estilo inválido no segundo save.
  - O diálogo de alterações não salvas do **Presentations** é renderizado sem CSS e fica inacessível quando aberto pelo menu.
  - Arquivos não suportados escolhidos pelo seletor nativo, ou recebidos via `launchQueue`, falham **silenciosamente** em vários apps.
- **Visual: existe uma linguagem comum real.** Tokens, header, drawer, cartão de início e status bar são compartilhados. Há, porém, desvios acidentais mensuráveis (TXT é o maior outlier) e controles duplicados de aparência em três apps.
- **Performance: aceitável em arquivos pequenos e médios em todos os apps** (primeiro conteúdo em 60–390 ms). Não é aceitável em dois casos grandes: **TXT de 13 MB**, com ~1,3 s por tecla, e **XLSX de 20 mil linhas**, com ~4 s de abertura e uma long task de 2,3 s.
- **CI verde ≠ produto correto, comprovado.** Nenhum dos defeitos acima é detectado pela suíte. 11 dos 173 testes mapeados falham localmente, na maioria por estarem obsoletos. O audit "exhaustive button" passa com **0 controles** se o servidor não estiver presente.

---

## 1. Ambiente e limitações da auditoria

| Item | Situação |
|---|---|
| Site publicado (`vfydr2m9wk-ops.github.io`) | **NOT VERIFIED.** A política de rede deste ambiente bloqueou o host (proxy 403). Toda a auditoria de UI foi feita servindo o **mesmo commit `main`** por HTTP estático local, sob o prefixo `/InkDOS/`, que imita o GitHub Pages. Não foi possível confirmar que o Pages publica exatamente esse commit. |
| Chromium | Playwright/Chromium headless **141.0.7390.37**, Linux. |
| Firefox / WebKit | **NOT VERIFIED.** Os binários não estão instalados e a política do ambiente proíbe `playwright install`. **Não há nenhuma evidência WebKit/iPadOS nesta auditoria.** |
| iPad real / XeOS / iCloud File Provider | **NOT VERIFIED.** Foi feita uma emulação de viewport de iPad no Chromium (1024×1366, toque, UA iPad), que não substitui o WebKit. |
| Fixtures | Gerados localmente e de forma sintética: DOCX/XLSX/PPTX (python-docx/openpyxl/python-pptx), DOC/XLS/PPT convertidos pelo LibreOffice 24, RTF, TXT, MD, JSON, EPUB 3 gerado à mão, PDFs (reportlab). Também arquivos grandes, inválidos, vazios e com extensão errada. |
| Salvamento | Perfil `fs`: `showSaveFilePicker` substituído por um stub que captura os bytes e simula Cancel (`AbortError`) e erro de escrita. Perfil `nofs`: APIs de sistema de arquivos removidas, como no Safari/iPad, forçando o fallback de download. `navigator.share` não existe no Chromium desktop headless, então **Share ficou NOT VERIFIED**. |
| Impressão | Diálogo de impressão não observável em headless: **NOT VERIFIED**. |

Os scripts reproduzíveis estão em `harness/` e as evidências brutas em `evidence/`.

---

## 2. Quadro consolidado

| App | Arquitetura | Visual | Funcionalidade | Performance |
|---|---|---|---|---|
| Documents | PASS | WARNING | WARNING | PASS |
| Spreadsheets | PASS | WARNING | **FAIL** | WARNING |
| Presentations | PASS | **FAIL** | **FAIL** | PASS |
| Plain Text | WARNING | WARNING | WARNING | **FAIL** (arquivos grandes) |
| EPUB | PASS | WARNING | WARNING | PASS |
| PDF | WARNING | WARNING | WARNING | PASS |

Todas as notas de performance valem **apenas para Chromium desktop headless**. WebKit/iPad: NOT VERIFIED.

---

## 3. Estágio 1 — Código e arquitetura

### 3.1 Dependências cruzadas (mapa independente)
Todo `src/href/import/fetch/../` que sai de `apps/<app>/` foi resolvido.

**Resultado: PASS.** Cada app só sai do próprio diretório para:
- `../../shared/ui-density.css` e `../../shared/ui-density.js`;
- `../../index.html` (link Home, só visível com `?suite=1`).

`shared/localization/**` é carregado dinamicamente por `ui-density.js`. **Nenhum app referencia outro app.** Os validadores do repo também passaram: `validate_app_isolation`, `check_no_legacy_runtime`, `validate_repository`, `validate_suite_contracts`, `audit_source`, `generate_csp --check`, `build_offline_snapshot --check` e `build_txt_bundle --check`.

### 3.2 Exceções compartilhadas — dentro do contrato?

| Achado | Status |
|---|---|
| `shared/` contém apenas os 2 arquivos + o prefixo `localization/` permitidos por `config/shared-runtime-policy.json`. | PASS |
| Estado compartilhado usa chaves por app (`inkdos2:<app>:ui-density`, `inkdos2:<app>:language`, `inkdos2:<app>:appearance`), com migração única da chave de suíte. | PASS |
| `shared/ui-density.js` **também registra o service worker raiz** (`registerWorkspaceOffline`) e faz o bootstrap da localização. O contrato descreve `shared/` como "helpers de densidade e localização". Registrar o SW é uma responsabilidade de runtime/offline, fora desse escopo declarado. Funciona, mas o offline de cada app passa a depender de um helper chamado "ui-density". | WARNING |
| Um único `service-worker.js` (dono: hub) cacheia os 266 arquivos dos 6 apps num **único cache, instalado tudo-ou-nada**. Se um asset de um app falha, o offline cai para todos. Qualquer mudança em um app muda `CACHE_NAME` e força o re-download dos seis. Esse é um acoplamento operacional, não de runtime. | WARNING |

### 3.3 Isolamento de runtime, estado e inicialização

| Verificação | Status |
|---|---|
| Namespaces globais por app: `InkDOS2Documents`, `InkDOS2Spreadsheets`, `InkDOS2Presentations`, `InkDOS2Epub`, `InkDOS2PdfP4`. O TXT usa o nome genérico `InkDOS2`. O Spreadsheets vaza globais extras (`__inkdosSpreadsheetsS1`, `InkDOS2Spreadsheet*`). Sem colisão real, porque cada app é uma página. | PASS / WARNING (nomenclatura) |
| `storage` listeners filtram pela chave do próprio app. Não há `BroadcastChannel` entre apps (o TXT usa um canal próprio de recuperação). | PASS |
| Nenhuma dependência oculta da Home: aberturas diretas e via Home deram métricas idênticas em 12/12 combinações (ver 4.1). | PASS |
| `runtime/platform/file-launch.js` é **byte-idêntico nos 6 apps**: duplicação deliberada, conforme o `AGENTS.md`. | PASS |
| O TXT roda como **bundle monolítico inline** (`index.html` de 138 KB, 15+ hashes de CSP), enquanto os outros carregam módulos. O bundle está em sincronia com as fontes (`--check`). | WARNING (arquitetura divergente, custo de auditoria) |

### 3.4 CSP, file handling, segurança

| Verificação | Status |
|---|---|
| CSP estrita nos 6 apps: `default-src 'self'`, sem `unsafe-eval`, `object-src 'none'`, `frame-src 'none'`. `style-src 'unsafe-inline'` em todos. | PASS |
| Manifests com `file_handlers` coerentes com os `accept` efetivos (o TXT atualiza o `accept` em runtime para .md/.json/.yaml…). | PASS |
| `launchQueue` implementado nos 6. O caminho real de instalação PWA **NOT VERIFIED**; o caminho de código foi exercitado via `InkDOSFileLaunch.consume` (ver 5.7). | PASS / NOT VERIFIED |
| O evento `inkdos:file-launch-error` é disparado por `file-launch.js`, mas **nenhum app o escuta** (grep em todo `apps/`). Consequência em 5.7. | **FAIL** |
| `showOpenFilePicker({multiple:false})` é chamado **sem `types`**, então no Chromium o seletor não filtra por formato. | WARNING |
| Limites anti zip-bomb/DoS presentes em todos os parsers ZIP/OLE/RTF (bytes de entrada, bytes por entrada, total descomprimido, razão de compressão 250, contagem de slides/objetos/registros). | PASS |
| PDF: `pdf.js` **3.11.174** (versão afetada pelo CVE-2024-4367). Todas as 4 chamadas de `getDocument` usam `isEvalSupported:false` e a CSP não permite `unsafe-eval`, então **o vetor está mitigado**. O worker é uma versão **modificada localmente** (documentada em `VENDOR-PROVENANCE.txt`). | WARNING (dependência antiga, mitigada) |

### 3.5 Save / Save Copy / Share / Recovery / dirty guards (visão de código)

| Capacidade | Documents | Spreadsheets | Presentations | TXT | EPUB | PDF |
|---|---|---|---|---|---|---|
| `beforeunload` guard | ✔ | ✔ | ✔ | ✔ | ✔ (sem estado sujo) | ✔ |
| Save via File System Access + fallback | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Share (Web Share files) | código ✔ | código ✔ | código ✔ | código ✔ | código ✔ | código ✔ |
| **Recuperação de sessão ao usuário** | ✖ | ✖ | ✖ | ✖ (ver 5.4) | n/a (posição/anotações persistem) | ✖ |
| Diálogos nativos (`prompt/confirm`, contagem estática aproximada) | prompt×3, confirm×1 | prompt×4, confirm×4 | prompt×3 | 0 | prompt×1 | confirm×4 |

---

## 4. Estágio 2 — Auditoria visual

**Cobertura:** 6 apps × 2 entradas (direto, Home→app) × 2 temas = **24 combinações**. Para cada combinação: estado vazio, drawer aberto, após `Escape` e com arquivo carregado. Foram 96 screenshots, mais estilos computados de body, header, botão de menu, título, botão de toolbar, botão desabilitado, select, botões do cartão inicial, status bar e drawer (fundo, raio, sombra, itens, rótulos).

### 4.1 Direto vs Home
**PASS.** As métricas computadas são idênticas nas 12 combinações app×tema. A única diferença é o link Home, visível apenas via Home (`?suite=1`), como projetado. O retorno à Home e a reentrada funcionam nos 6 apps (5.8).

### 4.2 Linguagem comum — o que é consistente (PASS)
- Fundo `#eef1f5` / `#171a20`, chrome translúcido, texto `#1b1f27` / `#f2f4f8` e bordas iguais em 5 dos 6 apps.
- Header de 44 px, botão de menu de 30 px, drawer à esquerda com cabeçalho "ícone + nome + ×", seção FILE com atalhos ⌘N/⌘O/⌘S e faixa inferior "Appearance / Interface / Language / Help" nos 6.
- Cartão de início idêntico (botão primário de 44 px, raio 11 px, cor de destaque do app) nos 6.
- Status bar de 26 px em 5 dos 6.
- A cor de destaque por app é **deliberada e coerente** com a Home.
- **EPUB:** a superfície de leitura "papel" (creme) permanece clara no tema escuro. Isso é **deliberado e funcionalmente justificado**: o chrome acompanha o tema e a superfície tem temas próprios no painel de aparência. Não foi classificado como inconsistência. O mesmo vale para a página branca de Documents, Presentations e PDF.

### 4.3 Inconsistências visuais (acidentais, com evidência medida)

| # | Onde | Evidência | Status |
|---|---|---|---|
| V1 | **Presentations — diálogo "Unsaved changes"** | Criado com `.error-overlay/.error-card` (`apps/presentations/ui/command-controller.js:19`), mas **o CSS do Presentations não define essas classes**. Resultado: texto e botões nativos sem estilo, no fim da página (`position: static`), empurrando o layout. Quando aberto pelo menu, fica **atrás do `#menuBackdrop`**. Ver `evidence/presentations-unsaved-guard-*.png`. | **FAIL** |
| V2 | TXT — outlier geral | Header de 54 px (vs 44), botão de menu de 36 px com fundo/borda (vs 30 transparente), paleta escura própria (`#11161c`, texto `#edf2f7`), drawer de 310 px, raio 14, fundo sólido (vs 340/18/translúcido), itens de 32 px (vs 40) em negrito, ícone do cartão inicial alinhado à esquerda (os outros são centrados). | WARNING |
| V3 | Controle de aparência duplicado | TXT, EPUB e PDF mostram no drawer um seletor "APPEARANCE Light/Dark/System" **e também** o botão "◐ Appearance" da faixa inferior. Documents, Spreadsheets e Presentations só têm o segundo. O seletor do PDF usa ainda outro estilo (pílulas com destaque vermelho). | WARNING |
| V4 | `Escape` não fecha o drawer | Spreadsheets e EPUB (4/4 combinações cada). Nos outros 4 apps fecha. | WARNING |
| V5 | Opacidade de desabilitado | 0.28 (Documents/Spreadsheets), 0.38 (Presentations), 0.42 (EPUB), 0.46 (TXT), 0.48 (PDF). | WARNING |
| V6 | Raio de botões | Botão de menu 12 px (4 apps) vs 9 px (TXT, PDF). Botões de toolbar 8/9/10 px. Fundo de toolbar transparente (Presentations) vs preenchido (TXT, EPUB, PDF). | WARNING |
| V7 | Tipografia | Título do documento 16 px (Documents, Spreadsheets, Presentations) vs 14 px (TXT, EPUB, PDF). Status 10,5 px (EPUB), 11 px (3 apps), 12 px (PDF). Pesos de título do drawer 750 vs 760. | WARNING |
| V8 | Tokens quase iguais | `--muted #697386` vs `#687286`, `--line #d9dee7` vs `#d8dee7`, chrome `.96` vs `.97`. Presentations e PDF usam valores deslocados em 1 unidade: indício de cópia divergente, não de design. | WARNING |
| V9 | Estilo de toolbar | Presentations e Spreadsheets usam botões com **rótulo de texto** ("Slide", "Text", "Print", "Paint"). Documents usa ícones para as mesmas ações (Print, Format painter). No Presentations o select de transição aparece truncado como "No tr". | WARNING |
| V10 | Rótulos do menu | "Open document / Open workbook / Open PPT / PPTX / Open / Open EPUB / Open PDF"; "Save copy" vs "Save XLSX copy"; guard do TXT com "Cancel · Save · Discard changes" (outros: "Cancel · Discard · Save"). Faixa inferior com "Appearan…" truncado nos 6. | WARNING |
| V11 | Diálogos nativos do navegador | `window.prompt/confirm` em Documents (inserir tabela: Rows/Columns), Spreadsheets, Presentations, EPUB e PDF (excluir página, imprimir com alterações). Destoam dos diálogos próprios do app e, no iPad/PWA standalone, têm aparência do sistema. | WARNING |
| V12 | Mensagem de erro de **gravação** | Documents, Spreadsheets e Presentations exibem **"… could not be opened"** para uma falha de escrita no Save. Documents e Presentations ainda oferecem o botão "Choose another file". Documents mostra também "Engine: Documents 2.0 private reader". Ver `evidence/documents-write-error-says-opened.png`. | WARNING (UX enganosa) |
| V13 | Títulos de janela | EPUB e PDF mostram sempre "EPUB Reader — InkDOS 2.0" / "PDF Workspace — InkDOS 2.0" (versão antiga, sem nome do arquivo). Presentations vazio mostra "Presentations — InkDOS 2.0". Os outros mostram "arquivo — App". | WARNING |
| V14 | `theme_color` dos manifests | `#eef1f5` (TXT, EPUB) vs `#f7f8fa` (4 apps). | WARNING |
| V15 | Densidade em viewport de iPad (Chromium) | Altura mínima dos controles da toolbar: 36–38 px (Spreadsheets, Documents, PDF) vs 40–42 px (TXT, Presentations, EPUB). Todos abaixo de 44 pt. Sem scroll horizontal da página. | WARNING |

**NOT VERIFIED:** estados hover/active de todos os controles (só foram medidos padrão e desabilitado), contraste WCAG formal, tooltips e menus contextuais do sistema.

---

## 5. Estágio 3 — Teste funcional real

**Cobertura:** 6 roteiros × 2 perfis (`fs`, `nofs`) = **302 passos verificados** (266 PASS, 22 INFO, 10 FAIL e 4 WARNING brutos, reclassificados abaixo após investigação). Além disso:
- audit exaustivo de botões do repo contra o servidor local: **475 controles descobertos, 370 cliques entregues**;
- audit condicional por app: **46 checagens**;
- testes cruzados de picker, launchQueue, Home e tema;
- offline nos 6 apps, em 2 caminhos de instalação.

### 5.1 Documents
**PASS (verificado):**
- abrir DOCX/RTF/DOC;
- painel de navegação/outline;
- digitar e ver o dirty dot;
- negrito;
- Undo/Redo;
- zoom;
- inserir tabela (Cancel e OK);
- Save Copy com Cancel, picker cancelado e erro de escrita (o documento continua sujo);
- DOCX salvo válido no python-docx (edição, negrito e tabela preservados) e reaberto;
- guard ao abrir outro arquivo (Cancel/Discard);
- DOC/DOCX inválidos e vazios mostram erro e **preservam o documento anterior**;
- New;
- `beforeunload`;
- fallback de download (`nofs`).

**Problemas:** mensagem de erro de gravação enganosa (V12); `prompt` nativo na inserção de tabela (V11); seletor nativo com arquivo não suportado é silencioso (5.7).

### 5.2 Spreadsheets
**PASS:**
- XLSX abre com fórmulas em cache e texto numérico `00123` preservado;
- edição de célula, Enter, fórmula nova, recálculo em cadeia via barra de fórmulas;
- setas, Name Box, seleção de intervalo, negrito, Undo/Redo;
- excluir linha e desfazer;
- abas de planilha;
- zoom;
- XLS legado;
- XLSX inválido/vazio mostra erro e preserva a pasta anterior;
- New;
- `beforeunload`;
- download (`nofs`).

**FAIL S1 — XLSX salvo com índice de estilo inválido (corrompido).** Reprodução determinística:

| Sequência | `cellXfs` em styles.xml | índices usados | Resultado |
|---|---|---|---|
| negrito → salvar | 3 | [1,2] | válido |
| editar → salvar → negrito → salvar | 3 | [1,2] | válido |
| **negrito → salvar → editar → salvar** | **2** | **[1,2]** | **inválido** |
| negrito → Save cancelado → salvar | 2 | [1,2] | inválido |
| negrito → erro de escrita → salvar | 2 | [1,2] | inválido |

Um estilo novo criado antes da **primeira** serialização não entra no `styles.xml` das serializações seguintes, mas as células continuam apontando para ele. Efeitos observados:
- `openpyxl` rejeita o arquivo (`IndexError`);
- LibreOffice abre, mas **perde a formatação silenciosamente**;
- o próprio InkDOS reabre o arquivo;
- Excel: NOT VERIFIED (provavelmente dispara "reparar").

O cenário é comum: formatar, salvar, continuar trabalhando e salvar de novo. Script: `harness/repro_xlsx2.py`.

**FAIL S2 — guard duplicado ao abrir com alterações.** Com a pasta suja, o fluxo é:
1. Open → "Unsaved changes" → Discard;
2. escolher o arquivo;
3. **o mesmo diálogo aparece de novo**, com o arquivo novo já carregado por baixo.

Cancel nesse segundo diálogo não reverte nada. Script: `harness/repro_guard2.py`. Documents, Presentations e PDF perguntam uma vez só.

### 5.3 Presentations
**PASS:**
- PPTX abre com miniaturas;
- próximo/anterior;
- selecionar e editar placeholder;
- toolbar contextual de texto;
- adicionar, duplicar, excluir e mover slide, com Undo/Redo;
- caixa de texto;
- popover de background;
- zoom;
- modo Apresentar e saída com Esc;
- Save com cancelamento e erro;
- PPTX válido no python-pptx (slides e edição preservados) e reaberto;
- PPT legado abre em **somente-leitura** (deliberado: "Legacy PPT is read-only");
- inválido mostra erro e preserva a apresentação;
- `beforeunload`;
- download.

**Problemas:**
- **FAIL P1** — guard de alterações não estilizado (V1). Aberto pelo menu (Open/New/Home), os botões Discard/Save ficam sob o backdrop do drawer e **não recebem clique**. O usuário precisa fechar o menu e rolar até o fim da página.
- **FAIL P2** — PPTX vazio (0 bytes) é reportado como "**PPTX exceeds the compressed input-byte budget**" (mensagem errada).
- WARNING — erro de gravação dito "could not be opened" (V12).

### 5.4 Plain Text
**PASS:**
- TXT UTF-8 com ümlaut e 中文;
- digitar, Undo/Redo, Select all, tamanho da fonte, quebra de linha, Find;
- Save com cancelamento e erro (mensagem correta: "Export failed: The selected file could not be written.");
- bytes UTF-8 com LF preservado;
- .md, .json e vazio abrem;
- New;
- `beforeunload`;
- guard ao sair pela Home;
- download.

**Problemas:**
- WARNING T1 — ao abrir com alterações, o TXT **abre o seletor primeiro e pergunta depois** (os outros editores perguntam antes). Não há perda de dados, mas o fluxo é inconsistente.
- WARNING T2 — **recuperação inalcançável.** Checkpoints são gravados no IndexedDB (`inkdos2-txt-recovery`), mas `restoreRecovery()` não tem chamador. O contrato em `scripts/validate_suite_contracts.py:185-186` proíbe a restauração automática e não há caminho manual. Após recarregar ou fechar a aba, nada é oferecido. Isso parece uma desconexão deliberada, mas o texto não salvo continua gravado no IndexedDB sem nunca ser oferecido ao usuário, e o CHANGELOG ainda descreve a ativação por checkpoint.
- WARNING T3 — binário aberto como .txt mostra na status bar a exceção crua do `TextDecoder`. O arquivo anterior é preservado.

### 5.5 EPUB
**PASS:**
- abertura;
- paginação por botões e teclado;
- sumário e salto de capítulo;
- busca;
- tamanho da fonte;
- modo Scroll/Pages;
- marcador;
- slider de progresso;
- destaque por arrasto;
- Save Copy (ZIP válido, `mimetype` primeiro e armazenado);
- abrir outro EPUB troca livro e sumário;
- reabrir restaura a posição de leitura;
- inválido mantém o livro atual.

**Problemas:**
- WARNING E1 — EPUB vazio reportado como "input-budget: EPUB input exceeds the provisional compressed-byte budget" (mensagem errada).
- WARNING E2 — erros aparecem só na status bar, com códigos internos (`invalid-zip:`, `input-budget:`), sem diálogo como nos outros apps.
- INFO — Save Copy após destacar gera bytes idênticos ao original (5567 B). As anotações ficam no IndexedDB, não no arquivo.

### 5.6 PDF
**PASS:**
- abrir;
- próxima/anterior;
- campo de página, com valor fora do intervalo rejeitado;
- zoom;
- rotação de visualização;
- miniaturas e clique na miniatura;
- busca;
- modo Edit (0,09 s);
- caneta, com dirty e Undo/Redo;
- anotação de texto;
- Page Tools: rotacionar página; excluir página com Cancel e com confirmação;
- Save Copy com cancelamento e erro (mensagem correta: "PDF operation failed / Save failed");
- PDF salvo válido no pypdf (2 páginas, rotação 90°, 2 anotações);
- guard ao abrir outro PDF (Cancel/Discard);
- PDF de 400 páginas / 7,5 MB;
- PDF inválido, vazio ou com extensão errada mostra erro e preserva o anterior;
- download;
- Page Tools funciona **offline** (carregamento sob demanda coberto pelo SW).

**Problemas:**
- WARNING D1 — o painel de navegação abre na aba "Outline" mesmo sem outline ("No document outline"). As miniaturas exigem um clique extra.
- WARNING D2 — "ir para 350" no PDF de 400 páginas foi ignorado **1 vez em 8**, logo após trocar de documento. 0/6 em isolamento: intermitente, sem causa-raiz determinada.
- WARNING D3 — excluir página e imprimir com anotações usam `confirm()` nativo. A impressão avisa que anotações não salvas **não são impressas**.
- **NOT VERIFIED:** Print (iframe + `contentWindow.print()`), Share.

### 5.7 Arquivos não suportados por caminhos nativos (transversal)

| App | Seletor nativo (Chromium) com `.zip` | `launchQueue` com `.zip` |
|---|---|---|
| Documents | **silencioso** (só console) | erro visível ✔ |
| Spreadsheets | **silencioso** (reverificado) | erro visível ✔ |
| Presentations | não se aplica: usa `<input type=file>`, não o seletor nativo (reverificado) | erro visível ✔ |
| TXT | **silencioso** | **silencioso** |
| EPUB | **silencioso** | erro visível ✔ (`invalid-zip: …` na status bar; *corrigido após reverificação: a auditoria original marcou como silencioso*) |
| PDF | **silencioso** | **silencioso** |

Causa: `inkdos:file-launch-error` não tem ouvintes (3.4). **FAIL** transversal: o usuário escolhe um arquivo e nada acontece. No Safari/iPad o seletor usa `<input accept>`, então o impacto maior é em Chromium/Edge desktop e em arquivos abertos pelo sistema (PWA/Tauri).

### 5.8 Home, tema e offline
- **Home → app (sujo) → Home:** guard de saída nos 5 editores (Presentations com o diálogo sem estilo). Discard volta para a Home e a reentrada começa limpa. EPUB sai sem guard, o que é esperado. **PASS**
- **Tema:** Home em Dark faz cada app abrir Dark **na primeira visita** (migração). Depois disso, mudar a Home para Light **não afeta nenhum app** (6/6 continuam Dark). É consequência do estado por app (deliberado), mas a "Settings" da Home aparenta ser global. **WARNING**
- **Offline:** instalando pela Home ou abrindo o PDF direto primeiro, o cache completa 266/266. Sem rede, os 6 apps e a Home carregam e abrem arquivos, e os pacotes de idioma carregam. **PASS**

### 5.9 Suíte de testes do repositório (evidência "CI verde ≠ produto")
- 173 testes mapeados por `config/components.json` (`--full --browser`) mais os transversais: **162 PASS / 11 FAIL** localmente.
- Das 11 falhas:
  - **6 obsoletas:**
    - `test_txt_stability_browser` e `test_pdf_stability_frame` esperam `input.click`/`filechooser`, mas o app usa `showOpenFilePicker`;
    - `test_ppt_p2_transitions_browser` procura a animação no elemento errado (a transição existe);
    - `test_pdf_stability_offline` espera Page Tools carregado de forma eager, mas agora é lazy;
    - `test_pdf_stability_offline_contract` lê um workflow que não existe;
    - `test_pdf_toolbar_25_contract` faz assert de string antiga.
  - **1 bug no próprio teste:** `test_pptx_character_spacing_preservation_diagnostic` tem SyntaxError no JS.
  - **1 requer WebKit:** `test_pdf_open_picker_browser`.
  - **2 intermitentes:** `test_presentations_button_diagnostic` (**roda no CI**) e `test_ppt_p2_table_structure_browser` ("Execution context was destroyed", 2/4 e 1/3). Causa-raiz NOT VERIFIED.
  - **1 depende de servidor:** `test_conditional_button_audit_browser`.
- Apenas ~89 arquivos de teste são referenciados pelos workflows e por `run_release_validation.py`. Muitos testes de componente não rodam no CI, o que explica o acúmulo de testes obsoletos.
- `test_exhaustive_button_audit_browser.py` **passa com `controlsDiscovered: 0`** quando `INKDOS_ONLINE_BASE` não aponta para um servidor ativo: falso positivo sem assert mínimo. Com servidor: 475 controles, 370 cliques, 4 falhas (faixa de configurações do drawer do PDF "missing-on-replay", indício de inserção assíncrona da faixa).
- **Nenhum** dos FAIL desta auditoria (S1, S2, P1, P2, 5.7) é coberto por teste.

---

## 6. Estágio 4 — Performance (medida, Chromium headless, servidor local, contexto frio, mediana de 5)

"Seleção → recebido" em headless é `setInputFiles`, ~35–50 ms. **A materialização pelo iCloud/File Provider é NOT VERIFIED.**

| App / arquivo | Startup (UI utilizável) | Recebido → 1º conteúdo | Seleção → 1º conteúdo | Maior long task na abertura | CPU (tasks) |
|---|---|---|---|---|---|
| Documents audit.docx | 456 ms | 172 ms | 229 ms | 101 ms | 0,7 s |
| Documents large.docx (~1.500 parágrafos) | 464 ms | 662 ms | 716 ms | 297 ms | 2,3 s |
| Spreadsheets audit.xlsx | 402 ms | 172 ms | 213 ms | 92 ms | 0,2 s |
| **Spreadsheets large.xlsx (20.000×5)** | 411 ms | **3.924 ms** | **3.967 ms** | **2.256 ms** | 4,0 s |
| Presentations audit.pptx | 331 ms | 117 ms | 156 ms | 0 | 0,2 s |
| Presentations large.pptx (80 slides) | 363 ms | 188 ms | 226 ms | 64 ms | 0,9 s |
| TXT audit.txt | 141 ms | 22 ms | 60 ms | 0 | 0,1 s |
| **TXT large.txt (13,3 MB, 200k linhas)** | 133 ms | **3.938 ms** | **3.970 ms** (máx 6,2 s) | **3.008 ms** | 4,5 s |
| EPUB audit.epub | 304 ms | 61 ms | 101 ms | 0 | 0,1 s |
| EPUB large.epub (150 capítulos) | 294 ms | 446 ms | 485 ms | 296 ms | 0,5 s |
| PDF small.pdf (3 p.) | 420 ms | 349 ms | **388 ms** | 0 | 0,2 s |
| PDF large.pdf (400 p., 7,5 MB) | 386 ms | 478 ms | **517 ms** | 0 | 0,3 s |

### PDF — T1 − T0 (seleção → primeira página realmente legível)
"Legível" significa pixels escuros detectados no canvas da página 1, e não a existência da tela de loading. Marcos em ms desde o arquivo recebido:

| | getDocument | PDFDocumentProxy | getPage(1) | viewport | render início | render fim | 1º trabalho secundário | **T1−T0** |
|---|---|---|---|---|---|---|---|---|
| small.pdf | 10 | 261 | 266 | 267 | 277 | 309 | 357 | **388 ms** |
| large.pdf | 10 | 310 | 314 | 315 | 325 | 444 | 480 | **517 ms** |

O trabalho secundário (outras páginas) só começa **depois** do render da página 1: **first-page-first comprovado**. A maior parte do tempo (~250–300 ms) é bootstrap do worker e abertura do documento.

### Outras medições

| Medição | Resultado |
|---|---|
| Save (clique → bytes entregues; inclui ~350 ms de espera do harness ao abrir o menu) | Documents 784 ms (inclui painel), Spreadsheets 516, Presentations 566, TXT 460, EPUB 454, PDF 254 (botão direto). **PASS** |
| Troca de documento (arquivo limpo → outro arquivo visível) | Documents 49 ms, TXT 37, EPUB 44, Presentations 90, Spreadsheets 98, PDF 231. **PASS** |
| EPUB virada de página | conteúdo muda em ~280 ms; o status "n / N" só atualiza em ~700 ms. Sem long tasks, sem animação, igual com `reduced-motion`. WARNING (status atrasado) |
| **TXT 13 MB — digitação** | **1,1–1,5 s por tecla** até o próximo frame, long tasks de 300–590 ms após cada tecla. **FAIL** para arquivos grandes (o limite aceito é 64 MB). |
| Spreadsheets 20k linhas — rolagem | long tasks de 51–76 ms. PASS |
| Startup (todos) | long task máxima de 60 ms (PDF, carga do pdf.js). PASS |

**NOT VERIFIED:** dispositivo real, WebKit, throttling de CPU móvel, memória por processo, tempo de exportação separado do Save, iCloud.

---

## 7. Achados críticos
1. **Spreadsheets S1:** XLSX corrompido (estilo órfão) no segundo save após formatar. Perda silenciosa de formatação em outros aplicativos. Reprodução determinística.
2. **Presentations P1/V1:** diálogo de alterações não salvas sem CSS, fora do overlay e bloqueado pelo backdrop do menu. Afeta New, Open e Home com alterações.
3. **Transversal 5.7:** `inkdos:file-launch-error` sem ouvintes. O seletor nativo falha em silêncio em 5 apps (Documents, Spreadsheets, TXT, EPUB, PDF); o `launchQueue`, em 2 (TXT, PDF).

## 8. Inconsistências visuais
V1–V15 (seção 4.3). As prioritárias:
- V1 (diálogo do Presentations);
- V2 (TXT fora do sistema: header, botão de menu, paleta escura, drawer);
- V3 (controle de aparência duplicado em TXT, EPUB e PDF);
- V4 (`Escape` no drawer);
- V12 (erro de gravação intitulado "could not be opened").

Diferenças **deliberadas e aceitas**: cor de destaque por app, superfície papel do EPUB, páginas brancas de documento/slide/PDF.

## 9. Problemas funcionais
S1, S2, P1, P2 (FAIL). 5.7 (FAIL transversal). T1, T2, T3, E1, E2, D1, D2, D3 e tema da Home (WARNING). Nenhum dos seis apps oferece recuperação de sessão ao usuário.

## 10. Problemas de performance (somente os medidos)
- TXT com 13 MB: abertura de ~4 s e **~1,3 s de latência por tecla**.
- Spreadsheets com 20k linhas: abertura de ~4 s com uma long task de 2,3 s.
- Documents grande: abertura de 0,7 s com long task de 0,3 s (aceitável).
- EPUB: o indicador de página atrasa ~400 ms em relação ao conteúdo.

## 11. Pontos fortes (comprovados)
- Isolamento real: zero referências entre apps. Validadores e mapa independente concordam.
- Direto ≡ Home em 12/12 combinações. Offline completo nos 6 apps, com instalação pela Home ou por um app direto.
- Save seguro nos 6: nunca sobrescreve o original. Cancelar e errar mantém o estado sujo. Os arquivos salvos por Documents, Presentations, TXT, EPUB e PDF são válidos em ferramentas independentes.
- Guards de dirty state em Open, New, Home e `beforeunload` nos 5 editores.
- Arquivos inválidos, vazios ou com extensão errada **nunca destroem o documento aberto** (6/6).
- Parsers com limites anti-DoS; CSP estrita; o risco do pdf.js está mitigado.
- Arquivos pequenos e médios abrem em 60–390 ms. O PDF mostra a primeira página legível em 0,39 s (3 p.) / 0,52 s (400 p.) com first-page-first.
- Esqueleto visual comum real: tokens, header, drawer, cartão de início e status bar.

## 12. Cobertura
| Item | Quantidade |
|---|---|
| Apps | 6 (+ Home) |
| Rotas | 7 diretas (`/`, `/apps/<6>/`) + 6 Home→app + 6 app→Home→app |
| Temas | 2 (claro, escuro) × 24 combinações visuais |
| Controles | 475 descobertos / 370 clicados (audit exaustivo) + 46 checagens condicionais + ~120 interações roteirizadas |
| Estados | 302 passos funcionais: abrir, editar, desfazer, salvar, cancelar, erro de escrita, guard (Cancel/Discard), inválido, vazio, extensão errada, binário, New, reabrir, troca, reload, Home, offline, launchQueue, picker nativo |
| Arquivos | 32 fixtures (DOCX, DOC, RTF, XLSX, XLS, PPTX, PPT, TXT, MD, JSON, EPUB×3, PDF×3, grandes×6, inválidos/vazios×11) + 7 arquivos salvos reabertos |
| Testes | 173 testes do repo executados individualmente + 12 roteiros funcionais + 5 roteiros transversais + 4 baterias de performance (5 repetições) |
| Navegadores | Chromium 141 (desktop e viewport iPad emulado). **Firefox e WebKit: NOT VERIFIED** |
| Não verificado | site publicado, WebKit/Safari/iPadOS, Firefox, dispositivo real, iCloud File Provider, instalação PWA real (`launchQueue` do sistema), Share, Print, Excel/Word/PowerPoint abrindo os arquivos salvos, hover/active, contraste WCAG formal, Tauri desktop |

## 13. Separação final

**Comprovadamente correto:**
- isolamento entre apps;
- equivalência entre abertura direta e via Home;
- offline;
- CSP;
- limites de parsing;
- Save/Cancel/erro de escrita preservando o estado;
- validade dos arquivos salvos (exceto Spreadsheets S1);
- guards de alterações (exceto a apresentação do Presentations);
- tratamento de inválidos, vazios e extensão errada preservando o documento;
- performance de arquivos pequenos e médios;
- first-page-first do PDF.

**Precisa de correção** (proposta, não executada):

| Prioridade | Item | Escopo provável |
|---|---|---|
| 1 | S1 — reescrever/mesclar `styles.xml` a cada serialização | `apps/spreadsheets/io/` |
| 2 | P1/V1 — CSS local de overlay/card para o guard | `apps/presentations/` |
| 3 | 5.7 — ouvinte de `inkdos:file-launch-error` que mostre o erro no diálogo de cada app; opcionalmente, `types` no `showOpenFilePicker` | por app, respeitando a duplicação deliberada |
| 4 | S2 — guard duplicado | Spreadsheets |
| 5 | P2 / E1 — tratar 0 bytes antes do teste de orçamento | Presentations, EPUB |
| 6 | V12 — título/ação do erro de gravação | Documents, Spreadsheets, Presentations |
| 7 | TXT com arquivos grandes: política de modo grande (somente leitura ou virtualização) acima de N MB; recuperação: expor ou parar de gravar checkpoints | TXT |
| 8 | Padronização visual V2–V11, sem tocar outros apps "por consistência" antes de decisão do mantenedor | vários |
| 9 | Testes: remover ou atualizar os 6 testes obsoletos, exigir `controlsDiscovered > 0` e adicionar regressões para S1, P1 e 5.7 | `tests/` |

**Ainda não verificado:** ver a última linha da seção 12. Em especial: **todo o comportamento em WebKit/iPad**, que é o alvo principal.
