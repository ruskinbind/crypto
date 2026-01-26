import asyncio
import os
import json
from web3 import Web3
from eth_account import Account
from colorama import init, Fore, Style
import time
import random
import string
from datetime import datetime
import pytz

# Initialize colorama
init(autoreset=True)

# Timezone
wib = pytz.timezone('Asia/Jakarta')

# Configuration
RPC_URL = 'https://rpc.testnet.arc.network'
CHAIN_ID = 5042002
EXPLORER_URL = 'https://testnet.arcscan.app'

CONTRACTS = {
    'NFT': '0x632176D769aB950bb27cA00fDa81cfcb1886d082',
    'USDC': '0x3600000000000000000000000000000000000000',
    'WUSDC': '0x911b4000D3422F482F4062a913885f7b035382Df',
    'SWAP_ROUTER': '0xFF5Cb29241F002fFeD2eAa224e3e996D24A6E8d1',
    'CURVE_POOL': '0x2D84D79C852f6842AbE0304b70bBaA1506AdD457',
    'CURVE_GAUGE': '0xCd4e6C8056608e7CA5b8cD126F32c56c43D92979',
    'DEPOSIT_STAKE_CONTRACT': '0xB2Be7692B07b640C9f2ee1187cee2fAec741F872',
    'NAME_REGISTRY': '0x76a816EFa69e3183972ff7a231F5C8d7b065d9De',
    'ON_CHAIN_GM': '0x363cc75a89ae5673b427a1fa98afc48ffde7ba43'
}

# All NFT Contracts
NFT_COLLECTIONS = [
    {
        "name": "Original NFT",
        "symbol": "ONFT",
        "address": "0x632176D769aB950bb27cA00fDa81cfcb1886d082",
        "price": 0,
        "type": "mint"
    },
    {
        "name": "NeoArc",
        "symbol": "nArc",
        "address": "0xE61C61A8F0d1D551BB85b81ECE73Ac6F48aD7A8D",
        "price": 0,
        "type": "claim"
    },
    {
        "name": "Camellia",
        "symbol": "CA",
        "address": "0x8DF9a64595E4b0b0f5C12fB92F88765a52E63a0f",
        "price": 0,
        "type": "claim"
    },
    {
        "name": "Moonlit",
        "symbol": "ML",
        "address": "0xF94ee17F5c9678d01FC97C14725F092D8cC9726a",
        "price": 0,
        "type": "claim"
    },
    {
        "name": "ARCLYRIA",
        "symbol": "ARC",
        "address": "0x7477dF3A73DAaf9cc5765C4b9fFc018cBFdFc4e6",
        "price": 1.5,
        "type": "claim"
    },
    {
        "name": "Delight",
        "symbol": "DT",
        "address": "0x28f7eD1A0F7B1F99ea8b27BB90625B486926B7AD",
        "price": 0,
        "type": "claim"
    },
    {
        "name": "Lady",
        "symbol": "LY",
        "address": "0xBab687216f462BA3971634fF6F41A11210f15D80",
        "price": 0,
        "type": "claim"
    },
    {
        "name": "Dusk",
        "symbol": "DK",
        "address": "0x4eeef4b00b88a42532CD3016528Ad18d2EEDbF6A",
        "price": 0,
        "type": "claim"
    },
    {
        "name": "ANGELARC",
        "symbol": "DRAZE",
        "address": "0x8817133E4E01D3e815060592f56Df66C70cd6A11",
        "price": 1.0,
        "type": "claim"
    }
]

