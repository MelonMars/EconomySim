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
            "corn": random.randint(30, 100),
            "apples": random.randint(30, 100),
            "beef": random.randint(30, 100),
        }
        # Marginal value OR value of the good to the agent, subjectively in terms of how much utility it would bring.
        self.values = {
            "corn": max(random.randint(10, 15), 30),
            "apples": max(random.randint(10, 15), 50 - self.inventory["apples"]),
            "beef": max(random.randint(10, 15), 60 - self.inventory["beef"]),
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
            if self.prices[good] < self.model.costToProduce[good]:
                if self.money > self.model.costToProduce[good]:
                    self.money -= self.model.costToProduce[good]
                    self.inventory[good] += 1
                    self.available[good]["quantity"] = 1
                    self.available[good]["price"] = self.model.costToProduce[good] + 0.1
            elif self.values[good] < self.prices[good]:
                if self.inventory[good] > 0:
                    self.available[good]["quantity"] = 1
                    self.available[good]["price"] = self.prices[good]
        for neighbour in self.neighbours:
            for good in neighbour.available.keys():
                if neighbour.available[good]["quantity"] > 0:
                    offPrice = neighbour.available[good]["price"]
                    if offPrice < self.values[good]:
                        quant = max(0,
                                    min(neighbour.available[good]["quantity"], self.values[good] - self.inventory[good],
                                        self.money // offPrice, 1))
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
        self.costToProduce = {
            "corn": 10,
            "apples": 20,
            "beef": 30,
        }
        for i, node in enumerate(self.G.nodes()):
            agent = BaseAgent(i, self, 10000)
            self.schedule.add(agent)
            self.grid.place_agent(agent, node)
        self.datacollector = DataCollector(
            model_reporters={
                "Average Money": self.average_money,
                "Corn price": self.corn_price,
                "Apple price": self.apple_price,
                "Beef price": self.beef_price,
                "Corn available cost": self.corn_cost,
                "Corn marginal value": self.corn_val,
            }
        )

    def step(self):
        self.schedule.step()
        for agent in self.schedule.agents:
            agent.price_adjustment()
        self.datacollector.collect(self)

    def average_money(self):
        return sum([agent.money for agent in self.schedule.agents]) / self.N

    def corn_price(self):
        return sum([agent.prices.get("corn", 0) for agent in self.schedule.agents]) / self.N

    def apple_price(self):
        return sum([agent.prices["apples"] for agent in self.schedule.agents]) / self.N

    def beef_price(self):
        return sum([agent.prices["beef"] for agent in self.schedule.agents]) / self.N

    def corn_cost(self):
        return sum([agent.available["corn"]["price"] for agent in self.schedule.agents]) / self.N

    def corn_val(self):
        return sum([agent.values["corn"] for agent in self.schedule.agents]) / self.N