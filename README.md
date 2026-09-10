# Hermes Kickstart — guia pt-BR

Bootstrap didático para a live Hermes / Vibe Coding Society. **Não é um clone do ambiente do André nem uma reprodução exata de processos da QWize.** Nenhum vault pessoal foi incluído. Nenhum serviço fica conectado automaticamente.

## O que você recebe

- `AGENTS.md` (na raiz): roteiro que o Hermes lê automaticamente ao entrar no repo — clone → `bash -n` + hash + confirmação → entrevista curta → `install.sh` → `bin/hermes-workspace model` (token digitado pelo usuário, nunca em chat) → entrevista de personalização → gravar em PROJECT/DECISIONS. Já vem com a regra de **nunca usar `--install-hermes` no Hermes Cloud** (o agente Cloud já é o Hermes rodando).
- `install.sh`: arquivo único Bash com Python embutido; não depende deste repositório para funcionar.
- Workspace **novo**, vault local opcional e modelos de skills **Comms, Dev e PM**.
- `hermes-home/`: estado dedicado do Hermes; `runtime-user/`: HOME dedicado para ferramentas.
- `bin/hermes-workspace`: launcher que seleciona esses diretórios sem trocar o perfil default.
- Testes locais em `tests/`; evidências de execução em `outputs/`.

**Bootstrap não é instalação upstream.** Sem `--install-hermes`, não há download, execução do Hermes, setup de provider, criação de bot, serviço persistente, MCP, Drive ou sincronização.

## 1. Pré-requisitos e limites

Use um usuário comum, **sem sudo**. Plataformas alvo: Linux, macOS e Bash dentro do **WSL2**; não execute no PowerShell ou Git Bash. Bash 3.2+ e **Python 3.8+** são requisitos deste kickstart. A etapa upstream também precisa de `curl` e Git; no Linux, veja o requisito `xz-utils` na documentação oficial. O kickstart não instala seus próprios pré-requisitos.

```bash
bash --version
python3 --version
```

O diretório pai do workspace deve existir e ser gravável. Use caminhos absolutos entre aspas; espaços são aceitos. Não use `.` ou `..`, caracteres de controle, links simbólicos ou destinos dentro de `.hermes`/`HERMES_HOME`. No macOS, caminhos como `/tmp` podem ser links: use o caminho físico, obtido com `pwd -P`. Não selecione `/`, seu HOME inteiro ou um perfil como vault.

Não crie o diretório final antes de executar: até um destino **vazio existente** é recusado. Segunda execução no mesmo destino falha de propósito e preserva os arquivos.

## 2. Baixar, revisar, executar

**A URL abaixo é PLACEHOLDER e NÃO FOI PUBLICADA.** O domínio `.invalid` é propositalmente inválido. O responsável pela distribuição deverá publicar e substituir a URL antes de compartilhar comandos de download. Não existe link remoto funcional deste kickstart neste momento.

```bash
# EXEMPLO NÃO OPERACIONAL: substitua por URL realmente publicada e confiável.
KICKSTART_URL='https://SEU-DOMINIO.invalid/hermes-kickstart/install.sh'
# noclobber protege um install.sh local já existente.
(set -C; curl --proto '=https' --proto-redir '=https' -fSL "$KICKSTART_URL" > install.sh)
less install.sh
bash -n install.sh
# Execute somente depois de revisar o arquivo e confirmar o download.
```

Alternativa disponível agora: use o `install.sh` local entregue com este guia. Não precisa copiar os testes para o computador de destino. Não recomendamos `curl | bash`: baixar e revisar torna visível o código que será executado. Se um download falhar e deixar um arquivo parcial, inspecione-o e baixe com um novo nome.

### Já tenho Hermes, ou quero apenas os arquivos

```bash
bash install.sh --workspace "$HOME/Hermes Live" --dry-run
bash install.sh --workspace "$HOME/Hermes Live"
```

O launcher usa a instalação dedicada se existir; caso contrário, procura um **executável `hermes` no PATH**. Não aceita apenas uma função/alias de shell. Se não encontrar, informa a ausência; não instala silenciosamente. Ele não compartilha credenciais do Hermes existente.

### Ainda preciso instalar Hermes — opt-in explícito

Use **outro destino novo** caso já tenha executado o exemplo anterior:

```bash
bash install.sh --workspace "$HOME/Hermes Live Completo" --install-hermes --dry-run
bash install.sh --workspace "$HOME/Hermes Live Completo" --install-hermes
```

