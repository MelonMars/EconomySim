import mesa
from mesa.visualization.modules import NetworkModule
from mesa.visualization.ModularVisualization import ModularServer
from model import EconomyModel
from mesa.visualization.modules import ChartModule
import matplotlib.pyplot as plt
import matplotlib.colors as pltcolors


def money_color(money, minMoney, maxMoney):
    norm = pltcolors.Normalize(vmin=minMoney, vmax=maxMoney)
    colormap = plt.get_cmap('hot')
    return pltcolors.to_hex(colormap(norm(money)))


def network_portrayal(G):
    portrayal = {}
    moneys = [agents[0].money for (_, agents) in G.nodes.data("agent")]
    portrayal["nodes"] = [
        {
            "size": 6,
            "color": money_color(agents[0].money, min(moneys), max(moneys)),
            "tooltip": f"Agent {agents[0].uid}: Money: {agents[0].money}, Inventory: {agents[0].inventory} , Type: {type(agents[0]).__name__}",
        }
        for (_, agents) in G.nodes.data("agent")
    ]
    portrayal["edges"] = [
        {
            "source": source,
            "target": target,
            "color": "black",
            "width": 3,
        }
        for (source, target) in G.edges
    ]

    return portrayal


network = NetworkModule(
    portrayal_method=network_portrayal,
    canvas_height=500,
    canvas_width=500
)

moneyChart = ChartModule(
    [
        {"Label": "Average Consumer Money", "Color": "Blue"},
        {"Label": "Average Producer Money", "Color": "Green"},
    ],
    data_collector_name='datacollector'
)

cornChart = ChartModule(
    [
        {"Label": "Average Price of Corn", "Color": "Red"},
        {"Label": "Minimum Price of Corn", "Color": "Blue"},
        {"Label": "Maximum Price of Corn", "Color": "Black"},
    ]
)

model_params = {
    "consumers": mesa.visualization.Slider("Number of consumers", 10, 2, 50, 1),
    "producers": mesa.visualization.Slider("Number of producers", 10, 2, 50, 1)
}
server = ModularServer(
    model_cls=EconomyModel,
    visualization_elements=[network, cornChart, moneyChart],
    name="Economy Model",
    model_params=model_params
    )
server.port = 8521
server.launch()
