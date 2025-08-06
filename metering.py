import time

class RuntimeMetering:
    def __init__(self):
        self.start()

    def start(self):
        """
        Set the start of runtime metering
        """
        self.metering_checkpoints = {} # initialize dictionary of time metering checkpoints
        self.metering_start_time = time.time()
        self.metering_last_time = self.metering_start_time
        self.name_total = "meter-total"

    def add_checkpoint(self, name):
        """
        Add a checkpoint for runtime metering
        """
        if not name:
            raise ValueError(f"Metering checkpoint has to have a non-empty name.")
        elif name == self.name_total:
            raise ValueError(f"Metering checkpoint may not be named '{self.name_total}'.")
        elif name in self.metering_checkpoints:
            raise ValueError(f"Metering checkpoint '{name}' already exists.")
        current_time = time.time()
        self.metering_checkpoints[name] = current_time - self.metering_last_time
        self.metering_last_time = current_time

    
    def print_summary(self):
        """
        Prints a summary of the metering results
        """
        print (f"meter{' ' * (25 - len('meter'))}runtime(s)\n"
               f"{'-' * 40}")
        for name, time in self.metering_checkpoints.items():
            print(f"{name}{' ' * (25 - len(name))}{time}")
        print(f"{self.name_total}{' ' * (25 - len(self.name_total))}{self.metering_last_time - self.metering_start_time}")