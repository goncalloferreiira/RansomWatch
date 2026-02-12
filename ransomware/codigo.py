#!/usr/bin/env python3
"""
SISTEMA EDR - anti-Ransomware
"""

import os
import shutil
import time
import sys
import subprocess
import threading
import winsound
import ctypes
from datetime import datetime
from pathlib import Path

# Verificar dependências primeiro
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_DEPENDENCIES = True
except ImportError as e:
    print(f"ERRO: Dependencia faltando: {e}")
    print("Execute: pip install watchdog colorama")
    HAS_DEPENDENCIES = False
    sys.exit(1)

# ================= CONFIGURAÇÃO =================
class Config:
    # Usar a pasta Música do utilizador atual para evitar erros de permissão
    BASE_DIR = Path.home() / "Music"
    
    WATCH_FOLDER = BASE_DIR / "SistemaMonitorizado"
    SAFE_VAULT = BASE_DIR / "_SAFE"
    HONEYPOT_FOLDER = BASE_DIR / "_SISTEMA_CRITICO_WIN32"
    HONEYPOT_FILE = HONEYPOT_FOLDER / "sistema_config.sys"
    
    # Configurações de deteção
    THRESHOLD_FILES = 5
    THRESHOLD_SECONDS = 3
    BACKUP_INTERVAL = 30
    
    # Configurações Discord
    DISCORD_WEBHOOK = "https://discord.com/api/webhooks/SEU_WEBHOOK_AQUI"
    ENABLE_DISCORD = False
    ENABLE_KILL_SWITCH = True
    LOG_FILE = "relatorio_incidente.txt"

# ================= INICIALIZAÇÃO =================
def setup_system():
    """Prepara o sistema EDR na inicialização"""
    print(Fore.GREEN + "=" * 60)
    print(Fore.GREEN + "iniciando EDR")
    print(Fore.GREEN + "=" * 60)
    
    # Criar estrutura de pastas
    for folder in [Config.WATCH_FOLDER, Config.SAFE_VAULT, Config.HONEYPOT_FOLDER]:
        folder.mkdir(exist_ok=True, parents=True)
    
    create_initial_snapshot()
    create_honeypot()
    setup_logging()
    
    print(Fore.GREEN + "sistema inicializado com sucesso")
    print(Fore.CYAN + f"pasta monitorizada: {Config.WATCH_FOLDER}")
    print(Fore.CYAN + f"cofre seguro: {Config.SAFE_VAULT}")
    print(Fore.YELLOW + f"armadilha (honeypot): {Config.HONEYPOT_FOLDER}")

def create_initial_snapshot():
    """Cria backup inicial da pasta monitorizada"""
    print(Fore.CYAN + "a criar snapshot inicial...")
    
    if Config.SAFE_VAULT.exists():
        shutil.rmtree(Config.SAFE_VAULT)
    
    Config.SAFE_VAULT.mkdir(exist_ok=True)
    
    if Config.WATCH_FOLDER.exists():
        shutil.copytree(Config.WATCH_FOLDER, Config.SAFE_VAULT / "backup_inicial", 
                       dirs_exist_ok=True)
    
    log_event("SYSTEM", "snapshot inicial criado", "SUCCESS")

def create_honeypot():
    """Cria pasta e ficheiro isca para atrair ransomware"""
    print(Fore.CYAN + "configurando armadilha (honeypot)...")
    
    honeypot_content = """[System Configuration]
Windows Kernel File - DO NOT MODIFY
System32 Critical Configuration
BootLoader=Enabled
SecureBoot=Active
EncryptionLevel=Maximum

[Critical Settings]
NetworkSecurity=Enabled
FirewallPolicy=Strict
AutoBackup=Enabled
RansomwareProtection=Active
"""
    
    with open(Config.HONEYPOT_FILE, 'w') as f:
        f.write(honeypot_content)
    
    try:
        subprocess.run(['attrib', '+H', '+S', str(Config.HONEYPOT_FILE)], 
                      capture_output=True)
    except:
        pass
    
    log_event("SYSTEM", f"Honeypot criado: {Config.HONEYPOT_FILE}", "INFO")

