import * as config from '../config'
import { TezosToolkit } from '@taquito/taquito'
import { fetchFromCache } from '../utils'

const main = async () => {
    console.log("Loading results of deploy from cache")
    const newMinterContractAddress = (await fetchFromCache('new-minter')).contractAddress
    const breakGlassContractAddress = (await fetchFromCache('new-minter-break-glass')).contractAddress

    console.log("Validating storage from old minter copied correctly")
    const tezos: TezosToolkit = await config.getTezos()

    const oldMinterContract = await tezos.contract.at(config.coreContracts.MINTER!)
    const oldMinterStorage: any = await oldMinterContract.storage()

    const newMinterContract = await tezos.contract.at(newMinterContractAddress)
    const newMinterStorage: any = await newMinterContract.storage()

    if (
        !oldMinterStorage.collateralizationPercentage.isEqualTo(newMinterStorage.collateralizationPercentage) ||
        !oldMinterStorage.interestIndex.isEqualTo(newMinterStorage.interestIndex) ||
        !oldMinterStorage.liquidationFeePercent.isEqualTo(newMinterStorage.liquidationFeePercent) ||
        !oldMinterStorage.stabilityDevFundSplit.isEqualTo(newMinterStorage.devFundSplit) ||
        !oldMinterStorage.stabilityFee.isEqualTo(newMinterStorage.stabilityFee) ||
        oldMinterStorage.lastInterestIndexUpdateTime !== newMinterStorage.lastInterestIndexUpdateTime ||
        oldMinterStorage.developerFundContractAddress !== newMinterStorage.developerFundContractAddress ||
        oldMinterStorage.ovenProxyContractAddress !== newMinterStorage.ovenProxyContractAddress ||
        oldMinterStorage.stabilityFundContractAddress !== newMinterStorage.stabilityFundContractAddress ||
        oldMinterStorage.tokenContractAddress !== newMinterStorage.tokenContractAddress
    ) {

        throw new Error("Storage did not copy correctly!")
    }
    console.log("   > Validated")
    console.log("")

    console.log("Validating new values in Minter are as expected")
    if (
        newMinterStorage.governorContractAddress !== breakGlassContractAddress ||
        newMinterStorage.liquidityPoolContractAddress !== config.coreContracts.LIQUIDITY_POOL ||
        !newMinterStorage.privateOwnerLiquidationThreshold.isEqualTo(config.PRIVATE_OWNER_LIQUIDATION_THRESHOLD)
    ) {
        throw new Error("New values in minter storage are not set correctly!")
    }
    console.log("   > Validated")
    console.log("")

    console.log("Validating Break Glass Storage")
    const breakGlassContract = await tezos.contract.at(breakGlassContractAddress)
    const breakGlassStorage: any = await breakGlassContract.storage()
    if (
        breakGlassStorage.daoAddress !== config.coreContracts.DAO,
        breakGlassStorage.multisigAddress !== config.coreContracts.BREAK_GLASS_MULTISIG,
        breakGlassStorage.targetAddress !== newMinterContractAddress
    ) {
        throw new Error("Break glass is misconfigured!")
    }
    console.log("   > Validated")
    console.log("")

    console.log("All tests pass!")
}

main()