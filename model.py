import numpy as np
from mesa import Agent, Model, DataCollector
from mesa.time import RandomActivation
import networkx as nx
import random
from mesa.space import NetworkGrid


class Consumer(Agent):
    def __init__(self, uid, model, money):
        super().__init__(uid, model)
        self.uid = uid
        self.money = money
        self.neighbours = []
        self.inventory = {
            "corn": 10,
            "apples": 0,
            "beef": 0,
        }
        # Marginal value OR value of the good to the agent, subjectively in terms of how much utility it would bring.
        # Will be some complex value in the future, for now I just mainly want a SINGLE quantity market
        self.values = {
            "corn": 60 - self.inventory["corn"],
            "apples": 0,
            "beef": 0,
        }

    def step(self):
        self.neighbours = self.model.grid.get_neighbors(self.pos, include_center=False)
        random.shuffle(self.neighbours)
        lowest_price = 60
        lowest_neighbour = random.choice([neighbour for neighbour in self.neighbours if isinstance(neighbour, Producer)])
        good = "corn"
        self.inventory["corn"] -= 1
        self.values["corn"] = 60 - self.inventory["corn"]
        for neighbour in self.neighbours:
            if isinstance(neighbour, Producer):
                # for good in neighbour.available.keys():
                if neighbour.available[good]["quantity"] > 0:
                    offPrice = neighbour.available[good]["price"]
                    if offPrice < lowest_price:
                        lowest_price = offPrice
                        lowest_neighbour = neighbour
        if lowest_price < self.values[good] or self.inventory[good] == 0:
            quant = 1
            if lowest_neighbour.inventory[good] >= quant:
                self.inventory[good] += quant
                self.money -= quant * lowest_price
                lowest_neighbour.inventory[good] -= quant
                lowest_neighbour.money += quant * lowest_price
                lowest_neighbour.sales[good] += quant
                lowest_neighbour.available[good]["quantity"] -= quant
                print("Agent:", self.uid, "Buying:", good, "Value: ", self.values[good], "Price: ", str(lowest_price) + ".", "I currently have:", self.inventory[good])
            else:
                print("Agent:", self.uid, "not buying from", lowest_neighbour.uid, "because they don't have enough inventory.")

class Producer(Agent):
    def __init__(self, uid, model, money):
        super().__init__(uid, model)
        self.uid = uid
        self.model = model
        self.money = money
        self.neighbours = []
        self.inventory = {
            "corn": random.randint(30, 100),
            "apples": random.randint(30, 100),
            "beef": random.randint(30, 100),
        }
        self.prices = {
            "corn": model.costToProduce["corn"] * 1.5 + random.randint(-5, 5),
            "apples": model.costToProduce["apples"] * 1.5 + random.randint(-5, 5),
            "beef": model.costToProduce["beef"] * 1.5 + random.randint(-5, 5),
        }
        self.available = {
            "corn": {"price": self.prices["corn"], "quantity": 0},
            "apples": {"price": self.prices["apples"], "quantity": 0},
            "beef": {"price": self.prices["beef"], "quantity": 0},
        }
        self.sales = {
            "corn": 0,
            "apples": 0,
            "beef": 0,
        }

    def step(self):
        # If the price is less than what it costs to make it, don't make it and don't sell, you're loosing money no matter what. Otherwise, make it
        for good in self.prices.keys():
            if self.prices[good] < self.model.costToProduce[good]:
                self.prices[good] *= 1.05
            elif self.prices[good] > self.model.costToProduce[good] and self.money >= self.model.costToProduce[good]:
                self.money -= 2 * self.model.costToProduce[good]
                self.inventory[good] += 2
                self.available[good]["quantity"] += 2
                self.available[good]["price"] = self.prices[good]

    def price_adjustment(self):
        for good in self.prices.keys():
            if self.sales[good] > 0:
                self.prices[good] *= 1.1
            else:
                self.prices[good] *= 0.8
            self.sales[good] = 0
        print(self.prices["corn"])


class EconomyModel(Model):
    def __init__(self, consumers, producers):
        """
        :param N: Amount of agents in the model
        """
        super().__init__()
        self.consumers = consumers
        self.producers = producers
        self.schedule = RandomActivation(self)
        self.G = nx.connected_watts_strogatz_graph(n=self.consumers + self.producers, k=4, p=0.1)
        self.grid = NetworkGrid(self.G)
        self.costToProduce = {
            "corn": 10,
            "apples": 20,
            "beef": 30,
        }
        for i, node in enumerate(self.G.nodes()):
            if i % 2 == 0:
                agent = Consumer(i, self, 0)
            else:
                agent = Producer(i, self, 10000)
            self.schedule.add(agent)
            self.grid.place_agent(agent, node)
        self.datacollector = DataCollector(
            model_reporters={
                "Average Consumer Money": self.average_consumer_money,
                "Average Producer Money": self.average_producer_money,
                "Average Price of Corn": self.corn_price,
                "Minimum Price of Corn": self.corn_min_price,
                "Maximum Price of Corn": self.corn_price_max
            }
        )

    def step(self):
        self.schedule.step()
        for agent in self.schedule.agents:
            if isinstance(agent, Producer):
                agent.price_adjustment()
        self.datacollector.collect(self)

    def average_consumer_money(self):
        return sum([agent.money for agent in self.schedule.agents if isinstance(agent, Consumer)]) / self.consumers

    def average_producer_money(self):
        return sum([agent.money for agent in self.schedule.agents if isinstance(agent, Producer)]) / self.producers

    def corn_price(self):
        return sum([agent.prices["corn"] for agent in self.schedule.agents if isinstance(agent, Producer)]) / self.producers

    def corn_min_price(self):
        return min([agent.prices["corn"] for agent in self.schedule.agents if isinstance(agent, Producer)])

    def corn_price_max(self):
        return max([agent.prices["corn"] for agent in self.schedule.agents if isinstance(agent, Producer)])