from agents.utils import randomize_map_coordinates
from logger import logger
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import json
import random
import time
from uuid import uuid4


TIMEOUT = 10
MAP_COORDINATE_LIMIT = 100
BUS_AWAITING_TME = 3
TRAVELING_TIME = 5
BUS_NOT_ARRIVING_CHANCES = 0.05
BUS_BRAKING_DOWN_CHANCES = 0.01
USER_RETRY_AFTER_FAILED_TRIP_CHANCES = 0.5


class PassengerAgent(Agent):
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self.starting_point = randomize_map_coordinates(MAP_COORDINATE_LIMIT)
        self.destination = None
        self.bus_id = None
        self.passenger_id = uuid4()
        logger.info(f"Passenger with id {self.passenger_id} registered.")

    class PassengerBehaviour(FSMBehaviour):
        async def on_start(self) -> None:
            logger.info(f"Passenger FSM starting at initial state {self.current_state}")

        async def on_end(self) -> None:
            logger.info(f"Passsenger FSM finished at state {self.current_state}")
            await self.agent.stop()

    class SelectDestination(State):
        def select_destination(self) -> tuple[float, float]:
            # FIXME - this could be loaded from the config
            return randomize_map_coordinates(MAP_COORDINATE_LIMIT)
    
        async def run(self) -> None:
            logger.info(f"Passenger {self.agent.passenger_id} is selecting destination")

            # If the destination was previously selected, then it should stay the same
            if self.agent.destination is None:
                self.agent.destination = self.select_destination() 
            self.set_next_state("REQUEST_TRAVEL")   

    class RequestForTravel(State):
        async def run(self) -> None:
            logger.debug("Passenger RequestForTravel running")
            msg = Message(to="scheduler@localhost")             # Instantiate the message
            msg.set_metadata("performative", "cfp")             # Set the "inform" FIPA performative
            msg.set_metadata("ontology", "travel_request")
            msg.set_metadata("language", "JSON")                # Set the language of the message content
            body_dict = {
                "start_point": self.agent.starting_point,
                "destination": self.agent.destination}
            msg.body = json.dumps(body_dict)                    # Set the message content

            await self.send(msg)
            logger.debug(f"Message sent! \n Content: {body_dict}")

            self.set_next_state("AWAIT_TRAVEL_PLAN") 

    class AwaitTravelPlan(State):
        async def run(self) -> None:
            logger.debug("Passenger AwaitTravelPlan running")
            msg = await self.receive(timeout=TIMEOUT) # wait for a message for 10 seconds
            if msg:
                logger.info("Message received with content: {}".format(msg.body))
                self.agent.bus_id = json.loads(msg.body).get("bus_id")
                logger.info(f"Bus with id {self.agent.bus_id} is selected for the passenger with id {self.agent.passenger_id}")
                self.set_next_state("WAIT_FOR_BUS") 
            else:
                logger.warning(f"Did not received any message after {TIMEOUT} seconds")
                self.set_next_state("SELECT_DESTINATION") 

    class WaitForBus(State):
        def _wait_for_bus(self) -> bool:
            """
            Simulate waiting for the bus (wait for hardcoded time)
            """
            logger.info(f"Passenger {self.agent.passenger_id} is waiting for the bus {self.agent.bus_id}")
            time.sleep(BUS_AWAITING_TME)

            return random.random() > BUS_NOT_ARRIVING_CHANCES

        async def run(self) -> None:
            if self._wait_for_bus():
                self.set_next_state("TRAVEL")
            else:
                logger.info(f"Bus did not arrived in time due to technical problems. Passenger {self.agent.passenger_id} is starting looking for a next bus.")
                self.set_next_state("SELECT_DESTINATION")

    class PassengerTravel(State):
        def _travel(self) -> bool:
            """
            Simulate traveling by bus (wait for hardcoded time)
            """
            logger.info(f"Passenger {self.agent.passenger_id} is driving to its selected destination")
            time.sleep(TRAVELING_TIME)

            return random.random() > BUS_BRAKING_DOWN_CHANCES
        
        def _is_user_willing_to_retry(self) -> bool:
            return random.random() > USER_RETRY_AFTER_FAILED_TRIP_CHANCES
        
        async def run(self) -> None:
            if self._travel():
                logger.info(f"Passenger {self.agent.passenger_id} finished the trip from {self.agent.starting_point} to {self.agent.destination}")
                self.set_next_state("EXIT_BUS_SUCCESSFULL")
                
            else:
                self.agent.starting_point = randomize_map_coordinates(MAP_COORDINATE_LIMIT)
                logger.info(f"Bus broke down during the trip.")
                if self._is_user_willing_to_retry():
                    logger.info(f"Passenger {self.agent.passenger_id} is starting looking for a next bus from new startng location: {self.agent.starting_point}")
                    self.set_next_state("SELECT_DESTINATION")
                else:
                    logger.info(f"Passenger {self.agent.passenger_id} didn't agree to find a new bus.")
                    self.set_next_state("EXIT_BUS_FAILED")

    class ExitBus(State):
        async def run(self) -> None:
            await self.agent.stop()


    async def setup(self) -> None:
        logger.debug("PassengerAgent started")

        fsm = self.PassengerBehaviour()

        fsm.add_state(name="SELECT_DESTINATION", state=self.SelectDestination(), initial=True)
        fsm.add_state(name="REQUEST_TRAVEL", state=self.RequestForTravel())     
        fsm.add_state(name="AWAIT_TRAVEL_PLAN", state=self.AwaitTravelPlan())
        fsm.add_state(name="WAIT_FOR_BUS", state=self.WaitForBus())
        fsm.add_state(name="TRAVEL", state=self.PassengerTravel())
        fsm.add_state(name="EXIT_BUS_SUCCESSFULL", state=self.ExitBus())
        fsm.add_state(name="EXIT_BUS_FAILED", state=self.ExitBus())
        
        fsm.add_transition(source="SELECT_DESTINATION", dest="REQUEST_TRAVEL")
        fsm.add_transition(source="REQUEST_TRAVEL", dest="AWAIT_TRAVEL_PLAN")
        fsm.add_transition(source="AWAIT_TRAVEL_PLAN", dest="SELECT_DESTINATION")
        fsm.add_transition(source="AWAIT_TRAVEL_PLAN", dest="WAIT_FOR_BUS")
        fsm.add_transition(source="WAIT_FOR_BUS", dest="SELECT_DESTINATION")
        fsm.add_transition(source="WAIT_FOR_BUS", dest="TRAVEL")
        fsm.add_transition(source="TRAVEL", dest="SELECT_DESTINATION")
        fsm.add_transition(source="TRAVEL", dest="EXIT_BUS_SUCCESSFULL")
        fsm.add_transition(source="TRAVEL", dest="EXIT_BUS_FAILED")

        self.add_behaviour(fsm)
