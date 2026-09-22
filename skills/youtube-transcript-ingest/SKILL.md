---
name: youtube-transcript-ingest
description: Transcreve vídeo do YouTube via script bundlado e ingere no vault classificado por área de estudo. Use quando o usuário passar uma URL do YouTube com `/youtube-ingest <url>` ou pedir "transcrever esse vídeo", "ingerir esse vídeo", "trazer esse vídeo pro vault". Roda `scripts/transcribe-youtube/transcribe.py`, gera frontmatter Obsidian-ready, classifica entre `research/estudos/` e `personal/Estudos/`, busca repos GitHub mencionados e atualiza o índice.
---

# YouTube Ingest — Transcrição → Vault classificado

Pipeline completo: roda script Python bundlado em `scripts/transcribe-youtube/` → classifica conteúdo → escreve no vault com frontmatter padrão → busca repos GitHub mencionados → atualiza índice de estudos.

## Pré-requisitos

- Projeto `transcribe-youtube` bundlado em `scripts/transcribe-youtube/` (relativo à pasta `skills/youtube-transcript-ingest/` deste repositório). Setup inicial:
  ```bash
  cd skills/youtube-transcript-ingest/scripts/transcribe-youtube
  python -m venv venv
  ./venv/bin/pip install -r requirements.txt
  cp .env.example .env   # preencha OPENAI_API_KEY antes de rodar
  ```
- Estrutura do vault com `research/estudos/` (técnico) e `personal/Estudos/` (gestão/finanças/pessoal). O `vault-exemplo/` deste repositório já vem com essa estrutura criada.
- Todos os comandos `bash` deste skill assumem que o cwd é a **raiz do vault**.

## Passo 1 — Receber URL

A URL vem em `$ARGUMENTS` quando o usuário invoca `/youtube-ingest <url>`. Aceitar formatos: `https://www.youtube.com/watch?v=ID`, `https://youtu.be/ID`, ou só `ID`.

Se `$ARGUMENTS` estiver vazio, perguntar:

> "Qual a URL do vídeo do YouTube?"

Se o usuário também passar uma **descrição adicional do vídeo** (ex: lista de ferramentas mencionadas), guardar esse texto — é útil no Passo 6 para enriquecer a busca de repos.

## Passo 2 — Rodar transcribe.py

Bash one-liner (sem source venv):

```bash
cd skills/youtube-transcript-ingest/scripts/transcribe-youtube && \
./venv/bin/python transcribe.py "<URL>"
```

- Mostrar a saída em tempo real: extração de ID, busca de legendas, fallback para Whisper quando necessário, custo estimado.
- Tempo típico: 5–30s com legendas; 1–5min se cair em Whisper.
- Se der `403` do yt-dlp, mencionar a opção `YTDLP_COOKIES_FILE` no `.env`.

Após sucesso, capturar o nome do arquivo gerado:

```bash
ls -t skills/youtube-transcript-ingest/scripts/transcribe-youtube/transcricao_*.md | head -1
```

Padrão do nome: `transcricao_<VIDEO_ID>_<YYYYMMDD>_<HHMMSS>.md`

## Passo 3 — Ler transcrição e extrair metadados

Estrutura esperada do arquivo:

```
# Transcrição do Vídeo

**Video ID:** <ID>
**URL:** https://www.youtube.com/watch?v=<ID>
**Método:** <Legendas do YouTube | GPT-4o Audio (OpenAI)>
**Data:** DD/MM/YYYY HH:MM:SS

---

<conteúdo da transcrição em texto puro>
```

Extrair: `video_id`, `url`, `method`, `date_full`, `date_iso` (YYYY-MM-DD para frontmatter), `content` (tudo depois do `---`).

## Passo 4 — Classificar (auto-detect 2 níveis)

### Nível 1 — research vs personal

| Destino | Quando |
|---|---|
| `research/estudos/` | Técnico: programação, IA, ferramentas dev, arquitetura de software, modelos LLM, hardware GPU, RAG, agentes IA, harness engineering, spec-driven dev, startups AI-native, código aberto, frameworks, MCP |
| `personal/Estudos/` | Pessoal/gestão: liderança humana, gestão de equipes, finanças pessoais, tributário, marketing/criação de conteúdo, empreendedorismo focado em consultoria/vendas, produtividade pessoal |

Heurística: vídeo sobre **código/IA/tools/dev** → `research/`. Vídeo sobre **pessoas/dinheiro/marketing/liderança** → `personal/`.

### Nível 2 — subcategoria

Para `research/estudos/`, listar antes de decidir:

```bash
find research/estudos -maxdepth 1 -type d -not -path "*/estudos"
```

Subcategorias de partida (kebab-case): `agentes-ia`, `ai-local`, `arquitetura-software`, `claude-code`, `codigo-ia`, `ferramentas-ai`, `harness-engineering`, `modelos-llm`, `rag-architecture`, `spec-driven-dev`, `outros`.

Para `personal/Estudos/`, listar:

