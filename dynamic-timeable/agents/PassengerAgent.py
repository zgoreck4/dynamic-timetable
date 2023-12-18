from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json

class PassengerAgent(Agent):
    def __init__(self, jid, password, destination):
        super().__init__(jid, password)
        self.destination = destination

    class PassengerBehav(OneShotBehaviour):
        async def run(self):
            print("PassengerBehav running")
            msg = Message(to="scheduler@localhost")     # Instantiate the message
            msg.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
            msg.set_metadata("language", "JSON")        # Set the language of the message content
            msg.body = json.dumps(self.agent.destination)                   # Set the message content

            await self.send(msg)
            print("Message sent!")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("PassengerAgent started")
        b = self.PassengerBehav()
        self.add_behaviour(b)