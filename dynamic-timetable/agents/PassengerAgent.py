from agents.utils import randomize_map_coordinates
from logger import logger
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json
import random
import time
from uuid import uuid4


TIMEOUT = 10
MAP_COORDINATE_LIMIT = 100
BUS_AWAITING_TME = 3
TRAVELING_TIME = 5
TRAVELING_STEP = 1
TRAVELING_COUNTER = 5
CHANGE_PLAN_CHANCES = 0.05
BUS_BRAKING_DOWN_CHANCES = 0.01
USER_RETRY_AFTER_FAILED_TRIP_CHANCES = 0.5


class PassengerAgent(Agent):
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self.main_beh = None
        self.change_plan_beh = None
        self.starting_point = randomize_map_coordinates(MAP_COORDINATE_LIMIT)
        self.destination = None
        self.bus_id = None
        self.passenger_id = uuid4()
        self.travel_counter = 0
        logger.info(f"Passenger with id {self.passenger_id} registered.")

    class PassengerBehaviour(FSMBehaviour):
        async def on_start(self) -> None:
            logger.info(f"Passenger FSM starting at initial state {self.current_state}")

        async def on_end(self) -> None:
            logger.info(f"Passsenger FSM finished at state {self.current_state}")

    class SelectDestination(State):
        def select_destination(self) -> tuple[float, float]:
            # FIXME - this could be loaded from the config
            return randomize_map_coordinates(MAP_COORDINATE_LIMIT)
    
        async def run(self) -> None:
            logger.debug("Passenger: SelectDestination running")
            logger.info(f"Passenger {self.agent.passenger_id} is selecting destination")

            # If the destination was previously selected, then it should stay the same
            if self.agent.destination is None:
                self.agent.destination = self.select_destination() 
            self.set_next_state("REQUEST_TRAVEL")   

    class RequestForTravel(State):
        async def run(self) -> None:
            logger.debug("Passenger: RequestForTravel running")
            msg = Message(to="scheduler@localhost")             # Instantiate the message
            msg.set_metadata("performative", "cfp")             # Set the "inform" FIPA performative
            msg.set_metadata("ontology", "travel_request")
            msg.set_metadata("language", "JSON")                # Set the language of the message content
            body_dict = {
                "start_point": self.agent.starting_point,
                "destination": self.agent.destination}
            msg.body = json.dumps(body_dict)                    # Set the message content

            await self.send(msg)
            logger.info(f"Passenger: Message sent with content: {body_dict}")

            self.set_next_state("AWAIT_TRAVEL_PLAN") 

    class AwaitTravelPlan(State):
        async def run(self) -> None:
            logger.debug("Passenger: AwaitTravelPlan running")
            msg = await self.receive(timeout=TIMEOUT) # wait for a message for 10 seconds
            if msg:
                logger.info("Message received with content: {}".format(msg.body))
                self.agent.bus_id = json.loads(msg.body).get("bus_id")
                logger.info(f"Bus with id {self.agent.bus_id} is selected for the passenger with id {self.agent.passenger_id}")
                self.set_next_state("WAIT_FOR_BUS") 
            else:
                logger.warning(f"Passenger: AwaitTravelPlanDid - not received any message after {TIMEOUT} seconds")
                self.set_next_state("SELECT_DESTINATION") 

    class WaitForBus(State):

        async def run(self) -> None:
            logger.debug("Passenger: WaitForBus running")
            self.agent._add_handle_bus_fail_beh()
            self.agent.change_plan_beh = self.agent.ChangePlan()
            self.agent.add_behaviour(self.agent.change_plan_beh)
            logger.info(f"Passenger {self.agent.passenger_id} is waiting for the bus {self.agent.bus_id}")
            time.sleep(BUS_AWAITING_TME)
            self.agent.travel_counter = 0
            self.set_next_state("TRAVEL")

    class PassengerTravel(State):
        async def run(self) -> None:
            logger.debug("Passenger: PassengerTravel running")
            logger.info(f"Passenger {self.agent.passenger_id} is driving to its selected destination")
            time.sleep(TRAVELING_STEP)
            if self.agent.travel_counter == 5:
                logger.info(f"Passenger {self.agent.passenger_id} finished the trip from {self.agent.starting_point} to {self.agent.destination}")
                self.set_next_state("EXIT_BUS_SUCCESSFULL")
            else:
                self.agent.travel_counter += 1
                self.set_next_state("TRAVEL")

    class ExitBus(State):
        async def run(self) -> None:
            logger.debug("Passenger: ExitBus running")
            await self.agent.stop()

    class HandleBusFailBeh(FSMBehaviour):
        async def on_start(self) -> None:
            logger.info(f"Passenger FSM HandleBusFailBeh starting at initial state {self.current_state}")

        async def on_end(self) -> None:
            logger.info(f"Passsenger FSM HandleBusFailBeh finished at state {self.current_state}")

    class ReceiveBusFailureMsg(State):
        async def run(self) -> None:
            logger.debug("Passenger: ReceiveBusFailureMsg running")
            
            # template = Template()
            # template.set_metadata("performative", "failure")
            # template.set_metadata("ontology", "drive")
            # template.set_metadata("language", "JSON")

            # msg = await self.receive(timeout=2)
            # if msg and template.match(msg):
                # self.agent.msg = msg
                # logger.info(f"Passenger {self.agent.passenger_id}: Message received with content: {msg.body}")
                # self.set_next_state("HANDLE_BUS_FAILURE")
            time.sleep(2)  # only for simulation
            if random.random() < BUS_BRAKING_DOWN_CHANCES: # only for simulation
                logger.info("Passenger: ReceiveBusFailureMsg - Bus broke down during the trip.")
                self.agent.main_beh.kill()
                self.agent.main_beh = None
                self.set_next_state("HANDLE_BUS_FAILURE")
            else:
                self.set_next_state("BUS_FAILURE_MSG")

    class HandleBusFailure(State):
        def _is_user_willing_to_retry(self) -> bool:
            return random.random() > USER_RETRY_AFTER_FAILED_TRIP_CHANCES
        
        async def run(self) -> None:
            logger.debug("Passenger: HandleBusFailure running")
            self.agent.starting_point = randomize_map_coordinates(MAP_COORDINATE_LIMIT)
            if self._is_user_willing_to_retry():
                logger.info(f"Passenger {self.agent.passenger_id} is starting looking for a next bus from new startng location: {self.agent.starting_point}")
                self.agent.change_plan_beh.kill()
                self.agent.change_plan_beh = None
                self.agent._add_main_beh()
                self.kill()
            else:
                logger.info(f"Passenger {self.agent.passenger_id} didn't agree to find a new bus.")
                self.set_next_state("EXIT_BUS_FAILED")

    class ChangePlan(CyclicBehaviour):
        async def run(self):
            logger.debug("Passenger: ChangePlan running")
            time.sleep(2) # only for simulation
            if random.random() < CHANGE_PLAN_CHANCES:
                self.agent.main_beh.kill()
                self.agent.main_beh = None

                msg = Message(to=self.agent.bus_id)  
                msg.set_metadata("performative", "inform")
                msg.set_metadata("ontology", "resignation")
                msg.set_metadata("language", "JSON")          
                body_dict = {
                    "resignation": True, "destination": self.agent.destination}
                msg.body = json.dumps(body_dict)  

                await self.send(msg)
                logger.info(f"Passenger: Message sent with content: {body_dict}")

                await self.agent.stop()       

    def _add_main_beh(self) -> None:
        fsm = self.PassengerBehaviour()

        fsm.add_state(name="SELECT_DESTINATION", state=self.SelectDestination(), initial=True)
        fsm.add_state(name="REQUEST_TRAVEL", state=self.RequestForTravel())     
        fsm.add_state(name="AWAIT_TRAVEL_PLAN", state=self.AwaitTravelPlan())
        fsm.add_state(name="WAIT_FOR_BUS", state=self.WaitForBus())
        fsm.add_state(name="TRAVEL", state=self.PassengerTravel())
        fsm.add_state(name="EXIT_BUS_SUCCESSFULL", state=self.ExitBus())
        
        fsm.add_transition(source="SELECT_DESTINATION", dest="REQUEST_TRAVEL")
        fsm.add_transition(source="REQUEST_TRAVEL", dest="AWAIT_TRAVEL_PLAN")
        fsm.add_transition(source="AWAIT_TRAVEL_PLAN", dest="SELECT_DESTINATION")
        fsm.add_transition(source="AWAIT_TRAVEL_PLAN", dest="WAIT_FOR_BUS")
        fsm.add_transition(source="WAIT_FOR_BUS", dest="TRAVEL")
        fsm.add_transition(source="TRAVEL", dest="EXIT_BUS_SUCCESSFULL")

        self.main_beh = fsm
        self.add_behaviour(self.main_beh)

    def _add_handle_bus_fail_beh(self) -> None:
        fsm_handle_fail_bus = self.HandleBusFailBeh()

        fsm_handle_fail_bus.add_state(name="BUS_FAILURE_MSG", state=self.ReceiveBusFailureMsg(), initial=True)
        fsm_handle_fail_bus.add_state(name="HANDLE_BUS_FAILURE", state=self.HandleBusFailure())
        fsm_handle_fail_bus.add_state(name="EXIT_BUS_FAILED", state=self.ExitBus())
        
        fsm_handle_fail_bus.add_transition(source="BUS_FAILURE_MSG", dest="BUS_FAILURE_MSG")
        fsm_handle_fail_bus.add_transition(source="BUS_FAILURE_MSG", dest="HANDLE_BUS_FAILURE")
        fsm_handle_fail_bus.add_transition(source="HANDLE_BUS_FAILURE", dest="EXIT_BUS_FAILED")

        self.add_behaviour(fsm_handle_fail_bus)

    async def setup(self) -> None:
        logger.debug("PassengerAgent started")

        self._add_main_beh()
