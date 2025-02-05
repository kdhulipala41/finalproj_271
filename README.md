# CS271 Final Project

The objective of this project is to implement a fault-tolerant distributed transaction processing system that supports a simple banking application. To this end, we
partition servers into multiple clusters where each cluster maintains a data shard. Each
data shard is replicated on all servers of a cluster to provide fault tolerance. The system supports two types of transactions: intra-shard and cross-shard. An intra-shard
transaction accesses the data items of the same shard while a cross-shard transaction
accesses the data items on multiple shards. To process intra-shard transactions the
Raft protocol should be used while the two-phase commit protocol (2PC) is used to
process cross-shard transactions.

Due: March 7th, 2025
