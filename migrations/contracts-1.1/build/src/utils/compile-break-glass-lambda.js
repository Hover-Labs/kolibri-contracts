"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.compileLambda = exports.compileBreakGlassOperation = void 0;
const fs = require("fs");
const childProcess = require("child_process");
const compileBreakGlassOperation = (targetContract, targetEntrypoint, targetArgs, targetArgType, targetBreakGlass) => {
    const program = `
import smartpy as sp

def operation(self):
  arg = ${targetArgs}
  transfer_operation = sp.transfer_operation(
    arg,
    sp.mutez(0), 
    sp.contract(${targetArgType}, sp.address("${targetContract}"), "${targetEntrypoint}"
  ).open_some())

  operation_list = [ transfer_operation ]

  sp.result(operation_list)

def breakGlassOperation(self):
  breakGlassHandle = sp.contract(sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)), sp.address("${targetBreakGlass}"), "runLambda").open_some()
  sp.result([sp.transfer_operation(operation, sp.mutez(0), breakGlassHandle)])  

sp.add_expression_compilation_target("operation", breakGlassOperation)
`;
    return (0, exports.compileLambda)(program);
};
exports.compileBreakGlassOperation = compileBreakGlassOperation;
const compileLambda = (program) => {
    const dirName = `./.tmp-break-glass-compilation`;
    const fileName = `${dirName}/operation.py`;
    fs.mkdirSync(dirName);
    fs.writeFileSync(fileName, program);
    childProcess.execSync(`~/smartpy-cli/SmartPy.sh compile ${fileName} ${dirName}`);
    const outputFile = `${dirName}/operation/step_000_expression.tz`;
    const compiled = fs.readFileSync(outputFile).toString();
    fs.rmdirSync(dirName, { recursive: true });
    return compiled;
};
exports.compileLambda = compileLambda;
if (require.main === module) {
    (async () => {
        console.log(await (0, exports.compileBreakGlassOperation)('KT1FcUbcVS9ndvwWCftAYApmWJEHA9BpohpH', 'revoke', 'sp.nat(100000000000000)', 'sp.TNat', 'KT1FcUbcVS9ndvwWCftAYApmWJEHA9BpohpH'));
    })();
}
//# sourceMappingURL=compile-break-glass-lambda.js.map