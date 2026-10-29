import os
import sys
import glob
import time
import shutil
import getpass
import threading
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# Carrega variáveis de ambiente
load_dotenv()

USUARIO_ATUAL = getpass.getuser()
SUBPASTA = os.getenv("SUBPASTA_DESTINO", r"Dados\Bases")
PASTA_DESTINO = os.path.join(r"C:\Users", USUARIO_ATUAL, SUBPASTA)
PASTA_DOWNLOADS = os.path.join(r"C:\Users", USUARIO_ATUAL, "Downloads")
URL_BASE_LOGIN = os.getenv("URL_PORTAL_LOGIN", "https://intranet.exemplo.com/login.asp")
ARQUIVO_LOG = os.path.join(PASTA_DESTINO, "historico_execucoes.csv")

def obter_perfil_firefox():
    pasta_profiles = os.path.join(r"C:\Users", USUARIO_ATUAL, r"AppData\Roaming\Mozilla\Firefox\Profiles")
    if not os.path.exists(pasta_profiles):
        return None
    perfis = glob.glob(os.path.join(pasta_profiles, "*default-release*"))
    if not perfis:
        perfis = glob.glob(os.path.join(pasta_profiles, "*default*"))
    return max(perfis, key=os.path.getmtime) if perfis else None

CAMINHO_PERFIL = obter_perfil_firefox()

ARQUIVOS_CONFIG = [
    {"codigo": "SGPE001", "nomeplan": "quadrao_x", "url": os.getenv("URL_RELATORIO_01", f"{URL_BASE_LOGIN}/rel1.asp"), "nome": "quadrao_x_ATUAL.csv"},
    {"codigo": "SGPE002", "nomeplan": "HAP_42", "url": os.getenv("URL_RELATORIO_02", f"{URL_BASE_LOGIN}/rel2.asp"), "nome": "HAP_42_ATUAL.csv"},
    {"codigo": "SGPE003", "nomeplan": "Dependentes", "url": os.getenv("URL_RELATORIO_03", f"{URL_BASE_LOGIN}/rel3.asp"), "nome": "Dependentes_ATUAL.csv"},
    {"codigo": "SGPE004", "nomeplan": "Enderecos", "url": os.getenv("URL_RELATORIO_04", f"{URL_BASE_LOGIN}/rel4.asp"), "nome": "Enderecos_ATUAL.csv"},
    {"codigo": "SGPE009", "nomeplan": "Substitutos - caixinha", "url": os.getenv("URL_RELATORIO_05", f"{URL_BASE_LOGIN}/rel5.asp"), "nome": "substitutos_ccustos_ATUAL.csv"},
    {"codigo": "SGPE010", "nomeplan": "Substitutos - lider", "url": os.getenv("URL_RELATORIO_06", f"{URL_BASE_LOGIN}/rel6.asp"), "nome": "substitutos_lider_ATUAL.csv"},
    {"codigo": "SGPE011", "nomeplan": "incidencias_rubricas", "url": os.getenv("URL_RELATORIO_07", f"{URL_BASE_LOGIN}/rel7.asp"), "nome": "incidencias_rubricas_ATUAL.csv"},
    {"codigo": "SGPE012", "nomeplan": "ferias_LP", "url": os.getenv("URL_RELATORIO_08", f"{URL_BASE_LOGIN}/rel8.asp"), "nome": "ferias_LP_ATUAL.csv"},
    {"codigo": "SGPE016", "nomeplan": "afst_todos", "url": os.getenv("URL_RELATORIO_09", f"{URL_BASE_LOGIN}/rel9.asp"), "nome": "afst_todos.csv"},
    {"codigo": "SGPE017", "nomeplan": "cedidos_ativos", "url": os.getenv("URL_RELATORIO_10", f"{URL_BASE_LOGIN}/rel10.asp"), "nome": "cedidos_ativos.csv"},
    {"codigo": "SGPE30", "nomeplan": "lotc_todas", "url": os.getenv("URL_RELATORIO_11", f"{URL_BASE_LOGIN}/rel11.asp"), "nome": "Lotc_todas.csv"},
    {"codigo": "SGPE31", "nomeplan": "fconf_todas", "url": os.getenv("URL_RELATORIO_12", f"{URL_BASE_LOGIN}/rel12.asp"), "nome": "fconf_todas.csv"},
    {"codigo": "SGPE32", "nomeplan": "dadsfunc_todas", "url": os.getenv("URL_RELATORIO_13", f"{URL_BASE_LOGIN}/rel13.asp"), "nome": "dads_func_todos_com_horarios.csv"}
]

