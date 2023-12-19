import spade
from agents.PassengerAgent import PassengerAgent
from agents.SchedulerAgent import SchedulerAgent

async def main():
    scheduleragent = SchedulerAgent("scheduler@localhost", "scheduler")
    await scheduleragent.start()
    print("Scheduler started")

    destination1 = input("Destination 1. passenger: ")
    passengeragent = PassengerAgent("passenger@localhost", "passenger", destination1)
    await passengeragent.start()
    print("Passenger started")

    await spade.wait_until_finished(scheduleragent) # wait until user interrupts with ctrl+C ?
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())

