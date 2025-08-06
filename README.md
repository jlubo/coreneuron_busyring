### Execution

You may use `run_coreneuron_busyring_benchmarks.py` to run a variety of simulation paradigms in different HPC settings.

Use `run.sh` for single trials.

### Setup

The code provided here has been tested with NEURON v8.2.7. 

You may install the framework as follows (CPU only):

```
git clone https://github.com/neuronsimulator/nrn
cd nrn
git checkout 8.2.7
mkdir build
cd build
cmake .. \
	-DNRN_ENABLE_CORENEURON=ON \
	-DNRN_ENABLE_INTERVIEWS=OFF \
	-DNRN_ENABLE_RX3D=OFF \
	-DCMAKE_INSTALL_PREFIX=$HOME/nrn_installation \
	-DCMAKE_C_COMPILER=gcc \
	-DCMAKE_CXX_COMPILER=g++
make -j
make install
```

To use an NVIDIA GPU (e.g., with compute capability 7.5), you can adapt the `cmake` call as follows:
```
cmake .. \
	-DNRN_ENABLE_CORENEURON=ON \
	-DCORENRN_ENABLE_GPU=ON \
	-DNRN_ENABLE_INTERVIEWS=OFF \
	-DNRN_ENABLE_RX3D=OFF \
	-DCMAKE_INSTALL_PREFIX=$HOME/nrn_gpu_installation \
	-DCMAKE_C_COMPILER=nvc \
	-DCMAKE_CXX_COMPILER=nvc++ \
	-DCMAKE_CUDA_COMPILER=nvcc \
	-DCMAKE_CUDA_ARCHITECTURES=75
```