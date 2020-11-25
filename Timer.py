#!/usr/bin/env python3

import time

class TimerError(Exception):
    """ custom exception for errors in use of Timer """

class Timer:
    """ Timer class following Real Python tutorial:
    https://realpython.com/python-timer/ """
    # class variable for timing multiple routines
    timers = dict()
    
    def __init__(
        self,
        name=None,
        text="elapsed time: {:.4f} seconds",
        logger=print,
        ):
        self._start_time = None
        self.name = name
        self.text = text
        self.logger = logger

        if name:
            # ensure named Timer is in class dictionary
            self.timers.setdefault(name, 0)


    def __str__(self):
        return self.name + ' ' + self.text.format(self.timers[self.name])


    def start(self):
        """ start a new timer """
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()


    def stop(self):
        """ stop the timer and report elapsed time """
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None

        if self.name:
            self.timers[self.name] += elapsed_time

        return elapsed_time