Este opt-in autoriza baixar e executar **somente o instalador oficial** `https://hermes-agent.nousresearch.com/install.sh`. Ele é salvo em `outputs/official-install.sh`, tem sintaxe validada e SHA-256 registrado. O hash é evidência dos bytes baixados, **não assinatura/autenticidade nem versão fixada**. O endpoint upstream é móvel; revise a versão vigente antes de optar por executá-la. A compatibilidade futura não é garantida.

O upstream recebe `--skip-setup --skip-browser --skip-computer-use --no-skills --non-interactive`, `--dir` e `--hermes-home` explícitos, com ambiente limpo e HOME dentro do workspace. Não instala desktop, não configura provider nem inicia canal pelo kickstart. Browser/computer-use ficam pendentes; as skills oficiais não são semeadas por essa opção, apenas os três modelos locais.

**Importante:** HOME dedicado e HERMES_HOME são separação de estado, não sandbox de segurança. O instalador oficial pode instalar dependências e usar gerenciadores de pacotes/sudo disponíveis no sistema. Se você não autoriza alterações de dependências na máquina, **não use `--install-hermes` nela**: execute em VM/conta descartável ou instale Hermes separadamente segundo a documentação. A instalação upstream real não foi executada no host desta entrega.

## 3. Trazer um vault local (opcional)

```bash
bash install.sh --workspace "$HOME/Hermes com Vault" \
  --vault-source "$HOME/Minha copia revisada do vault" --dry-run
bash install.sh --workspace "$HOME/Hermes com Vault" \
  --vault-source "$HOME/Minha copia revisada do vault"
```

Combine com `--install-hermes` somente se também desejar a etapa upstream.

- Copia o conteúdo para `vault/`, incluindo arquivos ocultos. Não baixa Drive, não sincroniza e não modifica a origem.
- Não usa uma origem presumida. Sem `--vault-source`, cria apenas um **modelo didático** com README, inbox, projetos e conhecimento canônico vazio.
- Revise a origem antes: remova credenciais, dados de terceiros sem consentimento, `.git` sensível, plugins e scripts que não deseja carregar. Não há sanitização automática nem detecção completa de segredos.
- Links simbólicos, sockets, FIFOs e outros arquivos especiais são recusados. Permissões não são preservadas: cópia privada, sem bit executável. Não é um backup fiel de metadados.
- Copiar `AGENTS.md`, prompts ou plugins **não os valida**. O instalador não executa conteúdo do vault; abrir esse vault em outro aplicativo ou mudar o diretório do agente pode ativar regras/plugins. Faça revisão humana antes.
- Não altere a origem nem seus diretórios ancestrais durante a cópia. Este bootstrap não protege contra outro processo malicioso rodando com o mesmo usuário.

## 4. Conferir o workspace

```text
Hermes Live/
├── AGENTS.md, PROJECT.md, CONTEXT.md, DECISIONS.md
├── bin/hermes-workspace
├── hermes-home/skills/
│   ├── kickstart-comms/SKILL.md
│   ├── kickstart-dev/SKILL.md
│   └── kickstart-pm/SKILL.md
├── runtime-user/
├── vault/
└── outputs/bootstrap.json
```

`bootstrap.json` só aparece ao concluir. Com opt-in, a conclusão exige também launcher upstream executável e `--version` bem-sucedido. Isso **não comprova autenticação nem serviços conectados**. `outputs/INCOMPLETE` sinaliza execução incompleta. Em falha não há limpeza destrutiva ou sobrescrita: preserve a evidência, corrija a causa e escolha outro destino novo. Não reexecute no destino parcial.

Não mova o workspace depois da instalação upstream: virtualenvs/launchers podem conter caminhos absolutos. Mantenha `hermes-home/`, `runtime-user/`, `vault/` e `outputs/` fora de Git. O `.gitignore` gerado ajuda, mas não substitui a revisão de arquivos antes de publicar.

## 5. Configurar provider manualmente

Nos exemplos seguintes, ajuste `WS` para o destino que você realmente criou. **Use sempre o launcher, não `hermes` solto**, para não mexer no seu perfil normal.

```bash
WS="$HOME/Hermes Live"
"$WS/bin/hermes-workspace" --version
"$WS/bin/hermes-workspace" config path
"$WS/bin/hermes-workspace" config env-path
"$WS/bin/hermes-workspace" model
"$WS/bin/hermes-workspace" config set terminal.cwd "$WS"
"$WS/bin/hermes-workspace" doctor
"$WS/bin/hermes-workspace" skills list
```