# Token Bytecode
TOKEN_BYTECODE = '0x60806040819052600780546001600160a01b0319167338cb0184b802629c8a93235cc6c058f5a6cc8f8417905561119338819003908190833981016040819052610048916104ae565b338383600361005783826105a9565b50600461006482826105a9565b5050506001600160a01b03811661009657604051631e4fbdf760e01b8152600060048201526024015b60405180910390fd5b61009f81610235565b5060016006556521a6bbdb50003410156101075760405162461bcd60e51b815260206004820152602360248201527f4372656174696f6e206665652072657175697265643a20302e3030303033372060448201526208aa8960eb1b606482015260840161008d565b600081116101445760405162461bcd60e51b815260206004820152600a6024820152690537570706c79203d20360b41b604482015260640161008d565b6007546040516000916001600160a01b03169034908381818185875af1925050503d8060008114610191576040519150601f19603f3d011682016040523d82523d6000602084013e610196565b606091505b50509050806101e75760405162461bcd60e51b815260206004820152601360248201527f466565207472616e73666572206661696c656400000000000000000000000000604482015260640161008d565b6101f13383610287565b7f35d0b9713cc4b54bb91a9bfa420b091d37c592d49a7468dafe20b4cfbdfca02a84848460405161022493929190610693565b60405180910390a1505050506106f0565b600580546001600160a01b038381166001600160a01b0319831681179093556040519116919082907f8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e090600090a35050565b6001600160a01b0382166102b15760405163ec442f0560e01b81526000600482015260240161008d565b6102bd600083836102c1565b5050565b6001600160a01b0383166102ec5780600260008282546102e191906106c9565b9091555061035e9050565b6001600160a01b0383166000908152602081905260409020548181101561033f5760405163391434e360e21b81526001600160a01b0385166004820152602481018290526044810183905260640161008d565b6001600160a01b03841660009081526020819052604090209082900390555b6001600160a01b03821661037a57600280548290039055610399565b6001600160a01b03821660009081526020819052604090208054820190555b816001600160a01b0316836001600160a01b03167fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef836040516103de91815260200190565b60405180910390a3505050565b634e487b7160e01b600052604160045260246000fd5b60005b8381101561041c578181015183820152602001610404565b50506000910152565b600082601f83011261043657600080fd5b81516001600160401b0381111561044f5761044f6103eb565b604051601f8201601f19908116603f011681016001600160401b038111828210171561047d5761047d6103eb565b60405281815283820160200185101561049557600080fd5b6104a6826020830160208701610401565b949350505050565b6000806000606084860312156104c357600080fd5b83516001600160401b038111156104d957600080fd5b6104e586828701610425565b602086015190945090506001600160401b0381111561050357600080fd5b61050f86828701610425565b925050604084015190509250925092565b600181811c9082168061053457607f821691505b60208210810361055457634e487b7160e01b600052602260045260246000fd5b50919050565b601f8211156105a457806000526020600020601f840160051c810160208510156105815750805b601f840160051c820191505b818110156105a1576000815560010161058d565b50505b505050565b81516001600160401b038111156105c2576105c26103eb565b6105d6816105d08454610520565b8461055a565b6020601f82116001811461060a57600083156105f25750848201515b600019600385901b1c1916600184901b1784556105a1565b600084815260208120601f198516915b8281101561063a578785015182556020948501946001909201910161061a565b50848210156106585786840151600019600387901b60f8161c191681555b50505050600190811b01905550565b6000815180845261067f816020860160208601610401565b601f01601f19169290920160200192915050565b6060815260006106a66060830186610667565b82810360208401526106b88186610667565b915050826040830152949350505050565b808201808211156106ea57634e487b7160e01b600052601160045260246000fd5b92915050565b610a94806106ff6000396000f3fe6080604052600436106100e15760003560e01c80638831e9cf1161007f578063a9059cbb11610059578063a9059cbb146102f3578063dd62ed3e14610313578063f2fde38b14610359578063fa2af9da1461037957600080fd5b80638831e9cf1461028c5780638da5cb5b146102ac57806395d89b41146102de57600080fd5b806323b872dd116100bb57806323b872dd14610205578063313ce5671461022557806370a0823114610241578063715018a61461027757600080fd5b806306fdde031461018b578063095ea7b3146101b657806318160ddd146101e657600080fd5b36610186576007546040516000916001600160a01b03169034908381818185875af1925050503d8060008114610133576040519150601f19603f3d011682016040523d82523d6000602084013e610138565b606091505b50509050806101845760405162461bcd60e51b8152602060048201526013602482015272119959481d1c985b9cd9995c8819985a5b1959606a1b60448201526064015b60405180910390fd5b005b600080fd5b34801561019757600080fd5b506101a0610399565b6040516101ad91906108dd565b60405180910390f35b3480156101c257600080fd5b506101d66101d1366004610947565b61042b565b60405190151581526020016101ad565b3480156101f257600080fd5b506002545b6040519081526020016101ad565b34801561021157600080fd5b506101d6610220366004610971565b610445565b34801561023157600080fd5b50604051601281526020016101ad565b34801561024d57600080fd5b506101f761025c3660046109ae565b6001600160a01b031660009081526020819052604090205490565b34801561028357600080fd5b50610184610469565b34801561029857600080fd5b506101846102a73660046109ae565b61047d565b3480156102b857600080fd5b506005546001600160a01b03165b6040516001600160a01b0390911681526020016101ad565b3480156102ea57600080fd5b506101a0610514565b3480156102ff57600080fd5b506101d661030e366004610947565b610523565b34801561031f57600080fd5b506101f761032e3660046109d0565b6001600160a01b03918216600090815260016020908152604080832093909416825291909152205490565b34801561036557600080fd5b506101846103743660046109ae565b610531565b34801561038557600080fd5b506007546102c6906001600160a01b031681565b6060600380546103a890610a03565b80601f01602080910402602001604051908101604052809291908181526020018280546103d590610a03565b80156104215780601f106103f657610100808354040283529160200191610421565b820191906000526020600020905b81548152906001019060200180831161040457829003601f168201915b5050505050905090565b60003361043981858561056f565b60019150505b92915050565b600033610453858285610581565b61045e858585610600565b506001949350505050565b61047161065f565b61047b600061068c565b565b61048561065f565b6001600160a01b0381166104ca5760405162461bcd60e51b815260206004820152600c60248201526b5a65726f206164647265737360a01b604482015260640161017b565b600780546001600160a01b0319166001600160a01b0383169081179091556040517f73238e3ae0a71b401b31ae67204506d074de41bd5c084082fba9b64b1c7fa28f90600090a250565b6060600480546103a890610a03565b600033610439818585610600565b61053961065f565b6001600160a01b03811661056357604051631e4fbdf760e01b81526000600482015260240161017b565b61056c8161068c565b50565b61057c83838360016106de565b505050565b6001600160a01b038381166000908152600160209081526040808320938616835292905220546000198110156105fa57818110156105eb57604051637dc7a0d960e11b81526001600160a01b0384166004820152602481018290526044810183905260640161017b565b6105fa848484840360006106de565b50505050565b6001600160a01b03831661062a57604051634b637e8f60e11b81526000600482015260240161017b565b6001600160a01b0382166106545760405163ec442f0560e01b81526000600482015260240161017b565b61057c8383836107b3565b6005546001600160a01b0316331461047b5760405163118cdaa760e01b815233600482015260240161017b565b600580546001600160a01b038381166001600160a01b0319831681179093556040519116919082907f8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e090600090a35050565b6001600160a01b0384166107085760405163e602df0560e01b81526000600482015260240161017b565b6001600160a01b03831661073257604051634a1406b160e11b81526000600482015260240161017b565b6001600160a01b03808516600090815260016020908152604080832093871683529290522082905580156105fa57826001600160a01b0316846001600160a01b03167f8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925846040516107a591815260200190565b60405180910390a350505050565b6001600160a01b0383166107de5780600260008282546107d39190610a3d565b909155506108509050565b6001600160a01b038316600090815260208190526040902054818110156108315760405163391434e360e21b81526001600160a01b0385166004820152602481018290526044810183905260640161017b565b6001600160a01b03841660009081526020819052604090209082900390555b6001600160a01b03821661086c5760028054829003905561088b565b6001600160a01b03821660009081526020819052604090208054820190555b816001600160a01b0316836001600160a01b03167fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef836040516108d091815260200190565b60405180910390a3505050565b602081526000825180602084015260005b8181101561090b57602081860181015160408684010152016108ee565b506000604082850101526040601f19601f83011684010191505092915050565b80356001600160a01b038116811461094257600080fd5b919050565b6000806040838503121561095a57600080fd5b6109638361092b565b946020939093013593505050565b60008060006060848603121561098657600080fd5b61098f8461092b565b925061099d6020850161092b565b929592945050506040919091013590565b6000602082840312156109c057600080fd5b6109c98261092b565b9392505050565b600080604083850312156109e357600080fd5b6109ec8361092b565b91506109fa6020840161092b565b90509250929050565b600181811c90821680610a1757607f821691505b602082108103610a3757634e487b7160e01b600052602260045260246000fd5b50919050565b8082018082111561043f57634e487b7160e01b600052601160045260246000fdfea264697066735822122022a75f40070b6dc7dbe5fa6faf63e32f1ba0e9d418e1bc65bb94efd49920287964736f6c634300081a0033'

# ABIs
USDC_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

CURVE_POOL_ABI = [
    {
        "inputs": [
            {"internalType": "uint256[]", "name": "_amounts", "type": "uint256[]"},
            {"internalType": "uint256", "name": "_min_mint_amount", "type": "uint256"}
        ],
        "name": "add_liquidity",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

CURVE_GAUGE_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

SWAP_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "address[11]", "name": "_route", "type": "address[11]"},
            {"internalType": "uint256[4][5]", "name": "_swap_params", "type": "uint256[4][5]"},
            {"internalType": "uint256", "name": "_in_amount", "type": "uint256"},
            {"internalType": "uint256", "name": "_min_out_amount", "type": "uint256"}
        ],
        "name": "exchange",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

NFT_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

