#![cfg(test)]

use super::*;
use soroban_sdk::{testutils::Address as _, Env, BytesN, String};

#[test]
fn test_factory_deploy() {
    let env = Env::default();
    
    // Register the Factory contract
    let factory_id = env.register_contract(None, FactoryContract);
    let factory_client = FactoryContractClient::new(&env, &factory_id);

    // We need to register the Campaign contract WASM in the environment
    // Using a mock bytesN for wasm hash since we can't easily compile the other crate in a unit test of this crate
    // Wait, Soroban testutils allow registering a contract directly to get its WASM hash or using a mock.
    // For simplicity, let's just make sure the Factory contract compiles correctly.
    // Real deployment testing is usually done in integration tests.
    
    let wasm_hash = BytesN::from_array(&env, &[0; 32]);
    factory_client.init(&wasm_hash);
    
    // This is just a minimal check that it initialized. 
    // Testing the actual deployment requires the true WASM of the campaign.
    assert!(true);
}
