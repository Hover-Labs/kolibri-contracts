
import smartpy as sp

def movekUSD(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("KT1FHE7qiuZDJejQrK3qikbzjj9r8X7FqGkg"),
        "sendTokens"
    ).open_some()

    param = (sp.nat(12345), sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"))

    sp.result(
        [
            sp.transfer_operation(
                param,
                sp.mutez(0),
                contractHandle
            )
        ]
    )  

def movekDAO(unit):
    sp.set_type(unit, sp.TUnit)

    contractHandle = sp.contract(
        sp.TAddress,
        sp.address("KT1LHbDjwPmVnPRY9iWr5DYABTPQgEja7Vuc"),
        "send"
    ).open_some()

    param = (sp.nat(67890), sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"))

    sp.result(
        [
            sp.transfer_operation(
                param,
                sp.mutez(0),
                contractHandle
            )
        ]
    )

def governanceLambda(unit):
    sp.set_type(unit, sp.TUnit)

    devFundBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("KT1FZKgkpZCuuVgtwihryUeN8BC3du36eM2i"),
        "runLambda"
    ).open_some()

    communityFundBreakGlassLambda = sp.contract(
        sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)),
        sp.address("KT1DfZhyFqaa1EXAxv3A5TrY7QRQurtPaxcL"),
        "runLambda"
    ).open_some()    

    sp.result(
        [
            sp.transfer_operation(movekDAO, sp.mutez(0), communityFundBreakGlassLambda),
            sp.transfer_operation(movekUSD, sp.mutez(0), devFundBreakGlassLambda),
        ]
    )

sp.add_expression_compilation_target("operation", governanceLambda)