def limpar_travas():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "firefox.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    except Exception:
        pass
    if CAMINHO_PERFIL:
        trava = os.path.join(CAMINHO_PERFIL, "parent.lock")
        if os.path.exists(trava):
            try:
                os.remove(trava)
            except Exception:
                pass

def obter_proximo_indice():
    if not os.path.exists(ARQUIVO_LOG):
        return 1
    ultimo = 0
    try:
        with open(ARQUIVO_LOG, "r", encoding="utf-8-sig") as f:
            for linha in f:
                linha_limpa = linha.strip()
                if not linha_limpa:
                    continue
                partes = linha_limpa.split(";")
                if partes and partes[0].isdigit():
                    ultimo = int(partes[0])
        return ultimo + 1
    except Exception:
        return 1

def registrar_log(i, codigo, nomeplan, inicio_str, fim_str, tempo_s, tentativas=5):
    cabecalho = "i;codigo;nomeplan;data-hora inicio;data-hora fim;tempo decorrido (s);quem\n"
    linha = f"{i};{codigo};{nomeplan};{inicio_str};{fim_str};{tempo_s};{USUARIO_ATUAL}\n"
    for _ in range(tentativas):
        try:
            existe = os.path.exists(ARQUIVO_LOG)
            with open(ARQUIVO_LOG, "a", encoding="utf-8-sig") as f:
                if not existe:
                    f.write(cabecalho)
                f.write(linha)
            return True
        except PermissionError:
            time.sleep(1.5)

    # Registo de contingência caso o ficheiro esteja bloqueado no Excel
    log_backup = os.path.join(PASTA_DESTINO, f"historico_execucoes_{datetime.now().strftime('%Y%m%d')}.csv")
    try:
        existe_bkp = os.path.exists(log_backup)
        with open(log_backup, "a", encoding="utf-8-sig") as f:
            if not existe_bkp:
                f.write(cabecalho)
            f.write(linha)
    except Exception:
        pass
    return False

def mover_com_seguranca(origem, destino, tentativas=5):
    for _ in range(tentativas):
        try:
            if os.path.exists(destino):
                os.remove(destino)
            shutil.move(origem, destino)
            return True
        except PermissionError:
            time.sleep(1)
        except Exception:
            break
    return False

