# Here you define the commands that will be added to your add-in.

from .addPartDialog import entry as addPartDialog

# Fusion calls start() and stop() on every module in this list.
commands = [
    addPartDialog
]


# Assumes you defined a "start" function in each of your modules.
# The start function will be run when the add-in is started.
def start():
    for command in commands:
        command.start()


# Assumes you defined a "stop" function in each of your modules.
# The stop function will be run when the add-in is stopped.
def stop():
    for command in commands:
        command.stop()