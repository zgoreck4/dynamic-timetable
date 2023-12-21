from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour, FSMBehaviour, State
from spade.message import Message
from spade.template import Template
import json

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

    async def setup(self):
        print("*** RoutingBus: started")
        fsm = self.RoutingBusBehaviour()

        fsm.add_state(name="RECEIVE_CFP", state=self.ReceiveCfp(), initial=True)

        fsm.add_transition(source="RECEIVE_CFP", dest="RECEIVE_CFP")

        self.add_behaviour(fsm)