def setup_logging():
    """Configura sistema de log"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

# ================= MONITORIZAÇÃO =================
class EDREventHandler(FileSystemEventHandler):
    """Handler para eventos do sistema de ficheiros"""
    
    def __init__(self):
        super().__init__()
        self.file_changes = []
        self.lock = threading.Lock()
        self.attack_detected = False
        self.last_backup = time.time()
    
    def on_created(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path, "CREATED")
            self.backup_file(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path, "MODIFIED")
            if Config.WATCH_FOLDER in Path(event.src_path).parents:
                self.backup_file(event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path, "DELETED")
    
    def on_moved(self, event):
        self.handle_event(event.src_path, f"MOVED to {event.dest_path}")
    
    def handle_event(self, filepath, action):
        with self.lock:
            now = time.time()
            
            # Verificar honeypot (Método A)
            if self.check_honeypot(filepath, action):
                self.trigger_alarm("HoneyPot", f"ataque detectado via honeypot: {filepath}")
                return
            
            # Adicionar à lista de mudanças para heurística
            self.file_changes.append((now, filepath, action))
            
            # Limpar eventos antigos
            self.file_changes = [(t, f, a) for t, f, a in self.file_changes 
                                if now - t < Config.THRESHOLD_SECONDS]
            
            # Verificar heurística (Método B)
            if self.check_behavioral_heuristics():
                self.trigger_alarm("HEURISTIC", f"ataque detectado via heurística: {len(self.file_changes)} ficheiros em {Config.THRESHOLD_SECONDS}s")
            
            # Backup automático periódico
            if now - self.last_backup > Config.BACKUP_INTERVAL:
                self.backup_all_files()
                self.last_backup = now
    
    def check_honeypot(self, filepath, action):
        honeypot_path = str(Config.HONEYPOT_FILE).lower()
        filepath_lower = filepath.lower()
        
        if honeypot_path in filepath_lower:
            print(Fore.RED + "HoneyPot violado")
            print(Fore.RED + f"   arquivo: {filepath}")
            print(Fore.RED + f"   ação: {action}")
            return True
        
        honeypot_dir = str(Config.HONEYPOT_FOLDER).lower()
        if honeypot_dir in filepath_lower:
            print(Fore.YELLOW + "alerta: Atividade na pasta honeypot")
            return True
        
        return False
    
    def check_behavioral_heuristics(self):
        if len(self.file_changes) >= Config.THRESHOLD_FILES:
            extensions = [Path(f).suffix.lower() for _, f, _ in self.file_changes[-Config.THRESHOLD_FILES:]]
            unique_extensions = set(extensions)
            
            if len(unique_extensions) > 2:
                print(Fore.YELLOW + f"comportamento suspeito detectado: {len(self.file_changes)} alterações")
                return True
        
        return False
    
    def backup_file(self, filepath):
        try:
            src_path = Path(filepath)
            if src_path.exists() and src_path.is_file():
                rel_path = src_path.relative_to(Config.WATCH_FOLDER)
                dst_path = Config.SAFE_VAULT / "dynamic_backup" / rel_path
                
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                
                print(Fore.GREEN + f"backup dinâmico: {rel_path}")
        except Exception as e:
            pass
    
    def backup_all_files(self):
        try:
            backup_dir = Config.SAFE_VAULT / f"backup_auto_{int(time.time())}"
            if Config.WATCH_FOLDER.exists():
                shutil.copytree(Config.WATCH_FOLDER, backup_dir, dirs_exist_ok=True)
                print(Fore.CYAN + f"backup automático criado: {backup_dir.name}")
        except:
            pass
    
    def trigger_alarm(self, method, reason):
        if self.attack_detected:
            return
        
        self.attack_detected = True
        threading.Thread(target=lambda: trigger_alarm(method, reason)).start()

# ================= RESPOSTA A AMEAÇAS =================
def trigger_alarm(method, reason):
    """Ativa todos os sistemas de resposta a ameaças"""
    print(Fore.RED + "=" * 60)
    print(Fore.RED + "ALERTA DE SEGURANCA MAXIMA")
    print(Fore.RED + "=" * 60)
    print(Fore.RED + f"Metodo de deteccao: {method}")
    print(Fore.RED + f"Razao: {reason}")
    print(Fore.RED + f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    threading.Thread(target=sound_alarm).start()
    threading.Thread(target=show_alert_popup, args=(method, reason)).start()
    
    if Config.ENABLE_DISCORD:
        threading.Thread(target=send_discord_alert, args=(method, reason)).start()
    
    if Config.ENABLE_KILL_SWITCH:
        threading.Thread(target=activate_network_kill_switch).start()
    
    log_event("ATTACK", f"{method} - {reason}", "CRITICAL")
    threading.Thread(target=auto_recovery).start()

def sound_alarm():
    """Ativa alarme sonoro"""
    try:
        for _ in range(5):
            winsound.Beep(1000, 500)
            winsound.Beep(500, 500)
            time.sleep(0.2)
    except:
        pass

def show_alert_popup(method, reason):
    """Mostra pop-up de alerta no Windows"""
    try:
        title = "alerta EDR"
        message = f"""ameaca de ransomware detetada

