#!/bin/sh

# Examples to run simulations
# ===========================

# Compile mechanisms for NEURON and CoreNEURON (pre-cleanup is necessary if multiple NEURON installations are used interchangeably)
# rm -R -f x86_64/* 
# nrnivmodl -coreneuron mod

# Run NEURON test
#python3 run_ring_network.py -num_threads 3 -duration 30 -num_rand_syns 512

# Run NEURON test with pre-compiled binary (may provide performance boost)
#./x86_64/special -python run_ring_network.py -duration 30 -num_rand_syns 512

# Run CoreNEURON test
#python3 run_ring_network.py -coreneuron -num_threads 3 -duration 30 -num_rand_syns 512

# Run CoreNEURON test with GPU with pre-compiled binary
#./x86_64/special -python  run_ring_network.py -coreneuron -num_threads 3 -gpu -duration 30 -num_rand_syns 512

# Run CoreNEURON with MPI with pre-compiled binary
mpiexec -n 2 ./x86_64/special -mpi -python run_ring_network.py -coreneuron -num_threads 3 -params_file 'simple-n=1024-stdp=on-depth=2.json'

# Run CoreNEURON with MPI and GPU with pre-compiled binary
mpiexec -n 2 ./x86_64/special -mpi -python run_ring_network.py -coreneuron -num_threads 3 -gpu -params_file 'simple-n=1024-stdp=on-depth=2.json'