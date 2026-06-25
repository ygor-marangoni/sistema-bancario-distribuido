import argparse
import json
import random
import socket
import time
from typing import Any, Dict


def enviar_json(conexao_file, dados: Dict[str, Any]) -> None:
    linha = json.dumps(dados, ensure_ascii=False) + "\n"
    conexao_file.write(linha.encode("utf-8"))
    conexao_file.flush()


def receber_json(conexao_file) -> Dict[str, Any]:
    linha = conexao_file.readline()
    if not linha:
        raise ConnectionError("Servidor encerrou a conexao.")
    return json.loads(linha.decode("utf-8"))


def imprimir_resposta(resposta: Dict[str, Any]) -> None:
    status = "OK" if resposta.get("ok") else "ERRO"
    print(f"[{status}] {resposta.get('mensagem')}")

    if "saldo" in resposta:
        print(f"Saldo atual: R$ {float(resposta['saldo']):.2f}")

    if resposta.get("extrato"):
        print("\nExtrato:")
        for item in resposta["extrato"]:
            print(
                f"- {item['data_hora']} | {item['tipo']} | "
                f"R$ {item['valor']:.2f} | {item['cliente']} | "
                f"saldo: R$ {item['saldo_apos_operacao']:.2f}"
            )

    print()


def montar_requisicao_interativa(nome_cliente: str) -> Dict[str, Any]:
    print("Escolha uma opcao:")
    print("1 - Consultar saldo")
    print("2 - Depositar")
    print("3 - Sacar")
    print("4 - Ver extrato")
    print("0 - Sair")
    opcao = input("Opcao: ").strip()

    if opcao == "1":
        return {"cliente": nome_cliente, "comando": "SALDO"}
    if opcao == "2":
        valor = float(input("Valor do deposito: R$ ").replace(",", "."))
        return {"cliente": nome_cliente, "comando": "DEPOSITAR", "valor": valor}
    if opcao == "3":
        valor = float(input("Valor do saque: R$ ").replace(",", "."))
        return {"cliente": nome_cliente, "comando": "SACAR", "valor": valor}
    if opcao == "4":
        return {"cliente": nome_cliente, "comando": "EXTRATO"}
    if opcao == "0":
        return {"cliente": nome_cliente, "comando": "SAIR"}

    return {"cliente": nome_cliente, "comando": "INVALIDO"}


def executar_cliente_interativo(host: str, porta: int, nome_cliente: str) -> None:
    with socket.create_connection((host, porta)) as conexao:
        conexao_file = conexao.makefile("rwb")
        boas_vindas = receber_json(conexao_file)
        imprimir_resposta(boas_vindas)

        while True:
            try:
                requisicao = montar_requisicao_interativa(nome_cliente)
            except ValueError:
                print("Valor invalido. Tente novamente.\n")
                continue

            enviar_json(conexao_file, requisicao)
            resposta = receber_json(conexao_file)
            imprimir_resposta(resposta)

            if requisicao["comando"] == "SAIR":
                break


def executar_cliente_demo(host: str, porta: int, nome_cliente: str, operacoes: int) -> None:
    comandos_possiveis = ["DEPOSITAR", "SACAR", "SALDO"]

    with socket.create_connection((host, porta)) as conexao:
        conexao_file = conexao.makefile("rwb")
        imprimir_resposta(receber_json(conexao_file))

        for indice in range(operacoes):
            # A primeira operacao sempre deposita para deixar a demonstracao mais clara.
            # Depois disso, os clientes fazem operacoes variadas ao mesmo tempo.
            comando = "DEPOSITAR" if indice == 0 else random.choice(comandos_possiveis)
            valor = random.choice([10, 20, 30, 50, 100])
            requisicao = {"cliente": nome_cliente, "comando": comando, "valor": valor}
            print(f"{nome_cliente} enviando: {requisicao}")
            enviar_json(conexao_file, requisicao)
            imprimir_resposta(receber_json(conexao_file))
            time.sleep(random.uniform(0.1, 0.6))

        enviar_json(conexao_file, {"cliente": nome_cliente, "comando": "SAIR"})
        imprimir_resposta(receber_json(conexao_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente da conta bancaria compartilhada")
    parser.add_argument("--host", default="127.0.0.1", help="Host do servidor")
    parser.add_argument("--port", type=int, default=5000, help="Porta do servidor")
    parser.add_argument("--name", default="Cliente", help="Nome exibido no extrato")
    parser.add_argument("--demo", action="store_true", help="Executa operacoes automaticas para demonstracao")
    parser.add_argument("--operations", type=int, default=5, help="Quantidade de operacoes no modo demo")
    args = parser.parse_args()

    if args.demo:
        executar_cliente_demo(args.host, args.port, args.name, args.operations)
    else:
        executar_cliente_interativo(args.host, args.port, args.name)
