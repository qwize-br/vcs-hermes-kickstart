# Bootstrap do agente — kickstart dinâmico

Este repositório é lido pelo Hermes quando o usuário pede para "construir meu workspace a partir deste repo". Se você é o agente executando isso, siga este roteiro. **Não improvise etapas fora desta lista sem perguntar.**

## O que este repositório é

- `install.sh` — cria um workspace **novo** (nunca sobrescreve), com vault starter ou cópia local, e skills didáticas Comms/Dev/PM.
- `vault-exemplo/` — modelo anonimizado de organização (cliente fictício "Aurora"). Serve de referência ou de `--vault-source`.
- `skills/` — modelos de skills que o install.sh copia para `hermes-home/skills/`.

## Roteiro — quando o usuário pedir o setup a partir deste repo

1. **Localização do repo.** Se o usuário passou uma URL git, faça `git clone <url> kickstart-src` em um diretório temporário (não na raiz do HOME). Se já está dentro do repo clonado, pule para 3.
2. **Revisão obrigatória.** Rode `bash -n kickstart-src/install.sh` e mostre o hash: `sha256sum kickstart-src/install.sh`. Pergunte: "Revisou o script? Posso executar?" Só continue com confirmação.
3. **Perguntas antes de executar** (não execute sem estas respostas):
   - "Qual caminho absoluto você quer para o workspace? (ex.: `$HOME/workspace` — não pode existir)"
   - "Quer usar o vault de exemplo `vault-exemplo/` como ponto de partida, tem um vault local seu para copiar, ou prefere starter mínimo vazio?"
   - "Nesta máquina/Cloud já existe Hermes instalado? Se não, você autoriza `--install-hermes` (baixa o instalador oficial)?" — **no Hermes Cloud a resposta padrão é "já existe"; NÃO use `--install-hermes`.**
4. **Executar:**
   ```bash
   bash kickstart-src/install.sh --workspace "<CAMINHO ABSOLUTO>" [--vault-source "kickstart-src/vault-exemplo" | --vault-source "<caminho do usuário>"]
   ```
5. **Verificar o resultado:**
   - `cat "$WS/outputs/bootstrap.json"` — deve dizer `"status": "bootstrap-complete"`.
   - `"$WS/bin/hermes-workspace" --version` — confirma launcher.
6. **Iniciar a configuração (com o launcher, nunca `hermes` solto):**
   ```bash
   "$WS/bin/hermes-workspace" model        # escolher provider/modelo — guia interativo
   "$WS/bin/hermes-workspace" doctor
   ```
   **Importante:** `model`/`setup` abrem OAuth/chave de forma interativa. Rode e entregue a URL/instruções ao usuário; **nunca peça nem cole token em chat** — o usuário completa no terminal.
7. **Entrevista de personalização** (depois de `model` funcionando), uma pergunta por vez:
   - nome e como prefere ser chamado;
   - principal objetivo com o agente (produtividade pessoal, prestador de serviço, conteúdo);
   - canal preferido (terminal agora; Telegram depois);
   - se quer manter as skills Comms/Dev/PM ou renomear/remover alguma.
8. **Gravar o que aprendeu** em `$WS/PROJECT.md` e `$WS/DECISIONS.md` (via `patch`/`write_file`).
9. **Encerrar com resumo honesto:** o que ficou configurado, o que depende do usuário (token, Telegram), e os próximos passos.

## Regras rígidas

- Use **sempre** `"$WS/bin/hermes-workspace"` para qualquer comando Hermes deste workspace. Ele isola o estado em `hermes-home/` e `runtime-user/`; `hermes` puro no Cloud operaria no perfil da própria Cloud e misturaria contextos.
- Não execute `kickstart-src/install.sh` sem `bash -n` + hash + confirmação do usuário.
- Não use `--install-hermes` dentro do Hermes Cloud (o Hermes já está instalado pela Nous). Só faz sentido em máquina própria onde `hermes` não existe.
- Não prometa Telegram, Drive ou MCPs — a configuração de canais vem depois, manual, seguindo `README.md` seção 6.
- Se o usuário interromper ou algo falhar, pare e relate. Não tente corrigir reexecutando no mesmo workspace (ele recusa segunda execução de propósito).
