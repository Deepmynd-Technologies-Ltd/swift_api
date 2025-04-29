from typing import Dict
from home.wallet_schema import Symbols
from swap.swap_schema import ChainEnum, ChainToken

# Token mapping with chain details
TOKEN_MAPPING: Dict[str, ChainToken] = {
    Symbols.BNB: ChainToken(
        name="BNB BEP20",
        chain=ChainEnum.BSC,
        address="native",  # Native token
        decimals=18,
        logoUrl="/media/icons/bnb_iicon.svg"
    ),
    Symbols.BTC: ChainToken(
        name="Bitcoin",
        chain=ChainEnum.BITCOIN,
        address="native",  # Native token
        decimals=8,
        logoUrl="/media/icons/btc_icon.svg"
    ),
    Symbols.DODGE: ChainToken(
        name="Doge coin",
        chain=ChainEnum.DOGECOIN,
        address="native",  # Native token
        decimals=8,
        logoUrl="/media/icons/doge_icon.svg"
    ),
    Symbols.ETH: ChainToken(
        name="Ethereum",
        chain=ChainEnum.ETHEREUM,
        address="native",  # Native token
        decimals=18,
        logoUrl="/media/icons/eth_icon.svg"
    ),
    Symbols.SOL: ChainToken(
        name="Solana",
        chain=ChainEnum.SOLANA,
        address="native",  # Native token
        decimals=9,
        logoUrl="/media/icons/sol_icon.svg"
    ),
    Symbols.USDT: ChainToken(
        name="USDT BEP20",
        chain=ChainEnum.BSC,
        address="0x55d398326f99059fF775485246999027B3197955",  # USDT on BSC
        decimals=18,
        logoUrl="/media/icons/usdt_icon.svg"
    ),
}

# Chain RPC endpoints for connecting to nodes
CHAIN_RPC_URLS = {
    ChainEnum.ETHEREUM: "https://ethereum.publicnode.com",
    ChainEnum.BSC: "https://bsc-dataseed.binance.org",
    ChainEnum.SOLANA: "https://api.mainnet-beta.solana.com",
    # Bitcoin and Dogecoin will use specific APIs
}

# API endpoints for different swap services
API_ENDPOINTS = {
    "1inch": {
        "base_url": "https://api.1inch.io/v5.0",
        "quote": "/quote",
        "swap": "/swap",
    },
    "0x": {
        "base_url": "https://api.0x.org",
        "quote": "/swap/v1/quote",
        "price": "/swap/v1/price",
    },
    "lifi": {
        "base_url": "https://li.quest/v1",
        "quote": "/quote",
        "status": "/status",
        "tokens": "/tokens",
    },
    "rango": {
        "base_url": "https://api.rango.exchange",
        "quote": "/routing/best",
        "status": "/tx/status",
        "tokens": "/basic/tokens",
    }
}

# Define which chains can be swapped internally (using 1inch or 0x)
INTRA_CHAIN_SUPPORTED = {
    ChainEnum.ETHEREUM: ["1inch", "0x"],
    ChainEnum.BSC: ["1inch", "0x"],
    # Solana would use a different DEX API if supported for intra-chain
}
1
# Define which chain pairs can be swapped using cross-chain protocols
INTER_CHAIN_ROUTES = {
    # From Ethereum
    (ChainEnum.ETHEREUM, ChainEnum.BSC): ["lifi", "rango"],
    (ChainEnum.ETHEREUM, ChainEnum.SOLANA): ["lifi"],
    
    # From BSC
    (ChainEnum.BSC, ChainEnum.ETHEREUM): ["lifi", "rango"],
    (ChainEnum.BSC, ChainEnum.SOLANA): ["lifi"],
    
    # From Solana
    (ChainEnum.SOLANA, ChainEnum.ETHEREUM): ["lifi"],
    (ChainEnum.SOLANA, ChainEnum.BSC): ["lifi"],
    
    # Bitcoin and Dogecoin routes would depend on available bridge services
}