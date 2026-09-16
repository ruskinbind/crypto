const colors = require("colors");

class Logger {
  constructor({ prefix = "BOT", accountIndex = 0, getProxyIP = () => null, useProxy = false, address = "" } = {}) {
    this.prefix = prefix;
    this.accountIndex = accountIndex;
    this.getProxyIP = getProxyIP;
    this.useProxy = useProxy;
    this.address = address;
  }

  log(msg, type = "info") {
    const accountPrefix = `[${this.prefix}][${this.accountIndex + 1}]${this.address ? `[${this.address}]` : ""}`;
    const ip = this.getProxyIP();
    const ipPrefix = ip ? `[${ip}]` : this.useProxy ? "[Unknown IP]" : "[Local IP]";
    const line = `${accountPrefix}${ipPrefix} ${msg}`;
    switch (type) {
      case "success":
        console.log(line.green);
        break;
      case "error":
        console.log(line.red);
        break;
      case "warning":
        console.log(line.yellow);
        break;
      case "custom":
        console.log(line.magenta);
        break;
      default:
        console.log(line.blue);
    }
  }
}

module.exports = Logger;