class AppRPA(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Robô Extrator de Bases")
        self.geometry("680x520")
        self.minsize(580, 420)

        self.evento_login = threading.Event()
        self.driver = None

        self._criar_interface()

    def _criar_interface(self):
        frame_topo = ttk.Frame(self, padding=10)
        frame_topo.pack(fill="x")

        ttk.Label(frame_topo, text="Automação de Extração de Bases", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(frame_topo, text=f"Operador: {USUARIO_ATUAL} | Destino: {PASTA_DESTINO}", foreground="gray").pack(anchor="w")

        frame_botoes = ttk.Frame(self, padding=10)
        frame_botoes.pack(fill="x")

        self.btn_iniciar = ttk.Button(frame_botoes, text="1. Iniciar Processo", command=self.iniciar_automacao)
        self.btn_iniciar.pack(side="left", padx=5)

        self.btn_continuar = ttk.Button(frame_botoes, text="2. Continuar após Login", command=self.confirmar_login, state="disabled")
        self.btn_continuar.pack(side="left", padx=5)

        self.progresso = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.progresso.pack(fill="x", padx=15, pady=5)

        frame_log = ttk.LabelFrame(self, text="Consola de Execução", padding=5)
        frame_log.pack(fill="both", expand=True, padx=15, pady=10)

        self.txt_log = scrolledtext.ScrolledText(frame_log, wrap="word", font=("Consolas", 9))
        self.txt_log.pack(fill="both", expand=True)

    def log(self, mensagem):
        self.txt_log.insert(tk.END, mensagem + "\n")
        self.txt_log.see(tk.END)

    def iniciar_automacao(self):
        self.btn_iniciar.config(state="disabled")
        self.txt_log.delete("1.0", tk.END)
        self.progresso["value"] = 0
        self.evento_login.clear()

        t = threading.Thread(target=self._rotina_execucao, daemon=True)
        t.start()

    def confirmar_login(self):
        self.btn_continuar.config(state="disabled")
        self.evento_login.set()

    def _rotina_execucao(self):
        os.makedirs(PASTA_DESTINO, exist_ok=True)
        os.makedirs(PASTA_DOWNLOADS, exist_ok=True)

        self.log("[*] A verificar processos do Firefox...")
        limpar_travas()

        options = Options()
        if CAMINHO_PERFIL and os.path.exists(CAMINHO_PERFIL):
            options.add_argument("-profile")
            options.add_argument(CAMINHO_PERFIL)

        options.page_load_strategy = 'eager'
        options.accept_insecure_certs = True
        options.set_preference("security.enterprise_roots.enabled", True)
        options.set_preference("security.tls.version.min", 1)
        options.set_preference("security.tls.version.enable-deprecated", True)
        options.set_preference("network.proxy.type", 5)

        options.set_preference("browser.download.folderList", 1)
        options.set_preference("browser.download.dir", PASTA_DOWNLOADS)
        options.set_preference("browser.download.useDownloadDir", True)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream,text/csv,text/plain,application/vnd.ms-excel")
        options.set_preference("pdfjs.disabled", True)

        try:
            self.driver = webdriver.Firefox(options=options)
            self.driver.set_page_load_timeout(300)

            self.log(f"[*] Acedendo ao portal: {URL_BASE_LOGIN}")
            try:
                self.driver.get(URL_BASE_LOGIN)
            except Exception as e:
                self.log(f"[!] Aviso no carregamento: {e}")

            self.log("\n" + "=" * 50)
            self.log(" AÇÃO NECESSÁRIA:")
            self.log(" Conclua a autenticação na janela do Firefox.")
            self.log(" Em seguida, clique em '2. Continuar após Login'.")
            self.log("=" * 50 + "\n")

            self.btn_continuar.config(state="normal")
            self.evento_login.wait()

            indice_atual = obter_proximo_indice()
            self.progresso["maximum"] = len(ARQUIVOS_CONFIG)

            for idx, item in enumerate(ARQUIVOS_CONFIG, start=1):
                url = item["url"]
                nome_final = item["nome"]
                caminho_final = os.path.join(PASTA_DESTINO, nome_final)

                t0 = time.time()
                dt_inicio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                self.log(f"A descarregar [{item['codigo']} - {item['nomeplan']}]: {nome_final}...")
                arquivos_antes = set(os.listdir(PASTA_DOWNLOADS))
                self.driver.execute_script("window.location.href = arguments[0];", url)

                novo_arquivo = None
                tempo_espera = time.time()
                while time.time() - tempo_espera < 300:
                    atuais = set(os.listdir(PASTA_DOWNLOADS))
                    novos = atuais - arquivos_antes
                    completos = [f for f in novos if not f.endswith(".part")]
                    partes = [f for f in novos if f.endswith(".part")]
                    if completos and not partes:
                        novo_arquivo = os.path.join(PASTA_DOWNLOADS, completos[0])
                        break
                    time.sleep(2)

                if novo_arquivo:
                    if mover_com_seguranca(novo_arquivo, caminho_final):
                        self.log(f"    [OK] Concluído: {nome_final}")
                else:
                    time.sleep(3)
                    conteudo = self.driver.execute_script("return document.body ? document.body.innerText : '';")
                    if conteudo and (";" in conteudo or "," in conteudo) and len(conteudo) > 50:
                        try:
                            with open(caminho_final, "w", encoding="utf-8-sig", errors="replace") as f:
                                f.write(conteudo.strip())
                            self.log(f"    [OK] Conteúdo em tela extraído: {nome_final}")
                        except PermissionError:
                            self.log(f"    [!] Ficheiro em uso: {nome_final}")

                t1 = time.time()
                dt_fim = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                registrar_log(indice_atual, item["codigo"], item["nomeplan"], dt_inicio, dt_fim, int(t1 - t0))
                indice_atual += 1
                self.progresso["value"] = idx

            self.log(f"\n[✔] Processamento concluído!\nRegisto guardado em: {ARQUIVO_LOG}")
            messagebox.showinfo("Sucesso", "Todas as bases foram descarregadas com sucesso!")

        except Exception as erro:
            self.log(f"\n[ERRO CRÍTICO] {erro}")
            messagebox.showerror("Erro", f"Ocorreu uma falha: {erro}")

        finally:
            self.log("[*] A encerrar o navegador...")
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            self.btn_iniciar.config(state="normal")
            self.btn_continuar.config(state="disabled")

if __name__ == "__main__":
    app = AppRPA()
    app.mainloop()