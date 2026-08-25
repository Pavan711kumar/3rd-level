#![no_std]

use soroban_sdk::{
    contract, contractimpl, contracttype, symbol_short, Address, Env, String,
};

#[contract]
pub struct CampaignContract;

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum DataKey {
    Creator,
    Goal,
    Deadline,
    State,
    Pledge(Address),
    Balance,
    Name,
}

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CampaignState {
    Active,
    Successful,
    Failed,
}

#[contractimpl]
impl CampaignContract {
    pub fn init(
        env: Env,
        creator: Address,
        name: String,
        goal: i128,
        deadline: u64,
    ) {
        if env.storage().instance().has(&DataKey::Creator) {
            panic!("already initialized");
        }
        
        env.storage().instance().set(&DataKey::Creator, &creator);
        env.storage().instance().set(&DataKey::Name, &name);
        env.storage().instance().set(&DataKey::Goal, &goal);
        env.storage().instance().set(&DataKey::Deadline, &deadline);
        env.storage().instance().set(&DataKey::State, &CampaignState::Active);
        env.storage().instance().set(&DataKey::Balance, &0i128);
    }

    pub fn pledge(env: Env, user: Address, amount: i128) {
        user.require_auth();
        
        let state: CampaignState = env.storage().instance().get(&DataKey::State).unwrap();
        if state != CampaignState::Active {
            panic!("campaign is not active");
        }
        
        let deadline: u64 = env.storage().instance().get(&DataKey::Deadline).unwrap();
        if env.ledger().timestamp() > deadline {
            env.storage().instance().set(&DataKey::State, &CampaignState::Failed);
            panic!("deadline has passed");
        }
        
        if amount <= 0 {
            panic!("amount must be positive");
        }

        // Normally we would transfer XLM here using the token contract.
        // For simplicity, we just track the ledger in storage in this demo.
        let mut user_pledge: i128 = env.storage().instance().get(&DataKey::Pledge(user.clone())).unwrap_or(0);
        user_pledge += amount;
        env.storage().instance().set(&DataKey::Pledge(user.clone()), &user_pledge);
        
        let mut balance: i128 = env.storage().instance().get(&DataKey::Balance).unwrap();
        balance += amount;
        env.storage().instance().set(&DataKey::Balance, &balance);

        let goal: i128 = env.storage().instance().get(&DataKey::Goal).unwrap();
        if balance >= goal {
            env.storage().instance().set(&DataKey::State, &CampaignState::Successful);
        }
        
        env.events().publish((symbol_short!("pledged"), user), amount);
    }

    pub fn get_state(env: Env) -> CampaignState {
        env.storage().instance().get(&DataKey::State).unwrap_or(CampaignState::Active)
    }
    
    pub fn get_balance(env: Env) -> i128 {
        env.storage().instance().get(&DataKey::Balance).unwrap_or(0)
    }
}

#[cfg(test)]
mod test;
