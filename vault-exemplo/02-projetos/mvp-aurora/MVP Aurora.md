---
type: projeto
projeto: MVP Aurora
status: em-execucao
cliente: "[[../../03-clientes/aurora/Aurora|Aurora]]"
---

# MVP Aurora — Automação de Obrigações Fiscais

> Demonstração anonimizada — dados fictícios. Mostra como uma **entrega com início, meio e fim** fica separada do **relacionamento contínuo** com o cliente.

## Por que projeto e não cliente?

A pasta `03-clientes/aurora/` guarda o **relacionamento** (quem são, contrato, stakeholders). Este arquivo guarda a **entrega**: escopo, cronograma e entregáveis aceitos. Quando o MVP terminar, ele vira arquivo — o cliente continua ativo.

## Escopo (da proposta aprovada)

- Ingestão NFS-e via API da prefeitura + parser XML (NF-e 55, CT-e)
- Motor DAS / ISS / retenções com memória de cálculo auditável
- Dashboard do mês + relatório comentado em linguagem simples + PDF com marca Aurora
- Go-live assistido com 5 clientes piloto

## Cronograma

| Sprint | Período | Marco de aceite |
|---|---|---|
| 1 | semanas 1–2 | Ingestão lendo NFS-e de homologação |
| 2 | semanas 3–4 | 3 cenários de ISS validados por Paulo |
| 3 | semanas 5–6 | Relatório aprovado por Mariana |
| 4 | semanas 7–8 | Go-live + rollback documentado |

## Entregáveis e evidências

Cada entregável tem dono único, prazo e evidência (PR/teste). O painel completo fica em `exemplos/acompanhamento-projeto.html` na pasta da live.

## Pendências ativas

- Credencial de produção da prefeitura — **bloqueia o go-live** (ver pendência no cliente).
- Estimativa da fase 2 (folha) — faixa R$ 12–18 mil, a apresentar como contrato separado.

## Decisões

- **09/09:** pedido de folha tratado como fase 2 — não afeta o cronograma do MVP.
- **04/09:** relatório passa a ter seção "o que pagar, quando e por quê" em linguagem simples (requisito do cliente via WhatsApp).
