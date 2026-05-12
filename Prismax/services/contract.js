const { ethers } = require("ethers");
const settings = require("../config/config");
const { getRandomNumber, sleep } = require("../utils/utils");

const ERC20_ABI = [
  "function balanceOf(address owner) view returns (uint256)",
  "function approve(address spender, uint256 value) returns (bool)",
  "function allowance(address owner, address spender) view returns (uint256)",
  "function transfer(address to, uint amount) returns (bool)",
  "function deposit() payable returns ()",
  "function withdraw(uint256 wad) returns ()",
];
class ContractSv {
  constructor({ wallet, log, makeRequest, token, provider }) {
    this.wallet = wallet;
    this.log = log;
    this.makeRequest = makeRequest;
    this.provider = provider;
  }

  async checkBalances() {
    this.log(`Checking balances`);
    const wallet = this.wallet;
    try {
      let nativeBalance = await this.provider.getBalance(wallet.address);
      nativeBalance = parseFloat(ethers.formatUnits(nativeBalance, 18)).toFixed(6);

      this.log(`ETH: ${nativeBalance}`, "custom");
    } catch (e) {
      this.log(`ERR Failed to check balances.: ${e.message}`, "warning");
    }
  }
}

module.exports = ContractSv;
