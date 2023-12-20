import spade
from agents.PassengerAgent import PassengerAgent
from agents.SchedulerAgent import SchedulerAgent

async def main():
    scheduleragent = SchedulerAgent("scheduler@localhost", "scheduler")
    await scheduleragent.start()

    passengeragent = PassengerAgent("passenger@localhost", "passenger")
    await passengeragent.start()

    await spade.wait_until_finished(scheduleragent)
    await scheduleragent.stop()
    await passengeragent.stop()
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())

