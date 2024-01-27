from agents.PassengerAgent import PassengerAgent
from unittest.mock import Mock
import asyncio
import pytest


pytest_plugins = ('pytest_asyncio',)



def test_select_destination(monkeypatch):
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]

    select_dest_state = passenger.SelectDestination()
    select_dest_state.set_agent(passenger)

    monkeypatch.setattr("agents.PassengerAgent.randomize_map_coordinates", Mock(return_value=[50, 50]))
    dest = select_dest_state.select_destination()
    assert dest == [50, 50]


def test_request_for_travel():
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]

    req_travel_state = passenger.RequestForTravel()
    req_travel_state.set_agent(passenger)
    msg = req_travel_state._create_message()

    assert msg.body == '{"start_point": [0, 0], "destination": [100, 100]}'
    assert msg.to.localpart == "scheduler"
    assert msg.metadata["language"] == "JSON"
    assert msg.metadata["ontology"] == "travel_request"
    assert msg.metadata["performative"] == "cfp"


@pytest.mark.asyncio
async def test_await_travel_plan():
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]

    await_travel_plan_state = passenger.AwaitTravelPlan()
    await_travel_plan_state.set_agent(passenger)

    class MockMsg:
        body = '{"bus_id": 1}'

    async def mock_receive(**kwargs):
        return MockMsg()

    await_travel_plan_state.receive = mock_receive

    await await_travel_plan_state.run()
    assert await_travel_plan_state.next_state == "WAIT_FOR_BUS"


@pytest.mark.asyncio
async def test_await_bus(monkeypatch):
    monkeypatch.setattr("agents.PassengerAgent.BUS_AWAITING_TME", 0.1)
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]

    bus_await_state = passenger.WaitForBus()
    bus_await_state.set_agent(passenger)

    await bus_await_state.run()

    assert bus_await_state.next_state == "TRAVEL"


@pytest.mark.asyncio
async def test_passenger_travel(monkeypatch):
    monkeypatch.setattr("agents.PassengerAgent.TRAVELING_STEP", 0.1)
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]
    passenger.travel_counter = 5

    travel_state = passenger.PassengerTravel()
    travel_state.set_agent(passenger)

    await travel_state.run()

    assert travel_state.next_state == "EXIT_BUS_SUCCESSFULL"


@pytest.mark.asyncio
async def test_bus_failure(monkeypatch):
    monkeypatch.setattr("agents.PassengerAgent.BUS_BRAKING_DOWN_CHANCES", -1)
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]

    receive_bus_failure_state = passenger.ReceiveBusFailureMsg()
    receive_bus_failure_state.set_agent(passenger)

    await receive_bus_failure_state.run()

    assert receive_bus_failure_state.next_state == "BUS_FAILURE_MSG"


@pytest.mark.asyncio
async def test_bus_handle_failure_retry(monkeypatch):
    monkeypatch.setattr("agents.PassengerAgent.PassengerAgent.HandleBusFailure._is_user_willing_to_retry", Mock(return_value=True))
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]
    passenger.change_plan_beh = passenger.ChangePlan()

    handle_bus_failure_state = passenger.HandleBusFailure()
    handle_bus_failure_state.set_agent(passenger)

    await handle_bus_failure_state.run()

    assert handle_bus_failure_state.is_running == False


@pytest.mark.asyncio
async def test_bus_handle_failure_no_retry(monkeypatch):
    monkeypatch.setattr("agents.PassengerAgent.PassengerAgent.HandleBusFailure._is_user_willing_to_retry", Mock(return_value=False))
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]
    passenger.change_plan_beh = passenger.ChangePlan()

    handle_bus_failure_state = passenger.HandleBusFailure()
    handle_bus_failure_state.set_agent(passenger)

    await handle_bus_failure_state.run()

    assert handle_bus_failure_state.next_state == "EXIT_BUS_FAILED"


@pytest.mark.asyncio
async def test_change_plan(monkeypatch):
    monkeypatch.setattr("agents.PassengerAgent.CHANGE_PLAN_CHANCES", 1000)
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]
    passenger._add_main_beh()

    change_plan_state = passenger.ChangePlan()
    change_plan_state.set_agent(passenger)

    class MockMsg:
        body = '{"bus_id": 1}'

    async def mock_send(msg, **kwargs):
        return MockMsg()

    change_plan_state.send = mock_send

    await change_plan_state.run()
    assert change_plan_state.is_running == False


def test_change_plan_msg(monkeypatch):
    monkeypatch.setattr("agents.PassengerAgent.CHANGE_PLAN_CHANCES", 1000)
    passenger = PassengerAgent("passenger@localhost", "passenger")
    passenger.destination = [100, 100]
    passenger.starting_point = [0, 0]
    passenger._add_main_beh()

    change_plan_state = passenger.ChangePlan()
    change_plan_state.set_agent(passenger)

    msg = change_plan_state._create_msg()
    assert msg.body == '{"resignation": true, "destination": [100, 100]}'
    assert msg.metadata["language"] == "JSON"
    assert msg.metadata["ontology"] == "resignation"
    assert msg.metadata["performative"] == "inform"


