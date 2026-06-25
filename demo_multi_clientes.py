import argparse
import subprocess
import sys
import time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Abre varios clientes simultaneamente para demonstrar concorrencia")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--clients", type=int, default=5)
    parser.add_argument("--operations", type=int, default=4)
    args = parser.parse_args()

    processos = []

    for i in range(1, args.clients + 1):
        nome = f"Cliente-{i}"
        processo = subprocess.Popen(
            [
                sys.executable,
                "client.py",
                "--host",
                args.host,
                "--port",
                str(args.port),
                "--name",
                nome,
                "--demo",
                "--operations",
                str(args.operations),
            ]
        )
        processos.append(processo)
        time.sleep(0.1)

    for processo in processos:
        processo.wait()

    print("\nDemonstracao finalizada: todos os clientes terminaram.")
