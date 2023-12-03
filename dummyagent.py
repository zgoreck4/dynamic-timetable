import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template


class PassengerAgent(Agent):
    class PassengerBehav(OneShotBehaviour):
        async def run(self):
            print("PassengerBehav running")
            msg = Message(to="scheduler@localhost")     # Instantiate the message
            msg.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
            msg.set_metadata("language", "JSON")        # Set the language of the message content
            msg.body = "Hello World"                    # Set the message content

            await self.send(msg)
            print("Message sent!")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("PassengerAgent started")
        b = self.PassengerBehav()
        self.add_behaviour(b)

class SchedulerAgent(Agent):
    class SchedulerBehav(OneShotBehaviour):
        async def run(self):
            print("SchedulerBehav running")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("SchedulerAgent started")
        b = self.SchedulerBehav()
        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(b, template)



async def main():
    scheduleragent = SchedulerAgent("scheduler@localhost", "scheduler")
    await scheduleragent.start()
    print("Scheduler started")

    passengeragent = PassengerAgent("passenger@localhost", "passenger")
    await passengeragent.start()
    print("Passenger started")

    await spade.wait_until_finished(scheduleragent)
    print("Agents finished")


if __name__ == "__main__":
    spade.run(main())
