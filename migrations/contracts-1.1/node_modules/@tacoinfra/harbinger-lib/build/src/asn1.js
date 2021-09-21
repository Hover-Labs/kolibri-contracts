"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ASN1 = require('@lapo/asn1js');
ASN1.prototype.toHexStringContent = function () {
    const hex = this.stream.hexDump(this.posContent(), this.posEnd(), true);
    return hex.startsWith('00') ? hex.slice(2) : hex;
};
exports.default = ASN1;
//# sourceMappingURL=asn1.js.map