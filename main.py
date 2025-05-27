from colorama import init, Fore, Style
import argparse
import json
import uuid
import hashlib
import time
from datetime import datetime
from RNode import RNodeInterface
from typing import Dict, List, Tuple

# Initialize colorama
init()

# Global dictionary to store incomplete messages with timestamps and part numbers
# Format: {msg_id: [(fragment_data, part_number, timestamp), ...]}
incomplete_messages: Dict[str, List[Tuple[str, int, float]]] = {}

# Add at the top with other constants
FRAGMENT_EXPIRY_TIME = 3600  # 1 hour in seconds

def fragment_message(message: str, max_size: int = 200) -> List[dict]:
    """Split message into fragments with metadata"""
    fragments = [message[i:i + max_size] for i in range(0, len(message), max_size)]
    total_parts = len(fragments)
    msg_id = str(uuid.uuid4())  # Generate one UUID for all fragments
    checksum = hashlib.md5(message.encode('utf-8')).hexdigest()
    
    return [
        {
            'msg_id': msg_id,
            'part': i + 1,
            'total_parts': total_parts,
            'checksum': checksum,
            'data': fragment
        } for i, fragment in enumerate(fragments)
    ]

def cleanup_expired_fragments(current_time: float) -> None:
    """Remove fragments older than FRAGMENT_EXPIRY_TIME seconds"""
    expired_msgs = []
    for msg_id, fragments in incomplete_messages.items():
        # Check if any fragment is older than expiry time
        for _, _, timestamp in fragments:
            if timestamp > 0 and current_time - timestamp > FRAGMENT_EXPIRY_TIME:
                expired_msgs.append(msg_id)
                break
    
    # Remove expired messages
    for msg_id in expired_msgs:
        print(f"{Fore.YELLOW}⚠️ Removing expired fragments for message {msg_id}{Style.RESET_ALL}")
        del incomplete_messages[msg_id]

def reconstruct_message(fragment: dict, rnode: RNodeInterface) -> str:
    """Try to reconstruct message from fragments"""
    msg_id = fragment['msg_id']
    current_time = time.time()
    
    # Clean up expired fragments
    cleanup_expired_fragments(current_time)
    
    if msg_id not in incomplete_messages:
        incomplete_messages[msg_id] = [('', 0, 0)] * fragment['total_parts']
    
    # Store this fragment with part number and timestamp
    incomplete_messages[msg_id][fragment['part'] - 1] = (fragment['data'], fragment['part'], current_time)
    
    # Check if message is complete
    if all(data != '' for data, _, _ in incomplete_messages[msg_id]):
        # Sort by part number before joining
        sorted_fragments = sorted(incomplete_messages[msg_id], key=lambda x: x[1])
        complete_message = ''.join(data for data, _, _ in sorted_fragments)
        
        # Get timestamps for reporting
        timestamps = [ts for _, _, ts in incomplete_messages[msg_id]]
        first_fragment = min(timestamps)
        last_fragment = max(timestamps)
        
        print(f"\n⏰ Fragment timing:")
        print(f"First fragment received: {datetime.fromtimestamp(first_fragment).isoformat()}")
        print(f"Last fragment received: {datetime.fromtimestamp(last_fragment).isoformat()}")
        print(f"Total time: {last_fragment - first_fragment:.2f} seconds")
        
        # Verify checksum
        received_checksum = fragment['checksum']
        calculated_checksum = hashlib.md5(complete_message.encode('utf-8')).hexdigest()
        
        del incomplete_messages[msg_id]
        
        if received_checksum == calculated_checksum:
            # Send acknowledgment
            ack_message = {
                'type': 'ack',
                'msg_id': msg_id,
                'status': 'success',
                'timestamp': time.time()
            }
            try:
                ack_data = json.dumps(ack_message).encode('utf-8')
                rnode.send(ack_data)
                print(f"{Fore.GREEN}✅ Sent acknowledgment for message {msg_id}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Failed to send acknowledgment: {e}{Style.RESET_ALL}")
            
            return complete_message
        else:
            # Send negative acknowledgment
            nack_message = {
                'type': 'ack',
                'msg_id': msg_id,
                'status': 'checksum_error',
                'timestamp': time.time()
            }
            try:
                nack_data = json.dumps(nack_message).encode('utf-8')
                rnode.send(nack_data)
                print(f"{Fore.YELLOW}⚠️ Sent negative acknowledgment for message {msg_id}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Failed to send negative acknowledgment: {e}{Style.RESET_ALL}")
            
            print("\n=== Checksum Error ===")
            print("Message integrity check failed!")
            print("=====================")
            return ''
    return ''

