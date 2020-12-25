import sys
import json
from enum import Enum
import subprocess

# Returns current date
def getDate():
	return subprocess.check_output("date").decode()[:-1]

# Returns delta time in hours
# Inputs are in HH:MM:SS 24-hour format
# Output will assume delta time is less than 24 hours
def timeDifference(startTime, endTime):
	startHours = float(startTime[:2]) + float(startTime[3:5]) / 60
	endHours = float(endTime[:2]) + float(endTime[3:5]) / 60
	return (endHours - startHours) % 24.0	# Mod 24 so that if negative, it adds 24 hours
											# In the case that the log range includes 12 AM

# Print invalid usage
def printInvalidUsage():
	print("Usage: python3 hoursLogger.py 'start description'|stop|clear|state")

# Returns a string of n spaces
def nSpaces(n):
	return ' '*n

# Possible States are:
#	Idle: Waiting for a log to start
#	Logging: Started logging
class LogState(Enum):
	loggingState = "Logging"
	idleState = "Idle"

# Check arguments
if len(sys.argv) == 1:
	printInvalidUsage()
	sys.exit()

elif len(sys.argv) == 2:
	if not(	sys.argv[1] == "stop" or \
		sys.argv[1] == "clear" or \
		sys.argv[1] == "state"
		):

		printInvalidUsage()
		sys.exit()

elif len(sys.argv) == 3:
	if not(sys.argv[1] == "start"):
		printInvalidUsage()

else:
	printInvalidUsage()

# Check if clearing
if sys.argv[1] == "clear":

	# Open log file
	with open('log.txt', 'r+') as logFile:
		
		# Copy log file to history file
		with open('log_history.txt', 'a') as historyFile:

			historyFile.write("----Logged hours cleared on" + nSpaces(4) + getDate() + '----\n')
			historyFile.write( logFile.read() )
			historyFile.write('\n')
		
		# Clear log file
		logFile.truncate(0)
		logFile.seek(0)

		# Put in headers
		logFile.write("Description" + nSpaces(9) + "Start Date" + nSpaces(22) + "End Date" + nSpaces(24) + "Hours\n")

		# Reset state
		with open('state.txt', 'w') as stateFile:
			
			json.dump(LogState.idleState.value, stateFile)
			stateFile.truncate()

	# Exit program
	sys.exit()

# Init. state var
state = ""

# Open state file in read/write
stateFile = open('state.txt', 'r+')

# Get current state
state = json.load(stateFile)

stateFile.seek(0)	# Reset file ptr

# If command is state, then print it and stop here
if sys.argv[1] == "state":
	print("Current state is:", state)
	sys.exit()

# Valid actions are:
#	start: Starts logging if state is Idle
#	stop: Ends logging if state is Logging

# Open logging file in append mode
with open('log.txt', 'a+') as logFile:

	# Start
	if sys.argv[1] == "start":

		if state == "Idle":
			
			# Insert description (padded or clipped to size 20)
			descripColSize = 20	# column size of description
			description = sys.argv[2][:descripColSize - 4] + ' ' * max(descripColSize - 4 - len(sys.argv[2]), 0)
			logFile.write(description + ' ' * 4)

			# Insert start date
			logFile.write( getDate() + nSpaces(4) )

			# Update state
			json.dump(LogState.loggingState.value, stateFile)
			stateFile.truncate()	# Cuts down to correct size

		else:
			
			# Print invalid
			print("Cannot start logging. Current state is already Logging")
	
	elif sys.argv[1] == "stop":

		if state == "Logging":
			
			# Calc. delta time in hours
			logFile.seek( logFile.tell() - 32)	# Go back to beginning of the start date
			startTime = logFile.readline()[11:19]	# Read the startTime
			endDate = getDate()
			endTime = endDate[11:19]	# Get the endTime
			deltaTime = timeDifference(startTime, endTime)

			# Insert end date
			logFile.write( endDate + nSpaces(4) )

			# Insert hours difference
			logFile.write('{:.2f}'.format(deltaTime) + '\n')

			# Update state
			json.dump(LogState.idleState.value, stateFile)
			stateFile.truncate()	# Cuts down to correct size

		else:
			# Print invalid
			print("Cannot end logging. Current state is Idle")

	else:
		# Print invalid command
		print("Usage: python3 hoursLogger.py 'start description'|stop|clear")
		sys.exit()

# Close the state file
stateFile.close()