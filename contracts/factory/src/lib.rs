#![no_std]

use soroban_sdk::{contract, contractimpl, contracttype, Address, BytesN, Env, String};
use campaign::CampaignContractClient;

#[contract]
pub struct FactoryContract;

#[contracttype]
pub enum DataKey {
    WasmHash,
}

#[contractimpl]
impl FactoryContract {
    pub fn init(env: Env, wasm_hash: BytesN<32>) {
        env.storage().instance().set(&DataKey::WasmHash, &wasm_hash);
    }

    pub fn deploy_campaign(
        env: Env,
        creator: Address,
        name: String,
        goal: i128,
        deadline: u64,
        salt: BytesN<32>,
    ) -> Address {
        creator.require_auth();

        let wasm_hash: BytesN<32> = env.storage().instance().get(&DataKey::WasmHash).unwrap();
        
        // Deploy the campaign contract
        let campaign_addr = env.deployer().with_address(creator.clone(), salt).deploy(wasm_hash);
        
        // Initialize it
        let client = CampaignContractClient::new(&env, &campaign_addr);
        client.init(&creator, &name, &goal, &deadline);

        campaign_addr
    }
}

#[cfg(test)]
mod test;
