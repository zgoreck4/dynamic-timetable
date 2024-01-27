import pytest
import spade
from agents.PassengerAgent import PassengerAgent
from agents.SchedulerAgent import SchedulerAgent
from agents.RoutingBusAgent import RoutingBusAgent

pytest_plugins = ('pytest_asyncio',)


@pytest.skip(reason="This test can take a while. Comment this line to run it.", allow_module_level=True)
@pytest.mark.asyncio
async def test_e2e_travel(monkeypatch):
    monkeypatch.setattr("agents.PassengerAgent.BUS_AWAITING_TME", 0.1)
    monkeypatch.setattr("agents.PassengerAgent.TRAVELING_STEP", 0.1)
    monkeypatch.setattr("agents.PassengerAgent.BUS_BRAKING_DOWN_CHANCES", -1) # no chance of bus breaking down
    monkeypatch.setattr("agents.PassengerAgent.CHANGE_PLAN_CHANCES", -1) # no chance of changing plan

    initial_path = [[0, 0], [20, 20], [40, 40], [60, 60], [80, 80]]
    routingbusagent1 = RoutingBusAgent("routing_bus1@localhost", "routing_bus1", initial_path)
    await routingbusagent1.start()

    initial_path = [[100, 0], [80, 20], [60, 40], [40, 60], [20, 80]]
    routingbusagent2 = RoutingBusAgent("routing_bus2@localhost", "routing_bus2", initial_path)
    await routingbusagent2.start()

    scheduleragent = SchedulerAgent(
        "scheduler@localhost",
        "scheduler",
        [str(routingbusagent1.jid), str(routingbusagent2.jid)]
    )
    await scheduleragent.start()

    passengeragent = PassengerAgent("passenger@localhost", "passenger")
    passengeragent.destination = [100, 100]
    passengeragent.starting_point = [0, 0]

    await passengeragent.start()
    await passengeragent.stop()
    await spade.wait_until_finished(scheduleragent)
    await scheduleragent.stop()
    await routingbusagent1.stop()
    await routingbusagent2.stop()

    assert passengeragent.travel_counter == 5
    assert not passengeragent.is_alive()
