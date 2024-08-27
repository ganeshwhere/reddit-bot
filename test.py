import requests
import time
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque

# Function to get the transaction history of a Bitcoin wallet address
def get_transactions(address, retries=3):
    url = f'https://blockchain.info/rawaddr/{address}'
    for attempt in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get('txs', [])
            elif response.status_code == 429:
                print(f"Rate limited. Retrying in 10 seconds...")
                time.sleep(10)
            else:
                print(f"Error: {response.status_code}")
                return []
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            time.sleep(5)  # wait before retrying
    return []

# Function to follow the trail of a specific transaction
def follow_transaction(tx_hash, retries=3):
    url = f'https://blockchain.info/rawtx/{tx_hash}'
    for attempt in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data
            elif response.status_code == 429:
                print(f"Rate limited. Retrying in 10 seconds...")
                time.sleep(10)
            else:
                print(f"Error: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            time.sleep(5)  # wait before retrying
    return None

# Function to find the next receiver(s) from a transaction
def get_receivers(transaction):
    outputs = transaction.get('out', [])
    receivers = [output.get('addr', 'unknown') for output in outputs if 'addr' in output]
    return receivers

# Function to trace transactions and update the graph in real-time
def trace_transactions_realtime(start_address, depth=3):
    graph = nx.DiGraph()
    queue = deque([(start_address, 0)])
    visited = set()

    # Enable interactive mode in matplotlib
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 12))

    while queue:
        current_address, current_depth = queue.popleft()

        if current_depth > depth or current_address in visited:
            continue

        visited.add(current_address)
        transactions = get_transactions(current_address)

        if not transactions:
            continue  # Skip if no transactions found

        for tx in transactions:
            tx_hash = tx['hash']
            detailed_tx = follow_transaction(tx_hash)

            if detailed_tx:
                receivers = get_receivers(detailed_tx)
                for receiver in receivers:
                    if receiver not in visited:
                        graph.add_node(current_address, label=current_address)
                        graph.add_edge(current_address, receiver)
                        queue.append((receiver, current_depth + 1))

                        # Update the graph in real-time
                        ax.clear()
                        pos = nx.spring_layout(graph, k=0.5)
                        nx.draw(graph, pos, ax=ax, with_labels=True, node_size=3000, node_color='lightblue', font_size=8, font_weight='bold', edge_color='gray')
                        plt.draw()
                        plt.pause(0.1)

    # Turn off interactive mode and show the final graph
    plt.ioff()
    plt.show()

# Example usage
start_address = '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'  # Replace with your starting Bitcoin address
depth = 3  # Depth of recursive tracing
trace_transactions_realtime(start_address, depth)
