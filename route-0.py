#!/usr/bin/env python

import argparse
import os

from mininet.net import Mininet
from mininet.cli import CLI

from router import Router
from topology.one_node.topo import NetTopo as OneNode
from topology.two_nodes.topo import NetTopo as TwoNodes
from scenario import Basic, Plain, Isis


def start_daemon(node, daemon, conf_dir):
    """Start one FRR daemon on a given node.

    """
    node.cmd("/usr/lib/frr/{daemon}"
             " -f {conf_dir}/{node_name}.conf"
             " -d"
             " -i /tmp/{node_name}-{daemon}.pid"
             " > /tmp/{node_name}-{daemon}.out 2>&1"
             .format(daemon=daemon, conf_dir=conf_dir, node_name=node.name))
    node.waitOutput()


def run(topo, scenario):
    """Start a network scenario.
    """

    daemons = [
        "zebra",
        "staticd",
        "isisd",
    ]

    os.system("rm -f /tmp/R*.log /tmp/R*.pid /tmp/R*.out")
    os.system("rm -f /tmp/h*.log /tmp/h*.pid /tmp/h*.out")
    os.system("mn -c >/dev/null 2>&1")
    os.system("killall -9 {} > /dev/null 2>&1".format(' '.join(daemons)))

    net = Mininet(topo=topo, switch=Router)
    net.start()
    scenario.setup(net, topo.topo_dir)

    # WARNING: FRR can get confused unless all daemons on each node are started
    #          together.
    for node in net.switches:
        for daemon in daemons:
            if node in getattr(scenario, daemon):
                conf_dir = getattr(scenario, "{}_conf".format(daemon))
                start_daemon(node, daemon, conf_dir)

        if node.name.startswith('R'):
            # Enable IP forwarding
            node.cmd("sysctl -w net.ipv4.ip_forward=1")
            node.waitOutput()

            # Delete spare loopback address for convenience
            node.cmd("ip addr del 127.0.0.1/8 dev lo")
            node.waitOutput()

    CLI(net)
    net.stop()
    os.system("killall -9 {}".format(' '.join(daemons)))


if __name__ == "__main__":
    topology = {
        "one_node": OneNode,
        "two_nodes": TwoNodes,
    }

    scenario = {
        "plain": Plain,
        "basic": Basic,
        "isis": Isis,
    }

    supported = {
        "one_node": set(["plain", "basic"]),
        "two_nodes": set(["plain", "basic", "isis"]),
    }

    parser = argparse.ArgumentParser(
        description='Launch a network scenario Mininet.')
    parser.add_argument('--topology', type=str, required=True,
                        choices=topology.keys(),
                        help='the topology of the network')
    parser.add_argument('--scenario', type=str, required=True,
                        choices=scenario.keys(),
                        help='the scenario to set up in the network')
    ARGS = parser.parse_args()

    if ARGS.scenario not in supported[ARGS.topology]:
        raise ValueError("Scenario \"{}\" is not supported for topology \"{}\""
                         .format(ARGS.scenario, ARGS.topology))

    run(topology[ARGS.topology](),
        scenario[ARGS.scenario]())
