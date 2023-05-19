import tkinter as tk
from datetime import datetime, timedelta
import time
import pandas as pd

"""
run the script:
    python timer.py

config file:
    base_pace: the initial pace of the timer
    countdown_time: the time (in seconds) from which the timer starts to count down
    add_increment: how much we want to change the pace, negative number (< 0 and > -1) means decrease the pace (slow down), positive number (> 0 and < 1) means increase the pace (speed up)

    e.g., set base_pace = 1, countdown_time = 5, add_increment = 0.1
          The timer will start from normal pace, and increase by 0.1 every time we restart the timer until the "CHANGE" button is pressed 
    Note that when decrease the pace (add_increment set to a negative number), there is a lower bound, the pace will stop decreasing when it will become negative.

output file:
    pace_at_keypress: the pace of the clock when the "CHANGE" button is pressed
    timer_count: how many times the timer was started before the CHANGE is noticed (including the base pace one)
    time_elapsed: the actual time elapsed for the timer when the CHANGE is noticed
"""

class Timer(tk.Frame):
    def __init__(self, window=None):
        super().__init__(window)
        self.window = window
        self.pack()

        self.time_scale = 1.0  # Scaling factor for the pace of time

        self.seconds = 0
        self.minutes = 0
        self.hours = 0

        self.config_df = self.read_config("config.csv")
        self.output_df = self.config_df.copy()

        self.output_df.insert(3, "pace_at_keypress", "NAN")
        self.output_df.insert(4, "timer_count", "NAN")
        self.output_df.insert(5, "time_elapsed", "NAN")

        self.trial_num = 0
        self.base_pace = 1
        self.countdown_time = 0
        self.add_increment = 0

        self.counter = 0

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
        self.time_label = tk.Label(self, text=self.format_time(self.countdown_time), font=("Arial", 85), background= "black", bd = 10, width= 11, foreground= "cyan", anchor=tk.CENTER)
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
        self.window.title('Timer')

    def update_trial(self, trial_num): 
        if trial_num < 0:
            trial_num = self.config_df.index[-1] - 1
        
        if trial_num > self.config_df.index[-1] - 1:
            trial_num = self.config_df.index[0] - 1

        self.trial_num = trial_num
        self.time_scale = self.config_df.iloc[trial_num]['base_pace']
        self.countdown_time = int(self.config_df.iloc[trial_num]['countdown_time'])
        self.add_increment = self.config_df.iloc[trial_num]['add_increment']

        # self.hours = self.countdown_time // 3600
        # self.minutes = (self.countdown_time % 3600) // 60
        # self.seconds = self.countdown_time % 60
        
        self.trial_num_label.config(text='Trial' + str(self.trial_num + 1))
        self.time_label.config(text=self.format_time(self.countdown_time))
        self.window.update()

    def next(self): 
        self.reset()
        self.update_trial(self.trial_num + 1)

    def prev(self): 
        self.reset()
        self.update_trial(self.trial_num - 1) 
        
    def start(self):
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        total_seconds = self.countdown_time
        while total_seconds >= 0:

            self.time_label.config(text=self.format_time(total_seconds))
            self.window.update()
            self.time_scale = self.add_increment*self.counter + 1
            if self.time_scale <= 0:
                self.time_scale = self.add_increment*(self.counter - 1) + 1
            print(self.base_pace/self.time_scale, self.time_scale)
            time.sleep(self.base_pace/(self.time_scale))
          
            total_seconds -= 1
        self.start_button.config(state=tk.NORMAL)

        self.time_label.config(text=self.format_time(self.countdown_time))
        self.counter += 1


    def change(self):
        self.stop()
        self.output_df.at[self.trial_num+1, "pace_at_keypress"] = self.time_scale
        self.output_df.at[self.trial_num+1, "timer_count"] = ((self.time_scale - 1) / self.add_increment) + 1
        self.output_df.at[self.trial_num+1, "time_elapsed"] = self.countdown_time / self.time_scale
            
    def stop(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)


    def reset(self):
        self.stop()
        self.counter = 0

  
        
    @staticmethod
    def format_time(time):
        hours =time // 3600
        minutes = (time // 3600) % 60 
        seconds = time % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

root = tk.Tk()
timer = Timer(window=root)
timer.mainloop()
