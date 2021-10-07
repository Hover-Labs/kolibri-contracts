import fs = require('fs')
import childProcess = require('child_process')

/**
 * Compile an operation to a michelson lambda.
 *
 * This relies on having SmartPy installed and likely only works on OSX. Sorry!
 */
export const compileBreakGlassOperation = (
    targetContract: string,
    targetEntrypoint: string,
    targetArgs: string,
    targetArgType: string,
    targetBreakGlass: string
): string => {
    // A simple program that executes the lambda.
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
`
    return compileLambda(program)
}

export const compileLambda = (program: string) => {
    // Make a directory and write the program to it.
    const dirName = `./.tmp-break-glass-compilation`
    const fileName = `${dirName}/operation.py`
    fs.mkdirSync(dirName)
    fs.writeFileSync(fileName, program)

    // Compile the operation.
    childProcess.execSync(
        `~/smartpy-cli/SmartPy.sh compile ${fileName} ${dirName}`,
    )

    // Read the operation back into memory.
    const outputFile = `${dirName}/operation/step_000_expression.tz`
    const compiled = fs.readFileSync(outputFile).toString()

    // Cleanup files
    fs.rmdirSync(dirName, { recursive: true })

    return compiled
}

// If called directly
if (require.main === module) {
    (async () => {
        console.log(await compileBreakGlassOperation(
            'KT1FcUbcVS9ndvwWCftAYApmWJEHA9BpohpH',
            'revoke',
            'sp.nat(100000000000000)',
            'sp.TNat',
            'KT1FcUbcVS9ndvwWCftAYApmWJEHA9BpohpH'
        ))
    })()
}
