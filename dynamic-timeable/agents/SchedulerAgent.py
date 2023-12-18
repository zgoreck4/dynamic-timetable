import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template

class SchedulerAgent(Agent):
    class SchedulerBehav(OneShotBehaviour):
        async def run(self):
            print("SchedulerBehav running")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("SchedulerAgent started")
        b = self.SchedulerBehav()
        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(b, template)