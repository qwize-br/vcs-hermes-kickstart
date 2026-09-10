# vault-exemplo — Modelo de Operação (anonimizado)

Mini-vault demonstrativo adaptado do modelo QWize real (`~/Obsidian/projects/qwize`), para uso na live e como ponto de partida do kickstart.

## O que mostra

1. **Estrutura áreas / projetos / clientes** — a divisão que mantém a operação organizada quando entram mais clientes.
2. **Regra do inbox** — reunião gravada (Plaud) entra bruta, vira briefing, e só o contexto tratado é distribuído.
3. **Separação relacionamento × entrega** — cliente (contínuo) ≠ projeto (tem fim).
4. **Ingestão de conteúdo de referência** — integra com o skill `youtube-transcript-ingest` (YouTube → vault classificado por área de estudo).

## Arquivos

```
vault-exemplo/
  ÍNDICE — Minha Operação.md        ← índice central (comece por aqui)
  00-global/
    templates/TEMPLATE — Cliente.md
    reunioes/02-processadas/2026-09-07-status-aurora.md   ← briefing processado com distribuição
  01-areas/INSTRUÇÕES.md            ← por que áreas são contínuas
  02-projetos/mvp-aurora/MVP Aurora.md                    ← entrega com início/meio/fim
  03-clientes/aurora/Aurora.md                            ← relacionamento contínuo
```

Todos os dados são **fictícios** (cliente Aurora Contabilidade Digital). A estrutura, os frontmatters e a regra de distribuição são **idênticos aos do vault real**.

## Como isso se conecta ao Hermes

- O agente **PM** lê `02-projetos/mvp-aurora/` e `03-clientes/aurora/` para gerar o painel de acompanhamento.
- O agente **Comms** usa `03-clientes/` para saber quem é quem antes de triar e-mails/WhatsApp.
- A skill `youtube-transcript-ingest` joga conteúdo de estudo em `research/estudos/` ou `personal/Estudos/` do vault real — fora do âmbito deste exemplo.
