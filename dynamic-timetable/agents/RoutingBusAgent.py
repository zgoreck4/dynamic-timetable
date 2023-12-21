from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour, FSMBehaviour, State
from spade.message import Message
from spade.template import Template
import json
import random


class RoutingBusAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.active = False
        self.id = None # pewnie powinniśmy zainicjalizować

    class RoutingBusBehaviour(FSMBehaviour):
        async def on_start(self):
            print(f"*** RoutingBus: FSM starting at initial state {self.current_state}")

        async def on_end(self):
            print(f"*** RoutingBus: FSM finished at state {self.current_state}")
            await self.agent.stop()

    class ReceiveCfp(State):
        async def run(self):
            print("*** RoutingBus: ReceiveCfp running")

            template = Template()
            template.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
            template.set_metadata("ontology", "select_bus")
            template.set_metadata("language", "JSON")        # Set the language of the message content

            msg = await self.receive(timeout=10)
            if msg and template.match(msg):
                self.agent.msg = msg
                print("*** RoutingBus: Message received with content: {}".format(msg.body))
                self.set_next_state("GET_BUS_INFORMATION")
            else:
                self.set_next_state("RECEIVE_CFP")

    class GetBusInformation(State):
        async def run(self):
            print("*** RoutingBus: GetBusInformation running")

            x = round(random.random()*50, 2)
            y = round(random.random()*50, 2)
            self.position = [x, y]

            print("*** RoutingBus: Position: {}".format(self.position))

            self.set_next_state("CALCULATE_POTENTIAL_COST")

    async def setup(self):
        print("*** RoutingBus: started")
        fsm = self.RoutingBusBehaviour()

        fsm.add_state(name="RECEIVE_CFP", state=self.ReceiveCfp(), initial=True)
        fsm.add_state(name="GET_BUS_INFORMATION", state=self.GetBusInformation())

        fsm.add_transition(source="RECEIVE_CFP", dest="RECEIVE_CFP")
        fsm.add_transition(source="RECEIVE_CFP", dest="GET_BUS_INFORMATION")

        self.add_behaviour(fsm)
