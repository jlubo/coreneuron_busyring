"""
Adapted from the NSuite benchmarking framework (https://github.com/arbor-sim/nsuite.git).
"""

from neuron import h
import cell
import numpy as np

class RingNetwork(object):

    def __init__(self, params, pc):
        
        # Parallelization parameters
        self.rank_id = int(pc.id()) # host process/rank ID
        self.num_ranks = int(pc.nhost()) # number of host processes
        print(f"Initializing ring on rank_id={self.rank_id} (num_ranks={self.num_ranks}).")

        # Model parameters
        self.num_cells = params.num_cells
        self.min_delay = params.min_delay
        self.cell_params = params.cell
        self.ring_size = params.ring_size
        self.nrand_synapses = params.cell.synapses

        # Distribute the gids across ranks in a round-robin fashion
        self.gids = range(self.rank_id, self.num_cells, self.num_ranks)

        # Generate the cells
        self.cells = []
        for gid in self.gids:
            c = cell.branchy_cell(gid, self.cell_params)

            self.cells.append(c)

            # register this gid
            pc.set_gid2node(gid, self.rank_id)

            # This is the neuronic way to register a cell in a distributed
            # context. The netcon isn't meant to be used, so we hope that the
            # garbage collection does its job.
            nc = h.NetCon(c.soma(0.5)._ref_v, None, sec=c.soma)
            nc.threshold = 10
            pc.cell(gid, nc) # Associate the cell with this host and gid

        # Calculate and show cell stats
        total_comp = 0
        total_seg = 0
        for c in self.cells:
            total_comp += c.ncomp
            total_seg += c.nseg
        if self.num_ranks > 1:
            from mpi4py import MPI
            total_comp = MPI.COMM_WORLD.reduce(total_comp, op=MPI.SUM, root=0)
            total_seg = MPI.COMM_WORLD.reduce(total_seg, op=MPI.SUM, root=0)
        if self.rank_id == 0:
            print(f"Cell stats: {self.num_cells} cells; {total_seg} segments; {total_comp} compartments; {total_comp/self.num_cells} comp/cell.")
        print(f"Number of cells on rank {pc.id()}: {len(self.gids)}.")

        # Generate the connections to each gid on the current rank (and, thereby, create the rings):
        # 1. make an incoming connection from (gid-1) on the same ring
        # 2. add random connections (from within and across rings)
        self.connections = []
        self.stims = []
        self.stim_connections = []
        num_rings_created = 0
        num_syns_created = 0
        for i, gid in enumerate(self.gids):
            # Attach ring connection to previous gid in local ring
            rs = self.ring_size
            current_ring = int(gid/rs)
            ring_start = rs*current_ring
            ring_end = min(ring_start+rs, self.num_cells)
            src = gid-1
            if gid == ring_start:
                src = ring_end-1

            con = pc.gid_connect(src, self.cells[i].synapses[0])
            con.delay = self.min_delay
            con.weight[0] = params.event_weight
            self.connections.append(con)
            num_syns_created += 1

            # Attach stimulus if cell is first in the local ring
            if gid == ring_start:
                #print(f"Adding ring #{current_ring}...")
                stim = h.NetStim()
                stim.number = 1 # one spike
                stim.start = 0  # at t=0
                stim_con = h.NetCon(stim, self.cells[i].synapses[0])
                stim_con.delay = 1
                stim_con.weight[0] = params.event_weight
                self.stims.append(stim)
                self.stim_connections.append(stim_con)
                num_rings_created += 1
                num_syns_created += 1

            # Generate dummy connections with random source and zero weights
            src_gen = np.random.Generator(np.random.MT19937(seed=gid))
            delay_gen = np.random.Generator(np.random.MT19937(seed=gid))
            # Loop over all incoming synapses of this neuron, except the first one (which is the connection to the previous gid)
            for synapse_id in range(1, self.nrand_synapses+1):
                src = src_gen.integers(0, self.num_cells-2)
                if src == gid:
                    src += 1
                delay = self.min_delay + delay_gen.uniform(0, 2*self.min_delay)
                con = pc.gid_connect(src, self.cells[i].synapses[synapse_id])
                con.weight[0] = 0
                con.delay = delay
                self.connections.append(con)
                num_syns_created += 1
        
        print(f"Number of rings on rank {pc.id()} (created/expected): {num_rings_created}"
              f"/{len(self.gids)/self.ring_size}.")
        print(f"Number of synapses on rank {pc.id()} (created/expected): {num_syns_created}"
              f"/{(self.nrand_synapses*self.num_cells + self.num_cells)/self.num_ranks + len(self.gids)/self.ring_size}.")

