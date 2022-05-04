EOF_MARKER = "===== END OF FILE ====="

def check_response(rdt_sock, expected_msg):
    actual_msg = rdt_sock.receive()
    if actual_msg != expected_msg:
        print(f"Expected response msg of '{expected_msg}', but got '{actual_msg}'")
