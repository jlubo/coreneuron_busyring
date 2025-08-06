import os
import itertools
import pandas as pd
import numpy as np

def extract_benchmark_data(input_file):
    '''
    Extracts the essential information (parameters, specific runtimes)
    from log file.

    Parameters
    ----------
    input_file : str
      Name of the log file.

    Returns
    -------
    extract_results : dict
      With the following entries:
        runtime_model_init : float
          Runtime of model initialization
        runtime_model_run : float
          Runtime of model run
        runtime_total : float
          Total runtime
        memory_model_init : float
          Memory of model initialization
        memory_model_run : float
          Memory of model run
        memory_total : float
          Total memory
        num_threads : int
          Number of threads
        num_ranks : int
          Number of ranks
        used_stdp : bool
          Whether or not STDP was enabled
        num_cells : int
          Number of cells used
        num_branches : int
          Number of branches used
        num_compartments : int
          Number of compartments used
    '''

    # Dictionary of variables for the implementation, with their related keyword
    # to look for at the start of a line and the index of the column to extract
    extract_parameters = {"runtime_model_init" : ("model-init", 0),
                          "runtime_model_run" : ("model-run", 0),
                          "runtime_total" : ("meter-total", 0),
                          "memory_nrn_setup" : (" Memory (MBs) :          After nrn_setup", 2),
                          "memory_nrn_finitialize" : ("Memory (MBs) :     After nrn_finitialize", 2),
                          "model_size" : ("Model size", 1),
                          "num_ranks" : ("num_mpi=", 0),
                          "num_cells" : ("Cell stats:", 0),
                          "num_segments" : ("Cell stats:", 2),
                          "num_compartments" : ("Cell stats:", 4)}

    # Dictionary of variables for the implementation, with their assigned results
    extract_results = {}

    with open(input_file, 'r') as file:
        for line in file:
            # After indicator keywords, extract the rest of the line 
            for var_name, indicator in extract_parameters.items():
                if indicator[0] in line:
                    # Find the end of the keyword and extract the rest of the line
                    idx = line.find(indicator[0])
                    extracted = line[idx+len(indicator[0]):].strip()
                    # Assign indicated value from extracted line to corresponding variable
                    if not np.isnan(indicator[1]):
                        extract_results[var_name] = extracted.split()[indicator[1]].replace(",", "")
                    else:
                        extract_results[var_name] = extracted

    return extract_results

# Set environment variables (NOTE make sure that the installation directory is correct!)
home_dir = os.path.expanduser("~")
new_path = f"{home_dir}/nrn_installation/bin"
current_paths = os.environ.get("PATH", "")
if new_path not in current_paths:
    os.environ["PATH"] = current_paths + ":" + new_path
new_python_path = f"{home_dir}/nrn_installation/lib/python"
current_python_paths = os.environ.get("PYTHONPATH", "")
if new_python_path not in current_python_paths:
    os.environ["PYTHONPATH"] = current_python_paths + ":" + new_python_path
#print("PATH =", os.environ.get("PATH"))
#print("PYTHONPATH =", os.environ.get("PYTHONPATH"))

# Compile mod files
os.system("rm -R -f x86_64/*")
os.system("nrnivmodl -coreneuron")

# Run different simulations in raster of thread and rank numbers
for trial in range(10):
  for paradigm in ["simple-n=1024-stdp=off-depth=0",
                   "simple-n=1024-stdp=off-depth=2",
                   "simple-n=1024-stdp=off-depth=10",
                   "simple-n=16384-stdp=off-depth=0",
                   "simple-n=16384-stdp=off-depth=2",
                   "simple-n=16384-stdp=off-depth=10",
                   "simple-n=32768-stdp=off-depth=0",
                   "simple-n=32768-stdp=off-depth=2",
                   "simple-n=32768-stdp=off-depth=10"]:
      for num_threads, num_ranks, gpu in itertools.product([4, 8, 16, 32, 64],
                                                           [4, 8, 16, 32, 64],
                                                           [False]):
                                                           #[False, True]): # for GPU use, make sure that CoreNEURON was built accordingly
          # Run with specific number of MPI ranks and threads without GPU
          if not gpu:
            log_file = f"busyring_benchmark_output_{paradigm}_{num_threads}_{num_ranks}.log"
            os.system(f"mpiexec -n {num_ranks} ./x86_64/special -mpi -python run_ring_network.py -coreneuron -num_threads {num_threads} -params_file '{paradigm}.json' " +
                      f"> {log_file}")
          # Run with specific number of MPI ranks and threads with GPU
          else:
            log_file = f"busyring_benchmark_output_{paradigm}_{num_threads}_{num_ranks}_gpu.log"
            os.system(f"mpiexec -n {num_ranks} ./x86_64/special -mpi -python run_ring_network.py -coreneuron -num_threads {num_threads} -gpu -params_file '{paradigm}.json' " +
                      f"> {log_file}")

          # Scrape information from file and print some
          extracted_results = extract_benchmark_data(log_file)
          print(f"Paradigm: {paradigm}\n" +
                f"  with num_threads = {num_threads}, num_ranks = {num_ranks}\n" +
                f"Trial: {trial}\n" +
                f"  runtime_model_init  =  {extracted_results['runtime_model_init']}\n" +
                f"  runtime_model_run   =  {extracted_results['runtime_model_run']}\n" +
                f"  runtime_total       =  {extracted_results['runtime_total']}\n" +
                f"  num_cells           =  {extracted_results['num_cells']}\n" +
                f"  num_compartments    =  {extracted_results['num_compartments']}\n")
          #print(extracted_results)

          # Store everything to CSV file
          out_file = "busyring_benchmark_data.csv"
          output_results = {"paradigm" : paradigm, "num_threads_set" : num_threads, "num_ranks_set" : num_ranks}
          output_results.update(extracted_results)
          if not os.path.exists(out_file):
              pd.DataFrame([output_results]).to_csv(out_file, mode="w", index=False, header=True, sep="\t")
          else:
              pd.DataFrame([output_results]).to_csv(out_file, mode="a", index=False, header=False, sep="\t")