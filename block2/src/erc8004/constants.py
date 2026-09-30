"""
Constants and Contract Definitions for ERC-8004 Analysis
"""

# CREATE2 vanity deployment addresses (identical across EVM chains)
IDENTITY_REGISTRY_ADDRESS = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
REPUTATION_REGISTRY_ADDRESS = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"

# Chain Configurations
CHAINS = {
    1: {
        "name": "ethereum",
        "chain_id": 1,
        "anchor_block": 24339991,
        "anchor_timestamp": 1769683463,  # 2026-01-29 10:44:23 UTC
        "block_time_seconds": 12.0,
    },
    8453: {
        "name": "base",
        "chain_id": 8453,
        "anchor_block": 40000000,
        "anchor_timestamp": 1766789347,  # verified on-chain
        "block_time_seconds": 2.0,
    }
}

# IdentityRegistry Event Signatures and Hashes
# Registered(uint256 indexed agentId, string agentURI, address indexed owner)
TOPIC_REGISTERED = "0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a"

# Transfer(address indexed from, address indexed to, uint256 indexed tokenId)
TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# URIUpdated(uint256 indexed agentId, string newURI, address indexed updatedBy)
TOPIC_URI_UPDATED = "0x3a2c7fffc2cba7582c690e3b82c453ea02a308326a98a3ad7576c606336409fb"

# MetadataSet(uint256 indexed agentId, string indexed indexedMetadataKey, string metadataKey, bytes metadataValue)
TOPIC_METADATA_SET = "0x2c149ed548c6d2993cd73efe187df6eccabe4538091b33adbd25fafdb8a1468b"

# ReputationRegistry Event Signatures and Hashes
# NewFeedback(uint256 indexed agentId, address indexed clientAddress, uint64 feedbackIndex, int128 value, uint8 valueDecimals, string indexed indexedTag1, string tag1, string tag2, string endpoint, string feedbackURI, bytes32 feedbackHash)
TOPIC_NEW_FEEDBACK = "0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc"
# FeedbackRevoked(uint256 indexed agentId, address indexed clientAddress, uint64 indexed feedbackIndex)
TOPIC_FEEDBACK_REVOKED = "0x25156fd3288212246d8b008d5921fde376c71ed14ac2e072a506eb06fde6d09d"
# ResponseAppended(uint256 indexed agentId, address indexed clientAddress, uint64 feedbackIndex, address indexed responder, string responseURI, bytes32 responseHash)
TOPIC_RESPONSE_APPENDED = "0xb1c6be0b5b8aef6539e2fac0fd131a2faa7b49edf8e505b5eb0ad487d56051d4"

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
