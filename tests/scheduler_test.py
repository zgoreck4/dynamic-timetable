from agents.SchedulerAgent import SchedulerAgent
import asyncio
import pytest
from spade.message import Message
import json
from aioxmpp import JID


pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_receive_travel_request():
    scheduler = SchedulerAgent("scheduler@localhost", "scheduler", ["routing_bus1@localhost", "routing_bus2@localhost"])

    receive_travel_req = scheduler.ReceiveTravelRequest()
    receive_travel_req.set_agent(scheduler)

    async def simul_receive_req_async(**kwargs):
        msg = Message(to="scheduler@localhost")  # Instantiate the message
        msg.set_metadata("performative", "cfp")  # Set the "inform" FIPA performative
        msg.set_metadata("ontology", "travel_request")
        msg.set_metadata("language", "JSON")  # Set the language of the message content
        return msg

    receive_travel_req.receive = simul_receive_req_async

    await receive_travel_req.run()
    assert receive_travel_req.next_state == "SAVE_PASSENGER_INFO"

@pytest.mark.asyncio
async def test_save_psg_info():
    scheduler = SchedulerAgent("scheduler@localhost", "scheduler", ["routing_bus1@localhost", "routing_bus2@localhost"])

    save_psgr_info = scheduler.SavePassengerInfo()
    save_psgr_info.set_agent(scheduler)

    def simul_receive_req():
        msg = Message(to="scheduler@localhost")  # Instantiate the message
        body_dict = {
            "start_point": [12, 32],
            "destination": [79, 10]}
        msg.body = json.dumps(body_dict)
        msg.sender = "passenger@localhost"
        return msg

    scheduler.msg = simul_receive_req()
    await save_psgr_info.run()
    assert scheduler.passenger_info.start_point == [12, 32]
    assert scheduler.passenger_info.destination == [79, 10]
    assert scheduler.passenger_info.passenger_jid == JID(localpart='passenger', domain='localhost', resource=None)


def test_cfp():
    scheduler = SchedulerAgent("scheduler@localhost", "scheduler", ["routing_bus1@localhost", "routing_bus2@localhost"])
    paasenger_info = scheduler.PassengerInfo('passenger@localhost', [20, 13], [60,4])
    scheduler.passenger_info = paasenger_info

    cfp = scheduler.Cfp()
    cfp.set_agent(scheduler)

    msg = cfp._create_cfp("routing_bus1@localhost")

    assert msg.body == '{"passenger_info": {"passenger_jid": "passenger@localhost", "start_point": [20, 13], "destination": [60, 4]}}'
    assert msg.to.localpart == "routing_bus1"
    assert msg.metadata["language"] == "JSON"
    assert msg.metadata["ontology"] == "select_bus"
    assert msg.metadata["performative"] == "cfp"

@pytest.mark.asyncio
async def test_receive_bus_prop():
    scheduler = SchedulerAgent("scheduler@localhost", "scheduler", ["routing_bus1@localhost", "routing_bus2@localhost"])

    receive_bus_prop = scheduler.ReceiveBusPropose()
    receive_bus_prop.set_agent(scheduler)

    async def simul_receive_bus_prop(**kwargs):
        msg = Message(to="scheduler@localhost")  # Instantiate the message
        msg.set_metadata("performative", "propose")  # Set the "inform" FIPA performative
        msg.set_metadata("ontology", "select_bus")
        msg.body = json.dumps({"id": "routing_bus1@localhost", "potential_cost": 30})  
        return msg

    receive_bus_prop.receive = simul_receive_bus_prop

    await receive_bus_prop.run()
    assert scheduler.costs["routing_bus1@localhost"] == 30
    assert receive_bus_prop.next_state == "SELECT_BUS"

@pytest.mark.asyncio
async def test_select_bus():
    scheduler = SchedulerAgent("scheduler@localhost", "scheduler", ["routing_bus1@localhost", "routing_bus2@localhost", "routing_bus3@localhost"])
    scheduler.costs = {"routing_bus1@localhost": 20, "routing_bus2@localhost":4, "routing_bus3@localhost": 130}
    
    select_bus = scheduler.SelectBus()
    select_bus.set_agent(scheduler)
    await select_bus.run()

    assert scheduler.selected_bus == "routing_bus2@localhost"

def test_reply_bus():
    scheduler = SchedulerAgent("scheduler@localhost", "scheduler", ["routing_bus1@localhost", "routing_bus2@localhost"])
    scheduler.selected_bus = "routing_bus2@localhost"

    reply_bus = scheduler.ReplyBus()
    reply_bus.set_agent(scheduler)

    msg = reply_bus._create_msg()

    assert msg.body == '{"accepted": true}'
    assert msg.to.localpart == "routing_bus2"
    assert msg.metadata["language"] == "JSON"
    assert msg.metadata["ontology"] == "select_bus"
    assert msg.metadata["performative"] == "accept"

def test_send_travel_plan():
    scheduler = SchedulerAgent("scheduler@localhost", "scheduler", ["routing_bus1@localhost", "routing_bus2@localhost"])
    scheduler.selected_bus = "routing_bus2@localhost"
    paasenger_info = scheduler.PassengerInfo('passenger@localhost', [20, 13], [60,4])
    scheduler.passenger_info = paasenger_info

    send_travel_plan = scheduler.SendTravelPlan()
    send_travel_plan.set_agent(scheduler)

    msg = send_travel_plan._create_msg()

    assert msg.body == '{"bus_id": "routing_bus2@localhost"}'
    assert msg.to.localpart == "passenger"
    assert msg.metadata["language"] == "JSON"
    assert msg.metadata["ontology"] == "travel_request"
    assert msg.metadata["performative"] == "propose"