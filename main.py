import networkx as nx
import random
import matplotlib.pyplot as plt


class BaseTrader:
    def __init__(self, unique_id, money, food, appetite):
        self.unique_id = unique_id
        self.money = money
        self.food = food
        self.appetite = appetite

    def step(self):
        print(f"Agent {self.unique_id} Step")
        self.food -= self.appetite
        if self.food < self.appetite:
            self.money -= self.appetite
            self.food += self.appetite


class EconomySim:
    def __init__(self, N):
        print("N:", N)
        self.N = N
        self.agents = []
        self.G = nx.erdos_renyi_graph(n=self.N, p=0.1)
        for i in range(self.N):
            agent = BaseTrader(i, random.randint(10, 100), random.randint(10, 100), random.randint(1, 4))
            self.agents.append(agent)
            self.G.nodes[i]['agent'] = agent

    def step(self):
        print(f"Agents: {self.N}")
        for agent in self.agents:
            agent.step()
        self.visualize()

    def visualize(self):
        plt.figure(figsize=(8, 6))
        money_values = [self.G.nodes[i]['agent'].money for i in self.G.nodes()]
        norm = plt.Normalize(vmin=min(money_values), vmax=max(money_values))
        cmap = plt.get_cmap("hot")
        colors = [cmap(norm(money)) for money in money_values]
        pos = nx.spring_layout(self.G)
        nx.draw(self.G, pos, with_labels=True, node_size=500, node_color=colors, edge_color='gray',
                cmap=cmap)
        plt.show()


if __name__ == "__main__":
    sim = EconomySim(N=10)
    for _ in range(10):
        sim.step()
