---
name: youtube-transcript-ingest
description: Transcreve vídeo do YouTube e ingere no vault classificado por área de estudo. Use quando usuário passar URL do YouTube ou pedir "transcrever esse vídeo", "ingerir esse vídeo", "trazer esse vídeo pro vault". Roda script bundlado, classifica entre research/estudos ou personal/Estudos, busca repos GitHub mencionados e atualiza índice.
---

# YouTube Transcript Ingest — Transcrição → Vault classificado

Pipeline: transcreve com script Python bundlado → classifica conteúdo → escreve no vault com frontmatter padrão → busca repos GitHub mencionados → atualiza índice de estudos.

## Pré-requisitos
- Script bundlado em `scripts/transcribe-youtube/` (venv + requirements + .env com chaves).
- Estrutura do vault com `research/estudos/` (técnico) e `personal/Estudos/` (gestão/pessoal).
- Cwd dos comandos = **raiz do vault**.

## Pipeline (resumo)

1. **Receber URL** (`/youtube-transcript-ingest <url>` ou linguagem natural).
2. **Rodar script:** `cd scripts/transcribe-youtube && ./venv/bin/python transcribe.py "<URL>"` → gera `transcricao_<ID>_<TS>.md`.
3. **Classificar:** técnico → `research/estudos/<categoria>/`; gestão/pessoal → `personal/Estudos/<Área>/`.
4. **Slug + título** humano em pt-BR, kebab-case no nome do arquivo.
5. **Repos GitHub** mencionados: buscar e incluir seção "Recursos / Repositórios" quando ≥2.
6. **Escrever no vault** com frontmatter (`tags`, `up`, `source`, `date_transcribed`, `method`).
7. **Atualizar índice** (`research/estudos/index.md` ou `personal/Estudos/_master-index.md`).
8. **Limpar** o arquivo bruto temporário.
9. **Reportar** ao usuário em ≤5 linhas.

## Saída final (exemplo)

```
Transcrição salva: research/estudos/agentes-ia/hermes-masterclass-dexter.md
Categoria: agentes-ia
Repos encontrados: 4/6
Índice atualizado: 58 → 59 transcrições.
```

**Nunca editar o script `transcribe.py`** — a skill apenas o invoca.
