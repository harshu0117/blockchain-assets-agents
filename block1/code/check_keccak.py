import hashlib

def keccak256(text):
    import sha3
    k = sha3.keccak_256()
    k.update(text.encode('utf-8'))
    return '0x' + k.hexdigest()

try:
    import sha3
except ImportError:
    try:
        from Crypto.Hash import keccak
        def keccak256(text):
            k = keccak.new(digest_bits=256)
            k.update(text.encode('utf-8'))
            return '0x' + k.hexdigest()
    except ImportError:
        try:
            from eth_utils import keccak
            def keccak256(text):
                return '0x' + keccak(text.encode('utf-8')).hex()
        except ImportError:
            # Let's test with web3 or pysha3 or sha3
            pass

events = [
    "Transfer(address,address,uint256)",
    "Approval(address,address,uint256)",
    "ApprovalForAll(address,address,bool)",
    "Registered(uint256,address,string)",
    "Registered(uint256,string)",
    "MetadataUpdated(uint256,string)",
    "AgentWalletUpdated(uint256,address)",
    "FeedbackSubmitted(uint256,address,int256,uint8,string,string)",
    "FeedbackRevoked(uint256,address,uint64)",
    "FeedbackRevoked(uint256,address,uint256)",
]

known_topics = {
    '0x2c149ed548c6d2993cd73efe187df6eccabe4538091b33adbd25fafdb8a1468b': '?',
    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef': 'Transfer(address,address,uint256)',
    '0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a': '?',
    '0xf8e1a15aba9398e019f0b49df1a4fde98ee17ae345cb5f6b5e2c27f5033e8ce7': '?',
    '0x3a2c7fffc2cba7582c690e3b82c453ea02a308326a98a3ad7576c606336409fb': '?',
    '0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc': '?',
    '0xb1c6be0b5b8aef6539e2fac0fd131a2faa7b49edf8e505b5eb0ad487d56051d4': '?'
}

try:
    for e in events:
        h = keccak256(e)
        print(f"{e} -> {h}")
        if h in known_topics:
            known_topics[h] = e
    print("\nMatched:")
    for k, v in known_topics.items():
        print(k, "->", v)
except Exception as err:
    print("Keccak test error:", err)
