import queue
import packet
from autobahn.twisted.websocket import WebSocketServerProtocol

class ServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        super().__init__()
        self._packet_queue: queue.Queue[tuple['ServerProtocol', packet.Packet]] = queue.Queue()
        self._state: callable = self.LOGIN
        self._name = None

    def PLAY(self, sender: 'ServerProtocol', p: packet.Packet):
        if p.action == packet.Action.Chat:  
            if sender == self:
                message         = p.payloads[0]
                message_sender  = self.name
                p = packet.ChatPacket(message,message_sender)
                self.broadcast(p,exclude_self=False)
            
        if p.action == packet.Action.Disconnect:
            if sender == self:
                self.send_client(p)

    def LOGIN(self, sender: 'ServerProtocol', p: packet.Packet):
        if p.action == packet.Action.Register:
            self.send_client(packet.DenyPacket('Registered'))

        if p.action == packet.Action.Login:
            self.name = p.payloads[0]
            self.send_client(packet.OkPacket())
            self._state = self.PLAY

            p = packet.ChatPacket(f'{self.name} Logged in')
            self.broadcast(p,exclude_self=False)

    def tick(self):
        if not self._packet_queue.empty():
            s, p = self._packet_queue.get()
            self._state(s, p)
    
    def broadcast(self, p: packet.Packet, exclude_self: bool = True):
        for client in self.factory.clients:
            if client == self and exclude_self:
                continue
            if client._state != client.PLAY:
                continue

            client.send_client(p)
        return

    def onPacket(self, sender: 'ServerProtocol', p: packet.Packet):
        self._packet_queue.put((sender, p))

    # Override
    def onConnect(self, request):
        print('Client connecting: ', request.peer)

    # Override
    def onOpen(self):
        print('Websocket connection open')
        self._state = self.LOGIN 

    # Override
    def onClose(self, wasClean, code, reason):
        if self._state == self.PLAY:
            p = packet.ChatPacket(f'{self.name} Disconnected')
            self.broadcast(p,exclude_self=True)

        self.factory.remove_protocol(self)
        print('Websocket connection closed ', 'unexpectedly' if not wasClean else 'cleanly', ' with code ', code,':', reason) 

    # Override
    def onMessage(self, payload, isBinary):
        try:
            decoded_payload = payload.decode('utf-8')

            p: packet.Packet = packet.from_json(decoded_payload)
            if p != None:
                self.onPacket(self, p)
        except Exception as e:
            print(f'Could not load message as packet: {e}. Message was: {payload.decode("utf8")}')

    def send_client(self, p: packet.Packet):
        b = bytes(p)
        try:
            self.sendMessage(b)
        except Exception as e:
            print(e)


