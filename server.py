import mesa
from mesa.visualization.modules import NetworkModule
from mesa.visualization.ModularVisualization import ModularServer
from model import BaseAgent, EconomyModel
from mesa.visualization.modules import ChartModule
import matplotlib.pyplot as plt
import matplotlib.colors as pltcolors


def money_color(money, minMoney, maxMoney):
    norm = pltcolors.Normalize(vmin=minMoney, vmax=maxMoney)
    colormap = plt.get_cmap('hot')  # You can choose different colormaps here
    return pltcolors.to_hex(colormap(norm(money)))


def network_portrayal(G):
    portrayal = {}
    moneys = [agents[0].money for (_, agents) in G.nodes.data("agent")]
    portrayal["nodes"] = [
        {
            "size": 6,
            "color": money_color(agents[0].money, min(moneys), max(moneys)),
            "tooltip": f"Agent {agents[0].uid}: Money: {agents[0].money}, Food: {agents[0].food}, Appetite: {agents[0].appetite}",
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
    [{"Label": "Average Money", "Color": "Blue"}],
    data_collector_name='datacollector'
)


model_params = {
    "N": mesa.visualization.Slider("Number of agents", 10, 2, 50, 1)
}
server = ModularServer(
    model_cls=EconomyModel,
    visualization_elements=[network, moneyChart],
    name="Economy Model",
    model_params=model_params
    )
server.port = 8521  # The default
server.launch()