```bash
find personal/Estudos -maxdepth 2 -type d
```

Áreas de partida: `Lideranca e Gestao/`, `Negocios Digitais e Empreendedorismo/`, `Tributario e Reforma Tributaria/`, `Criacao de Conteudo e Marketing/`.

Se nenhuma encaixar bem, criar nova subcategoria (kebab-case em research, Title Case em personal) — e registrar no índice no Passo 8.

## Passo 5 — Gerar slug e título descritivos

A partir do conteúdo, gerar:

- **Título humano** (≤10 palavras, em português, descritivo). Ex: "9 Ferramentas IA para Devs e Agentes em 2026"
- **Slug em kebab-case** (≤6 palavras, sem caracteres especiais, sem acento). Ex: `9-ferramentas-ia-devs-agentes-2026`

Padrão: slug humano no nome do arquivo, **não** o ID do vídeo.

## Passo 6 — Buscar repos GitHub mencionados

Se a transcrição mencionar **≥2 ferramentas/projetos com nomes próprios**, buscar para cada um:

```
"<NomeFerramenta> github" OR "<NomeFerramenta> open source"
```

Critérios:
- Owner deve bater com algum sinal contextual (autor mencionado, organização conhecida).
- Se houver ambiguidade, preferir o que tem mais stars ou foi mais recente.
- Se nenhum match claro, **omitir** a ferramenta — não inventar URL.

## Passo 7 — Reescrever arquivo final no vault

Caminho final: `<destino_base>/<categoria>/<slug>.md`
- Ex research: `research/estudos/ferramentas-ai/9-ferramentas-ia-devs-agentes-2026.md`
- Ex personal: `personal/Estudos/Lideranca e Gestao/<slug>.md`

Se a subpasta não existir, criar via `mkdir -p`.

Conteúdo do arquivo:

```markdown
---
tags:
  - estudo/<categoria-kebab>
up: '[[../../_index|Índice]]'
source: https://www.youtube.com/watch?v=<VIDEO_ID>
date_transcribed: <YYYY-MM-DD>
method: <método original>
---

# <Título humano>

**Video ID:** <ID>
**URL:** https://www.youtube.com/watch?v=<ID>
**Método:** <método original>
**Data:** <DD/MM/YYYY HH:MM:SS>

---

## Recursos / Repositórios mencionados

- **<Nome>** — <descrição curta> — [github.com/owner/repo](https://github.com/owner/repo)
- **<Nome>** — <descrição curta> *(repo não localizado)*

---

<conteúdo original da transcrição>
```

**Regras**:
- Seção "Recursos / Repositórios" só aparece se houver **pelo menos 2** ferramentas mencionadas.
- Para ferramentas sem repo localizado, listar o nome com `*(repo não localizado)*`.
- Para `personal/Estudos/`, o `up` pode ser `'[[../../_master-index|Índice]]'` se a área tiver `_master-index.md`; caso contrário omitir o campo.

## Passo 8 — Atualizar índice

### Para research/estudos/

Editar `research/estudos/index.md`:

1. Localizar a seção `## <Nome da Categoria>` (mapeamento subpasta → nome de seção).
2. Inserir nova linha na tabela em ordem alfabética por slug:
   ```
   | [[<slug>]] | <Título humano> |
   ```
3. Atualizar o rodapé:
   ```
   *Índice gerado em <YYYY-MM-DD>. Total: <N+1> transcrições em <K> categorias.*
   ```

Se a categoria for nova, criar a seção antes de `## Outros` com tabela própria.

### Para personal/Estudos/

Editar `personal/Estudos/_master-index.md` ou o `Índice.md` da subárea, seguindo o padrão observado quando abrir o arquivo.

## Passo 9 — Limpar arquivo original

```bash
rm skills/youtube-transcript-ingest/scripts/transcribe-youtube/transcricao_<ID>_<TS>.md
```

Só executar **após** confirmar escrita bem-sucedida no Passo 7.

## Passo 10 — Reportar ao usuário

Resposta final em ≤5 linhas:

```
Transcrição salva: research/estudos/ferramentas-ai/9-ferramentas-ia-devs-agentes-2026.md
Categoria: ferramentas-ai
Repos encontrados: 6/9 (Caveman, Graphify, ...)
Índice atualizado: 58 → 59 transcrições.
```

## Notas operacionais

- **Custos**: vídeos com legendas do YouTube → grátis. Sem legendas → GPT-4o Audio (~$0.006/min). Avisar antes se for vídeo > 30min sem legendas.
- **Idioma**: o script usa `pt` por padrão. Para vídeo em inglês onde o usuário quer transcrição em inglês, passar `--lang en` no Passo 2.
- **Limite de tamanho**: o script lida com chunks > 25MB automaticamente.
- **Nunca mexer** no script `transcribe.py` — a skill apenas o invoca.
- **Sem credenciais**: o `.env` é local. `OPENAI_API_KEY` nunca entra neste repositório nem em chats.
