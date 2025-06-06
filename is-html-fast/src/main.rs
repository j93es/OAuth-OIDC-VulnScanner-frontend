use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use rayon::prelude::*;
use reqwest::blocking::Client;
use reqwest::header::CONTENT_TYPE;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let input_file = File::open("domains.txt")?;
    let reader = BufReader::new(input_file);
    let domains: Vec<String> = reader.lines().filter_map(Result::ok).collect();

    let output_file = OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(true)
        .open("domains-filtered.txt")?;

    let output = Arc::new(Mutex::new(output_file));

    let client = Arc::new(
        Client::builder()
            .timeout(Duration::from_secs(5))
            .build()?,
    );

    domains.par_iter().for_each(|domain| {
        let url = format!("https://{}", domain);
        println!("Checking {}", url);

        let response = client.get(&url).send();

        match response {
            Ok(resp) => {
                if let Some(content_type) = resp.headers().get(CONTENT_TYPE) {
                    if let Ok(content_type_str) = content_type.to_str() {
                        if content_type_str.starts_with("text/html") {
                            if let Ok(mut file) = output.lock() {
                                writeln!(file, "{}", domain).ok();
                            }
                            println!("✅ HTML: {}", domain);
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
    });

    Ok(())
}
