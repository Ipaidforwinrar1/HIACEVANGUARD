import socket
import threading
import keyboard
import time

def handle_client(conn, addr):
    print(f"Connected to {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                key = data.decode()
                if len(key) == 1 and key.isalnum():  # Check if the key is valid
                    keyboard.send(key)
                time.sleep(0.01)
            except Exception as e:
                print(f"Error: {e}")
                break
    print(f"Connection to {addr} closed")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 65432))
    sock.listen(5)  # Allows for multiple clients to connect

    print("Server is listening... Press Ctrl+C to stop the server.")

    try:
        while True:
            conn, addr = sock.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
