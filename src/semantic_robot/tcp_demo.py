"""Real TCP loopback semantic exchange; not measured wireless performance."""
import argparse,socket,struct,msgpack
from .codec import Packet,encode,decode
from .decision import decide
from .vision import ColorDetector
from .types import Observation
from .warehouse import make_scene
MAX_MESSAGE=8*1024*1024

def receive_exact(sock,n):
    buf=bytearray()
    while len(buf)<n:
        chunk=sock.recv(n-len(buf))
        if not chunk:raise EOFError('Connection closed')
        buf.extend(chunk)
    return bytes(buf)
def send_message(sock,data):
    if len(data)>MAX_MESSAGE:raise ValueError('Message too long')
    sock.sendall(struct.pack('!I',len(data))+data)
def receive_message(sock):
    size=struct.unpack('!I',receive_exact(sock,4))[0]
    if size>MAX_MESSAGE:raise ValueError('Message too long')
    return receive_exact(sock,size)
def serve(host='127.0.0.1',port=8765,max_clients=1):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        listener.bind((host,port));listener.listen(2)
        print(f'Edge TCP server at {host}:{port}',flush=True)
        for _ in range(max_clients):
            conn,_=listener.accept()
            with conn:
                method,frame,task,payload=msgpack.unpackb(receive_message(conn),raw=False)
                obs=decode(Packet(method,payload,frame,task,0),ColorDetector())
                result={'frame_id':obs.frame_id,'task':obs.task,'decision':decide(obs),'objects':len(obs.objects)}
                send_message(conn,msgpack.packb(result,use_bin_type=True))
def request(host='127.0.0.1',port=8765,method='adaptive',frame=36,task='navigation'):
    scene=make_scene(frame,task)
    obs=Observation(frame,task,ColorDetector().detect(scene.image))
    packet=encode(method,scene.image,obs,budget=80)
    with socket.create_connection((host,port),timeout=5) as conn:
        send_message(conn,msgpack.packb([method,frame,task,packet.data],use_bin_type=True))
        result=msgpack.unpackb(receive_message(conn),raw=False)
    print(f'Sent {len(packet.data)} bytes by TCP: {result}')
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('role',choices=('server','client'))
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--method',choices=('raw','roi','fixed','adaptive'),default='adaptive')
    a=parser.parse_args()
    return serve(a.host,a.port) if a.role=='server' else request(a.host,a.port,method=a.method)
if __name__=='__main__':main()