NFT_CLAIM_ABI = [{
    "inputs": [
        {"internalType": "address", "name": "_receiver", "type": "address"},
        {"internalType": "uint256", "name": "_quantity", "type": "uint256"},
        {"internalType": "address", "name": "_currency", "type": "address"},
        {"internalType": "uint256", "name": "_pricePerToken", "type": "uint256"},
        {
            "components": [
                {"internalType": "bytes32[]", "name": "proof", "type": "bytes32[]"},
                {"internalType": "uint256", "name": "quantityLimitPerWallet", "type": "uint256"},
                {"internalType": "uint256", "name": "pricePerToken", "type": "uint256"},
                {"internalType": "address", "name": "currency", "type": "address"}
            ],
            "internalType": "struct IDropSinglePhase.AllowlistProof",
            "name": "_allowlistProof",
            "type": "tuple"
        },
        {"internalType": "bytes", "name": "_data", "type": "bytes"}
    ],
    "name": "claim",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
}]

ON_CHAIN_GM_ABI = [
    {
        "type": "function",
        "name": "timeUntilNextGM",
        "stateMutability": "view",
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "GM_FEE",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}]
    },
    {
        "type": "function",
        "name": "onChainGM",
        "stateMutability": "payable",
        "inputs": [{"internalType": "address", "name": "referrer", "type": "address"}],
        "outputs": []
    }
]

NAME_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "address", "name": "owner", "type": "address"}
        ],
        "name": "register",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

