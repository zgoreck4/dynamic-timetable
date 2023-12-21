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
        self.id = jid
        self.path = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)] # TODO - jakoś inaczej inicjalizować
        self.potential_new_path = None

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

    class CalculatePotentialCost(State):
        async def run(self):
            print("*** RoutingBus: CalculatePotentialCost running")

            msg_body = json.loads(self.agent.msg.body)
            start_point = msg_body.get('passenger_info', None).get('start_point', None)
            destination = msg_body.get('passenger_info', None).get('destination', None)

            increase_in_length, potential_new_path = self.add_points_with_nearest_neighbor_heuristic(
                self.agent.path,
                [start_point, destination]
            )

            print("*** RoutingBus: increase_in_length = {}".format(increase_in_length))
            print("*** RoutingBus: potential_new_path = {}".format(potential_new_path))

            self.agent.potential_new_path = potential_new_path

            msg = Message(to="scheduler@localhost")     # Instantiate the message
            msg.set_metadata("performative", "propose")
            msg.set_metadata("ontology", "select_bus")
            msg.set_metadata("language", "JSON")        # Set the language of the message content

            body_dict = json.dumps({"id": self.agent.id, "potential_cost": increase_in_length})  
            msg.body = body_dict                 # Set the message content

            await self.send(msg)
            print("*** RoutingBus: potential_cost sent!")

            self.set_next_state("WAIT_FOR_DECISION")

        def calculate_distance(self, point1, point2):
            return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])

        def calculate_path_length(self, path):
            return sum(self.calculate_distance(path[i], path[i+1]) for i in range(len(path) - 1))

        def find_optimal_insertion_point_for_new_point(self, original_path, new_point, start_index=0):
            """Znajdowanie optymalnego miejsca wstawienia nowego punktu na ścieżce."""
            min_increase = float('inf')
            optimal_insertion_index = start_index

            # Sprawdzanie wstawienia na początku ścieżki
            if original_path and start_index==0:
                increase_at_start = self.calculate_distance(new_point, original_path[0])
                if increase_at_start < min_increase:
                    min_increase = increase_at_start
                    optimal_insertion_index = 0

            # Sprawdzanie wstawienia między istniejącymi punktami
            for i in range(start_index, len(original_path) - 1):
                increase = (self.calculate_distance(original_path[i], new_point) +
                            self.calculate_distance(new_point, original_path[i + 1]) -
                            self.calculate_distance(original_path[i], original_path[i + 1]))

                if increase < min_increase:
                    min_increase = increase
                    optimal_insertion_index = i + 1

            # Sprawdzanie wstawienia na końcu ścieżki
            if original_path:
                increase_at_end = self.calculate_distance(new_point, original_path[-1])
                if increase_at_end < min_increase:
                    min_increase = increase_at_end
                    optimal_insertion_index = len(original_path)

            return optimal_insertion_index, min_increase

        def add_points_with_nearest_neighbor_heuristic(self, original_path, new_points):
            if not original_path:
                return 0, new_points  # Nowa ścieżka składa się tylko z nowych punktów

            total_increase = 0
            new_path = original_path.copy()
            first_point_insertion_index, increase = self.find_optimal_insertion_point_for_new_point(new_path, new_points[0])
            new_path.insert(first_point_insertion_index, new_points[0])
            total_increase += increase

            # Drugi punkt musi być wstawiony po pierwszym
            second_point_insertion_index, increase = self.find_optimal_insertion_point_for_new_point(new_path, new_points[1], first_point_insertion_index + 1)
            new_path.insert(second_point_insertion_index, new_points[1])
            total_increase += increase

            return total_increase, new_path
        
    class WaitForDecision(State):
        async def run(self):
            print("*** RoutingBus: WaitForDecision running")

            template = Template()
            template.set_metadata("performative", "accept")  # Set the "inform" FIPA performative
            template.set_metadata("ontology", "select_bus")
            template.set_metadata("language", "JSON")        # Set the language of the message content

            msg = await self.receive(timeout=10)
            if msg and template.match(msg):
                print("*** RoutingBus: New route accepted")
                self.set_next_state("CALCULATE_ROUTE")
            else:
                print("*** RoutingBus: New route not accepted")
                self.set_next_state("RECEIVE_CFP")

    async def setup(self):
        print("*** RoutingBus: started")
        fsm = self.RoutingBusBehaviour()

        fsm.add_state(name="RECEIVE_CFP", state=self.ReceiveCfp(), initial=True)
        fsm.add_state(name="GET_BUS_INFORMATION", state=self.GetBusInformation())
        fsm.add_state(name="CALCULATE_POTENTIAL_COST", state=self.CalculatePotentialCost())
        fsm.add_state(name="WAIT_FOR_DECISION", state=self.WaitForDecision())

        fsm.add_transition(source="RECEIVE_CFP", dest="RECEIVE_CFP")
        fsm.add_transition(source="RECEIVE_CFP", dest="GET_BUS_INFORMATION")
        fsm.add_transition(source="GET_BUS_INFORMATION", dest="CALCULATE_POTENTIAL_COST")
        fsm.add_transition(source="CALCULATE_POTENTIAL_COST", dest="WAIT_FOR_DECISION")

        self.add_behaviour(fsm)
