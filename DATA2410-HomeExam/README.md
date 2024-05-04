---README for File Transfer Application---

Overview:

This README provides instructions on how to run application.py and execute tests to generate data. 

The application is designed to simulate a network communication environment that provides reliable data delivery (DRTP) on top of UDP between a client and server.

Requirements:

- Python 3.x
- Access to a commandline interface or terminal

Running application.py:

To run application.py, you need to specify whether you want to run the application in server mode or client mode. Additionally, you must provide the IP address and port number for the server.

    Running as a Server:

    1. Open a terminal
    2. Navigate to the directiory where the application.py is
    3. Run the following command
        python3 application.py -s -i (serverIP) -p (serverPort)
    
    Replace the (serverIP) with the IP address of the server and (serverPort) with the port number of the server.

    Running as a Client:

    1. Open a terminal
    2. Navigate to the directiory where the application.py is
    3. Run the following command
        python3 application.py -c -f (filename) -i (serverIP) -p (serverPort) -w (windowSize)
    
    Replace the (serverIP) with the IP address of the server, (serverPort) with the port number of the server, (filename) with the path of the file you want to send, and (windowSize) with the size of the sliding window.


Testing and Generating Data:

In order to test the application and generate data, you can run the client and server on different terminals or machines within the same network.

Example Test:

1. Start the server:
    python3 application.py -s -i 127.0.0.1 -p 8989    

2. Start the client:
    python3 application.py -c -f photo.jpg -i 127.0.0.1 -p 8989 -w 3

This setup will initiate a connection between the client and the server. The client will send a file to the server using specified sliding window protocol.