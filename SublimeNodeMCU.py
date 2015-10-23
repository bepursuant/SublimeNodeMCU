import os, serial, sys

verbose = True

#Serial Configuration
port = 'COM4'
baud = 9600 #usually 9600 or 115200

reset = True #automtically reset the NodeMCU before writing
execute = False #automatically execute uploaded file after upload



#########################################################
#define a lua script to receive the data we will be sending
receiveLua = \
r"""file.remove('%s')
    file.open('%s', 'w')
    uart.on('data', 255,
      function (d)
        c = tonumber(d:sub(1, 4))
        d = d:sub(5, 4+c)
        file.write(d)
        if c ~= 251 then
            file.close()
        end
        uart.write(0, 'Y')
      end, 0)"""
receiveLua = ' '.join([line.strip() for line in receiveLua.split('\n')]).replace(', ', ',')

prompt = b'\n> '
def waitForPrompt():
    data = b''
    while data[-3:] != prompt:
        d = ser.read()
        #writeV(d.decode())

        if d == b'':
            writeV('.')

        data += d

    return data

def waitForAck():
    d = b''
    while True:
        d = ser.read(1)
        #writeLnV("ACK?" + d.decode())

        if(d == b'Y'):
            break
    return

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

writeLn('Uploading to NodeMCU...')

writeV('Opening serial port ' + port + ':' + str(baud) + '...')
ser = serial.Serial(port, baud, timeout=1)
writeLnV('ok!')

# Opening the serial port changes DTR and RTS to 0.

if reset:
    writeV('Reset')
    ser.setDTR(False) # Setting them to False sets their logic level back to 1.
    ser.setRTS(False)
    waitForPrompt() # Wait until Lua has booted after the reset caused by RTS.
                    # This waits forever in case RTS is not connected to RESET.
    writeLnV('ok!')
else:
    writeLn('If nothing happens, try setting reset = True in uploader.py')

file_path = sys.argv[1]
file_name = os.path.basename(file_path)
save_command = receiveLua % (file_name, file_name) + '\r'

assert len(save_command) < 256, 'Save_command too long: %s bytes' % len(save_command)

#let's send the save command to the nodeMCU to get it ready to receive the data
writeV('Sending Save Command to NodeMCU...')
ser.write(save_command.encode())
response = waitForPrompt()
#assert response == save_command + prompt, response
writeLnV('ok!')

#read the file into buffer
writeV('Reading ' + file_path + ' into memory...')
f = open( file_path, 'rb' ); content = f.read(); f.close()
writeLnV('ok!')

pos = 0
chunk_size = 251 # 255 (maximum) - 4 (hex_size)

while pos <= len(content):
    data = content[pos : pos + chunk_size]
    pos += chunk_size
    data_size = len(data)

    if data_size != chunk_size:
        data += b' ' * (chunk_size - data_size) # Fill up to get a full chunk to send.

    hex_size = '0x' + hex(data_size)[2:].zfill(2) # Tell the receiver the real size.

    #writeLnV("Writing: " + str(hex_size.encode()) + str(data))
    ser.write(hex_size.encode() + data)

    waitForAck()

    percent = int(100 * pos / ((len(content) + chunk_size) / chunk_size * chunk_size))

    write('%3s %%' % percent)

#we're done!
writeLn('')

if execute and file_name.endswith('.lua'):
    ser.write('dofile("%s")\r' % file_name)
    waitForPrompt(do_log=True)

ser.close()
