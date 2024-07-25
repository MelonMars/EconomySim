from mesa import Agent, Model, DataCollector
from mesa.time import RandomActivation
import networkx as nx
import random
from mesa.space import NetworkGrid


class BaseAgent(Agent):
    def __init__(self, uid, model, money, food, appetite):
        super().__init__(uid, model)
        self.uid = uid
        self.money = money
        self.food = food
        self.appetite = appetite
        self.neighbours = []

    def step(self):
        self.food -= self.appetite
        self.neighbours = self.model.grid.get_neighbors(self.pos, include_center=False)
        for neighbour in self.neighbours:
            if self.food > self.appetite and neighbour.food < neighbour.appetite:
                quant = min(self.food - self.appetite, neighbour.appetite - neighbour.food)
                self.food -= quant
                self.money += quant
                neighbour.food += quant
                neighbour.money -= quant
            elif self.food < self.appetite and neighbour.food > neighbour.appetite:
                quant = min(self.appetite - self.food, neighbour.food - neighbour.appetite)
                self.food += quant
                self.money -= quant
                neighbour.food -= quant
                neighbour.money += quant


class Farmer(Agent):
    def __init__(self, uid, model, money, food, appetite):
        super().__init__(uid, model)
        self.uid = uid
        self.money = money
        self.food = food
        self.appetite = appetite
        self.neighbours = []

    def step(self):
        self.food -= self.appetite
        self.food += 10
        self.neighbours = self.model.grid.get_neighbors(self.pos, include_center=False)
        random.shuffle(self.neighbours)
        for neighbour in self.neighbours:
            if self.food > self.appetite and neighbour.food < neighbour.appetite:
                quant = self.food - self.appetite
                self.food -= quant
                self.money += quant
                neighbour.food += quant
                neighbour.money -= quant
            elif self.food < self.appetite and neighbour.food > neighbour.appetite:
                quant = self.appetite - self.food
                self.food += quant
                self.money -= quant
                neighbour.food -= quant
                neighbour.money += quant



class EconomyModel(Model):
    def __init__(self, N):
        """
        :param N: Amount of agents in the model
        """
        super().__init__()
        self.N = N
        self.schedule = RandomActivation(self)
        self.G = nx.connected_watts_strogatz_graph(n=self.N, k=4, p=0.1)
        self.grid = NetworkGrid(self.G)
        fnode = random.choice(list(self.G.nodes()))
        for i, node in enumerate(self.G.nodes()):
            if node == fnode:
                agent = Farmer(i, self, random.randint(10, 100), random.randint(10, 100), random.randint(1, 4))
            else:
                agent = BaseAgent(i, self, random.randint(10, 100), random.randint(10, 100), random.randint(1, 4))
            self.schedule.add(agent)
            self.grid.place_agent(agent, node)
        self.datacollector = DataCollector(
            model_reporters={
                "Average Money": self.average_money,
            }
        )

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

    def average_money(self):
        agent_money = [agent.money for agent in self.schedule.agents]
        return sum(agent_money) / self.N
