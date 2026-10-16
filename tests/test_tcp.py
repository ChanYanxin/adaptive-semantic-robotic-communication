import socket,threading,time
from semantic_robot.tcp_demo import send_message,receive_message,request,serve

def test_framing():
    a,b=socket.socketpair()
    try:
        send_message(a,b'hello\x00world')
        assert receive_message(b)==b'hello\x00world'
    finally:a.close();b.close()

def test_tcp_roundtrip():
    probe=socket.socket();probe.bind(('127.0.0.1',0));port=probe.getsockname()[1];probe.close()
    thread=threading.Thread(target=serve,kwargs={'port':port,'max_clients':1},daemon=True)
    thread.start();result=None
    for _ in range(25):
        try:result=request(port=port);break
        except (ConnectionRefusedError,TimeoutError,OSError):time.sleep(.03)
    thread.join(timeout=2)
    assert result is not None and result['decision'] in ('STOP','GO','SEARCH','PICKUP')
