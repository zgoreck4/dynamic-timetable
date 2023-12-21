import spade
from agents.PassengerAgent import PassengerAgent
from agents.SchedulerAgent import SchedulerAgent
from agents.RoutingBusAgent import RoutingBusAgent

async def main():
    scheduleragent = SchedulerAgent("scheduler@localhost", "scheduler")
    await scheduleragent.start()

    passengeragent = PassengerAgent("passenger@localhost", "passenger")
    await passengeragent.start()

    routingbusagent = RoutingBusAgent("routing_bus@localhost", "routing_bus")
    await routingbusagent.start()

    await spade.wait_until_finished(scheduleragent)
    await scheduleragent.stop()
    await passengeragent.stop()
    await routingbusagent.stop()
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())

