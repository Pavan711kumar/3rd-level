use axum::{
    extract::{Path, Query},
    http::{HeaderValue, Method, StatusCode},
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;

#[tokio::main]
async fn main() {
    // Set up CORS
    let cors = CorsLayer::new()
        .allow_origin("http://localhost:5173".parse::<HeaderValue>().unwrap())
        .allow_methods([Method::GET, Method::POST])
        .allow_headers([axum::http::header::CONTENT_TYPE]);

    let app = Router::new()
        .route("/api/price", get(get_xlm_price))
        .route("/api/faucet", post(fund_account))
        .route("/api/transactions/:address", get(get_transactions))
        .layer(cors);

    let addr = SocketAddr::from(([127, 0, 0, 1], 8080));
    println!("Stellar Backend API listening on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

#[derive(Serialize)]
struct PriceResponse {
    xlm_usd: f64,
    source: String,
}

async fn get_xlm_price() -> impl IntoResponse {
    let client = reqwest::Client::new();
    let url = "https://api.coingecko.com/api/v3/simple/price?ids=stellar&vs_currencies=usd";
    
    // We attempt to fetch from CoinGecko, otherwise fallback to a static price
    let result = client
        .get(url)
        .header("User-Agent", "StellarJourneyBackend/1.0")
        .send()
        .await;

    match result {
        Ok(res) => {
            if let Ok(json) = res.json::<serde_json::Value>().await {
                if let Some(price) = json["stellar"]["usd"].as_f64() {
                    return (StatusCode::OK, Json(PriceResponse {
                        xlm_usd: price,
                        source: "coingecko".to_string(),
                    }));
                }
            }
        }
        Err(_) => {}
    }

    // Fallback price if API fails/is rate limited
    (StatusCode::OK, Json(PriceResponse {
        xlm_usd: 0.102,
        source: "fallback".to_string(),
    }))
}

#[derive(Deserialize)]
struct FaucetRequest {
    address: String,
}

#[derive(Serialize)]
struct FaucetResponse {
    success: bool,
    message: String,
}

async fn fund_account(Json(payload): Json<FaucetRequest>) -> impl IntoResponse {
    if payload.address.is_empty() || !payload.address.starts_with('G') || payload.address.len() != 56 {
        return (
            StatusCode::BAD_REQUEST,
            Json(FaucetResponse {
                success: false,
                message: "Invalid Stellar public address format.".to_string(),
            }),
        );
    }

    let url = format!("https://friendbot.stellar.org/?addr={}", payload.address);
    let client = reqwest::Client::new();

    match client.get(&url).send().await {
        Ok(res) => {
            if res.status().is_success() {
                (
                    StatusCode::OK,
                    Json(FaucetResponse {
                        success: true,
                        message: format!("Successfully funded account {} with 10,000 testnet XLM.", payload.address),
                    }),
                )
            } else {
                let err_text = res.text().await.unwrap_or_default();
                (
                    StatusCode::BAD_GATEWAY,
                    Json(FaucetResponse {
                        success: false,
                        message: format!("Friendbot funding failed: {}", err_text),
                    }),
                )
            }
        }
        Err(err) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(FaucetResponse {
                success: false,
                message: format!("Network error requesting faucet funding: {}", err),
            }),
        ),
    }
}

#[derive(Serialize, Deserialize, Debug)]
struct HorizonPayment {
    id: String,
    transaction_hash: String,
    created_at: String,
    type_i: u32,
    #[serde(default)]
    from: String,
    #[serde(default)]
    to: String,
    #[serde(default)]
    amount: String,
    #[serde(default)]
    asset_type: String,
}

#[derive(Deserialize)]
struct HorizonEmbeddedPayments {
    records: Vec<HorizonPayment>,
}

#[derive(Deserialize)]
struct HorizonResponse {
    _embedded: HorizonEmbeddedPayments,
}

#[derive(Serialize)]
struct TxResponse {
    payments: Vec<HorizonPayment>,
}

async fn get_transactions(Path(address): Path<String>) -> impl IntoResponse {
    if address.is_empty() || !address.starts_with('G') || address.len() != 56 {
        return (
            StatusCode::BAD_REQUEST,
            Json(TxResponse { payments: vec![] }),
        );
    }

    let url = format!("https://horizon-testnet.stellar.org/accounts/{}/payments?limit=10&order=desc", address);
    let client = reqwest::Client::new();

    match client.get(&url).send().await {
        Ok(res) => {
            if res.status().is_success() {
                match res.json::<HorizonResponse>().await {
                    Ok(horizon_res) => {
                        (StatusCode::OK, Json(TxResponse {
                            payments: horizon_res._embedded.records,
                        }))
                    }
                    Err(err) => {
                        println!("JSON parse error: {:?}", err);
                        (StatusCode::INTERNAL_SERVER_ERROR, Json(TxResponse { payments: vec![] }))
                    }
                }
            } else {
                (StatusCode::NOT_FOUND, Json(TxResponse { payments: vec![] }))
            }
        }
        Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, Json(TxResponse { payments: vec![] })),
    }
}
