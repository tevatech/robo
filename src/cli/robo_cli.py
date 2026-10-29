import os
import sys
import glob
import time
import shutil
import getpass
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# Carrega variáveis de ambiente locais
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

def executar_downloads():
    os.makedirs(PASTA_DESTINO, exist_ok=True)
    os.makedirs(PASTA_DOWNLOADS, exist_ok=True)

    print("[*] A verificar ambiente...")
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

    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(300)

    try:
        try:
            driver.get(URL_BASE_LOGIN)
        except Exception as e:
            print(f"[!] Aviso no carregamento inicial: {e}")

        print("\n" + "=" * 60)
        print(" AÇÃO NECESSÁRIA:")
        print(" Conclua o login na janela do Firefox e pressione ENTER no terminal.")
        print("=" * 60 + "\n")
        input("Pressione [ENTER] para prosseguir...")

        indice_atual = obter_proximo_indice()

        for item in ARQUIVOS_CONFIG:
            url = item["url"]
            nome_final = item["nome"]
            caminho_final = os.path.join(PASTA_DESTINO, nome_final)

            t0 = time.time()
            dt_inicio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            print(f"A descarregar [{item['codigo']} - {item['nomeplan']}]: {nome_final}...")
            arquivos_antes = set(os.listdir(PASTA_DOWNLOADS))
            driver.execute_script("window.location.href = arguments[0];", url)

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
                    print(f"    [OK] Salvo em: {caminho_final}")
            else:
                time.sleep(3)
                conteudo = driver.execute_script("return document.body ? document.body.innerText : '';")
                if conteudo and (";" in conteudo or "," in conteudo) and len(conteudo) > 50:
                    try:
                        with open(caminho_final, "w", encoding="utf-8-sig", errors="replace") as f:
                            f.write(conteudo.strip())
                        print(f"    [OK] Texto gravado em: {caminho_final}")
                    except PermissionError:
                        print(f"    [!] Ficheiro em uso no Excel: {nome_final}")

            t1 = time.time()
            dt_fim = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            registrar_log(indice_atual, item["codigo"], item["nomeplan"], dt_inicio, dt_fim, int(t1 - t0))
            indice_atual += 1

        print("\n[✔] Processamento concluído com sucesso!")
    finally:
        driver.quit()

if __name__ == "__main__":
    executar_downloads()