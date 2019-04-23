# MiniFRC Driver Station

Things you can type into the config file (exclude "<>"):
COM<#> 		// Defines the COM port number the program will try to connect to the robot with
COMtest		// The program will not attempt to connect with the robot
joysticktest	// The program ill automaticaly find all joystick inputs and activate them
BAUD<#>		// Changes the Baud rate from the default of 9600

axis,<Name>,j,<Joystick Number>,<Axis Number>		// Activates an joystick controlled axis, notice the j tag
axis,<Name>,k,<Forward Key>,<Backward Key>		// Activates a keyboard controlled axis, notice the k tag
button,<Name>,j,<Joystick Number>,<Button Number>	// Activates a joystick controlled button, notice the j tag
button,<Name>,k,<Key>					// Activates a keyboard controlled button, notice the k tag
hat,<Name>,<Joystick Number>,<Hat Number>		// Activates a hat, hats are always joystick controlled and don't need a j tag
