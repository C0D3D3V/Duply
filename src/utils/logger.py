#!/usr/bin/env python2
# -*- coding: utf-8 -*-

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"

# BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE


def log(logString, level=0):
    if level == 0:    # Info white
        print(COLOR_SEQ % 37 + logString + RESET_SEQ)
    elif level == 1:  # Debug cyan
        print(COLOR_SEQ % 36 + logString + RESET_SEQ)
    elif level == 2:  # Warning yellow
        print(COLOR_SEQ % 33 + logString + RESET_SEQ)
    elif level == 3:  # Error red
        print(COLOR_SEQ % 31 + logString + RESET_SEQ)
    elif level == 4:  # Critical magenta
        print(COLOR_SEQ % 35 + logString + RESET_SEQ)
    elif level == 5:  # Success green
        print(COLOR_SEQ % 32 + logString + RESET_SEQ)
