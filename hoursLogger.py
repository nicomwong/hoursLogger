import sys
import json
from enum import Enum
import subprocess

# Get current executable path
execPath = subprocess.check_output("pwd").decode()[:-1]

logFilePath = execPath + "/log.txt"
logHistoryPath = execPath + "/log_history.txt"
stateFilePath = execPath + "/state.txt"

# Define enum class for log state
# Possible States are:
#	Idle: Waiting for a log to start
#	Logging: Started logging
class LogState(Enum):
	loggingState = "Logging"
	idleState = "Idle"

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
	print("Usage: python3 hoursLogger.py 'start description'|end|clear|state|total")

# Returns a string of n spaces
def nSpaces(n):
	return ' '*n

# Runs the "help" command
# Only for the interactive mode
def runHelpCommand():
	
	print("	Valid commands are:\n\
			help:\tOutputs this list of commands\n\
			start description:\tStarts logging if state is Idle\n\
						'description' is a maximum of 40 characters\n\
			hours:\tDisplays how many hours have passed since the log was started\n\
			end:\tEnds logging if state is Logging\n\
			clear:\tClears log.txt and appends it to log_history.txt\n\
			state:\tDisplays current state\n\
			total:\tDisplays total hours in current log\n\
			show:\tShows current log\n\
			quit:\tQuits this program")

# Runs the "clear" command
def runClearCommand():

	# Open log file
	with open(logFilePath, 'r+') as logFile:
		
		# Copy log file to history file
		with open(logHistoryPath, 'a') as historyFile:

			historyFile.write("----Logged hours cleared on" + nSpaces(4) + getDate() + '----\n')
			historyFile.write( logFile.read() )
			historyFile.write('\n')
		
		# Clear log file
		logFile.truncate(0)
		logFile.seek(0)

		# Put in headers
		logFile.write("Description" + nSpaces(29) + "Start Date" + nSpaces(22) + "End Date" + nSpaces(24) + "Hours\n")

		# Reset state
		with open(stateFilePath, 'w') as stateFile:
			
			json.dump(LogState.idleState.value, stateFile)
			stateFile.truncate()

	# Print clearing file
	print("Clearing log.txt (it can now be found in log_history.txt)")

# Runs the "state" command
def runStateCommand(state):
	
	# Display the current state
	print("Current state is:", state)

# Runs the "start" command
def runStartCommand(stateFile, description):
	
	# Trim off edge quotes if description had them
	if description[0] == '\"' and description[-1] == '\"':
		description = description[1:-1]

	# Get padded or clipped description to size 20
	descripColSize = 40	# column size of description
	trimmedDescription = description[:descripColSize - 4] + ' ' * max(descripColSize - 4 - len(description), 0)
	# This block is redudant since below checks for description size

	# Check if the description is too long
	if len(description) > descripColSize:
		print("Description is too long. Maximum size is " + str(descripColSize))
		return

	# Open logging file in append mode
	with open(logFilePath, 'a+') as logFile:

		# Insert description
		logFile.write(trimmedDescription + ' ' * 4)

		# Insert start date
		logFile.write( getDate() + nSpaces(4) )

		# Update state
		json.dump(LogState.loggingState.value, stateFile)
		stateFile.truncate()	# Cuts down to correct size

		# Print started logging
		print("Started logging:", trimmedDescription)

# Runs the "check" command
def runHoursCommand(stateFile):

	# Open logging file in append mode
	with open(logFilePath, 'a+') as logFile:

		# Calc. delta time in hours
		logFile.seek( logFile.tell() - 32)	# Go back to beginning of the start date
		startTime = logFile.readline()[11:19]	# Read the startTime
		endDate = getDate()
		endTime = endDate[11:19]	# Get the endTime
		deltaTime = timeDifference(startTime, endTime)

		# Print the number of hours passed
		print("{:.2f}".format(deltaTime), "hours since log started")

# Runs the "end" command
def runEndCommand(stateFile):
	
	# Open logging file in append mode
	with open(logFilePath, 'a+') as logFile:

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

		# Print ended logging and hours spent
		print("Spent " + "{:.2f}".format(deltaTime), "hours. Ending log...")

# Runs the "total" command
def runTotalCommand():
	
	# Open logging file in read mode
	with open(logFilePath, 'r') as logFile:
		
		# Get list of lines of log file
		logFile.seek(0)	# Reset to start of file
		lineList = logFile.readlines()

		# Add up the total hours
		totalHours = 0
		for line in lineList[1:]:	# Skip first line (headers)
			totalHours += float(line[104:109])
		
		# Print total hours
		print("Total hours logged since " + getDate()[:10] + ": {:.2f}".format(totalHours) + " hours")

# Runs the "show" command
def runShowCommand():
	
	print("Displaying log.txt...")

	# Displays the log file to stdout
	subprocess.run("cat log.txt", shell=True)

# Returns true iff the input command parameter list is valid
def isValidCommand(cmdParamList):
	
	cmd = cmdParamList[0]	# For readability
	
	if len(cmdParamList) == 1:

		if (cmd == "help" or \
			cmd == "hours" or \
			cmd == "end" or \
			cmd == "clear" or \
			cmd == "state" or \
			cmd == "total" or \
			cmd == "show" or \
			cmd == "quit"
			):
			return True
		
		else:
			return False

	elif len(cmdParamList) == 2:

		if cmd == "start" and cmdParamList[1] != "":
			return True

		else:
			return False

	else:
		return False

