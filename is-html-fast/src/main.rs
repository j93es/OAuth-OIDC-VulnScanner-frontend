use std::fs::File;
use std::io::Write;
use std::time::Duration;

use futures::stream::{FuturesUnordered, StreamExt};
use reqwest::Client;
use tokio::fs;
use tokio::io::AsyncBufReadExt;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let file = fs::File::open("domains.txt").await?;
    let reader = tokio::io::BufReader::new(file);
    let mut lines = reader.lines();

    let client = Client::builder()
        .timeout(Duration::from_secs(5))
        .build()?;

    let mut tasks = FuturesUnordered::new();

    while let Some(line) = lines.next_line().await? {
        let client = client.clone();
        let domain = line.clone();
        tasks.push(tokio::spawn(async move {
            let url = format!("https://{}", domain);
            let resp = client.get(&url).send().await;

            match resp {
                Ok(resp) => {
                    if let Some(content_type) = resp.headers().get(reqwest::header::CONTENT_TYPE) {
                        if let Ok(content_type_str) = content_type.to_str() {
                            if content_type_str.starts_with("text/html") {
                                println!("✅ HTML: {}", domain);
                                return Some(domain);
                            } else {
                                println!("❌ Not HTML: {} ({})", domain, content_type_str);
                            }
                        }
                    } else {
                        println!("❌ No Content-Type: {}", domain);
                    }
                }
                Err(_) => {
                    println!("⚠️ Failed to connect: {}", domain);
                }
            }

            None
        }));
    }

    let mut results = Vec::new();
    while let Some(res) = tasks.next().await {
        if let Ok(Some(domain)) = res {
            results.push(domain);
        }
    }

    // 📝 한 번에 출력
    let mut output = File::create("domains-filtered.txt")?;
    for domain in results {
        writeln!(output, "{}", domain)?;
    }

    Ok(())
}