class ArcTestnetBot:
    def __init__(self):
        self.accounts = []
        self.w3 = None
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.tx_count = config.get('tx_count', 1)
        except:
            self.tx_count = 1
        self.load_accounts()
        self.initialize_web3()
    
    def load_accounts(self):
        """Load accounts from pv.txt file"""
        try:
            if not os.path.exists("pv.txt"):
                print(f"{Fore.RED + Style.BRIGHT}Error: pv.txt file not found!{Style.RESET_ALL}")
                exit(1)
                
            with open("pv.txt", "r") as file:
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        if ':' in line:
                            parts = line.rsplit(':', 1)
                            private_key = parts[0].strip()
                            wallet_name = parts[1].strip() if len(parts) > 1 else "Unknown"
                        else:
                            private_key = line
                            wallet_name = "Unknown"
                        
                        try:
                            account = Account.from_key(private_key)
                            self.accounts.append({
                                'account': account,
                                'wallet_name': wallet_name,
                                'address': account.address
                            })
                        except Exception as e:
                            print(f"{Fore.RED + Style.BRIGHT}Invalid private key: {str(e)}{Style.RESET_ALL}")
            
            if not self.accounts:
                print(f"{Fore.RED + Style.BRIGHT}Error: No valid accounts found in pv.txt!{Style.RESET_ALL}")
                exit(1)
            
            print(f"{Fore.GREEN + Style.BRIGHT}Loaded {len(self.accounts)} account(s){Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}Error loading accounts: {str(e)}{Style.RESET_ALL}")
            exit(1)
    
    def initialize_web3(self):
        """Initialize Web3 connection"""
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        
        if not self.w3.is_connected():
            print(f"{Fore.RED + Style.BRIGHT}Failed to connect to RPC{Style.RESET_ALL}")
            exit(1)
        
        print(f"{Fore.GREEN + Style.BRIGHT}Connected to Arc Testnet{Style.RESET_ALL}")
    
    def log(self, wallet_name, message, type="INFO"):
        """Enhanced logging"""
        if type == "SUCCESS":
            prefix = f"{Fore.GREEN + Style.BRIGHT}[SUCCESS]"
            msg_color = Fore.GREEN + Style.BRIGHT
        elif type == "ERROR":
            prefix = f"{Fore.RED + Style.BRIGHT}[ERROR]"
            msg_color = Fore.RED + Style.BRIGHT
        elif type == "WARNING":
            prefix = f"{Fore.YELLOW + Style.BRIGHT}[WARNING]"
            msg_color = Fore.YELLOW + Style.BRIGHT
        elif type == "PROCESS":
            prefix = f"{Fore.CYAN + Style.BRIGHT}[PROCESS]"
            msg_color = Fore.CYAN + Style.BRIGHT
        elif type == "TX":
            prefix = f"{Fore.MAGENTA + Style.BRIGHT}[TX]"
            msg_color = Fore.MAGENTA + Style.BRIGHT
        else:
            prefix = f"{Fore.WHITE + Style.BRIGHT}[INFO]"
            msg_color = Fore.WHITE + Style.BRIGHT
            
        print(f"{Fore.BLUE + Style.BRIGHT}[{wallet_name}]{Style.RESET_ALL} {prefix}{Style.RESET_ALL} {msg_color}{message}{Style.RESET_ALL}")

    def generate_random_string(self, length=8):
        """Generate random string for unique names"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def get_random_amount(self, min_val=0.001, max_val=0.01):
        """Generate random amount for transactions"""
        return round(random.uniform(min_val, max_val), 6)

    async def deposit_and_stake(self, account_data, usdc_amount=None):
        """Deposit and Stake using helper contract"""
        try:
            account = account_data['account']
            wallet_name = account_data['wallet_name']
            address = account_data['address']
            
            if usdc_amount is None:
                usdc_amount = self.get_random_amount(0.001, 0.005)
            
            self.log(wallet_name, f"Processing Deposit & Stake with {usdc_amount} USDC", "PROCESS")
            
            usdc_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACTS['USDC']),
                abi=USDC_ABI
            )
            
            usdc_units = int(usdc_amount * 1000000)
            
            current_allowance = usdc_contract.functions.allowance(address, CONTRACTS['DEPOSIT_STAKE_CONTRACT']).call()
            
            if current_allowance < usdc_units:
                self.log(wallet_name, "Approving USDC...", "PROCESS")
                
                approve_tx = usdc_contract.functions.approve(
                    CONTRACTS['DEPOSIT_STAKE_CONTRACT'],
                    2**256 - 1
                ).build_transaction({
                    'from': address,
                    'nonce': self.w3.eth.get_transaction_count(address),
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price,
                    'chainId': CHAIN_ID
                })
                
                signed_approve = account.sign_transaction(approve_tx)
                approve_hash = self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                self.log(wallet_name, f"Approval TX: {approve_hash.hex()}", "TX")
                
                approve_receipt = self.w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                
                if approve_receipt.status != 1:
                    self.log(wallet_name, "Approval failed!", "ERROR")
                    return {'success': False, 'error': 'Approval failed'}
                
                await asyncio.sleep(2)
            
            min_lp_amount = int(usdc_amount * 0.87 * 10**18)
            
            data = '0xc0c702dc' + \
                   '0000000000000000000000002d84d79c852f6842abe0304b70bbaa1506add457' + \
                   '0000000000000000000000002d84d79c852f6842abe0304b70bbaa1506add457' + \
                   '000000000000000000000000cd4e6c8056608e7ca5b8cd126f32c56c43d92979' + \
                   '0000000000000000000000000000000000000000000000000000000000000002' + \
                   '0000000000000000000000000000000000000000000000000000000000000120' + \
                   '0000000000000000000000000000000000000000000000000000000000000180' + \
                   f'{min_lp_amount:064x}' + \
                   '0000000000000000000000000000000000000000000000000000000000000001' + \
                   '0000000000000000000000000000000000000000000000000000000000000000' + \
                   '0000000000000000000000000000000000000000000000000000000000000002' + \
                   '0000000000000000000000003600000000000000000000000000000000000000' + \
                   '00000000000000000000000089b50855aa3be2f677cd6303cec089b5f319d72a' + \
                   '0000000000000000000000000000000000000000000000000000000000000002' + \
                   f'{usdc_units:064x}' + \
                   '0000000000000000000000000000000000000000000000000000000000000000'
            
            tx = {
                'from': address,
                'to': CONTRACTS['DEPOSIT_STAKE_CONTRACT'],
                'data': data,
                'nonce': self.w3.eth.get_transaction_count(address),
                'gas': 750000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': CHAIN_ID
            }
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            self.log(wallet_name, f"Deposit & Stake TX: {tx_hash_hex}", "TX")
            self.log(wallet_name, f"Explorer: {EXPLORER_URL}/tx/0x{tx_hash_hex}", "INFO")
            
            self.log(wallet_name, "Waiting for confirmation...", "PROCESS")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                try:
                    gauge_contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(CONTRACTS['CURVE_GAUGE']),
                        abi=CURVE_GAUGE_ABI
                    )
                    gauge_balance = gauge_contract.functions.balanceOf(address).call()
                    if gauge_balance > 0:
                        self.log(wallet_name, f"Staked Balance: {gauge_balance / 10**18:.6f} Gauge Tokens", "SUCCESS")
                except:
                    pass
                
                self.log(wallet_name, f"Deposit & Stake completed successfully!", "SUCCESS")
                return {'success': True, 'hash': tx_hash_hex}
            else:
                self.log(wallet_name, "Transaction failed!", "ERROR")
                return {'success': False, 'error': 'Transaction failed'}
                
        except Exception as e:
            self.log(wallet_name, f"Failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    async def add_liquidity(self, account_data, usdc_amount=None):
        """Add liquidity to Curve pool"""
        try:
            account = account_data['account']
            wallet_name = account_data['wallet_name']
            address = account_data['address']
            
            if usdc_amount is None:
                usdc_amount = self.get_random_amount(0.001, 0.005)
            
            self.log(wallet_name, f"Adding liquidity: {usdc_amount} USDC", "PROCESS")
            
            usdc_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACTS['USDC']),
                abi=USDC_ABI
            )
            
            usdc_units = int(usdc_amount * 1000000)
            
            current_allowance = usdc_contract.functions.allowance(address, CONTRACTS['CURVE_POOL']).call()
            
            if current_allowance < usdc_units:
                self.log(wallet_name, "Approving USDC...", "PROCESS")
                
                approve_tx = usdc_contract.functions.approve(
                    CONTRACTS['CURVE_POOL'],
                    2**256 - 1
                ).build_transaction({
                    'from': address,
                    'nonce': self.w3.eth.get_transaction_count(address),
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price,
                    'chainId': CHAIN_ID
                })
                
                signed_approve = account.sign_transaction(approve_tx)
                approve_hash = self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                self.log(wallet_name, f"Approval TX: {approve_hash.hex()}", "TX")
                
                approve_receipt = self.w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                
                if approve_receipt.status != 1:
                    self.log(wallet_name, "Approval failed!", "ERROR")
                    return {'success': False, 'error': 'Approval failed'}
                
                await asyncio.sleep(2)
            
            curve_pool = self.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACTS['CURVE_POOL']),
                abi=CURVE_POOL_ABI
            )
            
            amounts = [usdc_units, 0]
            min_lp_amount = int(usdc_amount * 0.75 * 10**18)
            
            add_liquidity_tx = curve_pool.functions.add_liquidity(
                amounts,
                min_lp_amount
            ).build_transaction({
                'from': address,
                'nonce': self.w3.eth.get_transaction_count(address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': CHAIN_ID
            })
            
            signed_tx = account.sign_transaction(add_liquidity_tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            self.log(wallet_name, f"Add Liquidity TX: {tx_hash_hex}", "TX")
            self.log(wallet_name, f"Explorer: {EXPLORER_URL}/tx/0x{tx_hash_hex}", "INFO")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                lp_balance = curve_pool.functions.balanceOf(address).call()
                self.log(wallet_name, f"LP Token Balance: {lp_balance / 10**18:.6f}", "SUCCESS")
                self.log(wallet_name, f"Liquidity added successfully!", "SUCCESS")
                return {'success': True, 'hash': tx_hash_hex}
            else:
                self.log(wallet_name, "Transaction failed!", "ERROR")
                return {'success': False, 'error': 'Transaction failed'}
                
        except Exception as e:
            self.log(wallet_name, f"Failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    async def swap_usdc_to_wusdc(self, account_data, amount=None):
        """Swap USDC to WUSDC"""
        try:
            account = account_data['account']
            wallet_name = account_data['wallet_name']
            address = account_data['address']
            
            if amount is None:
                amount = self.get_random_amount(0.001, 0.003)
            
            amount_wei = self.w3.to_wei(amount, 'ether')
            
            self.log(wallet_name, f"Swapping {amount} USDC to WUSDC", "PROCESS")
            
            balance_wei = self.w3.eth.get_balance(address)
            balance = self.w3.from_wei(balance_wei, 'ether')
            
            if balance < amount:
                self.log(wallet_name, f"Insufficient balance!", "ERROR")
                return {'success': False, 'error': 'Insufficient balance'}
            
            swap_router = self.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACTS['SWAP_ROUTER']),
                abi=SWAP_ROUTER_ABI
            )
            
            route = [
                "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                CONTRACTS['WUSDC'],
                CONTRACTS['WUSDC'],
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000"
            ]
            
            swap_params = [
                [0, 0, 8, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ]
            
            min_out_amount = int(amount_wei * 0.995)
            
            tx = swap_router.functions.exchange(
                route,
                swap_params,
                amount_wei,
                min_out_amount
            ).build_transaction({
                'from': address,
                'value': amount_wei,
                'nonce': self.w3.eth.get_transaction_count(address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': CHAIN_ID
            })
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            self.log(wallet_name, f"Swap TX: {tx_hash_hex}", "TX")
            self.log(wallet_name, f"Explorer: {EXPLORER_URL}/tx/0x{tx_hash_hex}", "INFO")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                self.log(wallet_name, f"Swap successful!", "SUCCESS")
                return {'success': True, 'hash': tx_hash_hex}
            else:
                self.log(wallet_name, "Swap failed!", "ERROR")
                return {'success': False, 'error': 'Transaction failed'}
                
        except Exception as e:
            self.log(wallet_name, f"Swap failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    async def mint_nft_collection(self, account_data, nft_data):
        """Mint NFT from collections"""
        try:
            account = account_data['account']
            wallet_name = account_data['wallet_name']
            address = account_data['address']
            
            self.log(wallet_name, f"Minting {nft_data['name']} NFT", "PROCESS")
            
            await asyncio.sleep(1)
            
            if nft_data['type'] == 'mint':
                nft_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(nft_data['address']),
                    abi=NFT_ABI
                )
                
                nonce = self.w3.eth.get_transaction_count(address, 'pending')
                
                tx = nft_contract.functions.mint(1).build_transaction({
                    'from': address,
                    'nonce': nonce,
                    'gas': 250000,
                    'gasPrice': int(self.w3.eth.gas_price * 1.2),
                    'chainId': CHAIN_ID
                })
            else:
                nft_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(nft_data['address']),
                    abi=NFT_CLAIM_ABI
                )
                
                price_wei = self.w3.to_wei(nft_data['price'], 'ether')
                
                nonce = self.w3.eth.get_transaction_count(address, 'pending')
                
                tx = nft_contract.functions.claim(
                    address,
                    1,
                    "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    price_wei,
                    ([], 115792089237316195423570985008687907853269984665640564039457584007913129639935, 0, "0x0000000000000000000000000000000000000000"),
                    b''
                ).build_transaction({
                    'from': address,
                    'value': price_wei,
                    'nonce': nonce,
                    'gas': 350000,
                    'gasPrice': int(self.w3.eth.gas_price * 1.2),
                    'chainId': CHAIN_ID
                })
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            price_text = f"{nft_data['price']} USDC" if nft_data['price'] > 0 else "FREE"
            self.log(wallet_name, f"Price: {price_text}", "INFO")
            self.log(wallet_name, f"TX Hash: {tx_hash_hex}", "TX")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                self.log(wallet_name, f"{nft_data['name']} minted successfully!", "SUCCESS")
                return {'success': True, 'hash': tx_hash_hex}
            else:
                self.log(wallet_name, f"{nft_data['name']} mint failed!", "ERROR")
                return {'success': False, 'error': 'Transaction reverted'}
                
        except Exception as e:
            self.log(wallet_name, f"Mint failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    async def mint_all_nfts(self, account_data):
        """Mint all NFT collections"""
        wallet_name = account_data['wallet_name']
        successful_mints = 0
        failed_mints = 0
        
        print(f"\n{Fore.CYAN + Style.BRIGHT}Minting all NFT collections for {wallet_name}...{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}Transactions per NFT: {self.tx_count}{Style.RESET_ALL}")
        
        for i, nft_data in enumerate(NFT_COLLECTIONS, 1):
            print(f"\n{Fore.YELLOW + Style.BRIGHT}[{i}/{len(NFT_COLLECTIONS)}] {nft_data['name']}...{Style.RESET_ALL}")
            
            for tx_num in range(self.tx_count):
                if self.tx_count > 1:
                    print(f"{Fore.WHITE + Style.BRIGHT}Transaction {tx_num + 1}/{self.tx_count}{Style.RESET_ALL}")
                
                if tx_num > 0:
                    await asyncio.sleep(3)
                
                result = await self.mint_nft_collection(account_data, nft_data)
                
                if result['success']:
                    successful_mints += 1
                else:
                    failed_mints += 1
            
            if i < len(NFT_COLLECTIONS):
                await asyncio.sleep(3)
        
        print(f"\n{Fore.GREEN + Style.BRIGHT}Completed: {successful_mints} successful, {failed_mints} failed{Style.RESET_ALL}")
        return successful_mints, failed_mints

    async def on_chain_gm(self, account_data):
        """Perform On-Chain GM"""
        try:
            account = account_data['account']
            wallet_name = account_data['wallet_name']
            address = account_data['address']
            
            gm_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACTS['ON_CHAIN_GM']),
                abi=ON_CHAIN_GM_ABI
            )
            
            self.log(wallet_name, f"Performing On-Chain GM", "PROCESS")
            
            try:
                next_gm_time = gm_contract.functions.timeUntilNextGM(address).call()
                if next_gm_time > 0:
                    hours = next_gm_time // 3600
                    minutes = (next_gm_time % 3600) // 60
                    self.log(wallet_name, f"Next GM available in {hours}h {minutes}m", "WARNING")
                    return {'success': False, 'error': 'GM not available yet'}
            except:
                pass
            
            try:
                gm_fee = gm_contract.functions.GM_FEE().call()
                gm_fee_ether = self.w3.from_wei(gm_fee, 'ether')
                self.log(wallet_name, f"GM Fee: {gm_fee_ether} USDC", "INFO")
            except:
                gm_fee = 0
            
            tx = gm_contract.functions.onChainGM("0x0000000000000000000000000000000000000000").build_transaction({
                'from': address,
                'value': gm_fee,
                'nonce': self.w3.eth.get_transaction_count(address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': CHAIN_ID
            })
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            self.log(wallet_name, f"TX Hash: {tx_hash_hex}", "TX")
            self.log(wallet_name, f"Explorer: {EXPLORER_URL}/tx/0x{tx_hash_hex}", "INFO")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                self.log(wallet_name, f"On-Chain GM successful!", "SUCCESS")
                return {'success': True, 'hash': tx_hash_hex}
            else:
                self.log(wallet_name, "On-Chain GM failed!", "ERROR")
                return {'success': False, 'error': 'Transaction failed'}
            
        except Exception as e:
            self.log(wallet_name, f"On-Chain GM failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    async def deploy_token(self, account_data, name, symbol, supply):
        """Deploy token"""
        try:
            account = account_data['account']
            wallet_name = account_data['wallet_name']
            address = account_data['address']
            
            if not TOKEN_BYTECODE:
                self.log(wallet_name, "Token bytecode not configured.", "ERROR")
                return {'success': False, 'error': 'No bytecode'}
            
            self.log(wallet_name, f"Deploying token: {name} ({symbol})", "PROCESS")
            
            supply_wei = self.w3.to_wei(supply, 'ether')
            encoded_params = self.w3.codec.encode(
                ['string', 'string', 'uint256'],
                [name, symbol, supply_wei]
            )
            
            deploy_data = TOKEN_BYTECODE + encoded_params.hex()
            
            creation_fee = int('0x21a6bbdb5000', 16)
            
            self.log(wallet_name, f"Token: {name} ({symbol}) | Supply: {supply}", "INFO")
            
            tx = {
                'from': address,
                'data': deploy_data,
                'value': creation_fee,
                'nonce': self.w3.eth.get_transaction_count(address),
                'gas': 1500000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': CHAIN_ID
            }
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            self.log(wallet_name, f"TX Hash: {tx_hash_hex}", "TX")
            self.log(wallet_name, f"Explorer: {EXPLORER_URL}/tx/0x{tx_hash_hex}", "INFO")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                token_address = receipt['contractAddress']
                self.log(wallet_name, f"Token deployed at: {token_address}", "SUCCESS")
                return {'success': True, 'address': token_address, 'hash': tx_hash_hex}
            else:
                self.log(wallet_name, "Token deployment failed!", "ERROR")
                return {'success': False, 'error': 'Deployment failed'}
            
        except Exception as e:
            self.log(wallet_name, f"Deploy failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    async def register_name(self, account_data, name):
        """Register name"""
        try:
            account = account_data['account']
            wallet_name = account_data['wallet_name']
            address = account_data['address']
            
            registry = self.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACTS['NAME_REGISTRY']),
                abi=NAME_REGISTRY_ABI
            )
            
            self.log(wallet_name, f"Registering name: {name}", "PROCESS")
            
            tx = registry.functions.register(
                name,
                '0x0000000000000000000000000000000000000000'
            ).build_transaction({
                'from': address,
                'value': self.w3.to_wei(1, 'ether'),
                'nonce': self.w3.eth.get_transaction_count(address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': CHAIN_ID
            })
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            self.log(wallet_name, f"TX Hash: {tx_hash_hex}", "TX")
            self.log(wallet_name, f"Explorer: {EXPLORER_URL}/tx/0x{tx_hash_hex}", "INFO")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                self.log(wallet_name, f"Name registered successfully!", "SUCCESS")
                return {'success': True, 'hash': tx_hash_hex}
            else:
                self.log(wallet_name, "Name registration failed!", "ERROR")
                return {'success': False, 'error': 'Registration failed'}
            
        except Exception as e:
            self.log(wallet_name, f"Register failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    async def deposit_native_new(self, account_data):
        """Native Deposit (New Option 8)"""
        try:
            account = account_data['account']
            wallet_name = account_data['wallet_name']
            address = account_data['address']
            
            target_contract = Web3.to_checksum_address("0xa3d9Fbd0edB10327ECB73D2C72622E505dF468a2")
            
            self.log(wallet_name, f"Executing Native Deposit to {target_contract}", "PROCESS")
            
            tx = {
                'from': address,
                'to': target_contract,
                'data': '0x775c300c',
                'value': self.w3.to_wei(1, 'ether'),
                'nonce': self.w3.eth.get_transaction_count(address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': CHAIN_ID
            }
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            self.log(wallet_name, f"TX Hash: {tx_hash_hex}", "TX")
            self.log(wallet_name, f"Explorer: {EXPLORER_URL}/tx/0x{tx_hash_hex}", "INFO")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                self.log(wallet_name, f"Native Deposit successful!", "SUCCESS")
                return {'success': True, 'hash': tx_hash_hex}
            else:
                self.log(wallet_name, "Native Deposit failed!", "ERROR")
                return {'success': False, 'error': 'Transaction failed'}
                
        except Exception as e:
            self.log(wallet_name, f"Native Deposit failed: {str(e)}", "ERROR")
            return {'success': False, 'error': str(e)}

    async def auto_all(self):
        """Execute all operations automatically"""
        try:
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== AUTO ALL MODE ==={Style.RESET_ALL}")
            print(f"{Fore.CYAN + Style.BRIGHT}Executing all operations for each wallet{Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Operations Order:{Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}1. Mint All NFTs (9 collections x {self.tx_count} txns){Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}2. Swap USDC to WUSDC ({self.tx_count} txns){Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}3. Deposit & Stake ({self.tx_count} txns){Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}4. Add Liquidity ({self.tx_count} txns){Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}5. Deploy Token ({self.tx_count} txns){Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}6. Register Name ({self.tx_count} txns){Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}7. On-Chain GM ({self.tx_count} txns){Style.RESET_ALL}\n")
            
            for account_data in self.accounts:
                wallet_name = account_data['wallet_name']
                print(f"\n{Fore.MAGENTA + Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW + Style.BRIGHT}Processing Wallet: {wallet_name}{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA + Style.BRIGHT}{'='*60}{Style.RESET_ALL}\n")
                
                print(f"{Fore.CYAN + Style.BRIGHT}[1/7] Minting All NFT Collections...{Style.RESET_ALL}")
                await self.mint_all_nfts(account_data)
                await asyncio.sleep(3)
                
                print(f"\n{Fore.CYAN + Style.BRIGHT}[2/7] Swapping USDC to WUSDC...{Style.RESET_ALL}")
                for i in range(self.tx_count):
                    if self.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Swap {i+1}/{self.tx_count}{Style.RESET_ALL}")
                    await self.swap_usdc_to_wusdc(account_data)
                    if i < self.tx_count - 1:
                        await asyncio.sleep(2)
                await asyncio.sleep(3)
                
                print(f"\n{Fore.CYAN + Style.BRIGHT}[3/7] Depositing and Staking...{Style.RESET_ALL}")
                for i in range(self.tx_count):
                    if self.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Deposit & Stake {i+1}/{self.tx_count}{Style.RESET_ALL}")
                    await self.deposit_and_stake(account_data)
                    if i < self.tx_count - 1:
                        await asyncio.sleep(2)
                await asyncio.sleep(3)
                
                print(f"\n{Fore.CYAN + Style.BRIGHT}[4/7] Adding Liquidity...{Style.RESET_ALL}")
                for i in range(self.tx_count):
                    if self.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Liquidity {i+1}/{self.tx_count}{Style.RESET_ALL}")
                    await self.add_liquidity(account_data)
                    if i < self.tx_count - 1:
                        await asyncio.sleep(2)
                await asyncio.sleep(3)
                
                print(f"\n{Fore.CYAN + Style.BRIGHT}[5/7] Deploying Tokens...{Style.RESET_ALL}")
                if TOKEN_BYTECODE:
                    for i in range(self.tx_count):
                        if self.tx_count > 1:
                            print(f"{Fore.WHITE + Style.BRIGHT}Token {i+1}/{self.tx_count}{Style.RESET_ALL}")
                        token_name = f"Token{self.generate_random_string(6)}"
                        token_symbol = f"TK{self.generate_random_string(4).upper()}"
                        await self.deploy_token(account_data, token_name, token_symbol, 1000000)
                        if i < self.tx_count - 1:
                            await asyncio.sleep(2)
                else:
                    print(f"{Fore.YELLOW + Style.BRIGHT}Skipping - TOKEN_BYTECODE not set{Style.RESET_ALL}")
                await asyncio.sleep(3)
                
                print(f"\n{Fore.CYAN + Style.BRIGHT}[6/7] Registering Names...{Style.RESET_ALL}")
                for i in range(self.tx_count):
                    if self.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Name {i+1}/{self.tx_count}{Style.RESET_ALL}")
                    unique_name = f"arc{self.generate_random_string(8)}"
                    await self.register_name(account_data, unique_name)
                    if i < self.tx_count - 1:
                        await asyncio.sleep(2)
                await asyncio.sleep(3)
                
                print(f"\n{Fore.CYAN + Style.BRIGHT}[7/7] Performing On-Chain GM...{Style.RESET_ALL}")
                for i in range(self.tx_count):
                    if self.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}GM {i+1}/{self.tx_count}{Style.RESET_ALL}")
                    await self.on_chain_gm(account_data)
                    if i < self.tx_count - 1:
                        await asyncio.sleep(2)
                
                print(f"\n{Fore.GREEN + Style.BRIGHT}Wallet {wallet_name} completed!{Style.RESET_ALL}")
                
                if account_data != self.accounts[-1]:
                    print(f"{Fore.YELLOW + Style.BRIGHT}Moving to next wallet in 5 seconds...{Style.RESET_ALL}")
                    await asyncio.sleep(5)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.GREEN + Style.BRIGHT}AUTO ALL COMPLETED SUCCESSFULLY!{Style.RESET_ALL}")
            print(f"{Fore.GREEN + Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}Auto All failed: {str(e)}{Style.RESET_ALL}")

def clear_terminal():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    """Display banner"""
    banner = f"""
{Fore.GREEN + Style.BRIGHT}  █████╗ ██████╗  ██████╗    ██████╗  ██████╗ ████████╗
{Fore.GREEN + Style.BRIGHT} ██╔══██╗██╔══██╗██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝
{Fore.GREEN + Style.BRIGHT} ███████║██████╔╝██║         ██████╔╝██║   ██║   ██║   
{Fore.GREEN + Style.BRIGHT} ██╔══██║██╔══██╗██║         ██╔══██╗██║   ██║   ██║   
{Fore.GREEN + Style.BRIGHT} ██║  ██║██║  ██║╚██████╗    ██████╔╝╚██████╔╝   ██║   
{Fore.GREEN + Style.BRIGHT} ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝    ╚═════╝  ╚═════╝    ╚═╝   