def gotPacket(data, rnode):
    try:
        fragment = json.loads(data.decode("utf-8"))
        
        # Handle acknowledgment messages
        if fragment.get('type') == 'ack':
            print(f"\n{Fore.BLUE}📨 Received {'success' if fragment['status'] == 'success' else 'error'} acknowledgment{Style.RESET_ALL}")
            print(f"📝 Message ID: {fragment['msg_id']}")
            print(f"⏰ Time: {datetime.fromtimestamp(fragment['timestamp']).isoformat()}")
            return
        
        current_time = datetime.now().isoformat()
        print(f"\n{Fore.BLUE}📦 Received fragment {fragment['part']}/{fragment['total_parts']} (ID: {fragment['msg_id']}) at {current_time}{Style.RESET_ALL} 📡 RSSI: {rnode.r_stat_rssi} dBm 📊 SNR:  {rnode.r_stat_snr} dB")
        complete_message = reconstruct_message(fragment, rnode)
        if complete_message:
            print(f"\n{Fore.GREEN}=== Complete Message ==={Style.RESET_ALL}")
            print(f"💬 Message: '{complete_message}'")
            print(f"{Fore.GREEN}====================={Style.RESET_ALL}")
    except json.JSONDecodeError:
        print(f"{Fore.RED}❌ Received malformed packet{Style.RESET_ALL}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='RNode example program')
    parser.add_argument('--port', default="/dev/ttyUSB0", help='Serial port for RNode (default: /dev/ttyUSB0)')
    parser.add_argument('--name', default="My RNode", help='Name for the RNode (default: My RNode)')
    parser.add_argument('--frequency', type=int, default=868000000, help='Frequency in Hz (default: 868000000)')
    parser.add_argument('--bandwidth', type=int, default=125000, help='Bandwidth in Hz (default: 125000)')
    parser.add_argument('--txpower', type=int, default=2, help='TX Power in dBm (default: 2)')
    parser.add_argument('--sf', type=int, default=7, help='Spreading Factor (default: 7)')
    parser.add_argument('--cr', type=int, default=5, help='Coding Rate (default: 5)')
    args = parser.parse_args()

    rnode = RNodeInterface(
        callback = gotPacket,
        name = args.name,
        port = args.port,
        frequency = args.frequency,
        bandwidth = args.bandwidth,
        txpower = args.txpower,
        sf = args.sf,
        cr = args.cr,
        loglevel = RNodeInterface.LOG_VERBOSE)

    # Print configuration and connection status
    print(f"\n{Fore.YELLOW}⚙️  RNode Configuration:{Style.RESET_ALL}")
    print(f"📝 Node Name: {rnode.name}")
    print(f"🔌 Port: {args.port}")
    print(f"📻 Frequency: {rnode.frequency/1000000:.2f} MHz")
    print(f"📊 Bandwidth: {rnode.bandwidth/1000:.0f} kHz")
    print(f"⚡ TX Power: {rnode.txpower} dBm")
    print(f"📈 Spreading Factor: {rnode.sf}")
    print(f"🔢 Coding Rate: {rnode.cr}")
    print(f"🔗 Connected: {Fore.GREEN + '✓ Yes' if rnode.online else Fore.RED + '✗ No'}{Style.RESET_ALL}\n")

    try:
        while True:
            message = input(f"{Fore.CYAN}💬 Enter message (Ctrl-C to exit): {Style.RESET_ALL}")
            if message:
                fragments = fragment_message(message)
                for fragment in fragments:
                    data = json.dumps(fragment).encode("utf-8")
                    rnode.send(data)
                    print(f"{Fore.BLUE}📤 Sent fragment {fragment['part']}/{fragment['total_parts']} (ID: {fragment['msg_id'][:8]}){Style.RESET_ALL}")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Exiting...{Style.RESET_ALL}")
        exit()

if __name__ == "__main__":
    main()