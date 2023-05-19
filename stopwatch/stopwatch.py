import tkinter as tk
from datetime import datetime, timedelta
import pandas as pd

"""
run the script:
    python stopwatch.py

config file:
    base_pace: the initial pace of the clock
    frequency_of_change: change the pace of the clock every few seconds  
    add_increment: how much we want to change the pace, negative number (> 0 and < 1) means decrease the pace (slow down), positive number (< 0 and > -1) means increase the pace (speed up)
    stop_time: stop the clock after some seconds
    e.g., set base_pace = 1, frequency_of_change = 5, add_increment = 0.1, stop_time = 20,
          the clock will start from normal pace, and increase by 0.1 every 5 seconds until the "CHANGE" button is pressed or 20 seconds has passed. 
    Note that when decrease the pace (add_increment set to a negative number), there is a lower bound, the pace will stop decreasing when it will become negative.

output file:
    time_elapsed_at_keypress: the elapsed time (in seconds) when the "CHANGE" button is pressed
    pace_at_keypress: the pace of the clock when the "CHANGE" button is pressed
"""

class Stopwatch(tk.Frame):
    def __init__(self, window=None):
        super().__init__(window)
        self.window = window
        self.pack()
        
        self.is_running = False
        self.start_time = None
        self.time_elapsed = timedelta()
        self.time_scale = 1.0  # Scaling factor for the pace of time

        self.scale_timer = None # timer to change the scale

        self.stop_timer = None # timer to stop the clock

        self.last_elapsed_time = timedelta() 
        self.last_start_time = None

        

        self.config_df = self.read_config("config.csv")
        self.output_df = self.config_df.copy()

        self.output_df.insert(4, "time_elapsed_at_keypress", "NAN")
        self.output_df.insert(5, "pace_at_keypress", "NAN")

        self.trial_num = 0
        self.base_pace = 0
        self.frequency_of_change = 0
        self.add_increment = 0

        self.create_widgets()
        self.update_trial(0)
        

    def read_config(self, file_name):
        df = pd.read_csv (file_name)
        df.reset_index()
        df = df.set_index("trial_num")
        return df

    def write_output(self): 
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        file_name = 'OUTPUT_' + current_time + '.csv'
        self.output_df.to_csv(file_name)

    def create_widgets(self):
        self.time_label = tk.Label(self, text='00:00:00:00', font=("Arial", 85), background= "black", bd = 10, width= 11, foreground= "cyan", anchor=tk.CENTER)
        self.time_label.grid(row = 0, column = 0, columnspan = 9)
        self.start_button = tk.Button(self, text='Start', height=4, width=15, font=('Arial', 20), command=self.start)
        self.start_button.grid(row = 1, column = 0, columnspan = 3)
        self.pause_button = tk.Button(self, text='CHANGE', state=tk.DISABLED, height=4, width=30, font=('Arial', 20), background="red", foreground="red", command=self.change)
        self.pause_button.grid(row = 1, column = 3, columnspan = 6)
        
        self.trial_num_label = tk.Label(self, text='Trial' + str(self.trial_num), font=("Arial", 10), bd = 10, width= 11, anchor=tk.CENTER)
        self.trial_num_label.grid(row = 2, column = 0)
        self.done_button = tk.Button(self, text='DONE', height=2, width=7, font=('Arial', 10), fg="red", command=self.write_output)
        self.done_button.grid(row = 2, column = 5)
        self.prev_trial_button = tk.Button(self, text='< Prev', height=2, width=7, font=('Arial', 10), fg="gray", command=self.prev)
        self.prev_trial_button.grid(row = 2, column = 7)
        self.next_trial_button = tk.Button(self, text='Next >', height=2, width=7, font=('Arial', 10), fg="gray", command=self.next)
        self.next_trial_button.grid(row = 2, column = 8)
        self.window.title('Stopwatch')

    def update_trial(self, trial_num): 
        if trial_num < 0:
            trial_num = self.config_df.index[-1] - 1
        
        if trial_num > self.config_df.index[-1] - 1:
            trial_num = self.config_df.index[0] - 1

        self.trial_num = trial_num
        self.time_scale = self.config_df.iloc[trial_num]['base_pace']
        self.frequency_of_change = self.config_df.iloc[trial_num]['frequency_of_change']
        self.add_increment = self.config_df.iloc[trial_num]['add_increment']
        self.stop_time = self.config_df.iloc[trial_num]['stop_time']

        self.trial_num_label.config(text='Trial' + str(self.trial_num + 1))

    def next(self): 
        self.reset()
        self.update_trial(self.trial_num + 1)

    def prev(self): 
        self.reset()
        self.update_trial(self.trial_num - 1) 
        
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            
            self.start_time = datetime.now()
            self.last_start_time = self.start_time
            
            self.update_time()
            
            self.schedule_scale_change()

            self.stop_after()

    def change(self):
        self.stop()
        self.output_df.at[self.trial_num+1, "time_elapsed_at_keypress"] = round((datetime.now() - self.start_time).microseconds/100000, 3)
        self.output_df.at[self.trial_num+1, "pace_at_keypress"] = self.time_scale
            
    def stop(self):
        if self.is_running:
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.time_elapsed += self.last_elapsed_time + (datetime.now() - self.last_start_time) * self.time_scale
            self.cancel_scale_change()

    def reset(self):
        self.stop()
        self.time_elapsed = timedelta()
        self.last_elapsed_time = timedelta()
        self.time_label.config(text="00:00:00.00")
        self.time_scale = self.config_df.iloc[self.trial_num]['base_pace'] # reset the pace so that we can restart the trial correctly
        self.window.after_cancel(self.stop_timer) # cancel the stop timer

        
    def update_time(self):
        if self.is_running:
            current_time = datetime.now()
            elapsed_time = self.last_elapsed_time + (current_time - self.last_start_time) * self.time_scale
            elapsed_time_str = self.format_time(elapsed_time)
            self.time_label.config(text=elapsed_time_str)
            self.window.after(1, self.update_time)

    def stop_after(self): # reset the clock after X seconds specified by "stop_time"
        self.stop_timer = self.window.after((int(self.stop_time) * 1000), self.reset)

    def schedule_scale_change(self): # change the pace after every X seconds specified by "frequency_of_change"
        self.scale_timer = self.window.after(int(self.frequency_of_change*1000), self.change_time_scale)

    def cancel_scale_change(self):
        if self.scale_timer is not None:
            self.window.after_cancel(self.scale_timer)
            self.scale_timer = None

    def change_time_scale(self):
        self.last_elapsed_time += (datetime.now() - self.last_start_time)*self.time_scale
        self.last_start_time = datetime.now()

        if (self.time_scale + self.add_increment) > 0.0001: # aovid the scale decreases to negative number
            self.time_scale += self.add_increment 
             
        # print(f"Scale changed. Current scale: {self.time_scale}")
 
        self.schedule_scale_change()

        
    @staticmethod
    def format_time(delta_time):
        hours = delta_time.seconds // 3600
        minutes = (delta_time.seconds // 60) % 60
        seconds = delta_time.seconds % 60
        milliseconds = delta_time.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds//10:02d}"

root = tk.Tk()
stopwatch = Stopwatch(window=root)
stopwatch.mainloop()
