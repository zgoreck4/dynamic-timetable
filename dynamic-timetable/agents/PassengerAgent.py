from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json
import random

class PassengerAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.selectDestination()
        self.bus_id = None

    # TODO: zmienić na zachowanie
    def selectDestination(self):
        # można też, aby miesjce docelowe było random
        # TODO: dodać sprawdzanie inputów
        print("Destination 1. passenger")
        x_dest = float(input("x coordinate: "))
        y_dest = float(input("y coordinate: "))
        self.destination = [x_dest, y_dest]
        x_start = round(random.random()*50, 2)
        y_start = round(random.random()*50, 2)
        self.start_point = [x_start, y_start]

    class RequestForTravel(OneShotBehaviour):
        async def run(self):
            print("Passenger RequestForTravel running")
            msg = Message(to="scheduler@localhost")     # Instantiate the message
            msg.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
            msg.set_metadata("ontology", "travel_request")
            msg.set_metadata("language", "JSON")        # Set the language of the message content
            body_dict = {"start_point": self.agent.start_point, "destination": self.agent.destination}
            msg.body = json.dumps(body_dict)                   # Set the message content

            await self.send(msg)
            print("Message sent!")

            # stop agent from behaviour
            await self.kill()

    async def setup(self):
        print("PassengerAgent started")
        b = self.RequestForTravel()
        self.add_behaviour(b)