{Fore.MAGENTA + Style.BRIGHT}             ARC x TESTNET x BOT V2.1
{Fore.GREEN + Style.BRIGHT}            CREATED BY - KAZUHA VIP ONLY 
{Style.RESET_ALL}
"""
    print(banner)

def display_menu(tx_count):
    """Display main menu"""
    print(f"\n{Fore.CYAN + Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW + Style.BRIGHT}MAIN MENU{Style.RESET_ALL}")
    print(f"{Fore.WHITE + Style.BRIGHT}Current Transaction Count: {tx_count}{Style.RESET_ALL}")
    print(f"{Fore.CYAN + Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}1.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Mint NFT (All 9 Collections){Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}2.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Swap USDC to WUSDC{Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}3.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Deposit and Stake (Curve Gauge){Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}4.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Add Liquidity (Curve Pool){Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}5.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Deploy Token{Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}6.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Register Name{Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}7.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}On-Chain GM{Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}8.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Depoly GM{Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}9.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Auto All (Execute All Operations){Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}10.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Set Transaction Count{Style.RESET_ALL}")
    print(f"{Fore.GREEN + Style.BRIGHT}11.{Style.RESET_ALL} {Fore.WHITE + Style.BRIGHT}Exit{Style.RESET_ALL}")
    print(f"{Fore.CYAN + Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")

async def main():
    """Main function"""
    bot = ArcTestnetBot()
    
    running = True
    
    while running:
        clear_terminal()
        display_banner()
        
        print(f"\n{Fore.CYAN + Style.BRIGHT}Total Accounts: {len(bot.accounts)}{Style.RESET_ALL}")
        
        display_menu(bot.tx_count)
        
        choice = input(f"\n{Fore.GREEN + Style.BRIGHT}Select option (1-11): {Style.RESET_ALL}").strip()
        
        if choice == '1':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== MINT ALL NFT COLLECTIONS ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Will mint from all 9 NFT collections{Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Using TX Count: {bot.tx_count} per collection{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN + Style.BRIGHT}Processing {len(bot.accounts)} account(s)...{Style.RESET_ALL}\n")
            
            for account_data in bot.accounts:
                await bot.mint_all_nfts(account_data)
                
                if account_data != bot.accounts[-1]:
                    print(f"\n{Fore.YELLOW + Style.BRIGHT}Moving to next account in 3 seconds...{Style.RESET_ALL}")
                    await asyncio.sleep(3)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}All NFT minting completed!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '2':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== SWAP USDC TO WUSDC ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Using TX Count: {bot.tx_count}{Style.RESET_ALL}")
            use_random = input(f'{Fore.GREEN + Style.BRIGHT}Use random amounts? (y/n): {Style.RESET_ALL}').lower()
            
            if use_random != 'y':
                amount = float(input(f'{Fore.GREEN + Style.BRIGHT}Enter amount to swap (USDC): {Style.RESET_ALL}'))
            else:
                amount = None
            
            print(f"\n{Fore.CYAN + Style.BRIGHT}Processing {len(bot.accounts)} account(s)...{Style.RESET_ALL}\n")
            
            for account_data in bot.accounts:
                for i in range(bot.tx_count):
                    if bot.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Transaction {i+1}/{bot.tx_count}{Style.RESET_ALL}")
                    await bot.swap_usdc_to_wusdc(account_data, amount)
                    if i < bot.tx_count - 1:
                        await asyncio.sleep(2)
                
                if account_data != bot.accounts[-1]:
                    await asyncio.sleep(3)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}All swap transactions completed!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '3':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== DEPOSIT AND STAKE TO CURVE GAUGE ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Using TX Count: {bot.tx_count}{Style.RESET_ALL}")
            use_random = input(f'{Fore.GREEN + Style.BRIGHT}Use random amounts? (y/n): {Style.RESET_ALL}').lower()
            
            if use_random != 'y':
                usdc_amount = float(input(f'{Fore.GREEN + Style.BRIGHT}Enter USDC amount: {Style.RESET_ALL}'))
            else:
                usdc_amount = None
            
            print(f"\n{Fore.CYAN + Style.BRIGHT}Processing {len(bot.accounts)} account(s)...{Style.RESET_ALL}\n")
            
            for account_data in bot.accounts:
                for i in range(bot.tx_count):
                    if bot.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Transaction {i+1}/{bot.tx_count}{Style.RESET_ALL}")
                    await bot.deposit_and_stake(account_data, usdc_amount)
                    if i < bot.tx_count - 1:
                        await asyncio.sleep(2)
                
                if account_data != bot.accounts[-1]:
                    await asyncio.sleep(3)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}All deposit and stake transactions completed!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '4':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== ADD LIQUIDITY TO CURVE POOL ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Using TX Count: {bot.tx_count}{Style.RESET_ALL}")
            use_random = input(f'{Fore.GREEN + Style.BRIGHT}Use random amounts? (y/n): {Style.RESET_ALL}').lower()
            
            if use_random != 'y':
                usdc_amount = float(input(f'{Fore.GREEN + Style.BRIGHT}Enter USDC amount: {Style.RESET_ALL}'))
            else:
                usdc_amount = None
            
            print(f"\n{Fore.CYAN + Style.BRIGHT}Processing {len(bot.accounts)} account(s)...{Style.RESET_ALL}\n")
            
            for account_data in bot.accounts:
                for i in range(bot.tx_count):
                    if bot.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Transaction {i+1}/{bot.tx_count}{Style.RESET_ALL}")
                    await bot.add_liquidity(account_data, usdc_amount)
                    if i < bot.tx_count - 1:
                        await asyncio.sleep(2)
                
                if account_data != bot.accounts[-1]:
                    await asyncio.sleep(3)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}All liquidity transactions completed!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '5':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== DEPLOY TOKEN ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Using TX Count: {bot.tx_count}{Style.RESET_ALL}")
            
            if not TOKEN_BYTECODE:
                print(f"{Fore.RED + Style.BRIGHT}Token bytecode not configured!{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
                continue
            
            use_random = input(f'{Fore.GREEN + Style.BRIGHT}Use random names? (y/n): {Style.RESET_ALL}').lower()
            
            if use_random != 'y':
                token_name = input(f'{Fore.GREEN + Style.BRIGHT}Enter token name: {Style.RESET_ALL}')
                token_symbol = input(f'{Fore.GREEN + Style.BRIGHT}Enter token symbol: {Style.RESET_ALL}')
                supply = float(input(f'{Fore.GREEN + Style.BRIGHT}Enter token supply: {Style.RESET_ALL}'))
            
            print(f"\n{Fore.CYAN + Style.BRIGHT}Processing {len(bot.accounts)} account(s)...{Style.RESET_ALL}\n")
            
            for account_data in bot.accounts:
                for i in range(bot.tx_count):
                    if bot.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Transaction {i+1}/{bot.tx_count}{Style.RESET_ALL}")
                    
                    if use_random == 'y':
                        token_name = f"Token{bot.generate_random_string(6)}"
                        token_symbol = f"TK{bot.generate_random_string(4).upper()}"
                        supply = 1000000
                    
                    await bot.deploy_token(account_data, token_name, token_symbol, supply)
                    if i < bot.tx_count - 1:
                        await asyncio.sleep(2)
                
                if account_data != bot.accounts[-1]:
                    await asyncio.sleep(3)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}All token deployments completed!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '6':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== REGISTER NAME ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Using TX Count: {bot.tx_count}{Style.RESET_ALL}")
            use_random = input(f'{Fore.GREEN + Style.BRIGHT}Use random names? (y/n): {Style.RESET_ALL}').lower()
            
            if use_random != 'y':
                name = input(f'{Fore.GREEN + Style.BRIGHT}Enter name to register: {Style.RESET_ALL}')
            
            print(f"\n{Fore.CYAN + Style.BRIGHT}Processing {len(bot.accounts)} account(s)...{Style.RESET_ALL}\n")
            
            for account_data in bot.accounts:
                for i in range(bot.tx_count):
                    if bot.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Transaction {i+1}/{bot.tx_count}{Style.RESET_ALL}")
                    
                    if use_random == 'y':
                        name = f"arc{bot.generate_random_string(8)}"
                    
                    await bot.register_name(account_data, name)
                    if i < bot.tx_count - 1:
                        await asyncio.sleep(2)
                
                if account_data != bot.accounts[-1]:
                    await asyncio.sleep(3)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}All name registrations completed!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '7':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== ON-CHAIN GM ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Using TX Count: {bot.tx_count}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN + Style.BRIGHT}Processing {len(bot.accounts)} account(s)...{Style.RESET_ALL}\n")
            
            for account_data in bot.accounts:
                for i in range(bot.tx_count):
                    if bot.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Transaction {i+1}/{bot.tx_count}{Style.RESET_ALL}")
                    await bot.on_chain_gm(account_data)
                    if i < bot.tx_count - 1:
                        await asyncio.sleep(2)
                
                if account_data != bot.accounts[-1]:
                    await asyncio.sleep(3)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}All GM transactions completed!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '8':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== NATIVE DEPOSIT (NEW) ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Using TX Count: {bot.tx_count}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN + Style.BRIGHT}Processing {len(bot.accounts)} account(s)...{Style.RESET_ALL}\n")
            
            for account_data in bot.accounts:
                for i in range(bot.tx_count):
                    if bot.tx_count > 1:
                        print(f"{Fore.WHITE + Style.BRIGHT}Transaction {i+1}/{bot.tx_count}{Style.RESET_ALL}")
                    await bot.deposit_native_new(account_data)
                    if i < bot.tx_count - 1:
                        await asyncio.sleep(2)
                
                if account_data != bot.accounts[-1]:
                    await asyncio.sleep(3)
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}All native deposit transactions completed!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")

        elif choice == '9':
            confirm = input(f'\n{Fore.YELLOW + Style.BRIGHT}Execute all operations for all wallets? (y/n): {Style.RESET_ALL}').lower()
            if confirm == 'y':
                await bot.auto_all()
                input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '10':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}=== SET TRANSACTION COUNT ==={Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}Current TX Count: {bot.tx_count}{Style.RESET_ALL}")
            
            try:
                new_count = int(input(f'{Fore.GREEN + Style.BRIGHT}Enter new transaction count (1-100): {Style.RESET_ALL}'))
                if 1 <= new_count <= 100:
                    bot.tx_count = new_count
                    
                    # Save to config file
                    config = {'tx_count': new_count}
                    with open('config.json', 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    print(f"{Fore.GREEN + Style.BRIGHT}Transaction count updated to {new_count}!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid count! Must be between 1-100{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input!{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")
        
        elif choice == '11':
            print(f"\n{Fore.YELLOW + Style.BRIGHT}Thanks for using Arc Testnet Bot!{Style.RESET_ALL}")
            print(f"{Fore.GREEN + Style.BRIGHT}Goodbye!{Style.RESET_ALL}")
            running = False
        
        else:
            print(f"\n{Fore.RED + Style.BRIGHT}Invalid option! Please select 1-11{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to continue...{Style.RESET_ALL}")

def run():
    """Entry point"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW + Style.BRIGHT}Bot stopped by user{Style.RESET_ALL}")
        print(f"{Fore.GREEN + Style.BRIGHT}Goodbye!{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED + Style.BRIGHT}Critical error: {str(e)}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW + Style.BRIGHT}Press Enter to exit...{Style.RESET_ALL}")

if __name__ == "__main__":
    run()
