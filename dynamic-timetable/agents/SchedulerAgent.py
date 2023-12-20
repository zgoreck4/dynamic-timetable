import spade
import json
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template

class SchedulerAgent(Agent):
    class ReceiveTravelRequest(CyclicBehaviour):
        async def run(self):
            print("Scheduler ReceiveTravelRequest running")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                msg_body = json.loads(msg.body)
                print("Message received with content: {}".format(msg.body))
                # TODO: chyba trzeba by było sprawdzić czy msg zawiera destination lub dodać ten warunek do template
                print(msg_body['destination'])
            else:
                print("Did not received any message after 10 seconds")
                self.kill()

        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        print("SchedulerAgent started")
        b_rec_trav_req = self.ReceiveTravelRequest()
        template = Template()
        template.set_metadata("performative", "cfp")
        self.add_behaviour(b_rec_trav_req, template)