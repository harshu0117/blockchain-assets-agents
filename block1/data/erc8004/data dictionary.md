The dataset is organized as a relational schema consisting of multiple tables that capture identity, metadata, services, reputation, and transaction-level information for ERC-8004 agents. The primary key across the dataset is agent\_id, corresponding to the ERC-721 token identifier assigned at registration. The dataset covers agents with identifiers 0–9999 and is anchored to a fixed observation block.

### **agents\_core**

The agents\_core table serves as the canonical index of all ERC-8004 agents included in the dataset. Each row represents a unique agent identity as registered in the ERC-8004 identity registry.

Fields include:

* agent\_id: Unique identifier assigned at mint (ERC-721 token ID)  
* mint\_block: Block number at which the agent identity was minted  
* mint\_timestamp: UTC timestamp corresponding to the mint block  
* mint\_tx\_hash: Transaction hash of the mint event  
* owner\_wallet: Address of the agent owner at the observation block  
* agent\_wallet: Declared agent wallet address, if available  
* token\_uri: Raw metadata URI associated with the token  
* metadata\_hosting\_type: Inferred storage type (e.g., IPFS, HTTPS)  
* lifecycle\_status: Derived status (minted\_only or metadata\_linked)

### **agent\_metadata**

The agent\_metadata table contains structured data parsed from off-chain metadata referenced by token\_uri.

Fields include:

* agent\_id: Foreign key linking to agents\_core  
* metadata\_url\_resolved: HTTP-accessible metadata endpoint  
* metadata\_content\_type: Reported content type of the metadata response  
* metadata\_updated\_at: Timestamp extracted from metadata where available  
* name: Agent name  
* description: Human-readable description  
* image\_url: URL of the associated image  
* x402\_support: Boolean flag indicating support for x402 payments  
* active: Boolean indicating whether the agent is marked active  
* service\_count: Number of declared services  
* trust\_count: Number of trust-related entries  
* registration\_count: Number of registration-related entries

### **agent\_services**

The agent\_services table captures structured service declarations extracted from metadata.

Each row corresponds to a single service entry associated with an agent.

Fields include:

* id: Internal row identifier  
* agent\_id: Foreign key linking to agents\_core  
* service\_order: Order of the service in the metadata array  
* service\_name: Declared service type (e.g., MCP, A2A, OASF, x402)  
* endpoint: Service endpoint URL or address  
* version: Declared version string  
* skills\_json: JSON-encoded list of skills, if provided  
* domains\_json: JSON-encoded list of domains, if provided

### **agent\_reputation\_summary**

The agent\_reputation\_summary table contains aggregated reputation metrics for each agent as reported by the ERC-8004 reputation registry.

Fields include:

* agent\_id: Foreign key linking to agents\_core  
* feedback\_count\_total: Total number of feedback entries  
* reputation\_score\_raw: Aggregated score in raw integer form  
* reputation\_score\_decimals: Decimal precision for the score  
* client\_count: Number of unique clients contributing feedback

### **agent\_feedback\_records**

The agent\_feedback\_records table stores individual feedback entries submitted to the reputation registry.

Fields include:

* agent\_id: Foreign key linking to agents\_core  
* client\_address: Address submitting the feedback  
* feedback\_index: Sequential index of the feedback entry  
* value\_raw: Raw integer value of the feedback  
* value\_decimals: Decimal precision for the value  
* tag1: First categorical tag  
* tag2: Second categorical tag  
* is\_revoked: Boolean flag indicating whether the feedback has been revoked

### **mint\_economics**

The mint\_economics table captures transaction-level data associated with agent identity creation.

Fields include:

* mint\_tx\_hash: Transaction hash  
* gas\_used: Gas consumed by the transaction  
* gas\_price\_wei: Gas price in wei  
* mint\_cost\_eth: Computed transaction cost in ETH  
* tx\_value\_wei: Transaction value transferred  
* nonce: Transaction nonce  
* block\_gas\_limit: Gas limit of the block  
* block\_gas\_used: Total gas used in the block

### **crosschain\_registrations**

The crosschain\_registrations table records cross-chain identity mappings where available.

Fields include:

* id: Internal identifier  
* source\_agent\_id: Agent identifier on the source chain  
* target\_chain\_namespace: Target chain namespace  
* target\_chain\_id: Target chain ID  
* target\_identity\_registry: Target registry address  
* target\_agent\_id: Corresponding agent identifier on the target chain

### **transfer\_history**

The transfer\_history table is designed to record ERC-721 ownership transfer events.

Fields include:

* id: Internal identifier  
* agent\_id: Foreign key linking to agents\_core  
* from\_wallet: Sender address  
* to\_wallet: Recipient address  
* tx\_hash: Transaction hash  
* block\_number: Block number  
* timestamp: Block timestamp  
* log\_index: Log index within the transaction

