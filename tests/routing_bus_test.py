from agents.RoutingBusAgent import RoutingBusAgent
from unittest.mock import Mock
import pytest
from spade.message import Message
import json

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test_receive_cfp(monkeypatch):
    initial_path = [[0, 0], [20, 20], [40, 40], [60, 60], [80, 80]]
    routing_bus = RoutingBusAgent("routing_bus1@localhost", "routing_bus1", initial_path)

    receive_cfp_state = routing_bus.ReceiveCfp()
    receive_cfp_state.set_agent(routing_bus)

    async def simul_receive_cfp_async(**kwargs):
        msg = Message(to="routing_bus1@localhost")  # Instantiate the message
        msg.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
        msg.set_metadata("ontology", "select_bus")
        msg.set_metadata("language", "JSON")  # Set the language of the message content
        return msg

    receive_cfp_state.receive = simul_receive_cfp_async

    await receive_cfp_state.run()
    assert receive_cfp_state.next_state == "GET_BUS_INFORMATION"

@pytest.mark.asyncio
async def test_get_bus_information(monkeypatch):
    initial_path = [[0, 0], [20, 20], [40, 40], [60, 60], [80, 80]]
    routing_bus = RoutingBusAgent("routing_bus1@localhost", "routing_bus1", initial_path)

    get_bus_information_state = routing_bus.GetBusInformation()
    get_bus_information_state.set_agent(routing_bus)

    MOCK_POSITION = [50, 50]

    monkeypatch.setattr("agents.RoutingBusAgent.randomize_map_coordinates", Mock(return_value=MOCK_POSITION))

    await get_bus_information_state.run()
    assert get_bus_information_state.position == MOCK_POSITION
    assert get_bus_information_state.next_state == "CALCULATE_POTENTIAL_COST"

@pytest.mark.asyncio
async def test_calculate_potential_cost_state(monkeypatch):
    initial_path = [[0, 0], [20, 20], [40, 40], [60, 60], [80, 80]]
    routing_bus = RoutingBusAgent("routing_bus1@localhost", "routing_bus1", initial_path)

    calculate_potential_cost_state = routing_bus.CalculatePotentialCost()
    calculate_potential_cost_state.set_agent(routing_bus)

    def simul_msg(**kwargs):
        msg = Message(to="routing_bus1")  # Instantiate the message
        msg.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
        msg.set_metadata("ontology", "select_bus")
        msg.set_metadata("language", "JSON")  # Set the language of the message content
        body_dict = json.dumps({"passenger_info": {
            "start_point": [10, 10],
            "destination": [30, 30]
        }})
        msg.body = body_dict  # Set the message content
        return msg

    async def simul_send(msg):
        pass

    routing_bus.msg = simul_msg()
    calculate_potential_cost_state.send = simul_send

    await calculate_potential_cost_state.run()
    assert calculate_potential_cost_state.next_state == "WAIT_FOR_DECISION"

def test_calculate_potential_cost_path(monkeypatch):
    initial_path = [[0, 0], [20, 20], [40, 40], [60, 60], [80, 80]]
    routing_bus = RoutingBusAgent("routing_bus1@localhost", "routing_bus1", initial_path)

    calculate_potential_cost_state = routing_bus.CalculatePotentialCost()
    calculate_potential_cost_state.set_agent(routing_bus)

    increase_in_length, potential_new_path = calculate_potential_cost_state.add_points_with_nearest_neighbor_heuristic(
        initial_path,
        [[10, 10], [30, 30]]
    )

    assert increase_in_length == 0
    assert potential_new_path == [[0, 0], [10, 10], [20, 20], [30, 30], [40, 40], [60, 60], [80, 80]]

@pytest.mark.asyncio
async def test_wait_for_decision(monkeypatch):
    initial_path = [[0, 0], [20, 20], [40, 40], [60, 60], [80, 80]]
    routing_bus = RoutingBusAgent("routing_bus1@localhost", "routing_bus1", initial_path)

    wait_for_decision_state = routing_bus.WaitForDecision()
    wait_for_decision_state.set_agent(routing_bus)

    async def simul_receive_decision_async(**kwargs):
        msg = Message(to="routing_bus1")  # Instantiate the message
        msg.set_metadata("performative", "accept")  # Set the "inform" FIPA performative
        msg.set_metadata("ontology", "select_bus")
        msg.set_metadata("language", "JSON")  # Set the language of the message content
        body_dict = json.dumps({"accepted": True})
        msg.body = body_dict  # Set the message content
        return msg

    wait_for_decision_state.receive = simul_receive_decision_async

    await wait_for_decision_state.run()
    assert wait_for_decision_state.next_state == "CALCULATE_ROUTE"

@pytest.mark.asyncio
async def test_calculate_route(monkeypatch):
    initial_path = [[0, 0], [20, 20], [40, 40], [60, 60], [80, 80]]
    routing_bus = RoutingBusAgent("routing_bus1@localhost", "routing_bus1", initial_path)

    calculate_route_state = routing_bus.CalculateRoute()
    calculate_route_state.set_agent(routing_bus)

    routing_bus.potential_path = [[0, 0], [10, 10], [20, 20], [30, 30], [40, 40], [60, 60], [80, 80]]

    assert routing_bus.path is initial_path
    await calculate_route_state.run()
    assert calculate_route_state.agent.path is not initial_path

    assert calculate_route_state.next_state == "RECEIVE_CFP"
