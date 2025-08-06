"""
Script to run busyring example
"""

import argparse
import numpy as np
import neuron
from neuron import h
import parameters
from metering import RuntimeMetering
from ring_network import RingNetwork

# Parse commandline arguments
parser = argparse.ArgumentParser()
# Model and simulation parameters
parser.add_argument("-num_rings", help="number of rings", type=int, default=256)
parser.add_argument("-num_ring_cells", help="number of cells per ring", type=int, default=4)
parser.add_argument("-num_rand_syns", help="number of random synapses of weight 0 per cell", type=int, default=10)
parser.add_argument("-p_branch", nargs=2, help="range of branching probabilities at each level",  type=float, default=[1.0, 0.5])
parser.add_argument("-num_comparts", nargs=2, help="range of compartments per branch (default [1,1])", type=int, default=[1, 1])
parser.add_argument("-params_file", help="JSON file containing parameter configuration", type=str, default="")
parser.add_argument("-duration", metavar='float', help="duration of the simulation in ms", type=float, default=200.0)
parser.add_argument("-num_threads", help="number of threads to use", type=int, default=1)
# CoreNEURON parameters (cf. https://github.com/neuronsimulator/ringtest/blob/master/ringtest.py)
parser.add_argument("-coreneuron", action='store_true', help="use CoreNEURON", default=False)
parser.add_argument("-file_mode", action='store_true', help="run CoreNEURON with file mode (instead of in-memory transfer)", default=False)
parser.add_argument("-gpu", action='store_true', help="run CoreNEURON on GPU", default=False)
parser.add_argument('-permutation', help="run CoreNEURON with permutation for cell topology", type=int, default=0)
args, _ = parser.parse_known_args()

# Initialize runtime metering
runtime_meter = RuntimeMetering()

# Set up parallelization
pc = h.ParallelContext() # create context
pc.nthread(args.num_threads) # set number of threads
#pc.set_maxstep(100*loaded_params.dt) # maximum timestep in ms (not used because CoreNEURON can only use fixed timestep methods)

# Load parameters (commandline arguments and default values will be used unless a configuration file is provided)
loaded_params = parameters.model_parameters(args.params_file, args.duration, args.num_rings, args.num_ring_cells,
                                            args.p_branch, args.num_comparts, args.num_rand_syns, pc)

# Output of key parameters
if pc.id() == 0:
    print(f"Using NEURON version {neuron.__version__}\n"
          f"Configuration" + (f" (loaded from {args.params_file}):\n" if args.params_file else ":\n") +
            f"  Total number of cells: {loaded_params.num_cells}\n"
            f"  Cells per ring: {loaded_params.ring_size}\n"
            f"  Branching probabilities: {loaded_params.cell.branch_probs}\n"
            f"  Compartments per cell:  {loaded_params.cell.compartments}\n"
            f"  Random synapses per cell: {loaded_params.cell.synapses}")

# Create network of rings of cells and set spike recorder
ring_network = RingNetwork(loaded_params, pc)
spike_times = h.Vector()
spike_gids = h.Vector()
pc.spike_record(-1, spike_times, spike_gids)

# Settings for numerical integration
h.load_file('stdgui.hoc') # needed for cvode settings
h.dt = loaded_params.dt # fixed timestep in ms
h.cvode.cache_efficient(1) # CoreNEURON requires this setting of data representation
h.stdinit()

# CoreNEURON settings
if args.coreneuron:
    from neuron import coreneuron
    coreneuron.enable = True
    coreneuron.file_mode = args.file_mode
    coreneuron.gpu = args.gpu
    if not coreneuron.gpu:
        coreneuron.cell_permute = args.permutation
    else:
        coreneuron.cell_permute = 2 # see https://github.com/neuronsimulator/ringtest/blob/master/ringtest.py
pc.barrier()
runtime_meter.add_checkpoint("model-init")

# Run the simulation
pc.psolve(loaded_params.duration)
pc.barrier()
runtime_meter.add_checkpoint("model-run")

# Write the spike data to file
spike_data = np.column_stack([np.array(spike_times), np.array(spike_gids)])
sorted_indices = np.lexsort((spike_data[:, 1], spike_data[:, 0]))
sorted_spike_data = spike_data[sorted_indices]
np.savetxt('spikes.dat', 
           sorted_spike_data,
           fmt="%.3f %d") # integer formatting for neuron number

# Print runtime summary and exit the NEURON environment
if pc.id() == 0:
    print("------------------\n"
          "Metering summary:\n"
          "------------------")
    runtime_meter.print_summary()
h.quit()
