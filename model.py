from mesa import Agent, Model, DataCollector
from mesa.time import RandomActivation
import networkx as nx
import random
from mesa.space import NetworkGrid


class BaseAgent(Agent):
    def __init__(self, uid, model, money):
        super().__init__(uid, model)
        self.uid = uid
        self.money = money
        self.neighbours = []
        self.inventory = {
            "corn": random.randint(0, 100),
            "apples": random.randint(0, 100),
            "beef": random.randint(0, 100),
        }
        self.goal = {
            "corn": random.randint(0, 100),
            "apples": random.randint(0, 50),
            "beef": random.randint(0, 10),
        }
        self.prices = {
            "corn": random.uniform(1.0, 10.0),
            "apples": random.uniform(1.0, 10.0),
            "beef": random.uniform(1.0, 10.0),
        }
        self.available = {
            "corn": {"quantity": 0, "price": self.prices["corn"]},
            "apples": {"quantity": 0, "price": self.prices["apples"]},
            "beef": {"quantity": 0, "price": self.prices["beef"]},
        }
        self.sales = {
            "corn": 0,
            "apples": 0,
            "beef": 0,
        }

    def step(self):
        self.neighbours = self.model.grid.get_neighbors(self.pos, include_center=False)
        random.shuffle(self.neighbours)
        for good in self.inventory.keys():
            if self.inventory[good] > 0:
                self.available[good]["quantity"] = 1
                self.available[good]["price"] = self.prices[good]
        for neighbour in self.neighbours:
            for good in neighbour.available.keys():
                if neighbour.available[good]["quantity"] > 0:
                    offPrice = neighbour.available[good]["price"]
                    if offPrice < self.prices[good]:
                        quant = max(0, min(neighbour.available[good]["quantity"], self.goal[good] - self.inventory[good],
                                   self.money // offPrice))
                        self.inventory[good] += quant
                        self.money -= quant * offPrice
                        neighbour.inventory[good] -= quant
                        neighbour.money += quant * offPrice
                        neighbour.sales[good] += quant
                        neighbour.available[good]["quantity"] -= quant

    def price_adjustment(self):
        for good in self.prices.keys():
            if self.sales[good] > 0:
                self.prices[good] *= 1.1
            elif self.sales[good] < 1:
                self.prices[good] *= 0.9
            self.sales[good] = 0


class Farmer(Agent):
    def __init__(self, uid, model, money):
        super().__init__(uid, model)
        self.uid = uid
        self.money = money
        self.neighbours = []
        self.inventory = {
            "corn": random.randint(0, 100),
            "apples": random.randint(0, 100),
            "beef": random.randint(0, 100),
        }
        self.goal = {
            "corn": random.randint(0, 100),
            "apples": random.randint(0, 50),
            "beef": random.randint(0, 10),
        }
        self.prices = {
            "corn": random.uniform(1.0, 10.0),
            "apples": random.uniform(1.0, 10.0),
            "beef": random.uniform(1.0, 10.0),
        }
        self.available = {
            "corn": {"quantity": 0, "price": self.prices["corn"]},
            "apples": {"quantity": 0, "price": self.prices["apples"]},
            "beef": {"quantity": 0, "price": self.prices["beef"]},
        }
        self.sales = {
            "corn": 0,
            "apples": 0,
            "beef": 0,
        }

    def step(self):
        self.inventory["corn"] += 10
        self.neighbours = self.model.grid.get_neighbors(self.pos, include_center=False)
        random.shuffle(self.neighbours)
        for good in self.inventory.keys():
            if self.inventory[good] > 0:
                self.available[good]["quantity"] = 1
                self.available[good]["price"] = self.prices[good]
        for neighbour in self.neighbours:
            for good in neighbour.available.keys():
                if neighbour.available[good]["quantity"] > 0:
                    offPrice = neighbour.available[good]["price"]
                    if offPrice < self.prices[good]:
                        quant = max(0, min(neighbour.available[good]["quantity"], self.goal[good] - self.inventory[good],
                                    self.money // offPrice))
                        self.inventory[good] += quant
                        self.money -= quant * offPrice
                        neighbour.inventory[good] -= quant
                        neighbour.money += quant * offPrice
                        neighbour.sales[good] += quant
                        neighbour.available[good]["quantity"] -= quant

    def price_adjustment(self):
        for good in self.prices.keys():
            if self.sales[good] > 0:
                self.prices[good] *= 1.1
            elif self.sales[good] < 1:
                self.prices[good] *= 0.9
            self.sales[good] = 0


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
                agent = Farmer(i, self, random.randint(10, 100))
            else:
                agent = BaseAgent(i, self, random.randint(10, 100))
            self.schedule.add(agent)
            self.grid.place_agent(agent, node)
        self.datacollector = DataCollector(
            model_reporters={
                "Average Money": self.average_money,
                "Corn price": self.corn_price,
                "Apple price": self.apple_price,
                "Beef price": self.beef_price,
            }
        )

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        print("Data collected:", self.datacollector.get_model_vars_dataframe().tail())
        for agent in self.schedule.agents:
            agent.price_adjustment()


    def average_money(self):
        return sum([agent.money for agent in self.schedule.agents]) / self.N

    def corn_price(self):
        return sum([agent.prices.get("corn", 0) for agent in self.schedule.agents]) / self.N

    def apple_price(self):
        return sum([agent.prices["apples"] for agent in self.schedule.agents]) / self.N

    def beef_price(self):
        return sum([agent.prices["beef"] for agent in self.schedule.agents]) / self.N