import { KeyStore } from "conseiljs";
declare type CrossCheckResult = {
    keystore: KeyStore;
    contractSources: object;
};
export default function crosscheck(config: any): Promise<CrossCheckResult>;
export {};
