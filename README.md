# 🤖 RPA Desktop: Automação Resiliente de Extração e Auditoria de Dados Legados

Aplicação Desktop desenvolvida em Python para orquestrar downloads automatizados, tratamento de consultas assíncronas e governança de auditoria em portais legados de intranet (.ASP).

---

## 💡 Contexto, Dores e Processo de Decisão

### O Cenário Inicial e os Gargalos
Em rotinas corporativas de análise e engenharia de dados, a dependência de extrações manuais em portais legados gera fricção constante:
* **Tempo improdutivo e tarefas repetitivas**: Necessidade de autenticar manualmente, navegar em dezenas de tabelas individuais, aguardar processamento e salvar uma a uma.
* **Fadiga de processo e erro humano**: Riscos frequentes de renomear arquivos incorretamente, sobrescrever versões erradas ou esquecer bases essenciais para os relatórios do setor.
* **Bloqueio de recursos e timeouts**: Portais baseados em arquiteturas legadas que demoram para processar consultas pesadas no banco de dados, resultando em quedas de sessão ou arquivos incompletos.
* **Falta de rastreabilidade**: Inexistência de métricas claras sobre quem baixou, quando baixou e quanto tempo cada base levou para ser gerada.

### A Jornada de Desenvolvimento
A solução foi arquitetada em duas fases com foco contínuo no usuário final:
1. **Versão 1.0 (Automação de Núcleo / CLI)**: Focada em validar a viabilidade técnica via script Python, manipulando o navegador de forma silenciosa, suprimindo caixas de diálogo do Windows e criando a rotina de monitoramento de diretório.
2. **Versão 2.0 (Produto Desktop / GUI & Executável)**: Ao perceber que colegas de equipe sem familiaridade com terminais ou ambientes Python precisavam utilizar a ferramenta, o script foi encapsulado em uma interface gráfica nativa em **Tkinter**, desacoplado com execução assíncrona em **Threads** (para impedir congelamento de tela) e empacotado em **arquivo executável (.exe)** independente.

---

## 🔒 Desenvolvimento Seguro (AppSec) e Segurança da Informação

O projeto foi construído seguindo diretrizes rigorosas de **Security by Design** e conformidade com diretrizes de privacidade (LGPD):

### 1. Higienização de Metadados e Topologia de Rede
* **Zero Hardcoding**: Nenhuma URL interna de homologação/produção, subdomínio institucional, endereço de IP ou estrutura de pastas locais foi exposta no código-fonte.
* **Segregação de Variáveis (`.env`)**: A configuração de endpoints e diretórios é desacoplada através de variáveis de ambiente locais, impedindo vazamento acidental em versionamento de código.
* **Auditoria de Commits (`.gitignore`)**: Arquivos de perfil de rede, históricos de auditoria (`.csv`), travas de lock (`parent.lock`) e dados baixados são sumariamente ignorados pelo controle de versão.

### 2. Autenticação e Gestão Segura de Sessão
* **Autenticação Assistida (No Credential Storage)**: O robô não armazena login ou senha em arquivos de texto, código ou memória. A autenticação é executada diretamente pelo operador humano na camada de aplicação do navegador.
* **Herança Segura de Perfil Corporativo**: A automação utiliza a infraestrutura de certificados corporativos e negociação de rede (Kerberos/NTLM) já validada pelo sistema operacional, sem contornar as políticas de segurança da estação de trabalho.

### 3. Concorrência e Integridade de I/O
* **Prevenção de Locks e Corrupção**: Tratamento contra travas de arquivos concorrentes (como arquivos abertos no Microsoft Excel), utilizando estratégias de substituição atômica (`os.replace`) e gravação resiliente em fila de logs.
* **Higienização de Preferências**: Rotinas seguras para garantir que preferências globais de download da máquina não sejam sobrescritas permanentemente, preservando o comportamento usual do navegador do operador.

---

## 🛠️ Stack Tecnológica e Bibliotecas Utilizadas

* **Python 3.13**: Linguagem base para desenvolvimento da lógica e manipulação de arquivos.
* **Selenium WebDriver**: Orquestração e controle da camada de visualização e navegação web.
* **Tkinter & Ttk**: Criação da interface gráfica de usuário (GUI) nativa, sem necessidade de dependências pesadas externas.
* **Threading**: Gerenciamento de tarefas em segundo plano para manter a interface fluida durante chamadas bloqueantes de rede.
* **PyInstaller**: Compilação e empacotamento da aplicação em executável autônomo (*standalone*).
* **Python-dotenv**: Gerenciamento seguro de configurações de ambiente e parâmetros sensíveis.

---

## 🚀 Como Executar

### Opção 1: Via Executável (.exe) - Usuário Final
1. Baixe o executável `app_robo.exe` disponível na aba **Releases**.
2. Dê dois cliques no arquivo para abrir a aplicação.
3. Clique em **1. Iniciar Processo**, autentique-se no navegador e clique em **2. Continuar após Login**.

### Opção 2: Via Código-fonte (Desenvolvimento)
1. Clone o repositório:
   ```bash
   git clone [https://github.com/tevatech/robo.git](https://github.com/tevatech/robo.git)
   cd robo
