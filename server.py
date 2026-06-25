import argparse
import json
import socket
import threading
import time
from datetime import datetime
from typing import Any, Dict, Tuple


class ContaCompartilhada:
    """
    Recurso compartilhado do servidor.

    Varios clientes podem tentar consultar/depositar/sacar ao mesmo tempo.
    Por isso, todas as operacoes que leem ou alteram saldo/extrato usam Lock.
    """

    def __init__(self) -> None:
        self.saldo = 0.0
        self.extrato = []
        self.lock = threading.Lock()

    def consultar_saldo(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "ok": True,
                "mensagem": "Saldo consultado com sucesso.",
                "saldo": round(self.saldo, 2),
            }

    def depositar(self, valor: float, cliente: str) -> Dict[str, Any]:
        if valor <= 0:
            return {"ok": False, "mensagem": "O valor do deposito deve ser maior que zero."}

        with self.lock:
            # Pequena pausa para deixar a concorrencia mais visivel na demonstracao.
            time.sleep(0.25)
            self.saldo += valor
            registro = self._registrar_operacao("DEPOSITO", valor, cliente)
            return {
                "ok": True,
                "mensagem": f"Deposito de R$ {valor:.2f} realizado.",
                "saldo": round(self.saldo, 2),
                "registro": registro,
            }

    def sacar(self, valor: float, cliente: str) -> Dict[str, Any]:
        if valor <= 0:
            return {"ok": False, "mensagem": "O valor do saque deve ser maior que zero."}

        with self.lock:
            time.sleep(0.25)
            if valor > self.saldo:
                return {
                    "ok": False,
                    "mensagem": f"Saldo insuficiente para sacar R$ {valor:.2f}.",
                    "saldo": round(self.saldo, 2),
                }

            self.saldo -= valor
            registro = self._registrar_operacao("SAQUE", valor, cliente)
            return {
                "ok": True,
                "mensagem": f"Saque de R$ {valor:.2f} realizado.",
                "saldo": round(self.saldo, 2),
                "registro": registro,
            }

    def listar_extrato(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "ok": True,
                "mensagem": "Extrato consultado com sucesso.",
                "saldo": round(self.saldo, 2),
                "extrato": list(self.extrato),
            }

    def _registrar_operacao(self, tipo: str, valor: float, cliente: str) -> Dict[str, Any]:
        registro = {
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "tipo": tipo,
            "valor": round(valor, 2),
            "cliente": cliente,
            "saldo_apos_operacao": round(self.saldo, 2),
        }
        self.extrato.append(registro)
        return registro


conta = ContaCompartilhada()


def log_servidor(mensagem: str) -> None:
    agora = datetime.now().strftime("%H:%M:%S")
    nome_thread = threading.current_thread().name
    print(f"[{agora}] [{nome_thread}] {mensagem}", flush=True)


def enviar_json(conexao_file, dados: Dict[str, Any]) -> None:
    linha = json.dumps(dados, ensure_ascii=False) + "\n"
    conexao_file.write(linha.encode("utf-8"))
    conexao_file.flush()


def processar_requisicao(requisicao: Dict[str, Any], endereco: Tuple[str, int]) -> Dict[str, Any]:
    comando = str(requisicao.get("comando", "")).strip().upper()
    cliente = str(requisicao.get("cliente") or f"{endereco[0]}:{endereco[1]}")

    try:
        valor = float(requisicao.get("valor", 0))
    except (TypeError, ValueError):
        return {"ok": False, "mensagem": "Valor invalido. Envie um numero."}

    if comando == "SALDO":
        return conta.consultar_saldo()
    if comando == "DEPOSITAR":
        return conta.depositar(valor, cliente)
    if comando == "SACAR":
        return conta.sacar(valor, cliente)
    if comando == "EXTRATO":
        return conta.listar_extrato()
    if comando == "SAIR":
        return {"ok": True, "mensagem": "Conexao finalizada pelo cliente."}

    return {
        "ok": False,
        "mensagem": "Comando desconhecido. Use: SALDO, DEPOSITAR, SACAR, EXTRATO ou SAIR.",
    }


def gerenciar_cliente(conexao: socket.socket, endereco: Tuple[str, int]) -> None:
    log_servidor(f"Cliente conectado: {endereco[0]}:{endereco[1]}")

    with conexao:
        conexao_file = conexao.makefile("rwb")
        enviar_json(
            conexao_file,
            {
                "ok": True,
                "mensagem": "Conectado ao servidor da conta compartilhada.",
                "comandos": ["SALDO", "DEPOSITAR", "SACAR", "EXTRATO", "SAIR"],
            },
        )

        while True:
            linha = conexao_file.readline()
            if not linha:
                break

            try:
                requisicao = json.loads(linha.decode("utf-8"))
            except json.JSONDecodeError:
                enviar_json(conexao_file, {"ok": False, "mensagem": "JSON invalido."})
                continue

            comando = str(requisicao.get("comando", "")).upper()
            log_servidor(f"Recebido de {endereco}: {requisicao}")
            resposta = processar_requisicao(requisicao, endereco)
            enviar_json(conexao_file, resposta)

            if comando == "SAIR":
                break

    log_servidor(f"Cliente desconectado: {endereco[0]}:{endereco[1]}")


def iniciar_servidor(host: str, porta: int) -> None:
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, porta))
    servidor.listen()

    log_servidor(f"Servidor iniciado em {host}:{porta}")
    log_servidor("Aguardando conexoes de clientes...")

    try:
        while True:
            conexao, endereco = servidor.accept()
            thread = threading.Thread(
                target=gerenciar_cliente,
                args=(conexao, endereco),
                daemon=True,
                name=f"Cliente-{endereco[1]}",
            )
            thread.start()
            log_servidor(f"Thread criada para {endereco[0]}:{endereco[1]}")
    except KeyboardInterrupt:
        log_servidor("Servidor encerrado manualmente.")
    finally:
        servidor.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor multithread de conta bancaria compartilhada")
    parser.add_argument("--host", default="0.0.0.0", help="Host do servidor")
    parser.add_argument("--port", type=int, default=5000, help="Porta do servidor")
    args = parser.parse_args()

    iniciar_servidor(args.host, args.port)
