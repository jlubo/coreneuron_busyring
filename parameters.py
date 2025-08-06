"""
Adapted from the NSuite benchmarking framework (https://github.com/arbor-sim/nsuite.git)
"""

import json

def from_json(o, key):
    if key in o:
        return o[key]
    else:
        raise Exception(str('parameter "'+ key+ '" not in input file'))

class cell_parameters:
    def __repr__(self):
        s = "cell parameters\n" \
            "  depth        :  {0:10d}\n" \
            "  branch prob  :  [{1:5.2f} : {2:5.2f}]\n" \
            "  compartments :  [{3:5d} : {4:5d}]\n" \
            "  lengths      :  [{5:5.1f} : {6:5.1f}]\n" \
            "  connections  :  {7:5.1f}\n" \
            .format(self.max_depth,
                    self.branch_probs[0], self.branch_probs[1],
                    self.compartments[0], self.compartments[1],
                    self.lengths[0], self.lengths[1],
                    self.synapses)
        return s

    def __init__(self, data, p_branch, num_comparts, num_rand_syns):
        # First setting default values (including those provided via commandline)
        self.max_depth    = 5
        self.branch_probs = p_branch
        self.compartments = num_comparts
        self.lengths      = [200, 20]
        self.synapses     = num_rand_syns

        # Overwriting with loaded configuration
        if data:
            self.max_depth    = from_json(data, 'depth')
            self.branch_probs = from_json(data, 'branch-probs')
            self.compartments = from_json(data, 'compartments')
            self.lengths      = from_json(data, 'lengths')
            self.synapses     = from_json(data, 'synapses')
            if bool(from_json(data, 'complex')):
                print("Warning: Cell type 'complex' is currently not supported. Using simple branchy cell instead.")

class model_parameters:
    def __repr__(self):
        s = "parameters\n" \
            "  name         : {0:>10s}\n" \
            "  cells        : {1:10d}\n" \
            "  ring size    : {2:10d}\n" \
            "  duration     : {3:10.0f} ms\n" \
            "  min delay    : {4:10.0f} ms\n" \
            "  dt           : {5:10.0f} ms\n" \
            .format(self.name, self.num_cells, self.ring_size, self.duration, self.min_delay, self.dt)
        s+= str(self.cell)
        return s

    def __init__(self,
                 filename, duration,
                 num_rings, num_ring_cells,
                 p_branch, num_comparts, num_rand_syns,
                 pc):
        # First setting default values (including those provided via commandline)
        self.name         = 'default'
        self.duration     = duration
        self.dt           = 0.025
        self.num_cells    = num_rings * num_ring_cells
        self.ring_size    = num_ring_cells
        self.min_delay    = 10
        self.event_weight = 0.01
        self.cell = cell_parameters(None, p_branch, num_comparts, num_rand_syns)

        # Overwriting with loaded configuration
        if filename:
            if pc.id() == 0:
                print(f"Configuration file has been provided - this will overwrite default parameter values and such provided via commandline arguments.")
            with open(filename) as f:
                data = json.load(f)
                self.name         = from_json(data, 'name')
                self.duration     = from_json(data, 'duration')
                self.dt           = from_json(data, 'dt')
                self.num_cells    = from_json(data, 'num-cells')
                self.ring_size    = from_json(data, 'ring-size')
                self.min_delay    = from_json(data, 'min-delay')
                self.event_weight = from_json(data, 'event-weight')
                self.cell         = cell_parameters(data, p_branch, num_comparts, num_rand_syns)
        else:
            if pc.id() == 0:
                print(f"No configuration file has been provided - using default parameter values and such provided via commandline arguments.")

