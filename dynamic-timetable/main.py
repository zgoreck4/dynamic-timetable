import spade
from agents.PassengerAgent import PassengerAgent
from agents.SchedulerAgent import SchedulerAgent
from agents.RoutingBusAgent import RoutingBusAgent

async def main():
    initial_path = [(0, 0), (5, 5), (10, 10), (15, 15), (20, 20)]
    routingbusagent1 = RoutingBusAgent("routing_bus1@localhost", "routing_bus1", initial_path)
    await routingbusagent1.start()

    initial_path = [(20, 0), (15, 5), (10, 10), (5, 15), (0, 20)]
    routingbusagent2 = RoutingBusAgent("routing_bus2@localhost", "routing_bus2", initial_path)
    await routingbusagent2.start()

    scheduleragent = SchedulerAgent(
        "scheduler@localhost",
        "scheduler",
        [str(routingbusagent1.jid), str(routingbusagent2.jid)]
    )
    await scheduleragent.start()

    passengeragent = PassengerAgent("passenger@localhost", "passenger")
    await passengeragent.start()

    await spade.wait_until_finished(scheduleragent)
    await scheduleragent.stop()
    await passengeragent.stop()
    await routingbusagent1.stop()
    await routingbusagent2.stop()
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())

