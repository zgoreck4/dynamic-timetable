from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json

class RoutingBusAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.active = False

    async def setup(self):
        print("RoutingBusAgent started")