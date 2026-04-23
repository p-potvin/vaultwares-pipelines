## 2026-04-18 - API Key Bcrypt Hashing Migration
**Vulnerability:** API Keys were hashed using simple SHA-256 with a pepper, and verified using direct database lookups.
**Learning:** Bcrypt hashing relies on generating a unique random salt per hash. Thus, standard direct DB queries `hash == db.hash` do not work anymore. You must loop over active keys in the database and verify each one sequentially.
**Prevention:** When upgrading hash algorithms from un-salted fast hashes to salted slow hashes, always remember to rewrite the lookup logic to iterate over candidates and use the verifying function (e.g., `pwd_context.verify()`) rather than doing an exact database string match.

## 2026-04-18 - Subprocess Command Injection Prevention
**Vulnerability:** Subprocesses generating Git commits used string formatting to construct commit messages and passed them to `git commit -m`.
**Learning:** While `shell=False` protects against basic command injection (e.g. `&& rm -rf /`), parameter injection or argument confusion is still possible if untrusted input slips in.
**Prevention:** Use standard input streams for passing untrusted strings as data rather than command arguments. In the context of `git commit`, this means using `-F -` and passing the message via `subprocess.run(..., input=message_string)`.
## 2026-04-22 - [Sentinel] DoS Prevention in Rate Limiting\n**Vulnerability:** Memory Exhaustion DoS in gate_requests middleware\n**Learning:** In api_server.py, the rate limiting middleware used a defaultdict to store request times per IP. Without a maximum size limit and periodic eviction, an attacker could spoof thousands of IPs or generate unique origins to unbounded increase memory usage, leading to a server crash.\n**Prevention:** Always set an explicit size boundary (e.g. 10000 items) when tracking state per client in memory. Evict stale entries, and forcefully clear state if it exceeds safety limits, to guarantee stable memory footprints during abuse.

## $(date +%Y-%m-%d) - X-Forwarded-For IP Spoofing Prevention
**Vulnerability:** The `_get_client_ip` function parsed the leftmost IP from the `X-Forwarded-For` header. Because clients can easily spoof this header, an attacker could set it to a trusted internal IP (like `127.0.0.1`), effectively bypassing `_is_trusted_client_ip` authorization checks intended only for internal services.
**Learning:** In scenarios behind trusted reverse proxies (like Nginx), the proxy *appends* the actual client IP to the `X-Forwarded-For` chain. The leftmost IP is always untrusted user input and can be anything.
**Prevention:** Always extract the rightmost IP address from the `X-Forwarded-For` header (or iterate right-to-left stopping at the first untrusted proxy) to ensure you are validating the true connection IP, preventing IP spoofing vulnerabilities.
