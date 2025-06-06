use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use std::sync::atomic::{AtomicUsize, Ordering};

use rayon::prelude::*;
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, CONTENT_TYPE, USER_AGENT, ACCEPT, ACCEPT_LANGUAGE, ACCEPT_ENCODING, CONNECTION, UPGRADE_INSECURE_REQUESTS};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let input_file = File::open("domains.txt")?;
    let reader = BufReader::new(input_file);
    let domains: Vec<String> = reader.lines().filter_map(Result::ok).collect();

    let total_count = domains.len();
    let counter = Arc::new(AtomicUsize::new(0));
    let html_count = Arc::new(AtomicUsize::new(0));
    let failed_count = Arc::new(AtomicUsize::new(0));
    let non_html_count = Arc::new(AtomicUsize::new(0));

    let output_file = OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(true)
        .open("domains-filtered.txt")?;

    let output = Arc::new(Mutex::new(output_file));

    // 브라우저 헤더 세팅
    let mut headers = HeaderMap::new();
    headers.insert(USER_AGENT, HeaderValue::from_static("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"));
    headers.insert(ACCEPT, HeaderValue::from_static("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"));
    headers.insert(ACCEPT_LANGUAGE, HeaderValue::from_static("ko,en-US;q=0.7,en;q=0.3"));
    headers.insert(ACCEPT_ENCODING, HeaderValue::from_static("gzip, deflate, br"));
    headers.insert(CONNECTION, HeaderValue::from_static("keep-alive"));
    headers.insert(UPGRADE_INSECURE_REQUESTS, HeaderValue::from_static("1"));

    let client = Arc::new(
        Client::builder()
            .timeout(Duration::from_secs(5))
            .default_headers(headers)
            .build()?,
    );

    domains.par_iter().for_each(|domain| {
        let current = counter.fetch_add(1, Ordering::SeqCst) + 1;
        let url = format!("https://{}", domain);

        let response = client.get(&url).send();

        match response {
            Ok(resp) => {
                if let Some(content_type) = resp.headers().get(CONTENT_TYPE) {
                    if let Ok(content_type_str) = content_type.to_str() {
                        if content_type_str.starts_with("text/html") {
                            if let Ok(mut file) = output.lock() {
                                writeln!(file, "{}", domain).ok();
                            }
                            html_count.fetch_add(1, Ordering::SeqCst);
                            println!("[{}/{}] ✅ HTML: {}", current, total_count, domain);
                        } else {
                            non_html_count.fetch_add(1, Ordering::SeqCst);
                            println!("[{}/{}] ❌ Not HTML: {} ({})", current, total_count, domain, content_type_str);
                        }
                    }
                } else {
                    non_html_count.fetch_add(1, Ordering::SeqCst);
                    println!("[{}/{}] ❌ No Content-Type: {}", current, total_count, domain);
                }
            }
            Err(_) => {
                failed_count.fetch_add(1, Ordering::SeqCst);
                println!("[{}/{}] ⚠️ Failed to connect: {}", current, total_count, domain);
            }
        }
    });

    // Final results
    let html_final = html_count.load(Ordering::SeqCst);
    let failed_final = failed_count.load(Ordering::SeqCst);
    let non_html_final = non_html_count.load(Ordering::SeqCst);

    println!("\n=== Final Results ===");
    println!("📊 Total domains: {}", total_count);
    println!("✅ HTML domains: {} ({:.1}%)", html_final, (html_final as f64 / total_count as f64) * 100.0);
    println!("❌ Non-HTML domains: {} ({:.1}%)", non_html_final, (non_html_final as f64 / total_count as f64) * 100.0);
    println!("⚠️ Failed connections: {} ({:.1}%)", failed_final, (failed_final as f64 / total_count as f64) * 100.0);
    println!("💾 HTML domains saved to: domains-filtered.txt");

    Ok(())
}
