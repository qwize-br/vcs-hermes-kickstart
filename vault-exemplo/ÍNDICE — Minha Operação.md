---
type: indice-central
area: minha-operacao
status: demonstracao-anonimizada
---

# Índice Central — Minha Operação (exemplo)

Adaptação do modelo QWize para um prestador de serviço individual ou pequena empresa. **Cliente, projetos e fatos são fictícios.** Aplica a lógica áreas / projetos / clientes vista no vault real.

## Navegação

- [[00-global/reunioes/ÍNDICE — Reuniões|Reuniões e triagem]]
- [[00-global/templates/ÍNDICE — Templates|Templates e instruções]]
- [[01-areas/ÍNDICE — Áreas|Áreas da operação]]
- [[02-projetos/ÍNDICE — Projetos|Projetos (internos e entregas)]]
- [[03-clientes/ÍNDICE — Clientes|Clientes e relacionamento]]

## Estrutura

```text
00-global/    políticas, conhecimento reutilizável, reuniões brutas → triagem → distribuição
01-areas/     comercial, desenvolvimento, operação, financeiro — contínuas e globais
02-projetos/  entregas com início e fim (o MVP Aurora, um site, uma integração)
03-clientes/  relacionamentos contínuos (Aurora, Vetor, Lume) — cada um com subpasta própria
```

## O que vai para onde

- **Decisão comercial recorrente** → `01-areas/comercial/`
- **Entrega com prazo definido** (MVP Aurora) → `02-projetos/mvp-aurora/`
- **Contexto do cliente como um todo** (quem são, stakeholders, contrato) → `03-clientes/aurora/`
- **Reunião gravada** → bruto em `00-global/reunioes/00-inbox-brutos` → briefing tratado é **distribuído** para a área + projeto + cliente correspondentes

## Clientes (exemplo)

- [[03-clientes/aurora/Aurora|Aurora Contabilidade Digital]] — projeto ativo: MVP de Obrigações
- [[03-clientes/vetor/Vetor|Vetor Engenharia]] — proposta em negociação
- [[03-clientes/lume/Lume|Clínica Lume]] — projeto: novo site institucional

## Regra de ouro

O bruto nunca é apagado. Toda reunião entra no inbox, passa por triagem, vira briefing e só então o contexto tratado é distribuído para cada cliente, projeto ou área relevante. **Áreas são contínuas e globais; projetos e clientes são destinos separados.**
