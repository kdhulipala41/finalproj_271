import hashlib
import time
import threading
import socket
import json

class Block:
    def __init__(self, index, previous_hash, transaction, timestamp):
        self.index = index
        self.previous_hash = previous_hash
        self.transaction = transaction
        self.timestamp = timestamp
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "0", {"sender": "None", "receiver": "None", "amount": 0}, time.time())

    def add_block(self, transaction):
        last_block = self.chain[-1]
        new_block = Block(last_block.index + 1, last_block.hash, transaction, time.time())
        self.chain.append(new_block)
        return new_block