Metodo: {method}
Razao: {reason}
Hora: {datetime.now().strftime('%H:%M:%S')}

O sistema iniciara a recuperacao automatica.
"""
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x30 | 0x1)
    except:
        print(Fore.YELLOW + "Nao foi possivel mostrar pop-up")

def send_discord_alert(method, reason):
    """Envia alerta para Discord via webhook"""
    if not Config.DISCORD_WEBHOOK or "SEU_WEBHOOK" in Config.DISCORD_WEBHOOK:
        return
    
    try:
        import requests
        import socket
        
        embed = {
            "title": "ALERTA EDR - ATAQUE DE RANSOMWARE",
            "description": "**Sistema comprometido detectado!**",
            "color": 0xFF0000,
            "fields": [
                {"name": "Metodo", "value": method, "inline": True},
                {"name": "Razao", "value": reason, "inline": True},
                {"name": "Hora", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True},
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        payload = {"embeds": [embed]}
        requests.post(Config.DISCORD_WEBHOOK, json=payload, timeout=5)
        print(Fore.CYAN + "Alerta enviado para o Discord")
        
    except Exception as e:
        print(Fore.YELLOW + f"Erro ao enviar para o Discord: {e}")

def activate_network_kill_switch():
    """Desativa conexões de rede para prevenir exfiltração"""
    print(Fore.RED + "Ativando Network Kill Switch...")
    
    try:
        commands = [
            'powershell -Command "Disable-NetAdapter -Name \'*\' -Confirm:$false"',
            'powershell -Command "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True"',
        ]
        
        for cmd in commands:
            subprocess.run(cmd, shell=True, capture_output=True)
        
        print(Fore.RED + "Rede isolada - Exfiltracao bloqueada")
        log_event("NETWORK", "Kill switch ativado - Rede isolada", "CRITICAL")
        
    except Exception as e:
        print(Fore.YELLOW + f"Erro ao ativar kill switch: {e}")

def auto_recovery():
    """Executa recuperação automática dos ficheiros"""
    print(Fore.GREEN + "INICIANDO RECUPERACAO AUTOMATICA...")
    
    try:
        # 1. Eliminar conteúdo da pasta infetada
        if Config.WATCH_FOLDER.exists():
            print(Fore.YELLOW + "Limpando pasta comprometida...")
            for item in Config.WATCH_FOLDER.iterdir():
                if item.name != "_SAFE":
                    try:
                        if item.is_file():
                            item.unlink()
                        else:
                            shutil.rmtree(item)
                    except:
                        pass
        
        # 2. Restaurar do cofre seguro
        print(Fore.CYAN + "Restaurando ficheiros do cofre seguro...")
        backup_source = Config.SAFE_VAULT / "backup_inicial"
        
        if backup_source.exists():
            shutil.copytree(backup_source, Config.WATCH_FOLDER, dirs_exist_ok=True)
        
        # 3. Restaurar backups dinâmicos
        dynamic_backup = Config.SAFE_VAULT / "dynamic_backup"
        if dynamic_backup.exists():
            shutil.copytree(dynamic_backup, Config.WATCH_FOLDER, dirs_exist_ok=True)
        
        print(Fore.GREEN + "RECUPERACAO COMPLETA!")
        print(Fore.GREEN + "Todos os ficheiros foram restaurados")
        
        try:
            ctypes.windll.user32.MessageBoxW(0, 
                "RECUPERACAO AUTOMATICA COMPLETA!\n\nTodos os ficheiros foram restaurados com sucesso.", 
                "EDR - Sistema Recuperado", 
                0x40 | 0x1)
        except:
            pass
        
        log_event("RECOVERY", "Recuperacao automatica executada com sucesso", "SUCCESS")
        
    except Exception as e:
        print(Fore.RED + f"Erro na recuperacao: {e}")
        log_event("RECOVERY", f"Falha na recuperacao: {e}", "ERROR")

def log_event(category, message, level="INFO"):
    """Regista evento no log forense"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{category}] [{level}] {message}\n"
    
    color_map = {
        "SUCCESS": Fore.GREEN,
        "INFO": Fore.CYAN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED
    }
    
    color = color_map.get(level, Fore.WHITE)
    print(color + log_entry.strip())
    
    with open(Config.LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)