# Processes the command with interactive-relevant output
def processCommandInteractively(cmdParamList):
	
	# Valid commands are:
	#	help: Outputs this list of commands
	#	start description: Starts logging if state is Idle
	#	hours: Displays how many hours have passed since the log was started
	#	end: Ends logging if state is Logging
	#	clear: Clears log.txt and appends it to log_history.txt
	#	state: Displays current state
	#	total: Displays total hours in current log
	#	show: Shows current log
	#	quit: Quits this program

	# Check command validity
	if not(isValidCommand(cmdParamList) ):
		# Print invalid command
		print("Invalid command. Type help to see a list of commands.")
		return

	# Assign cmd for readability
	cmd = cmdParamList[0]

	# Check if help command
	if cmd == "help":
		runHelpCommand()
		return

	# Check if clearing
	if cmd == "clear":
		runClearCommand()
		return

	# Open state file in read/write mode
	with open(stateFilePath, 'r+') as stateFile:

		# Get current state
		state = json.load(stateFile)
		stateFile.seek(0)	# Reset file ptr

		
		# Check if quitting
		if cmd == "quit":
			print("Quitting...")

			if state == "Logging":
				runEndCommand(stateFile)
			
			sys.exit()

		# State command
		elif cmd == "state":
			# Run the state command
			runStateCommand(state)
			
		# Start command
		elif cmd == "start":

			description = cmdParamList[1]

			if state == "Idle":
				# Run the start command
				runStartCommand(stateFile, description)

			else:
				# Print invalid
				print("Cannot start logging. Current state is already Logging.")

		# Check command
		elif cmd == "hours":
			
			if state == "Logging":
				# Run the check command
				runHoursCommand(stateFile)

			else:
				# Print invalid
				print("No log started yet.")

		# End command
		elif cmd == "end":

			if state == "Logging":
				# Run the end command
				runEndCommand(stateFile)

			else:
				# Print invalid
				print("Cannot end logging. Current state is Idle.")

		# Total command
		elif cmd == "total":
			
			if state == "Idle":
				# Run the total command
				runTotalCommand()

			else:
				print("To check the total, no log can be in progress")

		# Check if show command
		elif cmd == "show":

			if state == "Idle":
				runShowCommand()
				return

			else:
				print("To show, no log can be in progress")

		else:
			# Print invalid command
			print("Invalid command. Type help to see a list of commands.")

# Starts this program interactively
def runInteractively():

	# Print initial boot message
	print("Started interactive mode. Type commands or type \"help\" to see a list of available commands.")
	
	inputCommand = input("> ")	# Query for the command
	cmdParamList = inputCommand.split(" ")	# Get a list of the space-separated cmd params.

	# If command is start, then make everything else the second argument
	if cmdParamList[0] == "start" and len(cmdParamList) >= 2:
		cmdParamList[1] = ' '.join(cmdParamList[1:])
		cmdParamList = cmdParamList[:2]

	processCommandInteractively(cmdParamList)	# Process the command

	# Run until quit command is input
	while True:

		inputCommand = input("> ")	# Query for the command
		cmdParamList = inputCommand.split(" ")	# Get a list of the space-separated cmd params.

		# If command is start, then make everything else the second argument
		if cmdParamList[0] == "start" and len(cmdParamList) >= 2:
			cmdParamList[1] = ' '.join(cmdParamList[1:])
			cmdParamList = cmdParamList[:2]

		processCommandInteractively(cmdParamList)	# Process the command

# Check if interactive mode (no arguments)
if len(sys.argv) == 1:
	runInteractively()
	sys.exit()

# Check arguments
if not(isValidCommand(sys.argv[1:]) ):
	printInvalidUsage()
	sys.exit()

# Check if clearing
if sys.argv[1] == "clear":
	runClearCommand()
	sys.exit()

# Open state file in read/write
stateFile = open(stateFilePath, 'r+')

# Get current state
state = json.load(stateFile)

stateFile.seek(0)	# Reset file ptr

# Valid actions are:
#	start: Starts logging if state is Idle
#	end: Ends logging if state is Logging
#	state: Displays current state
#	total: Displays total hours in current log

# If command is state, then print it and end here
if sys.argv[1] == "state":
	# Run the state command
	runStateCommand(state)
	
# Start command
elif sys.argv[1] == "start":

	if state == "Idle":
		# Run the start command
		runStartCommand(stateFile, sys.argv[2])

	else:
		# Print invalid
		print("Cannot start logging. Current state is already Logging")

# End command
elif sys.argv[1] == "end":

	if state == "Logging":
		# Run the end command
		runEndCommand(stateFile)

	else:
		# Print invalid
		print("Cannot end logging. Current state is Idle")

# Total command
elif sys.argv[1] == "total":
	# Run the total command
	runTotalCommand()

else:
	# Print invalid command
	printInvalidUsage()
	sys.exit()

# Close the state file
stateFile.close()
