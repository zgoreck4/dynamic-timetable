from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json

class PassengerAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.selectDestination()

    def selectDestination(self):
        # TODO: dodać sprawdzanie inputów
        print("Destination 1. passenger")
        x = float(input("x coordinate: "))
        y = float(input("y coordinate: "))
        self.destination = [x, y]

    class RequestForTravel(OneShotBehaviour):
        async def run(self):
            print("Passenger RequestForTravel running")
            msg = Message(to="scheduler@localhost")     # Instantiate the message
            msg.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
            msg.set_metadata("language", "JSON")        # Set the language of the message content
            body_dict = {"destination": self.agent.destination}
            msg.body = json.dumps(body_dict)                   # Set the message content

            await self.send(msg)
            print("Message sent!")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("PassengerAgent started")
        b = self.RequestForTravel()
        self.add_behaviour(b)