# ================= INTERFACE DE CONTROLE =================
def get_last_incident():
    """Obtém último incidente registado"""
    try:
        with open(Config.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                return lines[-1].strip()
    except:
        pass
    return "Nenhum incidente registado"

def show_incident_log():
    """Mostra log de incidentes"""
    print(Fore.CYAN + "\nLOG DE INCIDENTES")
    print(Fore.CYAN + "=" * 60)
    
    try:
        with open(Config.LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if content:
                print(Fore.WHITE + content)
            else:
                print(Fore.YELLOW + "Nenhum incidente registado")
    except FileNotFoundError:
        print(Fore.YELLOW + "Ficheiro de log nao encontrado")

def menu_interface():
    """Interface de menu em thread separada"""
    while True:
        print(Fore.CYAN + "\n" + "=" * 60)
        print(Fore.CYAN + "EDR ATIVO - Menu de Controle")
        print(Fore.CYAN + "=" * 60)
        print(Fore.WHITE + "1. Criar backup manual")
        print(Fore.WHITE + "2. Ver status do sistema")
        print(Fore.WHITE + "3. Ver log de incidentes")
        print(Fore.WHITE + "4. Testar alarme (simulacao)")
        print(Fore.WHITE + "5. Sair do programa")
        
        try:
            choice = input(Fore.YELLOW + "\nOpcao: ").strip()
            
            if choice == "1":
                create_initial_snapshot()
                print(Fore.GREEN + "Backup manual criado!")
            
            elif choice == "2":
                print(Fore.CYAN + "\nSTATUS DO SISTEMA")
                print(Fore.CYAN + "-" * 40)
                print(Fore.WHITE + f"Pasta monitorizada: {Config.WATCH_FOLDER}")
                
                try:
                    watch_count = sum(1 for _ in Config.WATCH_FOLDER.rglob("*") if _.is_file())
                    safe_count = sum(1 for _ in Config.SAFE_VAULT.rglob("*") if _.is_file())
                    print(Fore.WHITE + f"Ficheiros monitorizados: {watch_count}")
                    print(Fore.WHITE + f"Backups no cofre: {safe_count}")
                except:
                    print(Fore.YELLOW + "Erro ao contar arquivos")
                
                print(Fore.WHITE + f"Honeypot ativo: {Config.HONEYPOT_FILE.exists()}")
                
                last_incident = get_last_incident()
                if "Nenhum" in last_incident:
                    print(Fore.GREEN + f"Ultimo incidente: {last_incident}")
                else:
                    print(Fore.YELLOW + f"Ultimo incidente: {last_incident}")
            
            elif choice == "3":
                show_incident_log()
            
            elif choice == "4":
                print(Fore.YELLOW + "Iniciando teste de alarme...")
                trigger_alarm("TEST", "Teste manual do sistema")
            
            elif choice == "5":
                print(Fore.YELLOW + "A encerrar sistema EDR...")
                os._exit(0)
            
            time.sleep(1)
        except EOFError:
            continue
        except Exception as e:
            print(Fore.RED + f"Erro no menu: {e}")
            time.sleep(2)

# ================= FUNÇÃO PRINCIPAL =================
def main():
    """Função principal do sistema EDR"""
    if not HAS_DEPENDENCIES:
        print("Instale as dependencias primeiro: pip install watchdog colorama")
        return
    
    try:
        setup_system()
        
        event_handler = EDREventHandler()
        observer = Observer()
        observer.schedule(event_handler, str(Config.WATCH_FOLDER), recursive=True)
        observer.schedule(event_handler, str(Config.HONEYPOT_FOLDER), recursive=True)
        
        print(Fore.GREEN + "Iniciando monitorizacao em tempo real...")
        print(Fore.CYAN + "Sistema ativo - Aguardando eventos")
        print(Fore.YELLOW + "-" * 60)
        
        observer.start()
        
        menu_thread = threading.Thread(target=menu_interface, daemon=True)
        menu_thread.start()
        
        print(Fore.CYAN + "Pressione Ctrl+C para encerrar o sistema\n")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nSistema interrompido pelo utilizador")
    except Exception as e:
        print(Fore.RED + f"Erro critico: {e}")
        log_event("SYSTEM", f"Erro critico: {e}", "ERROR")

# ================= EXECUÇÃO =================
if __name__ == "__main__":
    print(Fore.GREEN + """
    SISTEMA EDR AVANCADO - v2.0
    Protecao Ativa Contra Ransomware
    """)
    
    main()