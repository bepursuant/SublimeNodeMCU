import os, serial, sys

# These settings will control how the script interacts with your NodeMCU. The defaults
# are sensible, but you will likely need to adjust them for your specific computer.
# 
port = 'COM4'   #the COM port to which the NodeMCU is connected
baud = 115200     #usually 9600 or 115200

reset = True    #automtically reset the NodeMCU before writing
execute = True  #automatically execute uploaded file after upload

verbose = True  #write debugging information to the console

prompt = b'\n> '#this is the prompt we will wait for at times

ack = b'Y'      #this is the ack character from the receive script

######################################################################################################################

filepath = sys.argv[1]
filename = os.path.basename(filepath)

# This helper function will send to the NodeMCU a script that will be immediately
# run. This script waits for data on the uart, and writes it to the file. This
# is much faster than the ESPlorer method of sending the code line by line.
def sendReceiveScript(serial, filename='init.lua'):
    receiveLua = \
    r"""tmr.stop(0)
        file.remove('%s')
        file.open('%s', 'w')
        uart.on('data', 255,
          function (d)
            tmr.stop(0)
            c = tonumber(d:sub(1, 4))
            d = d:sub(5, 4+c)
            file.write(d)
            if c ~= 251 then
                file.close()
                uart.write(0, 'Y')
                return
            end
            uart.write(0, 'Y')
          end, 0)"""
    receiveLua = ' '.join([line.strip() for line in receiveLua.split('\n')]).replace(', ', ',')

    save_command = receiveLua % (filename, filename) + '\r'

    assert len(save_command) < 256, 'Save_command too long: %s bytes' % len(save_command)

    writeV('Sending receive script to NodeMCU...')
    serial.write(save_command.encode())
    response = waitFor(prompt)
    #assert response == save_command + prompt, response
    writeLnV('ok!')

# Because we are interacting with the NodeMCU through the console, we will at times
# need to wait for it to finish processing before we send our next command. This
# function can also passthrough the serial data between the console and COMs.
def waitFor(chars, passthrough=False):
    charslen = len(chars)

    data = b''          #to hold the serial data we receive

    #writeLnV('Waiting for: ' + str(chars) + ' len:' + str(-charslen))

    # While the last three bytes of the data variable are not equal to the chars
    # we are waiting for, we read a byte from the serial port and append it to
    # the data variable. This is also where we passthrough the serial data.
    while data[-charslen:] != chars:
        d = ser.read()

        if(passthrough):
            write(d.decode())

        #if d == b'':    #writing a dot to console every time we get a blank byte
        #    writeV('.')

        data += d

    return data

def resetNodeMCU():
    writeV('Reset...')
    ser.setDTR(False) # Setting them to False sets their logic level back to 1.
    ser.setRTS(False)
    waitFor(prompt) # Wait until Lua has booted after the reset caused by RTS.
                    # This waits forever in case RTS is not connected to RESET.
    writeLnV('ok!')

def write(towrite):
    sys.stdout.write(towrite)
    sys.stdout.flush()

def writeLn(towrite):
    write(towrite + '\n')

def writeV(towrite):
    if(verbose):
        write(towrite)

def writeLnV(towrite):
    if(verbose):
        writeLn(towrite);

# Here is where we actually begin our script! Here we will open our serial port, and begin
# interacting with the NodeMCU over it.
#
writeLn('[SublimeNodeMCU] Uploading...');

writeV('Opening serial port ' + port + ':' + str(baud) + '...')

try:
    ser = serial.Serial(port, baud, timeout=1)
except serial.SerialException as e:
    writeLnV('failed!')
    sys.exit()

writeLnV('ok!')

# Opening the serial port changes DTR and RTS to 0.
if reset:
    resetNodeMCU()
else:
    writeLn('If nothing happens, try setting reset = True in SublimeNodeMCU.py')


sendReceiveScript(ser, filename);   #send receive script to NodeMCU to get ready to receive data


#read the file into buffer
writeV('Reading ' + filepath + ' into memory...')
f = open( filepath, 'rb' ); content = f.read(); f.close()
writeLnV('ok!')

pos = 0
chunk_size = 251 # 255 (maximum) - 4 (hex_size)

writeV('Sending...')

while pos <= len(content):
    data = content[pos : pos + chunk_size]
    pos += chunk_size
    data_size = len(data)

    if data_size != chunk_size:
        data += b' ' * (chunk_size - data_size) # Fill up to get a full chunk to send.

    hex_size = '0x' + hex(data_size)[2:].zfill(2) # Tell the receiver the real size.

    #writeLnV("Writing: " + str(hex_size.encode()) + str(data))
    ser.write(hex_size.encode() + data)

    waitFor(ack)

    percent = int(100 * pos / ((len(content) + chunk_size) / chunk_size * chunk_size))

    write('%3s %%' % percent)

if percent != 100:  #literally just so it looks pretty
    write(' 100 %')

#we're done!
writeLn('')
writeLn('ok!')

if execute and filename.endswith('.lua'):
    if(reset):
        resetNodeMCU()

    writeV('Running ' + str(filename) + '... > ')
    run_command = 'dofile("%s")\r' % filename
    ser.write(run_command.encode())
    waitFor(chars=prompt, passthrough=True)

ser.close()
