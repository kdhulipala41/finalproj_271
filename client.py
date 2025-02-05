import hashlib
import heapq
import time
import threading
import socket
import json
from blockchain import Blockchain
from blockchain import Block


class Client:
    def __init__(self, client_id, ip, port, other_clients):
        self.client_id = client_id
        self.ip = ip
        self.port = port
        self.other_clients = other_clients
        self.blockchain = Blockchain()
        self.balance_table = {"A": 10, "B": 10, "C": 10}
        self.lamport_clock = 0
        self.ack_count = 0
        self.request_queue = []
        self.replies = set()
        self.lock = threading.Lock()

    def add_to_request_queue(self, client_id, timestamp):
        heapq.heappush(self.request_queue, (timestamp, client_id))

    def get_top_request(self):
        if self.request_queue:
            return self.request_queue[0]  # Peek at the top element
        return None

    def handle_transaction(self, transaction):
        print("Entered handle_transaction method at client ", self.client_id)
        # Increment Lamport clock
        self.lamport_clock += 1

        request_message = {
            "type": "REQUEST",
            "sender": self.client_id,
            "timestamp": self.lamport_clock
        }

        # Broadcast REQUEST
        for client_id, (ip, port) in self.other_clients.items():
            print(f"Client {self.client_id} sending REQUEST to {client_id}")
            self.send_message(request_message, ip, port)

        # Add request to local queue
        self.add_to_request_queue(self.client_id, self.lamport_clock)

        # Wait for REPLYs from all other clients
        while len(self.replies) < len(self.other_clients):
            print(f"Client {self.client_id} waiting for REPLIES... Current replies: {self.replies}")
            time.sleep(1)  # Simulate waiting

        # Check if request is at head of local queue
        top_request = self.get_top_request()
        if top_request and top_request[1] == self.client_id:
            # Enter critical section to access balancetable and blockchain
            self.lock.acquire()
            try:
                if self.balance_table[transaction["sender"]] >= transaction["amount"]:
                    # Append to blockchain
                    new_block = self.blockchain.add_block(transaction)

                    # Broadcast new block
                    block_update_message = {
                        "type": "BLOCK_UPDATE",
                        "sender": self.client_id,
                        "block": new_block.__dict__,
                        "timestamp": self.lamport_clock
                    }
                    for client_id, (ip, port) in self.other_clients.items():
                        print(f"Client {self.client_id} sending BLOCK_UPDATE to {client_id}")
                        self.send_message(block_update_message, ip, port)

                    # Wait for ACK responses from other clients
                    while self.ack_count < len(self.other_clients):
                        print(f"Client {self.client_id} waiting for ACKs... Current count: {self.ack_count}")
                        time.sleep(1)

                    # Update balancetable
                    self.balance_table[transaction["sender"]] -= transaction["amount"]
                    self.balance_table[transaction["receiver"]] += transaction["amount"]
                    print(f"SUCCESS: Transaction {transaction} completed.")
                else:
                    print(f"FAILED: Insufficient balance for transaction {transaction}.")
            finally:
                self.lock.release()

        # Remove request from local queue and reset replies
        self.request_queue = [req for req in self.request_queue if req[1] != self.client_id]
        self.replies = set()

        # Broadcast RELEASE
        release_message = {
            "type": "RELEASE",
            "sender": self.client_id,
            "timestamp": self.lamport_clock
        }
        for client_id, (ip, port) in self.other_clients.items():
            print(f"Client {self.client_id} sending RELEASE to {client_id}")
            self.send_message(release_message, ip, port)


    def send_message(self, message, client_ip, client_port):
        print(f"Client {self.client_id} sending message to {client_ip}:{client_port}: {message}")
        time.sleep(3)  # simulated network delay
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((client_ip, client_port))
                s.sendall(json.dumps(message).encode())
            except ConnectionRefusedError:
                print(f"Client {self.client_id} failed to connect to {client_ip}:{client_port}")
            except Exception as e:
                print(f"Client {self.client_id} encountered an error: {e}")


    def receive_message(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.port))
            s.listen()
            print(f"Client {self.client_id} listening on {self.ip}:{self.port}")
            while True:
                conn, addr = s.accept()
                # Forking new thread to process the message
                threading.Thread(target=self.handle_connection, args=(conn, addr)).start()

    def handle_connection(self, conn, addr):
        with conn:
            data = conn.recv(8192)
            if not data:
                print(f"Client {self.client_id} received empty data from {addr}")
                return
            try:
                message = json.loads(data.decode())
                print(f"Client {self.client_id} received message from {addr}: {message}")
                self.process_message(message, conn)
            except json.JSONDecodeError:
                print(f"Error: Invalid message received by client {self.client_id} from {addr}")

    def process_message(self, message, conn):
        if "timestamp" in message:
            self.lamport_clock = max(self.lamport_clock, message["timestamp"]) + 1

        if message["type"] == "REQUEST":
            print(f"Client {self.client_id} received REQUEST from {message['sender']}")
            # Add request to queue
            self.add_to_request_queue(message["sender"], message["timestamp"])

            # Send REPLY
            reply_message = {
                "type": "REPLY",
                "sender": self.client_id,
                "timestamp": self.lamport_clock
            }
            print(f"Client {self.client_id} sending REPLY to {message['sender']}")
            self.send_message(reply_message, *self.other_clients[message["sender"]])
        elif message["type"] == "REPLY":
            print(f"Client {self.client_id} received REPLY from {message['sender']}")

            # Add reply to replies set
            self.replies.add(message["sender"])
        elif message["type"] == "RELEASE":
            print(f"Client {self.client_id} received RELEASE from {message['sender']}")

            # Remove request from queue
            self.request_queue = [req for req in self.request_queue if req[1] != message["sender"]]
        elif message["type"] == "BLOCK_UPDATE":
            print(f"Client {self.client_id} received BLOCK_UPDATE from {message['sender']}")

            # Add block to local blockchain
            new_block = Block(
                index=message["block"]["index"],
                previous_hash=message["block"]["previous_hash"],
                transaction=message["block"]["transaction"],
                timestamp=message["block"]["timestamp"]
            )
            self.blockchain.chain.append(new_block)

            # Update balance table
            self.balance_table[new_block.transaction["sender"]] -= new_block.transaction["amount"]
            self.balance_table[new_block.transaction["receiver"]] += new_block.transaction["amount"]

            # Respond with ACK
            ack_message = {
                "type": "ACK",
                "sender": self.client_id,
                "timestamp": self.lamport_clock
            }
            print(f"Client {self.client_id} sending ACK to {message['sender']}")
            self.send_message(ack_message, *self.other_clients[message["sender"]])
        elif message["type"] == "ACK":
            print(f"Client {self.client_id} received ACK from {message['sender']}")

            # Increment ACK count
            self.ack_count += 1
        elif message["type"] == "COMMAND":
            if message["command"] == "balance":
                # Send local copy of balance
                response = json.dumps({self.client_id: self.balance_table[self.client_id]})
                conn.sendall(response.encode())
            elif message["command"] == "balance_table":
                # Send full balance table
                response = json.dumps(self.balance_table)
                conn.sendall(response.encode())
            elif message["command"] == "blockchain":
                # Send the blockchain as a response
                response = json.dumps([block.__dict__ for block in self.blockchain.chain])
                conn.sendall(response.encode())
            elif message["command"] == "transfer":
                self.handle_transaction(message["transaction"])


