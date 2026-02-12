#!/usr/bin/env python3
"""
Simulador de Ransomware 
"""

import os
import time
import random
import string
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

class RansomwareSimulator:
    def __init__(self):
        base = Path.home() / "Music"
        self.target_folder = base / "SistemaMonitorizado"
        self.honeypot_folder = base / "_SISTEMA_CRITICO_WIN32"
        self.encrypted_ext = ".encrypted"
        self.ransom_note = """
=== Os seus arquivos foram criptografados ===

Todos os seus documentos, fotos, bancos de dados e outros arquivos importantes
foram criptografados com um algoritmo forte.

Para descriptografar os seus arquivos, você precisa de:
1. Pagar 0.5 BC para o seguinte endereço: 1BtcoinAdDr3s5Fake123456789
2. Enviar um email para: exemplo@comiocudequemleu.com o seu ID

ID do seu computador: {id}

Tens 72 horas. Depois disso, a chave será destruída.

NÃO tente descriptografar por conta própria.
NÃO reinicie o computador.
"""
    
    def generate_fake_id(self):
        """Gera um ID de resgate falso"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    
    def simulate_encryption(self, filepath):
        """Simula criptografia (apenas renomeia com extensão)"""
        try:
            new_name = filepath.with_suffix(filepath.suffix + self.encrypted_ext)
            filepath.rename(new_name)
            return True
        except:
            return False
    
    def attack_honeypot_first(self):
        """Ataca primeiro o honeypot (comportamento típico)"""
        print(Fore.RED + "A ATACAR HONEYPOT (armadilha)...")
        
        if self.honeypot_folder.exists():
            for file in self.honeypot_folder.rglob("*"):
                if file.is_file():
                    if self.simulate_encryption(file):
                        print(Fore.RED + f"Criptografado: {file.name}")
                        return True
        return False
    
    def rapid_encryption_attack(self):
        """Simula ataque rápido de encriptação em massa"""
        print(Fore.RED + "INICIANDO MASS ATTACK...")
        
        files = list(self.target_folder.rglob("*"))
        random.shuffle(files)
        
        # Limitar a 15 ficheiros para demonstração
        files = files[:15]
        
        encrypted_count = 0
        start_time = time.time()
        
        for file in files:
            if file.is_file() and not file.name.startswith("."):
                time.sleep(0.1)  # Pequena pausa para parecer real
                
                if self.simulate_encryption(file):
                    encrypted_count += 1
                    print(Fore.RED + f"{encrypted_count:2d}. {file.name}")
        
        elapsed = time.time() - start_time
        print(Fore.RED + f"\nAtaque concluído em {elapsed:.1f}s")
        print(Fore.RED + f"Total criptografado: {encrypted_count} arquivos")
        
        return encrypted_count
    
    def drop_ransom_note(self):
        """Cria nota de resgate"""
        ransom_file = self.target_folder / "LEIA-ME_RESGATE.txt"
        
        with open(ransom_file, 'w', encoding='utf-8') as f:
            f.write(self.ransom_note.format(id=self.generate_fake_id()))
        
        print(Fore.RED + f"Nota de resgate criada: {ransom_file.name}")
    
    def exfiltrate_data_simulation(self):
        """Simula exfiltração de dados"""
        print(Fore.RED + "SIMULANDO EXFILTRAÇÃO DE DADOS...")
        
        # Simular coleta de dados sensíveis
        fake_data = [
            "senhas.txt",
            "cartoes_credito.csv", 
            "documentos_pessoais.zip",
            "historico_navegacao.db"
        ]
        
        for data_file in fake_data:
            print(Fore.RED + f"Enviando: {data_file}")
            time.sleep(0.5)
        
        print(Fore.RED + "Dados exfiltrados com sucesso")
    
    def run_demonstration(self):
        """Executa demonstração completa"""
        print(Fore.RED + """
╔══════════════════════════════════════════════════╗
║               SIMULADOR DE RANSOMWARE            ║
╚══════════════════════════════════════════════════╝
        """)
        
        print(Fore.YELLOW + "Este simulador demonstra como um ransomware real ataca.")
        print(Fore.YELLOW + "O sistema EDR deve detectar e bloquear este ataque.\n")
        
        input(Fore.CYAN + "Pressione ENTER para iniciar ataque simulado...")
        
        print(Fore.RED + "\n" + "=" * 60)
        print(Fore.RED + "INICIANDO SIMULAÇÃO DE RANSOMWARE")
        print(Fore.RED + "=" * 60)
        
        # Passo 1: Exfiltrar dados primeiro
        self.exfiltrate_data_simulation()
        time.sleep(1)
        
        # Passo 2: Atacar honeypot
        self.attack_honeypot_first()
        time.sleep(1)
        
        # Passo 3: Ataque em massa rápido
        print(Fore.RED + "\nA ATIVAR CRIPTOGRAFIA EM MASSA...")
        self.rapid_encryption_attack()
        time.sleep(1)
        
        # Passo 4: Deixar nota de resgate
        self.drop_ransom_note()
        
        print(Fore.RED + "\n" + "=" * 60)
        print(Fore.RED + "SIMULAÇÃO CONCLUÍDA")
        print(Fore.RED + "=" * 60)
        
        print(Fore.YELLOW + "\nO sistema EDR deve ter:")
        print(Fore.YELLOW + "1. Detetado o ataque via honeypot")
        print(Fore.YELLOW + "2. Cortado a conexão de internet")
        print(Fore.YELLOW + "3. Alertado o administrador")
        print(Fore.YELLOW + "4. Restaurado os arquivos automaticamente")
        
        input(Fore.CYAN + "\nPressione ENTER para ver o estado dos arquivos...")
        
        # Mostrar estado final
        self.show_current_state()

    def show_current_state(self):
        """Mostra estado atual dos arquivos"""
        print(Fore.CYAN + "\nESTADO ATUAL DOS ARQUIVOS:")
        print(Fore.CYAN + "-" * 40)
        
        if self.target_folder.exists():
            files = list(self.target_folder.rglob("*"))
            encrypted = [f for f in files if f.suffix == self.encrypted_ext]
            normal = [f for f in files if f.suffix != self.encrypted_ext and f.is_file()]
            
            print(Fore.RED + f"Criptografados: {len(encrypted)}")
            for f in encrypted[:5]:  # Mostrar apenas 5
                print(Fore.RED + f"   • {f.name}")
            
            if len(encrypted) > 5:
                print(Fore.RED + f"   ... e mais {len(encrypted)-5}")
            
            print(Fore.GREEN + f"\nNormais: {len(normal)}")
            for f in normal[:3]:
                print(Fore.GREEN + f"   • {f.name}")

def main():
    """Função principal do simulador"""
    simulator = RansomwareSimulator()
    
    choice = input(Fore.CYAN + "Iniciar simulação? (s/n): ").strip().lower()
    
    if choice == 's':
        simulator.run_demonstration()
    else:
        print(Fore.GREEN + "Simulação cancelada.")

if __name__ == "__main__":
    main()