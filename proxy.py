import datetime
import time
import socket
import sys
import _thread
import pickle  # library for store cache object


class Proxy:

    def __init__(self, Port):
        self.Ip = ''  # Localhost
        self.Port = int(Port)  # Set Port Number
        self.BACKLOG = 50  # A maximum of 50 connections will wait in the back
        self.MAX_DATA_RECV = 4096
        self.cacheObj = {}

    def write_log(self, msg):
        """
        Function to write log
        """
        with open("logs.txt", "a+") as file:
            file.write(msg)
            file.write("\n")

    def saveCache(self):
        """
        store cache to cache.pkl
        """
        print("Cache saved")
        with open('cache.pkl', 'wb') as obj:
            pickle.dump(self.cacheObj, obj, pickle.HIGHEST_PROTOCOL)

    def readCache(self):
        """
        cache reading function
        """
        with open('cache.pkl', 'rb') as obj:
            self.cacheObj = pickle.load(obj)

    # Helper Function to get Time Stamp
    def getTimeStampp(self):
        return "[" + str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')) + "] "

    def Start_Server(self):
        self.write_log(self.getTimeStampp() + "   \n\nStarting Server\n\n")
        try:
            # socket creation
            Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("[*] Initializing socket. Done.")
            self.write_log(self.getTimeStampp() + "Initializing socket. Done.")

            # bind IP and port with socket
            Socket.bind((self.Ip, self.Port))
            print("[*] Socket bind successfully...")
            self.write_log(self.getTimeStampp() + "Initializing Sockets [ready] Binding Sockets [ready] Listening...")

            # queue up as many as 50 connect requests before refusing more
            Socket.listen(self.BACKLOG)
            print("[*] Server started successfully at [{}]".format(self.Port))
            self.write_log(self.getTimeStampp() + "Server started successfully at [{}]".format(self.Port))

            while True:
                connection, connection_addr = Socket.accept()
                self.write_log(self.getTimeStampp() + "Request received from: " + connection_addr[0] +
                               " at port: " + str(connection_addr[1]))

                # initializing threading for every connection
                _thread.start_new_thread(self.read_request, (connection, connection_addr))

        except KeyboardInterrupt:
            if Socket:
                Socket.close()
            print("[?] KeyboardInterrupt (CTRL+C) Force-Quit!")
            self.write_log(self.getTimeStampp() + "KeyboardInterrupt (CTRL+C) Force-Quit!")
            sys.exit(1)
        except socket.error as Message:
            if Socket:
                Socket.close()
            print("[-] Could Not Open Socket:", Message)
            self.write_log(self.getTimeStampp() + f"Could Not Open Socket:{Message}")
            sys.exit(1)
        except Exception as Error:
            print("[-] Could Not Start Program:", Error)
            self.write_log(self.getTimeStampp() + f"Could Not Start Program:{Error}")
            sys.exit(1)

    def read_request(self, connection, connection_addr):

        try:
            Request = connection.recv(self.MAX_DATA_RECV)
            # check if request is empty
            if (str(Request).split('\n')[0] == "b''"):
                print("Empty request")
                connection.close()
            AllData = Request.decode().split()
            print("[+] Request Method: " + str(AllData[0]) + " Url: " + str(AllData[1]) + " " + str(AllData[2]))
            self.write_log(
                self.getTimeStampp() + f"Request Method: {str(AllData[0])} Url: {str(AllData[1])} {str(AllData[2])}")

            # request parsing
            Data = AllData[1]
            Storeindex = Data.find("://")

            Url = Data[Storeindex + 3:]

            Storeindex = Url.find("/")

            Url = Url[:Storeindex]

            Storeindex = Url.find(":")

            Port = 80
            if Storeindex != -1:
                Port = int(Url[Storeindex + 1:])

            if Url.find(":") != -1:
                Storeindex = Url.find(":")
                Url = Url[:Storeindex]

            adrr = AllData[1].split(':')
            if AllData[0] == "CONNECT":
                print(self.getTimeStampp() + "CONNECT Request")
                self.write_log(self.getTimeStampp() + "HTTPS Connection request")
                self.https_Proxy(connection, adrr[0])

            if Request in self.cacheObj:

                print("Cache hit, fetching from cache")
                self.write_log(self.getTimeStampp() + "Cache hit, fetching from cache")
                # count cache access timing
                start = time.time()
                # fetch data from cache
                Data = self.cacheObj[Request]
                while True:
                    if len(Data) > 0:
                        # send data to browser
                        connection.send(Data)
                        print("[+] Response Sent to Browser! " + str(AllData[1]))
                        self.write_log(self.getTimeStampp() + f"Response Sent to Browser! {str(AllData[1])}")
                        connection.close()
                    else:
                        break
                    break
                # ending timer
                end = time.time()
                timeElapsed = (end - start) * 1000
                print("[+] Request for " + str(AllData[1]) + " handled from cache in " + str(timeElapsed) + "ms")
                self.write_log(self.getTimeStampp() + "Request for " + str(AllData[1]) +
                               " handled from cache in " + str(timeElapsed) + "ms")
                connection.close()
            else:
                start = time.time()
                PSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                PSocket.connect((Url, Port))
                # send request to server
                PSocket.send(Request)
                while 1:
                    # receive data from server
                    data = PSocket.recv(self.MAX_DATA_RECV)
                    # save request in cache
                    self.cacheObj[Request] = data
                    self.saveCache()
                    self.readCache()
                    if len(data) > 0:
                        # send data to browser
                        connection.send(data)
                        print("[+] Response Sent to Browser! " + str(AllData[1]))
                        self.write_log(self.getTimeStampp() + f"Response Sent to Browser! {str(AllData[1])}")
                        connection.close()
                    else:
                        break
                    break
                end = time.time()
                timeElapsed = (end - start) * 1000
                print("[+] Request completed in " + str(timeElapsed) + "ms")
                self.write_log(self.getTimeStampp() + "Request completed in " + str(timeElapsed) + "ms")
                PSocket.close()
                connection.close()

        except socket.error as Message:
            self.write_log(self.getTimeStampp() + f"Could Not Open Socket:{Message}")
            sys.exit(1)

        except Exception as Error:
            self.write_log(self.getTimeStampp() + f"Could Not Start Program:{Error}")
            sys.exit(1)

    def https_Proxy(self, connection, url):
        PSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        PSocket.connect((url, 443))
        reply = "HTTP/1.0 200 Connection established\r\n"
        reply += "Proxy-agent: Proxy\r\n"
        reply += "\r\n"
        connection.sendall(reply.encode())

        connection.setblocking(0)
        PSocket.setblocking(0)
        print(self.getTimeStampp() + "HTTPS Connection Established")

        while True:
            try:
                request = connection.recv(self.MAX_DATA_RECV)
                PSocket.sendall(request)
            except socket.error:
                pass

            try:
                reply = PSocket.recv(self.MAX_DATA_RECV)
                connection.sendall(reply)
            except socket.error as e:
                pass


if __name__ == "__main__":
    Proxy = Proxy(sys.argv[1])
    Proxy.Start_Server()
