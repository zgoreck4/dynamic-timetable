import spade
import json
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour, FSMBehaviour, State
from spade.message import Message
from spade.template import Template
import datetime

class SchedulerAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.msg = None
        self.passenger_info = None
        self.selected_bus = None


    class SchedulerBehaviour(FSMBehaviour):
        async def on_start(self):
            print(f"FSM starting at initial state {self.current_state}")

        async def on_end(self):
            print(f"FSM finished at state {self.current_state}")
            await self.agent.stop()

    class ReceiveTravelRequest(State):
        async def run(self):
            print("Scheduler ReceiveTravelRequest running")

            template = Template()
            template.set_metadata("performative", "cfp")
            template.set_metadata("ontology", "travel_request")

            # można będzie usunąć timeout
            msg = await self.receive(timeout=10)
            if msg and template.match(msg):
                self.agent.msg = msg
                print("Message received with content: {}".format(msg.body))
                self.set_next_state("SAVE_PASSENGER_INFO")
            else:
                self.set_next_state("RECEIVE_PASSENGER")

    class SavePassengerInfo(State):
        async def run(self):
            print("Scheduler SavePassengerInfo running")

            msg_body = json.loads(self.agent.msg.body)
            start_point = msg_body.get('start_point', None)
            destination = msg_body.get('destination', None)
            passenger_jid = self.agent.msg.sender
            if (start_point != None) & (destination != None):
                passenger_info = self.agent.PassengerInfo(passenger_jid, start_point, destination)
                self.agent.passenger_info = passenger_info

            self.set_next_state("CFP")

    class PassengerInfo():
        def __init__(self, passenger_jid, start_point, destination):
            self.passenger_jid = passenger_jid
            self.start_point = start_point
            self.destination = destination

    class Cfp(State):
        async def run(self):
            print("Scheduler Cfp running")
            # TODO wysyłanie do wszytkich busów, a nie tylko 1
            msg = Message(to="routing_bus@localhost")     # Instantiate the message
            msg.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
            msg.set_metadata("ontology", "select_bus")
            msg.set_metadata("language", "JSON")        # Set the language of the message content
            # chyba zmienia "passenger_jid": passenger@localhost na "passenger_jid": ["passenger", "localhost", null]. Czy to nie problem?
            body_dict = json.dumps({"passenger_info": self.agent.passenger_info.__dict__})  
            msg.body = body_dict                 # Set the message content

            await self.send(msg)
            print("Message sent!")

            self.set_next_state("RECEIVE_BUS_PROPOSE")

    class ReceiveBusPropose(State):
        async def run(self):
            print("Scheduler ReceiveBusPropose running")

            template = Template()
            template.set_metadata("performative", "propose")
            template.set_metadata("ontology", "select_bus")
            # można dodać od koga ta wiadomość ma być (?)
            
            # TODO dodać odbieranie wiadomości od kilku busów
            msg = await self.receive(timeout=10)
            if msg and template.match(msg):
                self.agent.msg = msg
                print("Message received with content: {}".format(msg.body))
                # TODO zapisanie informacji z wiadomości
                self.set_next_state("SELECT_BUS")
            else:
                # można wpaść w nieskończoną pętle, można by dodać zwrot informacji do pasażera, że nie można przydzielić busa
                self.set_next_state("CFP")

    class SelectBus(State):
        async def run(self):
            print("Scheduler SelectBus running")

            # TODO algorytm wybierania busa
            # self.agent.selected_bus = #jakiś jid

            # self.set_next_state("RECEIVE_PASSENGER")

    async def setup(self):
        print("SchedulerAgent started")
        fsm = self.SchedulerBehaviour()

        fsm.add_state(name="RECEIVE_PASSENGER", state=self.ReceiveTravelRequest(), initial=True)     
        fsm.add_state(name="SAVE_PASSENGER_INFO", state=self.SavePassengerInfo())
        fsm.add_state(name="CFP", state=self.Cfp())
        fsm.add_state(name="RECEIVE_BUS_PROPOSE", state=self.ReceiveBusPropose())
        fsm.add_state(name="SELECT_BUS", state=self.SelectBus())
        
        fsm.add_transition(source="RECEIVE_PASSENGER", dest="RECEIVE_PASSENGER")
        fsm.add_transition(source="RECEIVE_PASSENGER", dest="SAVE_PASSENGER_INFO")
        fsm.add_transition(source="SAVE_PASSENGER_INFO", dest="CFP")
        fsm.add_transition(source="CFP", dest="RECEIVE_BUS_PROPOSE")
        fsm.add_transition(source="RECEIVE_BUS_PROPOSE", dest="CFP")
        fsm.add_transition(source="RECEIVE_BUS_PROPOSE", dest="SELECT_BUS")

        self.add_behaviour(fsm)