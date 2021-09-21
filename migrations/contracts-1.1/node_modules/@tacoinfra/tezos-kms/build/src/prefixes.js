"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const prefix = {
    secp256k1PublicKey: new Uint8Array([3, 254, 226, 86]),
    secp256k1PublicKeyHash: new Uint8Array([6, 161, 161]),
    ed25519SecretKey: new Uint8Array([43, 246, 78, 7]),
    smartContractAddress: new Uint8Array([2, 90, 121]),
    secp256k1signature: new Uint8Array([13, 115, 101, 19, 63]),
};
exports.default = prefix;
//# sourceMappingURL=prefixes.js.map