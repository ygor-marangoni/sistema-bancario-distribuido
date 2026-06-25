# Trabalho 3 - Sistemas Distribuidos

Projeto em Python para demonstrar comunicacao cliente-servidor, threads, concorrencia e sincronizacao.

Link para o Vídeo: https://youtu.be/0ucedOOouSI

Link para o repositório: https://github.com/ygor-marangoni/sistema-bancario-distribuido

## Ideia da aplicacao

O sistema simula uma **conta bancaria compartilhada**.

- O servidor guarda em memoria o saldo e o extrato da conta.
- Varios clientes podem se conectar ao mesmo tempo.
- Cada cliente pode consultar saldo, depositar, sacar e ver o extrato.
- O servidor cria uma thread para cada cliente conectado.
- O saldo e o extrato sao protegidos por `threading.Lock`, evitando condicoes de corrida.

## Arquivos

- `server.py`: servidor TCP multithread.
- `client.py`: cliente TCP interativo ou automatico.
- `demo_multi_clientes.py`: script para abrir varios clientes ao mesmo tempo.
- `Dockerfile`: empacota o servidor em uma imagem Docker.

## Parte A - Rodando sem Docker

Abra um terminal na pasta do projeto e execute o servidor:

```bash
python server.py
```

Em outro terminal, execute um cliente interativo:

```bash
python client.py --name Ygor
```

Para demonstrar varios clientes simultaneamente, deixe o servidor ligado e rode:

```bash
python demo_multi_clientes.py --clients 5 --operations 4
```

Durante essa demonstracao, observe o terminal do servidor. Ele mostra varias threads sendo criadas e atendendo clientes diferentes ao mesmo tempo.

## Parte B - Rodando o servidor com Docker

Crie a imagem Docker:

```bash
docker build -t banco-thread-server .
```

Execute o container, publicando a porta 5000:

```bash
docker run --rm -p 5000:5000 --name servidor-banco banco-thread-server
```

Com o servidor rodando dentro do container, abra outro terminal fora do Docker e execute o cliente local:

```bash
python client.py --host 127.0.0.1 --port 5000 --name Cliente-Fora-Do-Container
```

Tambem e possivel demonstrar varios clientes fora do container:

```bash
python demo_multi_clientes.py --host 127.0.0.1 --port 5000 --clients 5 --operations 4
```
