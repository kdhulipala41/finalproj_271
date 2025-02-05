import hashlib
import time
import threading
import socket
import json
from blockchain import Blockchain
from client import Client


def master_cli():
    clients = {
        "A": ("127.0.0.1", 6000),
        "B": ("127.0.0.1", 6001),
        "C": ("127.0.0.1", 6002)
    }

    while True:
        command = input("> ").strip().split()
        if not command:
            continue

        if command[0] == "transfer" and len(command) == 4:
            sender, receiver, amount = command[1], command[2], int(command[3])
            transaction = {"type": "transfer", "sender": sender, "receiver": receiver, "amount": amount}
            # Send the transaction to the sender client
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(clients[sender])
                s.sendall(json.dumps({"type": "COMMAND", "command": "transfer", "transaction": transaction}).encode())
        elif command[0] == "balance":
            # Retrieve balances from all clients
            balances = {}
            for client_id, (ip, port) in clients.items():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(json.dumps({"type": "COMMAND", "command": "balance"}).encode())
                    data = s.recv(8192)
                    try:
                        client_balance = json.loads(data.decode())
                        balances.update(client_balance)  # Aggregate balances
                    except json.JSONDecodeError:
                        print(f"Error: Invalid response from client {client_id}")
            # Print balances in a clean format
            print("Balances:")
            for client_id, balance in balances.items():
                print(f"{client_id}: ${balance}")
        elif command[0] == "balance_table":
            # Retrieve full balance tables from all clients
            balance_tables = {}
            for client_id, (ip, port) in clients.items():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(json.dumps({"type": "COMMAND", "command": "balance_table"}).encode())
                    data = s.recv(8192)
                    try:
                        balance_tables[client_id] = json.loads(data.decode())
                    except json.JSONDecodeError:
                        print(f"Error: Invalid response from client {client_id}")
            # Print balance tables
            print("Balance Tables:")
            for client_id, balance_table in balance_tables.items():
                print(f"Client {client_id}: {balance_table}")
        elif command[0] == "blockchain":
            # Retrieve blockchains from all clients
            blockchains = {}
            for client_id, (ip, port) in clients.items():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(json.dumps({"type": "COMMAND", "command": "blockchain"}).encode())
                    data = s.recv(8192)
                    try:
                        blockchains[client_id] = json.loads(data.decode())
                    except json.JSONDecodeError:
                        print(f"Error: Invalid response from client {client_id}")
            print("Blockchains:")
            for client_id, blockchain in blockchains.items():
                print(f"Client {client_id}:")
                for block in blockchain:
                    print(f"  Block {block['index']}: {block['transaction']} (Hash: {block['hash']})")
        else:
            print("Invalid command.")







# Initialize clients
client_A = Client("A", "127.0.0.1", 6000, {"B": ("127.0.0.1", 6001), "C": ("127.0.0.1", 6002)})
client_B = Client("B", "127.0.0.1", 6001, {"A": ("127.0.0.1", 6000), "C": ("127.0.0.1", 6002)})
client_C = Client("C", "127.0.0.1", 6002, {"A": ("127.0.0.1", 6000), "B": ("127.0.0.1", 6001)})

# Start threads for receiving messages
threading.Thread(target=client_A.receive_message).start()
threading.Thread(target=client_B.receive_message).start()
threading.Thread(target=client_C.receive_message).start()

# Start up console
master_cli()