Confirme que os caminhos exibidos ficam em `$WS/hermes-home`. `model` abre a seleção oficial de provider/modelo e autenticação. Como alternativa ao seletor, o assistente completo é `"$WS/bin/hermes-workspace" setup`. Escolha sua conta e complete OAuth/chave API no assistente; não cole tokens em apresentações, chats, screenshots ou comandos gravados no histórico.

O ambiente do launcher é deliberadamente limpo: tokens, perfil ativo, proxy, SSH agent e variáveis de ferramentas do shell não são herdados. Configure credenciais **deste workspace** pelo CLI. Segredos vão para `.env`/armazenamento OAuth em `hermes-home/`; configurações normais são geridas por `config set`. Não edite YAML manualmente. OAuth pode exigir abrir a URL exibida em outro navegador, pois variáveis da sessão gráfica não são repassadas.

Após autenticar, faça um teste que pode consumir créditos:

```bash
"$WS/bin/hermes-workspace" chat -q 'Responda apenas: conexão de modelo validada.'
```

Só a resposta real confirma esse teste. `doctor` pode apontar ferramentas opcionais ausentes; não esconda esses alertas. Skills Comms, Dev e PM são instruções, **não três bots nem integrações provisionadas**.

## 6. Telegram manual — somente depois do provider funcionar

1. No Telegram, fale com **@BotFather**, use `/newbot` e guarde o token em segredo. Use um bot exclusivo, não o token de outro gateway.
2. Obtenha seu **ID numérico de usuário** (por exemplo via @userinfobot). Não confunda com @username ou ID de grupo.
3. Execute o assistente oficial e selecione Telegram. Informe token e **apenas os IDs autorizados**; não use `*`.

```bash
"$WS/bin/hermes-workspace" gateway setup
# Leia os prompts e restrinja o acesso antes de iniciar.
"$WS/bin/hermes-workspace" gateway run
```

Envie `/start` e uma pergunta pelo usuário permitido, confira a resposta e os logs. Esse teste é manual, usa rede e pode consumir créditos. Comece em DM; grupos exigem revisão de permissões/privacy mode. Nunca exiba o token na live; se vazar, revogue pelo BotFather.

O gateway acima roda **em primeiro plano** e depende do terminal/processo ativo. Pare com `Ctrl+C`. Este guia não instala serviço systemd/launchd, não usa `gateway install/start` e não promete disponibilidade 24h. Não registre serviços enquanto não revisar a estratégia de instalação e o HOME dedicado.

## 7. Segurança, manutenção e testes

O launcher bloqueia seleção explícita de outro perfil e comandos `profile`, `update`, `uninstall` para evitar mudanças globais acidentais. Isso não é controle de acesso contra um usuário malicioso. Não use comandos de administração global, dashboard ou serviços para tentar modificar perfis reais por esse ambiente. Não faça atualização do binário compartilhado a partir do kickstart; consulte o procedimento oficial e revise o escopo separadamente.

O agente ainda tem as permissões do usuário do sistema: HOME dedicado **não impede leitura/escrita fora do workspace**. Para conteúdo não confiável, use isolamento de execução real, conta separada ou VM e mantenha aprovações habilitadas.

```bash
# Dentro da pasta da entrega, como usuário comum:
python3 tests/run_tests.py
```

Os testes executam Bash e cópia/validação reais em sandboxes temporários sob `outputs/`. A rede e o instalador upstream são **fixtures explícitas** apenas nos testes de opt-in/falha; nenhum Hermes é instalado. O relatório registra os resultados de verdade. macOS e WSL2 são plataformas alvo, mas esta entrega foi exercitada em Linux; o teste de root via user namespace é pulado se o host o bloquear. Não extrapole esses resultados para instalação completa, autenticação ou Telegram.

## Fontes oficiais consultadas

- [Instalação](https://hermes-agent.nousresearch.com/docs/getting-started/installation)
- [Instalador oficial](https://hermes-agent.nousresearch.com/install.sh) e [fonte dos argumentos](https://github.com/NousResearch/hermes-agent/blob/main/scripts/install.sh)
- [CLI](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)
- [Configuração](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)
- [Perfis e HERMES_HOME](https://hermes-agent.nousresearch.com/docs/user-guide/profiles)
- [Telegram](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram)

Se um comando divergir da versão instalada, consulte `"$WS/bin/hermes-workspace" <comando> --help` e a documentação oficial antes de mudar a configuração.
