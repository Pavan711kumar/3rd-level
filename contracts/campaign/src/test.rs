#![cfg(test)]

use super::*;
use soroban_sdk::{testutils::Address as _, Env, String};

#[test]
fn test_campaign_init_and_pledge() {
    let env = Env::default();
    let contract_id = env.register_contract(None, CampaignContract);
    let client = CampaignContractClient::new(&env, &contract_id);

    let creator = Address::generate(&env);
    let user1 = Address::generate(&env);
    
    // Init the contract
    let name = String::from_str(&env, "Save the Trees");
    let goal: i128 = 1000;
    let deadline: u64 = env.ledger().timestamp() + 1000;
    
    client.init(&creator, &name, &goal, &deadline);
    assert_eq!(client.get_state(), CampaignState::Active);
    assert_eq!(client.get_balance(), 0);

    // Pledge funds
    env.mock_all_auths();
    client.pledge(&user1, &500);
    assert_eq!(client.get_balance(), 500);
    assert_eq!(client.get_state(), CampaignState::Active);
    
    // Reach the goal
    client.pledge(&user1, &500);
    assert_eq!(client.get_balance(), 1000);
    assert_eq!(client.get_state(), CampaignState::Successful);
}
