import spade
import json
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template

class SchedulerAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.msg = None
        self.passenger_info = None

    class ReceiveTravelRequest(CyclicBehaviour):
        async def run(self):
            print("Scheduler ReceiveTravelRequest running")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                self.msg = msg
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")
                self.kill()

        async def on_end(self):
            # uwaga: kończy działanie całego agenta i zabija wszystkie zachowania
            await self.agent.stop()

    class SavePassengerInfo(CyclicBehaviour):
        async def run(self):
            print("Scheduler SavePassengerInfo running")

            if self.agent.msg:
                msg_body = json.loads(self.agent.msg.body)
                start_point = msg_body.get('start_point', None)
                destination = msg_body.get('destination', None)
                passenger_id = self.agent.msg.sender
                print(passenger_id)
                if (start_point != None) & (destination != None):
                    passenger_info = self.PassengerInfo(passenger_id, start_point, destination)
                    self.agent.passenger_info = passenger_info
            else:
                print("Wiadomość jest pusta")

    class PassengerInfo():
        def __init__(self, passenger_id, start_point, destination):
            self.passenger_id = passenger_id
            self.start_point = start_point
            self.destination = destination

    async def setup(self):
        print("SchedulerAgent started")
        b_rec_trav_req = self.ReceiveTravelRequest()
        template = Template()
        template.set_metadata("performative", "cfp")
        template.set_metadata("ontology", "travel_request")
        self.add_behaviour(b_rec_trav_req, template)

        # b_save_passenger_info = self.SavePassengerInfo()
        # self.add_behaviour(b_save_passenger_info)