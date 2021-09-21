import { KeyStore, Signer } from '../../../types/ExternalInterfaces';
export declare namespace StakerDAOTokenHelper {
    function verifyDestination(server: string, address: string): Promise<boolean>;
    function verifyScript(script: string): boolean;
    function getAccountBalance(server: string, mapid: number, account: string): Promise<number>;
    function getSimpleStorage(server: string, address: string): Promise<{
        mapid: number;
        council: string[];
        stage: number;
        phase: number;
        supply: number;
        paused: boolean;
    }>;
    function transferBalance(server: string, signer: Signer, keystore: KeyStore, contract: string, fee: number, source: string, destination: string, amount: number, gas: number, freight: number): Promise<string>;
}
