import spade
import json
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour, FSMBehaviour, State
from spade.message import Message
from spade.template import Template
from logger import logger
import datetime

class SchedulerAgent(Agent):
    def __init__(self, jid, password, buses):
        super().__init__(jid, password)
        self.msg = None
        self.passenger_info = None
        self.selected_bus = None
        self.buses = buses
        self.costs = {}

    class SchedulerBehaviour(FSMBehaviour):
        async def on_start(self):
            logger.info(f"Scheduler: FSM starting at initial state {self.current_state}")

        async def on_end(self):
            logger.info(f"Scheduler: FSM finished at state {self.current_state}")
            await self.agent.stop()

    class ReceiveTravelRequest(State):
        async def run(self):
            logger.debug("Scheduler: ReceiveTravelRequest running")

            template = Template()
            template.set_metadata("performative", "cfp")
            template.set_metadata("ontology", "travel_request")

            # można będzie usunąć timeout
            msg = await self.receive(timeout=10)
            if msg and template.match(msg):
                self.agent.msg = msg
                logger.info("Scheduler: Message received with content: {}".format(msg.body))
                self.set_next_state("SAVE_PASSENGER_INFO")
            else:
                self.set_next_state("RECEIVE_PASSENGER")

    class SavePassengerInfo(State):
        async def run(self):
            logger.debug("Scheduler: SavePassengerInfo running")

            msg_body = json.loads(self.agent.msg.body)
            start_point = msg_body.get('start_point', None)
            destination = msg_body.get('destination', None)
            passenger_jid = self.agent.msg.sender
            if (start_point != None) & (destination != None):
                passenger_info = self.agent.PassengerInfo(passenger_jid, start_point, destination)
                self.agent.passenger_info = passenger_info

            # Ponizej rzeczy do testowania pasazera bez kodu busa
            # class SBus:
            #     def __init__(self) -> None:
            #         self.id = 1
                

            # self.agent.selected_bus = SBus()
            # logger.info(f"Selected bus: {self.agent.selected_bus.id}")
            # self.set_next_state("SEND_TRAVELPLAN")
            self.set_next_state("CFP")

    class PassengerInfo():
        def __init__(self, passenger_jid, start_point, destination):
            self.passenger_jid = passenger_jid
            self.start_point = start_point
            self.destination = destination

    class Cfp(State):
        async def run(self):
            logger.debug("Scheduler: Cfp running")
            for bus in self.agent.buses:
                msg = Message(to=bus)     # Instantiate the message
                msg.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
                msg.set_metadata("ontology", "select_bus")
                msg.set_metadata("language", "JSON")        # Set the language of the message content
                # chyba zmienia "passenger_jid": passenger@localhost na "passenger_jid": ["passenger", "localhost", null]. Czy to nie problem?
                body_dict = json.dumps({"passenger_info": self.agent.passenger_info.__dict__})  
                msg.body = body_dict                 # Set the message content

                await self.send(msg)
                logger.debug("Scheduler: Message sent!")

            self.set_next_state("RECEIVE_BUS_PROPOSE")

    class ReceiveBusPropose(State):
        async def run(self):
            logger.debug("Scheduler: ReceiveBusPropose running")

            template = Template()
            template.set_metadata("performative", "propose")
            template.set_metadata("ontology", "select_bus")
            # można dodać od koga ta wiadomość ma być (?)
            
            # TODO dodać odbieranie wiadomości od kilku busów
            for _ in range(len(self.agent.buses)):
                msg = await self.receive(timeout=10)
                if msg and template.match(msg):
                    self.agent.msg = msg
                    logger.info("Scheduler: Message received with content: {}".format(msg.body))
                    # TODO zapisanie informacji z wiadomości
                    msg_body = json.loads(self.agent.msg.body)
                    self.agent.costs[msg_body.get("id")] = msg_body.get("potential_cost")
                else:
                    # można wpaść w nieskończoną pętle, można by dodać zwrot informacji do pasażera, że nie można przydzielić busa
                    self.set_next_state("CFP")

            self.set_next_state("SELECT_BUS")

    class SelectBus(State):
        async def run(self):
            logger.debug("Scheduler: SelectBus running")

            logger.debug(f"Scheduler: costs = {self.agent.costs}")

            min_cost = float('inf')
            for jid, cost in self.agent.costs.items():
                if cost < min_cost:
                    min_cost = cost
                    self.agent.selected_bus = jid

            logger.info(f"Scheduler: selected {self.agent.selected_bus} with cost {min_cost}")

            self.set_next_state("REPLY_BUS")

    class ReplyBus(State):
        async def run(self):
            logger.debug("Scheduler: ReplyBus running")
            msg = Message(to=self.agent.selected_bus)     # Instantiate the message
            msg.set_metadata("performative", "accept")  # Set the "inform" FIPA performative
            msg.set_metadata("ontology", "select_bus")
            msg.set_metadata("language", "JSON")        # Set the language of the message content
            body_dict = json.dumps({"accepted": True})  
            msg.body = body_dict                 # Set the message content

            await self.send(msg)
            logger.debug("Scheduler: Message sent!")

            self.set_next_state("SEND_TRAVELPLAN")

    class SendTravelPlan(State):
        async def run(self):
            logger.debug("Scheduler: SendTravelPlan running")

            msg = Message(to=str(self.agent.passenger_info.passenger_jid))     # Instantiate the message
            msg.set_metadata("performative", "propose")  # Set the "inform" FIPA performative
            msg.set_metadata("ontology", "travel_request")
            msg.set_metadata("language", "JSON")        # Set the language of the message content
            body_dict = json.dumps({"bus_id": self.agent.selected_bus})
            msg.body = body_dict                 # Set the message content

            await self.send(msg)
            logger.info("Scheduler: SEND_TRAVELPLAN - Message sent!")

            self.set_next_state("RECEIVE_PASSENGER")

    async def setup(self):
        logger.debug("Scheduler: SchedulerAgent started")
        fsm = self.SchedulerBehaviour()

        fsm.add_state(name="RECEIVE_PASSENGER", state=self.ReceiveTravelRequest(), initial=True)     
        fsm.add_state(name="SAVE_PASSENGER_INFO", state=self.SavePassengerInfo())
        fsm.add_state(name="CFP", state=self.Cfp())
        fsm.add_state(name="RECEIVE_BUS_PROPOSE", state=self.ReceiveBusPropose())
        fsm.add_state(name="SELECT_BUS", state=self.SelectBus())
        fsm.add_state(name="REPLY_BUS", state=self.ReplyBus())
        fsm.add_state(name="SEND_TRAVELPLAN", state=self.SendTravelPlan())
        
        fsm.add_transition(source="RECEIVE_PASSENGER", dest="RECEIVE_PASSENGER")
        fsm.add_transition(source="RECEIVE_PASSENGER", dest="SAVE_PASSENGER_INFO")
        fsm.add_transition(source="SAVE_PASSENGER_INFO", dest="CFP")
        fsm.add_transition(source="CFP", dest="RECEIVE_BUS_PROPOSE")
        fsm.add_transition(source="RECEIVE_BUS_PROPOSE", dest="CFP")
        fsm.add_transition(source="RECEIVE_BUS_PROPOSE", dest="SELECT_BUS")
        fsm.add_transition(source="SELECT_BUS", dest="REPLY_BUS")
        fsm.add_transition(source="REPLY_BUS", dest="SEND_TRAVELPLAN")
        fsm.add_transition(source="SEND_TRAVELPLAN", dest="RECEIVE_PASSENGER")

        # Ponizej do testowania pasazera bez kodu busa
        # fsm.add_transition(source="SAVE_PASSENGER_INFO", dest="SEND_TRAVELPLAN")

        self.add_behaviour(fsm)
