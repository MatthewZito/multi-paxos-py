import logging
import sys

from .network.network import Network
from .roles.initializer import Initializer
from .roles.requester import Requester
from .roles.seed import Seed

from .state_machines.test_machine import test_machine

sequences_running = 0

def proc_sequence(network, node, key):
    global sequences_running

    sequences_running += 1

    reqs = [
        (('get', key), None),
        (('set', key, 10), 10),
        (('get', key), 10),
        (('set', key, 20), 20),
        (('set', key, 30), 30),
        (('get', key), 30),
    ]

    def request():
        if not reqs:
            global sequences_running
            sequences_running -= 1

            if not sequences_running:
                network.stop()
            return

        inp, out = reqs.pop(0)

        def done(output):
            assert output == out, f'{output} != {out}'
            request()

        Requester(
            node,
            inp,
            done
        ).start()

    network.set_timer(None, 1.0, request)


def main():
    logging.basicConfig(
        format='%(name)s - %(message)s',
        level=logging.DEBUG
    )

    network = Network(int(sys.argv[1]))

    peers = [f'N{i for i in range(6)}']

    for peer in peers:
        node = network.new_node(addr=peer)

        if peer == 'N0':
            Seed(
                node,
                initial_state={},
                peers=peers,
                executor=test_machine
            )

        else:
            Initializer(
                node,
                executor=test_machine,
                peers=peers
            ).start()

    for key in 'abcdef':
        proc_sequence(
            network,
            node,
            key
        )

    network.run()

if __name__ == '__main__':
    main()
